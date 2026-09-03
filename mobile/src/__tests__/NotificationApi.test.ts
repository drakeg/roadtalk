import { NotificationApi, NotificationApiError } from "../notifications/api";
import type { SessionClient } from "../session/SessionClient";

const ordinary = {
  id: "00000000-0000-4000-8000-000000000101",
  notification_class: "channel_activity",
  priority: "normal",
  source: "roadtalk_channel",
  title: "Channel activity",
  message: "There is current activity in your selected channel.",
  channel_label: "General",
  issued_at: "2026-09-02T20:00:00Z",
  expires_at: "2026-09-02T22:00:00Z",
  read_at: null,
  dismissed_at: null,
  version: 1,
  verified: null,
  emergency_service: null,
  delivery_guaranteed: null,
  safety_not_emergency_service: null,
  safety_delivery_not_guaranteed: null,
  safety_emergency_services_guidance: null,
  safety_unverified: null,
};

const urgent = {
  id: "00000000-0000-4000-8000-000000000102",
  notification_class: "urgent_alert",
  priority: "urgent",
  source: "user_generated_urgent",
  title: null,
  message: "Disabled vehicle blocking the right lane.",
  channel_label: "General",
  issued_at: "2026-09-02T20:00:00Z",
  expires_at: "2026-09-02T20:10:00Z",
  read_at: null,
  dismissed_at: null,
  version: 2,
  verified: false,
  emergency_service: false,
  delivery_guaranteed: false,
  safety_not_emergency_service: "RoadTalk is not an emergency service.",
  safety_delivery_not_guaranteed: "Delivery is not guaranteed.",
  safety_emergency_services_guidance:
    "Contact local emergency services directly when emergency assistance is needed.",
  safety_unverified: "This alert is user-generated and unverified.",
};

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

describe("mobile notification transport", () => {
  it("maps inbox, preferences, state, and urgent command contracts", async () => {
    const client = session([
      { channel_activity_enabled: true, urgent_alert_enabled: true, version: 3 },
      { items: [ordinary, urgent] },
      { ...ordinary, read_at: "2026-09-02T20:01:00Z", version: 2 },
      { channel_activity_enabled: false, urgent_alert_enabled: true, version: 4 },
      {
        accepted: true,
        recipient_count: 2,
        issued_at: "2026-09-02T20:02:00Z",
        expires_at: "2026-09-02T20:12:00Z",
      },
    ]);
    const api = new NotificationApi(
      "https://roadtalk.test/api/v1",
      client,
      () => "mobile-urgent-key-0001",
    );

    const preferences = await api.preferences();
    expect(preferences).toEqual({
      channelActivityEnabled: true,
      urgentAlertEnabled: true,
      version: 3,
    });
    await expect(api.inbox()).resolves.toEqual({
      items: [
        expect.objectContaining({ source: "roadtalk_channel" }),
        expect.objectContaining({
          source: "user_generated_urgent",
          deliveryGuaranteed: false,
        }),
      ],
    });
    await expect(
      api.updateState(
        {
          ...apiRecord(ordinary),
          version: 1,
        },
        "read",
      ),
    ).resolves.toEqual(expect.objectContaining({ readAt: "2026-09-02T20:01:00Z" }));
    await expect(
      api.updatePreferences(preferences, {
        channelActivityEnabled: false,
        urgentAlertEnabled: true,
      }),
    ).resolves.toEqual(expect.objectContaining({ version: 4 }));
    await expect(api.sendUrgentAlert("Road hazard ahead")).resolves.toEqual(
      expect.objectContaining({ recipientCount: 2, accepted: true }),
    );

    const fetcher = client.authenticatedFetch as jest.Mock;
    expect(fetcher.mock.calls[2]?.[1]?.body).toBe(
      JSON.stringify({ state: "read", expected_version: 1 }),
    );
    expect(fetcher.mock.calls[3]?.[1]?.body).toBe(
      JSON.stringify({
        channel_activity_enabled: false,
        urgent_alert_enabled: true,
        expected_version: 3,
      }),
    );
    expect(fetcher.mock.calls[4]?.[1]?.body).toBe(
      JSON.stringify({
        message: "Road hazard ahead",
        idempotency_key: "mobile-urgent-key-0001",
      }),
    );
  });

  it("rejects sensitive notification fields and invalid urgent safety semantics", async () => {
    const disclosed = new NotificationApi(
      "https://roadtalk.test/api/v1",
      session([{ items: [{ ...ordinary, latitude: 40.1 }] }]),
    );
    await expect(disclosed.inbox()).rejects.toEqual(
      expect.objectContaining<Partial<NotificationApiError>>({
        code: "NOTIFICATION_RESPONSE_INVALID",
      }),
    );

    const unsafe = new NotificationApi(
      "https://roadtalk.test/api/v1",
      session([{ items: [{ ...urgent, delivery_guaranteed: true }] }]),
    );
    await expect(unsafe.inbox()).rejects.toEqual(
      expect.objectContaining<Partial<NotificationApiError>>({
        code: "NOTIFICATION_RESPONSE_INVALID",
      }),
    );
  });

  it("surfaces only stable nested error codes", async () => {
    const api = new NotificationApi(
      "https://roadtalk.test/api/v1",
      failedSession(403, {
        detail: {
          code: "REGISTERED_ACCOUNT_REQUIRED",
          detail: "private account detail",
        },
      }),
    );

    await expect(api.sendUrgentAlert("Need assistance")).rejects.toEqual(
      expect.objectContaining<Partial<NotificationApiError>>({
        status: 403,
        code: "REGISTERED_ACCOUNT_REQUIRED",
        message: "The notification request could not be completed.",
      }),
    );
  });
});

function apiRecord(body: typeof ordinary) {
  return {
    id: body.id,
    notificationClass: body.notification_class as "channel_activity",
    priority: body.priority as "normal",
    source: body.source as "roadtalk_channel",
    title: body.title,
    message: body.message,
    channelLabel: body.channel_label,
    issuedAt: body.issued_at,
    expiresAt: body.expires_at,
    readAt: body.read_at,
    dismissedAt: body.dismissed_at,
    version: body.version,
    verified: null,
    emergencyService: null,
    deliveryGuaranteed: null,
    safetyNotEmergencyService: null,
    safetyDeliveryNotGuaranteed: null,
    safetyEmergencyServicesGuidance: null,
    safetyUnverified: null,
  };
}
