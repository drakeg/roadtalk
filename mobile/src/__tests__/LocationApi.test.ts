import {
  LOCATION_DISCLOSURE_VERSION,
  LOCATION_POLICY_VERSION,
  LocationApi,
} from "../location/api";
import type { SessionClient } from "../session/SessionClient";

describe("private location transport", () => {
  it("uses authenticated JSON bodies and never places coordinates in URLs", async () => {
    const session = {
      authenticatedFetch: jest.fn(async () => new Response(null, { status: 200 })),
    };
    const api = new LocationApi(
      "https://roadtalk.test/api/v1",
      session as unknown as SessionClient,
    );

    await api.grantConsent();
    await api.publish({
      observed_at: "2026-07-16T12:00:00.000Z",
      latitude: 40.5,
      longitude: -75.5,
      horizontal_accuracy_m: 25,
      heading_deg: 90,
      speed_mps: 4,
      client_sequence: 1,
      consent_policy_version: LOCATION_POLICY_VERSION,
    });
    await api.pause();
    const calls = session.authenticatedFetch.mock.calls as unknown as Array<
      [string, RequestInit]
    >;

    expect(session.authenticatedFetch).toHaveBeenNthCalledWith(
      1,
      "https://roadtalk.test/api/v1/me/location-consent",
      expect.objectContaining({ method: "PUT" }),
    );
    const consent = JSON.parse(
      String(calls[0]?.[1].body),
    ) as Record<string, unknown>;
    expect(consent).toEqual({
      policy_version: LOCATION_POLICY_VERSION,
      disclosure_version: LOCATION_DISCLOSURE_VERSION,
    });

    const locationUrl = calls[1]?.[0];
    expect(locationUrl).toBe("https://roadtalk.test/api/v1/me/location");
    expect(locationUrl).not.toContain("40.5");
    expect(locationUrl).not.toContain("-75.5");
    expect(JSON.parse(String(calls[1]?.[1].body))).toEqual(
      expect.objectContaining({ latitude: 40.5, longitude: -75.5 }),
    );
    expect(session.authenticatedFetch).toHaveBeenNthCalledWith(
      3,
      "https://roadtalk.test/api/v1/me/location",
      { method: "DELETE" },
    );
  });

  it("returns one stable transport failure without exposing server response data", async () => {
    const session = {
      authenticatedFetch: jest.fn(async () =>
        new Response(JSON.stringify({ detail: "coordinate 40.5 rejected" }), {
          status: 422,
        }),
      ),
    };
    const api = new LocationApi(
      "https://roadtalk.test/api/v1",
      session as unknown as SessionClient,
    );

    await expect(api.pause()).rejects.toThrow(
      "The location service is temporarily unavailable.",
    );
  });
});
