export type LocationPrecision = "precise" | "approximate";

export type ForegroundPermission = {
  status: "granted" | "denied" | "undetermined";
  canAskAgain: boolean;
  precision: LocationPrecision | null;
};

export type LocationFix = {
  latitude: number;
  longitude: number;
  horizontalAccuracyM: number | null;
  headingDeg: number | null;
  speedMps: number | null;
  observedAtMs: number;
};

export type PublishedLocationSample = {
  observed_at: string;
  latitude: number;
  longitude: number;
  horizontal_accuracy_m: number;
  heading_deg: number | null;
  speed_mps: number | null;
  client_sequence: number;
  consent_policy_version: string;
};

export type NearbyBucket = "none" | "few" | "many";

export type NearbySummary = {
  availability: "available";
  bucket: NearbyBucket;
  freshness: "fresh";
  expiresAtMs: number;
};

export type LocalLocationState =
  | { status: "waiting" }
  | {
      status: "current" | "stale";
      horizontalAccuracyM: number;
      headingDeg: number | null;
      speedMps: number | null;
      observedAtMs: number;
    };

export type NearbyState =
  | { status: "waiting" | "unavailable" | "retrying" }
  | { status: "current"; bucket: NearbyBucket; expiresAtMs: number }
  | { status: "stale"; expiresAtMs: number };

export type LocationLifecycleSnapshot =
  | { status: "purpose" }
  | { status: "checking" }
  | { status: "unavailable" }
  | { status: "denied" }
  | { status: "blocked" }
  | { status: "paused" }
  | {
      status: "active";
      precision: LocationPrecision;
      upload: "waiting" | "current" | "retrying";
      local: LocalLocationState;
      nearby: NearbyState;
    }
  | { status: "error" };

export type LocationSubscription = {
  remove(): void;
};

export interface LocationGateway {
  hasServicesEnabled(): Promise<boolean>;
  getForegroundPermission(): Promise<ForegroundPermission>;
  requestForegroundPermission(): Promise<ForegroundPermission>;
  watch(
    onLocation: (fix: LocationFix) => void,
    onError: () => void,
  ): Promise<LocationSubscription>;
}

export interface LocationTransport {
  grantConsent(): Promise<void>;
  publish(sample: PublishedLocationSample): Promise<void>;
  pause(): Promise<void>;
  nearby(): Promise<NearbySummary | null>;
}

export interface LocationLifecycleControl {
  subscribe(listener: () => void): () => void;
  getSnapshot(): LocationLifecycleSnapshot;
  enable(): Promise<void>;
  pause(): Promise<void>;
  setAppActive(active: boolean): Promise<void>;
  setScreenActive(active: boolean): Promise<void>;
  setAuthenticated(authenticated: boolean): Promise<void>;
  dispose(): Promise<void>;
}
