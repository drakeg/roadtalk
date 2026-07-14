import { IdentityApi, IdentityApiError } from "../identity/api";
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

describe("identity API client", () => {
  it("uses the authenticated transport and URL-encodes callsigns", async () => {
    const session = {
      authenticatedFetch: jest.fn(async () =>
        response({ available: true, reason: "available" }),
      ),
    } as unknown as SessionClient;
    const api = new IdentityApi("https://roadtalk.test/api/v1", session);

    await expect(api.checkCallsign("Road Runner")).resolves.toEqual({
      available: true,
      reason: "available",
    });
    expect(session.authenticatedFetch).toHaveBeenCalledWith(
      "https://roadtalk.test/api/v1/callsigns/availability?callsign=Road%20Runner",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("sends only the profile fields explicitly supplied", async () => {
    const session = {
      authenticatedFetch: jest.fn(async () =>
        response({
          identity: { callsign: "Road-Runner", avatar_id: null },
          setup_completed: false,
          version: 2,
        }),
      ),
    } as unknown as SessionClient;
    const api = new IdentityApi("https://roadtalk.test/api/v1", session);

    await api.updateProfile({ version: 1, callsign: "Road-Runner" });

    expect(session.authenticatedFetch).toHaveBeenCalledWith(
      "https://roadtalk.test/api/v1/me/profile",
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({ version: 1, callsign: "Road-Runner" }),
      }),
    );
  });

  it("preserves stable problem codes and Retry-After without response data leakage", async () => {
    const session = {
      authenticatedFetch: jest.fn(async () =>
        response(
          {
            code: "CALLSIGN_CHANGE_COOLDOWN",
            detail: "The callsign cannot be changed yet.",
          },
          429,
          { "Retry-After": "60" },
        ),
      ),
    } as unknown as SessionClient;
    const api = new IdentityApi("https://roadtalk.test/api/v1", session);

    await expect(api.getProfile()).rejects.toEqual(
      expect.objectContaining<Partial<IdentityApiError>>({
        status: 429,
        code: "CALLSIGN_CHANGE_COOLDOWN",
        retryAfter: 60,
      }),
    );
  });
});
