import * as SecureStore from "expo-secure-store";

import type { StoredSession } from "./types";

const SESSION_KEY = "roadtalk.session.v1";
const INSTALLATION_KEY = "roadtalk.installation.v1";
const options: SecureStore.SecureStoreOptions = {
  keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
};

export type SessionStorage = {
  readSession(): Promise<StoredSession | null>;
  writeSession(session: StoredSession): Promise<void>;
  clearSession(): Promise<void>;
  readInstallationId(): Promise<string | null>;
  writeInstallationId(value: string): Promise<void>;
};

export const secureSessionStorage: SessionStorage = {
  async readSession() {
    const value = await SecureStore.getItemAsync(SESSION_KEY, options);
    return value === null ? null : (JSON.parse(value) as StoredSession);
  },
  async writeSession(session) {
    await SecureStore.setItemAsync(SESSION_KEY, JSON.stringify(session), options);
  },
  async clearSession() {
    await SecureStore.deleteItemAsync(SESSION_KEY, options);
  },
  readInstallationId() {
    return SecureStore.getItemAsync(INSTALLATION_KEY, options);
  },
  writeInstallationId(value) {
    return SecureStore.setItemAsync(INSTALLATION_KEY, value, options);
  },
};
