import type {
  MediaLifecycleControl,
  MediaLifecycleSnapshot,
  MicrophonePermission,
  MicrophonePermissionGateway,
  ReceiveGrantTransport,
  ReceiveRoomAdapter,
} from "./types";

type Listener = () => void;

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
  private generation = 0;

  constructor(
    private readonly permission: MicrophonePermissionGateway,
    private readonly transport: ReceiveGrantTransport,
    private readonly room: ReceiveRoomAdapter,
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

  async dispose(): Promise<void> {
    if (this.disposed) {
      return;
    }
    this.disposed = true;
    this.enabled = false;
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
            this.publish({ status: "reconnecting" });
          }
        },
        reconnected: () => {
          if (this.isCurrent(generation)) {
            this.publish({ status: "ready" });
          }
        },
        disconnected: () => {
          if (this.isCurrent(generation)) {
            void this.failAndStop();
          }
        },
      });
      if (!this.isCurrent(generation)) {
        await this.stop();
        return;
      }
      this.connected = true;
      this.publish({ status: "ready" });
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
    this.connecting = false;
    this.connected = false;
    this.permissionConfirmed = false;
    const grantId = this.grantId;
    this.grantId = null;
    try {
      await this.room.disconnect();
    } catch {
      // Local state must fail closed even if native cleanup reports an error.
    }
    if (grantId !== null) {
      await this.safeRelease(grantId);
    }
  }

  private async safeRelease(grantId: string): Promise<void> {
    try {
      await this.transport.releaseGrant(grantId);
    } catch {
      // The short-lived server grant expires independently of client cleanup.
    }
  }

  private publish(snapshot: MediaLifecycleSnapshot): void {
    this.snapshot = snapshot;
    this.listeners.forEach((listener) => listener());
  }
}
