import type { AuthApi } from "../session/api";
import { SessionClient } from "../session/SessionClient";
import type { SessionStorage } from "../session/storage";
import type { AnonymousSessionResponse, StoredSession } from "../session/types";

function stored(): StoredSession {
  return {
    accountId: "account-id",
    deviceId: "device-id",
    sessionId: "session-id",
    refreshToken: "old-refresh-token",
  };
}

function api() {
  return {
    register: jest.fn(),
    recover: jest.fn(),
    refresh: jest.fn(),
    logout: jest.fn(),
    revokeDevice: jest.fn(),
  };
}

function storage(initial: StoredSession | null = null) {
  let value = initial;
  return {
    readSession: jest.fn(async () => value),
    writeSession: jest.fn(async (session: StoredSession) => {
      value = session;
    }),
    clearSession: jest.fn(async () => {
      value = null;
    }),
    readInstallationId: jest.fn(async () => "installation-id"),
    writeInstallationId: jest.fn(async () => undefined),
  };
}

const created: AnonymousSessionResponse = {
  access_token: "access-token",
  refresh_token: "refresh-token",
  token_type: "bearer",
  expires_in: 900,
  account_id: "account-id",
  device_id: "device-id",
  session_id: "session-id",
};

describe("secure session client", () => {
  it("registers anonymously and keeps the access token in memory only", async () => {
    const remote = api();
    const secure = storage();
    remote.register.mockResolvedValue(created);
    const client = new SessionClient(
      remote as unknown as AuthApi,
      secure as SessionStorage,
      "ios",
    );

    await client.bootstrap();

    expect(client.getAccessToken()).toBe("access-token");
    expect(secure.writeSession).toHaveBeenCalledWith({
      accountId: "account-id",
      deviceId: "device-id",
      sessionId: "session-id",
      refreshToken: "refresh-token",
    });
    expect(JSON.stringify(secure.writeSession.mock.calls)).not.toContain(
      "access-token",
    );
  });

  it("rotates a stored refresh credential before authenticating", async () => {
    const remote = api();
    const secure = storage(stored());
    remote.refresh.mockResolvedValue({
      access_token: "new-access",
      refresh_token: "new-refresh",
      token_type: "bearer",
      expires_in: 900,
    });
    const client = new SessionClient(
      remote as unknown as AuthApi,
      secure as SessionStorage,
    );

    await client.bootstrap();

    expect(remote.refresh).toHaveBeenCalledWith("old-refresh-token");
    expect(client.getAccessToken()).toBe("new-access");
    expect(secure.writeSession).toHaveBeenCalledWith(
      expect.objectContaining({ refreshToken: "new-refresh" }),
    );
  });


  it("replaces the temporary session without persisting recovery material", async () => {
    const remote = api();
    const secure = storage();
    remote.register.mockResolvedValue(created);
    remote.recover.mockResolvedValue({
      access_token: "recovered-access",
      refresh_token: "recovered-refresh",
      token_type: "bearer",
      expires_in: 900,
      account_id: "recovered-account",
      device_id: "device-id",
      session_id: "recovered-session",
      recovery_key: "rtk1.rotated.secret",
      recovery_key_version: "rtk1",
    });
    const client = new SessionClient(
      remote as unknown as AuthApi,
      secure as SessionStorage,
      "ios",
    );
    await client.bootstrap();

    await expect(client.recover("rtk1.original.secret")).resolves.toEqual({
      recoveryKey: "rtk1.rotated.secret",
      recoveryKeyVersion: "rtk1",
    });

    expect(remote.recover).toHaveBeenCalledWith(
      "rtk1.original.secret",
      "installation-id",
      "ios",
    );
    expect(client.getAccessToken()).toBe("recovered-access");
    expect(client.getSnapshot()).toEqual({
      status: "authenticated",
      accountId: "recovered-account",
      deviceId: "device-id",
      sessionId: "recovered-session",
    });
    expect(secure.writeSession).toHaveBeenLastCalledWith({
      accountId: "recovered-account",
      deviceId: "device-id",
      sessionId: "recovered-session",
      refreshToken: "recovered-refresh",
    });
    expect(JSON.stringify(secure.writeSession.mock.calls)).not.toContain(
      "rtk1.",
    );
  });

  it("refreshes once when an authenticated identity request receives 401", async () => {
    const remote = api();
    const secure = storage();
    remote.register.mockResolvedValue(created);
    remote.refresh.mockResolvedValue({
      access_token: "rotated-access",
      refresh_token: "rotated-refresh",
      token_type: "bearer",
      expires_in: 900,
    });
    const fetcher = jest
      .fn()
      .mockResolvedValueOnce({ status: 401 })
      .mockResolvedValueOnce({ status: 200 });
    const client = new SessionClient(
      remote as unknown as AuthApi,
      secure as SessionStorage,
    );
    await client.bootstrap();

    await client.authenticatedFetch(
      "https://roadtalk.test/api/v1/me/profile",
      { method: "GET" },
      fetcher as typeof fetch,
    );

    expect(remote.refresh).toHaveBeenCalledWith("refresh-token");
    expect(fetcher).toHaveBeenCalledTimes(2);
    const firstHeaders = fetcher.mock.calls[0]?.[1]?.headers as Headers;
    const secondHeaders = fetcher.mock.calls[1]?.[1]?.headers as Headers;
    expect(firstHeaders.get("Authorization")).toBe("Bearer access-token");
    expect(secondHeaders.get("Authorization")).toBe("Bearer rotated-access");
    expect(JSON.stringify(secure.writeSession.mock.calls)).not.toContain(
      "rotated-access",
    );
  });

  it("clears credentials when refresh is rejected", async () => {
    const remote = api();
    const secure = storage(stored());
    remote.refresh.mockRejectedValue(new Error("revoked"));
    const client = new SessionClient(
      remote as unknown as AuthApi,
      secure as SessionStorage,
    );

    await client.bootstrap();

    expect(client.getAccessToken()).toBeNull();
    expect(secure.clearSession).toHaveBeenCalled();
    expect(client.getSnapshot().status).toBe("signed_out");
  });

  it("clears credentials if an authenticated request cannot refresh", async () => {
    const remote = api();
    const secure = storage();
    remote.register.mockResolvedValue(created);
    remote.refresh.mockRejectedValue(new Error("revoked"));
    const client = new SessionClient(
      remote as unknown as AuthApi,
      secure as SessionStorage,
    );
    await client.bootstrap();

    await expect(
      client.authenticatedFetch(
        "https://roadtalk.test/api/v1/me/profile",
        { method: "GET" },
        jest.fn(async () => ({ status: 401 })) as unknown as typeof fetch,
      ),
    ).rejects.toThrow("expired");

    expect(secure.clearSession).toHaveBeenCalled();
    expect(client.getSnapshot().status).toBe("signed_out");
  });

  it("attempts server logout and always clears local credentials", async () => {
    const remote = api();
    const secure = storage();
    remote.register.mockResolvedValue(created);
    remote.logout.mockRejectedValue(new Error("offline"));
    const client = new SessionClient(
      remote as unknown as AuthApi,
      secure as SessionStorage,
    );
    await client.bootstrap();

    await expect(client.logout()).resolves.toBeUndefined();

    expect(secure.clearSession).toHaveBeenCalled();
    expect(client.getAccessToken()).toBeNull();
  });
});
