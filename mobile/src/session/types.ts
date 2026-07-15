export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
};

export type AnonymousSessionResponse = TokenPair & {
  account_id: string;
  device_id: string;
  session_id: string;
};

export type RecoverySessionResponse = AnonymousSessionResponse & {
  recovery_key: string;
  recovery_key_version: "rtk1";
};

export type RecoveryResult = {
  recoveryKey: string;
  recoveryKeyVersion: "rtk1";
};

export type StoredSession = {
  accountId: string;
  deviceId: string;
  sessionId: string;
  refreshToken: string;
};

export type SessionSnapshot =
  | { status: "loading" }
  | { status: "signed_out"; message?: string }
  | {
      status: "authenticated";
      accountId: string;
      deviceId: string;
      sessionId: string;
    };
