import { randomUUID } from "expo-crypto";
import { Platform } from "react-native";

import { AuthApi } from "./api";
import type { SessionStorage } from "./storage";
import type { SessionSnapshot, StoredSession, TokenPair } from "./types";

type Listener = (snapshot: SessionSnapshot) => void;

export class SessionClient {
  private accessToken: string | null = null;
  private session: StoredSession | null = null;
  private snapshot: SessionSnapshot = { status: "loading" };
  private readonly listeners = new Set<Listener>();

  constructor(
    private readonly api: AuthApi,
    private readonly storage: SessionStorage,
    private readonly platform: "android" | "ios" =
      Platform.OS === "ios" ? "ios" : "android",
    private readonly createInstallationId: () => string = randomUUID,
  ) {}

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    listener(this.snapshot);
    return () => this.listeners.delete(listener);
  }

  getSnapshot(): SessionSnapshot {
    return this.snapshot;
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }

  async bootstrap(): Promise<void> {
    const stored = await this.storage.readSession();
    if (stored === null) {
      await this.register();
      return;
    }
    this.session = stored;
    try {
      const pair = await this.api.refresh(stored.refreshToken);
      await this.acceptRotation(pair);
    } catch {
      await this.clear("Your session expired. Connect again to continue.");
    }
  }

  async register(): Promise<void> {
    let installationId = await this.storage.readInstallationId();
    if (installationId === null) {
      installationId = this.createInstallationId();
      await this.storage.writeInstallationId(installationId);
    }
    const created = await this.api.register(installationId, this.platform);
    this.accessToken = created.access_token;
    this.session = {
      accountId: created.account_id,
      deviceId: created.device_id,
      sessionId: created.session_id,
      refreshToken: created.refresh_token,
    };
    await this.storage.writeSession(this.session);
    this.publishAuthenticated();
  }

  async refresh(): Promise<string> {
    if (this.session === null) {
      throw new Error("No authenticated session.");
    }
    const pair = await this.api.refresh(this.session.refreshToken);
    await this.acceptRotation(pair);
    return pair.access_token;
  }

  async logout(): Promise<void> {
    const token = this.accessToken;
    try {
      if (token !== null) {
        await this.api.logout(token);
      }
    } catch {
      // Local credential removal must not depend on network availability.
    } finally {
      await this.clear();
    }
  }

  async revokeCurrentDevice(): Promise<void> {
    if (this.accessToken === null || this.session === null) {
      await this.clear();
      return;
    }
    try {
      await this.api.revokeDevice(this.accessToken, this.session.deviceId);
    } catch {
      // The server will expire unreachable credentials; always clear this device.
    } finally {
      await this.clear();
    }
  }

  private async acceptRotation(pair: TokenPair): Promise<void> {
    if (this.session === null) {
      throw new Error("Cannot rotate a missing session.");
    }
    this.accessToken = pair.access_token;
    this.session = { ...this.session, refreshToken: pair.refresh_token };
    await this.storage.writeSession(this.session);
    this.publishAuthenticated();
  }

  private publishAuthenticated(): void {
    if (this.session === null) {
      return;
    }
    this.publish({
      status: "authenticated",
      accountId: this.session.accountId,
      deviceId: this.session.deviceId,
      sessionId: this.session.sessionId,
    });
  }

  private async clear(message?: string): Promise<void> {
    this.accessToken = null;
    this.session = null;
    await this.storage.clearSession();
    this.publish(
      message === undefined
        ? { status: "signed_out" }
        : { status: "signed_out", message },
    );
  }

  private publish(snapshot: SessionSnapshot): void {
    this.snapshot = snapshot;
    this.listeners.forEach((listener) => listener(snapshot));
  }
}
