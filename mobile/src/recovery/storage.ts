import * as SecureStore from "expo-secure-store";

const RECOVERY_KEY = "roadtalk.recovery-key.v1";
const options: SecureStore.SecureStoreOptions = {
  keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
};

export type RecoveryKeyStorage = {
  writeRecoveryKey(value: string): Promise<void>;
  clearRecoveryKey(): Promise<void>;
};

export const secureRecoveryKeyStorage: RecoveryKeyStorage = {
  writeRecoveryKey(value) {
    return SecureStore.setItemAsync(RECOVERY_KEY, value, options);
  },
  clearRecoveryKey() {
    return SecureStore.deleteItemAsync(RECOVERY_KEY, options);
  },
};
