import { RouteModeApi, RouteModeApiError } from "../routeMode/api";
import type { SessionClient } from "../session/SessionClient";

function session(payloads: unknown[]): SessionClient {
  return {
    authenticatedFetch: jest.fn(async () => {
      const payload = payloads.shift();
      return new Response(JSON.stringify(payload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }),
  } as unknown as SessionClient;
}

function failedSession(status: number, payload: unknown): SessionClient {
  return {
    authenticatedFetch: jest.fn(async () =>
      new Response(JSON.stringify(payload), {
        status,
        headers: { "Content-Type": "application/json" },
      }),
    ),
  } as unknown as SessionClient;
}

describe("route mode transport", () => {
  it("reads and updates the minimized route mode contract", async () => {
    const client = session([
      {
        mode: "nearby",
        version: 1,
        selected_at: "2026-08-26T03:30:00Z",
        availability: "available",
      },
      {
        mode: "same_road",
        version: 2,
        selected_at: "2026-08-26T03:31:00Z",
        availability: "unavailable",
      },
    ]);
    const api = new RouteModeApi("https://roadtalk.test/api/v1", client);

    await expect(api.current()).resolves.toEqual({
      mode: "nearby",
      version: 1,
      selectedAt: "2026-08-26T03:30:00Z",
      availability: "available",
    });
    await expect(api.update("same_road", 1)).resolves.toEqual({
      mode: "same_road",
      version: 2,
      selectedAt: "2026-08-26T03:31:00Z",
      availability: "unavailable",
    });

    const fetcher = client.authenticatedFetch as jest.Mock;
    expect(fetcher.mock.calls[1]?.[1]).toEqual(
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ mode: "same_road", expected_version: 1 }),
      }),
    );
  });

  it.each([
    "road_name",
    "route",
    "provider",
    "provider_corridor_ref",
    "corridor_digest",
    "direction",
    "latitude",
    "longitude",
    "distance_m",
    "bearing",
    "account_id",
    "device_id",
    "participant_ref",
    "eligibility_reason",
  ])("rejects disclosing response field %s", async (field) => {
    const api = new RouteModeApi(
      "https://roadtalk.test/api/v1",
      session([
        {
          mode: "same_road",
          version: 2,
          selected_at: "2026-08-26T03:31:00Z",
          availability: "available",
          [field]: "sensitive",
        },
      ]),
    );

    await expect(api.current()).rejects.toEqual(
      expect.objectContaining<Partial<RouteModeApiError>>({
        code: "ROUTE_MODE_INVALID_RESPONSE",
      }),
    );
  });

  it("keeps server failure detail out of client errors", async () => {
    const api = new RouteModeApi(
      "https://roadtalk.test/api/v1",
      failedSession(409, {
        detail: {
          code: "ROUTE_MODE_VERSION_CONFLICT",
          detail: "private route state",
        },
      }),
    );

    await expect(api.update("same_road", 1)).rejects.toEqual(
      expect.objectContaining<Partial<RouteModeApiError>>({
        code: "ROUTE_MODE_VERSION_CONFLICT",
        message: "RoadTalk could not update your audience mode.",
      }),
    );
  });
});
