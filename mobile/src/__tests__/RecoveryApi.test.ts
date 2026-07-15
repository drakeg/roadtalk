import { RecoveryApi, RecoveryApiError } from "../recovery/api";
import { ApiError } from "../session/api";
import type { SessionClient } from "../session/SessionClient";

function response(
  body: unknown,
  status = 200,
  headers: Record<string, string> = {},
): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers(headers),
    json: jest.fn(async () => body),
  } as unknown as Response;
}

describe("recovery API client", () => {
  it("creates a key through the authenticated in-memory token transport", async () => {
    const session = {
      authenticatedFetch: jest.fn(async () =>
        response({ recovery_key: "rtk1.selector.secret", key_version: "rtk1" }),
      ),
    } as unknown as SessionClient;
    const api = new RecoveryApi("https://roadtalk.test/api/v1", session);

    await expect(api.createRecoveryKey()).resolves.toEqual({
      recovery_key: "rtk1.selector.secret",
      key_version: "rtk1",
    });
    expect(session.authenticatedFetch).toHaveBeenCalledWith(
      "https://roadtalk.test/api/v1/me/recovery-key",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("delegates recovery to the session client without putting the key in a URL", async () => {
    const session = {
      recover: jest.fn(async () => ({
        recoveryKey: "rtk1.rotated.secret",
        recoveryKeyVersion: "rtk1" as const,
      })),
    } as unknown as SessionClient;
    const api = new RecoveryApi("https://roadtalk.test/api/v1", session);

    await api.recover("rtk1.original.secret");

    expect(session.recover).toHaveBeenCalledWith("rtk1.original.secret");
    expect(JSON.stringify(session)).not.toContain("rtk1.original.secret");
  });

  it("normalizes rate limits without exposing configured thresholds", async () => {
    const session = {
      recover: jest.fn(async () => {
        throw new ApiError(
          429,
          "RECOVERY_RATE_LIMITED",
          "Recovery requests are temporarily limited.",
          45,
        );
      }),
    } as unknown as SessionClient;
    const api = new RecoveryApi("https://roadtalk.test/api/v1", session);

    await expect(api.recover("invalid")).rejects.toEqual(
      expect.objectContaining<Partial<RecoveryApiError>>({
        status: 429,
        code: "RECOVERY_RATE_LIMITED",
        retryAfter: 45,
      }),
    );
  });
});
