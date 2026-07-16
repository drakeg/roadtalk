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
  PublishedLocationSample,
} from "./types";

type Clock = { now(): number };
type Listener = () => void;

const systemClock: Clock = { now: () => Date.now() };

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
  private precision: LocationPrecision = "precise";
  private sequence = 0;
  private lastUploadAtMs: number | null = null;
  private generation = 0;

  constructor(
    private readonly gateway: LocationGateway,
    private readonly transport: LocationTransport,
    private readonly clock: Clock = systemClock,
    private readonly minimumUploadIntervalMs = 10_000,
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
      this.publish({
        status: "active",
        precision: this.precision,
        upload: "waiting",
      });
      await this.reconcile();
    } catch {
      this.enabled = false;
      this.publish({ status: "error" });
    }
  }

  async pause(): Promise<void> {
    this.enabled = false;
    this.stopSubscription();
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
        await this.safeRemotePause();
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
    if (this.subscription !== null) {
      this.generation += 1;
      this.subscription.remove();
    }
    this.subscription = null;
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
      this.publish({
        status: "active",
        precision: this.precision,
        upload: "current",
      });
    } catch {
      this.publish({
        status: "active",
        precision: this.precision,
        upload: "retrying",
      });
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

  private publish(snapshot: LocationLifecycleSnapshot): void {
    this.snapshot = snapshot;
    this.listeners.forEach((listener) => listener());
  }
}
