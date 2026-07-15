export type RecoveryKeyResponse = {
  recovery_key: string;
  key_version: "rtk1";
};

export type OneTimeRecoveryKey = {
  value: string;
  version: "rtk1";
  savedOnDevice: boolean;
};
