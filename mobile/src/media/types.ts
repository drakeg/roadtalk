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
  createTransmitGrant(receiveGrantId: string): Promise<TransmitGrant>;
  publishTransmitTrack(
    transmitGrantId: string,
    trackRef: string,
  ): Promise<PublicationDelivery>;
  releaseGrant(grantId: string): Promise<void>;
};

export type TransmitGrant = {
  grantId: string;
  receiveGrantId: string;
  expiresAt: string;
};

export type PublicationDelivery = {
  transmitGrantId: string;
  deliveryState: "ready" | "no_nearby_listeners" | "reconciling" | "ended";
  expiresAt: string;
};

export type RoomConnectionHandlers = {
  reconnecting(): void;
  reconnected(): void;
  disconnected(): void;
  authorizedReceiveChanged(receiving: boolean): void;
};

export type ReceiveRoomAdapter = {
  connectReceiveOnly(
    grant: ReceiveGrant,
    handlers: RoomConnectionHandlers,
  ): Promise<void>;
  publishMicrophone(): Promise<string>;
  stopMicrophone(): Promise<void>;
  disconnect(): Promise<void>;
};

export type MediaLifecycleSnapshot =
  | { status: "purpose" }
  | { status: "checking" }
  | { status: "denied" }
  | { status: "blocked" }
  | { status: "unavailable" }
  | { status: "connecting" }
  | { status: "ready"; reason?: "maximum" }
  | { status: "receiving" }
  | { status: "authorizing" }
  | { status: "publishing" }
  | { status: "transmitting" }
  | { status: "nearby_unavailable" }
  | { status: "delivery_reconciling" }
  | { status: "busy" }
  | { status: "degraded" }
  | { status: "transmit_error" }
  | { status: "reconnecting" }
  | { status: "paused" }
  | { status: "error" };

export type MediaLifecycleControl = {
  subscribe(listener: () => void): () => void;
  getSnapshot(): MediaLifecycleSnapshot;
  enable(): Promise<void>;
  pressToTalk(): Promise<void>;
  releaseToTalk(): Promise<void>;
  pause(): Promise<void>;
  setAppActive(active: boolean): Promise<void>;
  setScreenActive(active: boolean): Promise<void>;
  setAuthenticated(authenticated: boolean): Promise<void>;
  dispose(): Promise<void>;
};
