import { LOCATION_POLICY_VERSION } from "./api";
import type {
  ForegroundPermission,
  LocationFix,
  LocationGateway,
  LocationLifecycleControl,
  LocationLifecycleSnapshot,
  LocationPrecision,
  LocationSubscription,
  LocationTransport,
  LocalLocationState,
  NearbyState,
  PublishedLocationSample,
} from "./types";

type Clock = { now(): number };
type Listener = () => void;
type TimerHandle = ReturnType<typeof setTimeout>;
type Scheduler = {
  setTimeout(callback: () => void, delayMs: number): TimerHandle;
  clearTimeout(handle: TimerHandle): void;
};

const systemClock: Clock = { now: () => Date.now() };
const systemScheduler: Scheduler = {
  setTimeout: (callback, delayMs) => {
    const handle = setTimeout(callback, delayMs);
    if (typeof handle === "object" && "unref" in handle) {
      handle.unref();
    }
    return handle;
  },
  clearTimeout: (handle) => clearTimeout(handle),
};

export class LocationLifecycleController implements LocationLifecycleControl {
  private snapshot: LocationLifecycleSnapshot = { status: "purpose" };
  private readonly listeners = new Set<Listener>();
  private subscription: LocationSubscription | null = null;
  private enabled = false;
  private appActive = false;
  private screenActive = false;
  private authenticated = false;
  private disposed = false;
  private starting = false;
  private uploadInFlight = false;
  private nearbyRequestGeneration: number | null = null;
  private precision: LocationPrecision = "precise";
  private upload: "waiting" | "current" | "retrying" = "waiting";
  private local: LocalLocationState = { status: "waiting" };
  private nearby: NearbyState = { status: "waiting" };
  private sequence = 0;
  private lastUploadAtMs: number | null = null;
  private nearbyTimer: TimerHandle | null = null;
  private localStaleTimer: TimerHandle | null = null;
  private generation = 0;

  constructor(
    private readonly gateway: LocationGateway,
    private readonly transport: LocationTransport,
    private readonly clock: Clock = systemClock,
    private readonly minimumUploadIntervalMs = 10_000,
    private readonly nearbyPollIntervalMs = 30_000,
    private readonly localFreshnessMs = 30_000,
    private readonly scheduler: Scheduler = systemScheduler,
  ) {}

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  getSnapshot(): LocationLifecycleSnapshot {
    return this.snapshot;
  }

  async enable(): Promise<void> {
    if (this.disposed || !this.authenticated) {
      return;
    }
    this.publish({ status: "checking" });
    try {
      if (!(await this.gateway.hasServicesEnabled())) {
        this.publish({ status: "unavailable" });
        return;
      }
      let permission = await this.gateway.getForegroundPermission();
      if (permission.status !== "granted" && permission.canAskAgain) {
        permission = await this.gateway.requestForegroundPermission();
      }
      if (!this.acceptPermission(permission)) {
        return;
      }

      await this.transport.grantConsent();
      await this.safeRemotePause();
      this.enabled = true;
      this.resetExperience();
      this.publishActive();
      await this.reconcile();
    } catch {
      this.enabled = false;
      this.publish({ status: "error" });
    }
  }

  async pause(): Promise<void> {
    this.enabled = false;
    this.stopSubscription();
    this.resetExperience();
    await this.safeRemotePause();
    if (!this.disposed) {
      this.publish({ status: "paused" });
    }
  }

  async setAppActive(active: boolean): Promise<void> {
    this.appActive = active;
    await this.reconcile();
  }

  async setScreenActive(active: boolean): Promise<void> {
    this.screenActive = active;
    await this.reconcile();
  }

  async setAuthenticated(authenticated: boolean): Promise<void> {
    this.authenticated = authenticated;
    await this.reconcile();
  }

  async dispose(): Promise<void> {
    if (this.disposed) {
      return;
    }
    this.disposed = true;
    this.enabled = false;
    this.stopSubscription();
    this.resetExperience();
    await this.safeRemotePause();
    this.listeners.clear();
  }

  private acceptPermission(permission: ForegroundPermission): boolean {
    if (permission.status !== "granted" || permission.precision === null) {
      this.publish({
        status: permission.canAskAgain ? "denied" : "blocked",
      });
      return false;
    }
    this.precision = permission.precision;
    return true;
  }

  private async reconcile(): Promise<void> {
    const shouldWatch =
      this.enabled &&
      this.appActive &&
      this.screenActive &&
      this.authenticated &&
      !this.disposed;
    if (!shouldWatch) {
      const hadSubscription = this.subscription !== null;
      this.stopSubscription();
      if (hadSubscription) {
        this.resetExperience();
        await this.safeRemotePause();
        if (!this.disposed && this.enabled) {
          this.publishActive();
        }
      }
      return;
    }
    if (this.subscription !== null || this.starting) {
      return;
    }
    this.starting = true;
    try {
      const subscription = await this.gateway.watch(
        (fix) => void this.handleFix(fix),
        () => this.handleWatchError(),
      );
      if (
        this.disposed ||
        !this.enabled ||
        !this.appActive ||
        !this.screenActive ||
        !this.authenticated
      ) {
        subscription.remove();
        return;
      }
      this.subscription = subscription;
    } catch {
      this.publish({ status: "error" });
    } finally {
      this.starting = false;
    }
  }

  private stopSubscription(): void {
    this.generation += 1;
    if (this.subscription !== null) {
      this.subscription.remove();
    }
    this.subscription = null;
    this.clearTimers();
  }

  private async safeRemotePause(): Promise<void> {
    if (!this.authenticated) {
      return;
    }
    try {
      await this.transport.pause();
    } catch {
      // Local foreground collection always stops even if the API is unreachable.
    }
  }

  private handleWatchError(): void {
    if (!this.disposed && this.enabled) {
      void this.failAndStop();
    }
  }

  private async failAndStop(): Promise<void> {
    this.enabled = false;
    this.stopSubscription();
    this.resetExperience();
    await this.safeRemotePause();
    if (!this.disposed) {
      this.publish({ status: "error" });
    }
  }

  private async handleFix(fix: LocationFix): Promise<void> {
    if (!this.canUpload(fix)) {
      return;
    }
    const now = this.clock.now();
    this.local = {
      status:
        now - fix.observedAtMs >= this.localFreshnessMs ? "stale" : "current",
      horizontalAccuracyM: fix.horizontalAccuracyM,
      headingDeg: this.optionalHeading(fix.headingDeg),
      speedMps: this.optionalNonnegative(fix.speedMps),
      observedAtMs: fix.observedAtMs,
    };
    this.scheduleLocalStale();
    this.publishActive();
    if (
      this.uploadInFlight ||
      (this.lastUploadAtMs !== null &&
        now - this.lastUploadAtMs < this.minimumUploadIntervalMs)
    ) {
      return;
    }

    const nextSequence = this.sequence + 1;
    const sample: PublishedLocationSample = {
      observed_at: new Date(fix.observedAtMs).toISOString(),
      latitude: fix.latitude,
      longitude: fix.longitude,
      horizontal_accuracy_m: fix.horizontalAccuracyM,
      heading_deg: this.optionalHeading(fix.headingDeg),
      speed_mps: this.optionalNonnegative(fix.speedMps),
      client_sequence: nextSequence,
      consent_policy_version: LOCATION_POLICY_VERSION,
    };
    this.uploadInFlight = true;
    const generation = this.generation;
    try {
      await this.transport.publish(sample);
      if (generation !== this.generation || !this.enabled) {
        await this.safeRemotePause();
        return;
      }
      this.sequence = nextSequence;
      this.lastUploadAtMs = now;
      this.upload = "current";
      this.publishActive();
      if (this.nearby.status === "waiting") {
        void this.refreshNearby();
      }
    } catch {
      this.upload = "retrying";
      this.publishActive();
    } finally {
      this.uploadInFlight = false;
    }
  }

  private canUpload(fix: LocationFix): fix is LocationFix & {
    horizontalAccuracyM: number;
  } {
    return (
      this.enabled &&
      this.subscription !== null &&
      Number.isFinite(fix.latitude) &&
      Number.isFinite(fix.longitude) &&
      fix.horizontalAccuracyM !== null &&
      Number.isFinite(fix.horizontalAccuracyM) &&
      fix.horizontalAccuracyM >= 0 &&
      Number.isFinite(fix.observedAtMs)
    );
  }

  private optionalNonnegative(value: number | null): number | null {
    return value !== null && Number.isFinite(value) && value >= 0 ? value : null;
  }

  private optionalHeading(value: number | null): number | null {
    return value !== null && Number.isFinite(value) && value >= 0 && value < 360
      ? value
      : null;
  }

  private async refreshNearby(): Promise<void> {
    if (!this.canPollNearby() || this.nearbyRequestGeneration !== null) {
      return;
    }
    const generation = this.generation;
    this.nearbyRequestGeneration = generation;
    try {
      const summary = await this.transport.nearby();
      if (generation !== this.generation || !this.canPollNearby()) {
        return;
      }
      if (summary === null) {
        this.nearby = { status: "unavailable" };
      } else if (summary.expiresAtMs <= this.clock.now()) {
        this.nearby = { status: "stale", expiresAtMs: summary.expiresAtMs };
      } else {
        this.nearby = {
          status: "current",
          bucket: summary.bucket,
          expiresAtMs: summary.expiresAtMs,
        };
      }
      this.publishActive();
    } catch {
      if (generation !== this.generation || !this.canPollNearby()) {
        return;
      }
      if (
        this.nearby.status === "current" &&
        this.nearby.expiresAtMs <= this.clock.now()
      ) {
        this.nearby = {
          status: "stale",
          expiresAtMs: this.nearby.expiresAtMs,
        };
      } else if (this.nearby.status !== "current") {
        this.nearby = { status: "retrying" };
      }
      this.publishActive();
    } finally {
      if (this.nearbyRequestGeneration === generation) {
        this.nearbyRequestGeneration = null;
      }
      if (generation === this.generation && this.canPollNearby()) {
        this.scheduleNearbyPoll();
      }
    }
  }

  private canPollNearby(): boolean {
    return this.canRunExperience() && this.upload === "current";
  }

  private canRunExperience(): boolean {
    return (
      this.enabled &&
      this.subscription !== null &&
      this.appActive &&
      this.screenActive &&
      this.authenticated &&
      !this.disposed
    );
  }

  private scheduleNearbyPoll(): void {
    if (this.nearbyTimer !== null) {
      this.scheduler.clearTimeout(this.nearbyTimer);
    }
    let delayMs = this.nearbyPollIntervalMs;
    if (this.nearby.status === "current") {
      delayMs = Math.min(
        delayMs,
        Math.max(0, this.nearby.expiresAtMs - this.clock.now()),
      );
    }
    this.nearbyTimer = this.scheduler.setTimeout(() => {
      this.nearbyTimer = null;
      void this.refreshNearby();
    }, delayMs);
  }

  private scheduleLocalStale(): void {
    if (this.localStaleTimer !== null) {
      this.scheduler.clearTimeout(this.localStaleTimer);
      this.localStaleTimer = null;
    }
    if (this.local.status !== "current") {
      return;
    }
    const delayMs = Math.max(
      0,
      Math.min(
        this.localFreshnessMs,
        this.local.observedAtMs + this.localFreshnessMs - this.clock.now(),
      ),
    );
    this.localStaleTimer = this.scheduler.setTimeout(() => {
      this.localStaleTimer = null;
      if (this.local.status === "current" && this.canRunExperience()) {
        this.local = { ...this.local, status: "stale" };
        this.publishActive();
      }
    }, delayMs);
  }

  private clearTimers(): void {
    if (this.nearbyTimer !== null) {
      this.scheduler.clearTimeout(this.nearbyTimer);
      this.nearbyTimer = null;
    }
    if (this.localStaleTimer !== null) {
      this.scheduler.clearTimeout(this.localStaleTimer);
      this.localStaleTimer = null;
    }
  }

  private resetExperience(): void {
    this.upload = "waiting";
    this.local = { status: "waiting" };
    this.nearby = { status: "waiting" };
    this.nearbyRequestGeneration = null;
    this.clearTimers();
  }

  private publishActive(): void {
    if (!this.disposed && this.enabled) {
      this.publish({
        status: "active",
        precision: this.precision,
        upload: this.upload,
        local: this.local,
        nearby: this.nearby,
      });
    }
  }

  private publish(snapshot: LocationLifecycleSnapshot): void {
    this.snapshot = snapshot;
    this.listeners.forEach((listener) => listener());
  }
}
