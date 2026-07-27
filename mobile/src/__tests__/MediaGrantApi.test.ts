import { MediaGrantApi } from "../media/api";

function response(body: unknown, status = 201): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("mobile receive-grant transport", () => {
  it("accepts only receive-only join/subscribe credentials", async () => {
    const authenticatedFetch = jest.fn(async () =>
      response({
        grant_id: "grant-1",
        mode: "receive",
        allowed_actions: ["join", "subscribe"],
        allowed_track_sources: [],
        server_url: "wss://synthetic.invalid",
        participant_token: "synthetic-test-token",
      }),
    );
    const api = new MediaGrantApi(
      "https://api.synthetic.invalid/api/v1",
      { authenticatedFetch } as never,
      () => "12345678-1234-1234-1234-123456789012",
    );

    await expect(api.createReceiveGrant()).resolves.toEqual({
      grantId: "grant-1",
      serverUrl: "wss://synthetic.invalid",
      participantToken: "synthetic-test-token",
    });
    expect(authenticatedFetch).toHaveBeenCalledWith(
      "https://api.synthetic.invalid/api/v1/ptt/grants",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          "Idempotency-Key": "12345678-1234-1234-1234-123456789012",
        }),
      }),
    );
  });

  it.each([
    {
      allowed_actions: ["join", "subscribe"],
      allowed_track_sources: ["microphone"],
    },
    {
      allowed_actions: ["join", "subscribe", "publish"],
      allowed_track_sources: [],
    },
    {
      allowed_actions: ["join", "subscribe"],
      allowed_track_sources: [],
      participant_token: null,
    },
  ])("rejects missing or over-scoped credentials", async (override) => {
    const authenticatedFetch = jest.fn(async () => {
      const baseline = {
        grant_id: "grant-1",
        mode: "receive",
        allowed_actions: ["join", "subscribe"],
        allowed_track_sources: [],
        server_url: "wss://synthetic.invalid",
        participant_token: "synthetic-test-token",
      };
      return response({ ...baseline, ...override });
    });
    const api = new MediaGrantApi("https://api.synthetic.invalid/api/v1", {
      authenticatedFetch,
    } as never);

    await expect(api.createReceiveGrant()).rejects.toThrow(/safely scoped/i);
  });

  it("releases the short-lived grant with authenticated idempotency", async () => {
    const authenticatedFetch = jest.fn(async () =>
      response({ state: "released" }, 200),
    );
    const api = new MediaGrantApi(
      "https://api.synthetic.invalid/api/v1",
      { authenticatedFetch } as never,
      () => "release-key-123456",
    );

    await api.releaseGrant("grant/unsafe");

    expect(authenticatedFetch).toHaveBeenCalledWith(
      "https://api.synthetic.invalid/api/v1/ptt/grants/grant%2Funsafe",
      {
        method: "DELETE",
        headers: { "Idempotency-Key": "release-key-123456" },
      },
    );
  });
});
