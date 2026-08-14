import { MediaGrantApi, MediaGrantError } from "../media/api";

function response(body: unknown, status = 201): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("mobile media-grant transport", () => {
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

  it("requests and accepts only a nested microphone-only transmit grant", async () => {
    const authenticatedFetch = jest.fn(async () =>
      response({
        grant_id: "transmit-1",
        receive_grant_id: "receive/grant",
        mode: "transmit",
        allowed_actions: ["publish"],
        allowed_track_sources: ["microphone"],
        expires_at: "2026-07-26T12:00:30Z",
      }),
    );
    const api = new MediaGrantApi(
      "https://api.synthetic.invalid/api/v1",
      { authenticatedFetch } as never,
      () => "transmit-key-123456",
    );

    await expect(api.createTransmitGrant("receive/grant")).resolves.toEqual({
      grantId: "transmit-1",
      receiveGrantId: "receive/grant",
      expiresAt: "2026-07-26T12:00:30Z",
    });
    expect(authenticatedFetch).toHaveBeenCalledWith(
      "https://api.synthetic.invalid/api/v1/ptt/grants/receive%2Fgrant/transmit",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": "transmit-key-123456",
        },
        body: "{}",
      },
    );
  });

  it.each([
    { allowed_actions: ["publish", "subscribe"] },
    { allowed_track_sources: ["microphone", "camera"] },
    { allowed_track_sources: ["camera"] },
    { receive_grant_id: "different-receive" },
    { expires_at: "not-a-date" },
  ])("rejects an invalid or over-scoped transmit grant", async (override) => {
    const authenticatedFetch = jest.fn(async () =>
      response({
        grant_id: "transmit-1",
        receive_grant_id: "receive-1",
        mode: "transmit",
        allowed_actions: ["publish"],
        allowed_track_sources: ["microphone"],
        expires_at: "2026-07-26T12:00:30Z",
        ...override,
      }),
    );
    const api = new MediaGrantApi("https://api.synthetic.invalid/api/v1", {
      authenticatedFetch,
    } as never);

    await expect(api.createTransmitGrant("receive-1")).rejects.toEqual(
      expect.objectContaining({
        name: "MediaGrantError",
        code: "PTT_TRANSMIT_SCOPE_INVALID",
      }),
    );
  });

  it("preserves a nested stable transmit denial code", async () => {
    const authenticatedFetch = jest.fn(async () =>
      response(
        {
          detail: {
            code: "PTT_TRANSMIT_BUSY",
            detail: "Synthetic detail is not shown to the user.",
          },
        },
        409,
      ),
    );
    const api = new MediaGrantApi("https://api.synthetic.invalid/api/v1", {
      authenticatedFetch,
    } as never);

    await expect(api.createTransmitGrant("receive-1")).rejects.toEqual(
      new MediaGrantError("PTT_TRANSMIT_BUSY"),
    );
  });

  it("reports only the opaque local track and accepts metadata-only delivery", async () => {
    const authenticatedFetch = jest.fn(async () =>
      response({
        transmit_grant_id: "transmit/1",
        delivery_state: "ready",
        proximity_policy_version: "proximity-v1",
        evaluated_at: "2026-08-08T03:00:00Z",
        expires_at: "2026-08-08T03:00:30Z",
        replayed: false,
      }),
    );
    const api = new MediaGrantApi(
      "https://api.synthetic.invalid/api/v1",
      { authenticatedFetch } as never,
    );

    await expect(
      api.publishTransmitTrack("transmit/1", "track_opaque-1"),
    ).resolves.toEqual({
      transmitGrantId: "transmit/1",
      deliveryState: "ready",
      expiresAt: "2026-08-08T03:00:30Z",
    });
    expect(authenticatedFetch).toHaveBeenCalledWith(
      "https://api.synthetic.invalid/api/v1/ptt/grants/transmit%2F1/publication",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ track_ref: "track_opaque-1" }),
      },
    );
  });

  it.each(["recipient_refs", "nearby_count", "distance_m", "latitude"])(
    "rejects publication metadata containing private %s",
    async (privateField) => {
      const authenticatedFetch = jest.fn(async () =>
        response({
          transmit_grant_id: "transmit-1",
          delivery_state: "ready",
          proximity_policy_version: "proximity-v1",
          evaluated_at: "2026-08-08T03:00:00Z",
          expires_at: "2026-08-08T03:00:30Z",
          replayed: false,
          [privateField]: "private-marker",
        }),
      );
      const api = new MediaGrantApi("https://api.synthetic.invalid/api/v1", {
        authenticatedFetch,
      } as never);

      await expect(
        api.publishTransmitTrack("transmit-1", "track-opaque"),
      ).rejects.toEqual(
        expect.objectContaining({ code: "PTT_PUBLICATION_SCOPE_INVALID" }),
      );
    },
  );

  it("maps uncertain provider publication cleanup to reconciling", async () => {
    const authenticatedFetch = jest.fn(async () =>
      response(
        {
          detail: {
            code: "PTT_PROVIDER_UNAVAILABLE",
            detail: "Synthetic provider detail is not rendered.",
          },
        },
        503,
      ),
    );
    const api = new MediaGrantApi("https://api.synthetic.invalid/api/v1", {
      authenticatedFetch,
    } as never);

    await expect(
      api.publishTransmitTrack("transmit-1", "track-opaque"),
    ).rejects.toEqual(
      expect.objectContaining({ code: "PTT_DELIVERY_RECONCILING" }),
    );
  });
});
