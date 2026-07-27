export type MicrophonePermission = {
  status: "undetermined" | "granted" | "denied";
  canAskAgain: boolean;
};

export type MicrophonePermissionGateway = {
  isAvailable(): boolean;
  getPermission(): Promise<MicrophonePermission>;
  requestPermission(): Promise<MicrophonePermission>;
};

export type ReceiveGrant = {
  grantId: string;
  serverUrl: string;
  participantToken: string;
};

export type ReceiveGrantTransport = {
  createReceiveGrant(): Promise<ReceiveGrant>;
  releaseGrant(grantId: string): Promise<void>;
};

export type RoomConnectionHandlers = {
  reconnecting(): void;
  reconnected(): void;
  disconnected(): void;
};

export type ReceiveRoomAdapter = {
  connectReceiveOnly(
    grant: ReceiveGrant,
    handlers: RoomConnectionHandlers,
  ): Promise<void>;
  disconnect(): Promise<void>;
};

export type MediaLifecycleSnapshot =
  | { status: "purpose" }
  | { status: "checking" }
  | { status: "denied" }
  | { status: "blocked" }
  | { status: "unavailable" }
  | { status: "connecting" }
  | { status: "ready" }
  | { status: "reconnecting" }
  | { status: "paused" }
  | { status: "error" };

export type MediaLifecycleControl = {
  subscribe(listener: () => void): () => void;
  getSnapshot(): MediaLifecycleSnapshot;
  enable(): Promise<void>;
  pause(): Promise<void>;
  setAppActive(active: boolean): Promise<void>;
  setScreenActive(active: boolean): Promise<void>;
  setAuthenticated(authenticated: boolean): Promise<void>;
  dispose(): Promise<void>;
};
