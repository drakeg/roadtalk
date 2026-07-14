export type PublicIdentity = {
  callsign: string | null;
  avatar_id: string | null;
};

export type Profile = {
  identity: PublicIdentity;
  setup_completed: boolean;
  version: number;
};

export type CallsignAvailability = {
  available: boolean;
  reason: "available" | "invalid" | "reserved" | "taken";
};

export type ProfileUpdate = {
  version: number;
  callsign?: string;
  avatar_id?: string;
};
