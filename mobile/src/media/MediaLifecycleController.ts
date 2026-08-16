import type {
  MediaLifecycleControl,
  MediaLifecycleSnapshot,
  MicrophonePermission,
  MicrophonePermissionGateway,
  ReceiveGrantTransport,
  ReceiveRoomAdapter,
} from "./types";
import { MediaGrantError } from "./api";

type Listener = () => void;
type TimerHandle = ReturnType<typeof setTimeout>;
type Scheduler = {
  setTimeout(callback: () => void, delayMs: number): TimerHandle;
  clearTimeout(handle: TimerHandle): void;
};

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

export class MediaLifecycleController implements MediaLifecycleControl {
  private snapshot: MediaLifecycleSnapshot = { status: "purpose" };
  private readonly listeners = new Set<Listener>();
  private enabled = false;
  private appActive = false;
  private screenActive = false;
  private authenticated = false;
  private connecting = false;
  private connected = false;
  private disposed = false;
  private permissionConfirmed = false;
  private grantId: string | null = null;
  private transmitGrantId: string | null = null;
  private transmitTimer: TimerHandle | null = null;
  private held = false;
  private remoteReceiving = false;
  private generation = 0;
  private transmitGeneration = 0;
  private microphoneOperation: Promise<unknown> = Promise.resolve();
  private resumeAfterChannelTransition = false;

  constructor(
    private readonly permission: MicrophonePermissionGateway,
    private readonly transport: ReceiveGrantTransport,
    private readonly room: ReceiveRoomAdapter,
    private readonly scheduler: Scheduler = systemScheduler,
    private readonly maximumTransmitMs = 30_000,
  ) {}

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  getSnapshot(): MediaLifecycleSnapshot {
    return this.snapshot;
  }

  async enable(): Promise<void> {
    if (this.disposed || !this.authenticated) {
      return;
    }
    this.enabled = true;
    this.publish({ status: "checking" });
    try {
      if (!this.permission.isAvailable()) {
        this.enabled = false;
        this.publish({ status: "unavailable" });
        return;
      }
      let permission = await this.permission.getPermission();
      if (permission.status !== "granted" && permission.canAskAgain) {
        permission = await this.permission.requestPermission();
      }
      if (!this.acceptPermission(permission)) {
        this.enabled = false;
        return;
      }
      this.permissionConfirmed = true;
      await this.reconcile();
    } catch {
      await this.failAndStop();
    }
  }

  async pause(): Promise<void> {
    this.enabled = false;
    await this.stop();
    if (!this.disposed) {
      this.publish({ status: "paused" });
    }
  }

  async pressToTalk(): Promise<void> {
    if (
      this.disposed ||
      !this.connected ||
      this.grantId === null ||
      this.held ||
      ![
        "ready",
        "receiving",
        "busy",
        "degraded",
        "nearby_unavailable",
        "delivery_reconciling",
        "transmit_error",
      ].includes(this.snapshot.status)
    ) {
      return;
    }
    this.held = true;
    const generation = ++this.transmitGeneration;
    const receiveGrantId = this.grantId;
    this.publish({ status: "authorizing" });
    try {
      const transmit = await this.transport.createTransmitGrant(receiveGrantId);
      if (!this.canStartTransmission(generation, receiveGrantId)) {
        await this.safeRelease(transmit.grantId);
        return;
      }
      this.transmitGrantId = transmit.grantId;
      const trackRef = await this.publishMicrophone();
      if (!this.canStartTransmission(generation, receiveGrantId)) {
        await this.stopTransmission();
        return;
      }
      this.publish({ status: "publishing" });
      const delivery = await this.transport.publishTransmitTrack(
        transmit.grantId,
        trackRef,
      );
      if (!this.canStartTransmission(generation, receiveGrantId)) {
        await this.stopTransmission();
        return;
      }
      if (delivery.deliveryState !== "ready") {
        this.held = false;
        await this.stopTransmission();
        this.publish({
          status:
            delivery.deliveryState === "no_nearby_listeners"
              ? "nearby_unavailable"
              : delivery.deliveryState === "reconciling"
                ? "delivery_reconciling"
                : "transmit_error",
        });
        return;
      }
      this.transmitTimer = this.scheduler.setTimeout(() => {
        void this.maximumReached();
      }, this.maximumTransmitMs);
      this.publish({ status: "transmitting" });
    } catch (error) {
      await this.handleTransmitFailure(error, generation);
    }
  }

  async releaseToTalk(): Promise<void> {
    this.held = false;
    this.transmitGeneration += 1;
    await this.stopTransmission();
    if (this.connected && !this.disposed) {
      this.publishReceiveState();
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
    if (!authenticated) {
      this.enabled = false;
      await this.stop();
      if (!this.disposed) {
        this.publish({ status: "paused" });
      }
      return;
    }
    await this.reconcile();
  }

  async prepareChannelTransition(): Promise<void> {
    if (this.disposed) return;
    this.resumeAfterChannelTransition = this.enabled;
    await this.stop();
    this.publish({ status: "paused" });
  }

  async completeChannelTransition(): Promise<void> {
    if (this.disposed) return;
    const resume = this.resumeAfterChannelTransition;
    this.resumeAfterChannelTransition = false;
    if (!resume) return;
    this.enabled = true;
    await this.reconcile();
  }

  async dispose(): Promise<void> {
    if (this.disposed) {
      return;
    }
    this.disposed = true;
    this.enabled = false;
    this.resumeAfterChannelTransition = false;
    await this.stop();
    this.listeners.clear();
  }

  private acceptPermission(permission: MicrophonePermission): boolean {
    if (permission.status === "granted") {
      return true;
    }
    this.publish({
      status: permission.canAskAgain ? "denied" : "blocked",
    });
    return false;
  }

  private async reconcile(): Promise<void> {
    const shouldConnect =
      this.enabled &&
      this.appActive &&
      this.screenActive &&
      this.authenticated &&
      !this.disposed;
    if (!shouldConnect) {
      if (this.connected || this.connecting || this.grantId !== null) {
        await this.stop();
        if (!this.disposed && this.enabled) {
          this.publish({ status: "paused" });
        }
      }
      return;
    }
    if (this.connected || this.connecting) {
      return;
    }
    if (!this.permissionConfirmed) {
      if (!this.permission.isAvailable()) {
        this.enabled = false;
        this.publish({ status: "unavailable" });
        return;
      }
      try {
        const permission = await this.permission.getPermission();
        if (!this.acceptPermission(permission)) {
          this.enabled = false;
          return;
        }
        this.permissionConfirmed = true;
      } catch {
        await this.failAndStop();
        return;
      }
    }

    const generation = ++this.generation;
    this.connecting = true;
    this.publish({ status: "connecting" });
    try {
      const grant = await this.transport.createReceiveGrant();
      if (!this.isCurrent(generation)) {
        await this.safeRelease(grant.grantId);
        return;
      }
      this.grantId = grant.grantId;
      await this.room.connectReceiveOnly(grant, {
        reconnecting: () => {
          if (this.isCurrent(generation)) {
            void this.handleReconnecting(generation);
          }
        },
        reconnected: () => {
          if (this.isCurrent(generation)) {
            this.publishReceiveState();
          }
        },
        disconnected: () => {
          if (this.isCurrent(generation)) {
            void this.failAndStop();
          }
        },
        authorizedReceiveChanged: (receiving) => {
          if (this.isCurrent(generation)) {
            this.remoteReceiving = receiving;
            if (
              this.snapshot.status === "ready" ||
              this.snapshot.status === "receiving"
            ) {
              this.publishReceiveState();
            }
          }
        },
      });
      if (!this.isCurrent(generation)) {
        await this.stop();
        return;
      }
      this.connected = true;
      this.publishReceiveState();
    } catch {
      if (this.isCurrent(generation)) {
        await this.failAndStop();
      }
    } finally {
      this.connecting = false;
    }
  }

  private isCurrent(generation: number): boolean {
    return (
      generation === this.generation &&
      this.enabled &&
      this.appActive &&
      this.screenActive &&
      this.authenticated &&
      !this.disposed
    );
  }

  private async failAndStop(): Promise<void> {
    this.enabled = false;
    await this.stop();
    if (!this.disposed) {
      this.publish({ status: "error" });
    }
  }

  private async stop(): Promise<void> {
    this.generation += 1;
    this.held = false;
    this.transmitGeneration += 1;
    this.connecting = false;
    this.connected = false;
    this.permissionConfirmed = false;
    this.remoteReceiving = false;
    const grantId = this.grantId;
    this.grantId = null;
    await this.stopTransmission();
    try {
      await this.room.disconnect();
    } catch {
      // Local state must fail closed even if native cleanup reports an error.
    }
    if (grantId !== null) {
      await this.safeRelease(grantId);
    }
  }

  private canStartTransmission(
    generation: number,
    receiveGrantId: string,
  ): boolean {
    return (
      generation === this.transmitGeneration &&
      this.held &&
      this.connected &&
      this.grantId === receiveGrantId &&
      this.isCurrent(this.generation)
    );
  }

  private async maximumReached(): Promise<void> {
    this.held = false;
    this.transmitGeneration += 1;
    await this.stopTransmission();
    if (this.connected && !this.disposed) {
      this.publish({ status: "ready", reason: "maximum" });
    }
  }

  private async handleReconnecting(generation: number): Promise<void> {
    this.held = false;
    this.transmitGeneration += 1;
    await this.stopTransmission();
    if (this.isCurrent(generation)) {
      this.publish({ status: "reconnecting" });
    }
  }

  private async handleTransmitFailure(
    error: unknown,
    generation: number,
  ): Promise<void> {
    this.held = false;
    await this.stopTransmission();
    if (
      generation !== this.transmitGeneration ||
      !this.connected ||
      this.disposed
    ) {
      return;
    }
    if (error instanceof MediaGrantError) {
      if (error.code === "PTT_TRANSMIT_BUSY") {
        this.publish({ status: "busy" });
        return;
      }
      if (error.code === "PTT_NO_NEARBY_LISTENERS") {
        this.publish({ status: "nearby_unavailable" });
        return;
      }
      if (error.code === "PTT_DELIVERY_RECONCILING") {
        this.publish({ status: "delivery_reconciling" });
        return;
      }
      if (
        error.code === "PTT_PROVIDER_UNAVAILABLE" ||
        error.code === "PTT_RATE_LIMITED"
      ) {
        this.publish({ status: "degraded" });
        return;
      }
    }
    try {
      const permission = await this.permission.getPermission();
      if (permission.status !== "granted") {
        this.enabled = false;
        await this.stop();
        this.publish({
          status: permission.canAskAgain ? "denied" : "blocked",
        });
        return;
      }
    } catch {
      // A permission check failure remains a generic fail-closed media error.
    }
    this.publish({ status: "transmit_error" });
  }

  private async stopTransmission(): Promise<void> {
    if (this.transmitTimer !== null) {
      this.scheduler.clearTimeout(this.transmitTimer);
      this.transmitTimer = null;
    }
    const transmitGrantId = this.transmitGrantId;
    this.transmitGrantId = null;
    try {
      // Capture is always disabled before any remote cleanup attempt.
      await this.stopMicrophone();
    } catch {
      // Continue server-side revocation even if native capture cleanup reports.
    }
    if (transmitGrantId !== null) {
      await this.safeRelease(transmitGrantId);
    }
  }

  private publishReceiveState(): void {
    this.publish({
      status: this.remoteReceiving ? "receiving" : "ready",
    });
  }

  private async safeRelease(grantId: string): Promise<void> {
    try {
      await this.transport.releaseGrant(grantId);
    } catch {
      // The short-lived server grant expires independently of client cleanup.
    }
  }

  private publishMicrophone(): Promise<string> {
    const operation = this.microphoneOperation
      .catch(() => undefined)
      .then(() => this.room.publishMicrophone());
    this.microphoneOperation = operation.catch(() => undefined);
    return operation;
  }

  private stopMicrophone(): Promise<void> {
    const operation = this.microphoneOperation
      .catch(() => undefined)
      .then(() => this.room.stopMicrophone());
    this.microphoneOperation = operation.catch(() => undefined);
    return operation;
  }

  private publish(snapshot: MediaLifecycleSnapshot): void {
    this.snapshot = snapshot;
    this.listeners.forEach((listener) => listener());
  }
}
