import { randomUUID } from "expo-crypto";
import { useMemo } from "react";

import { environment } from "../config";
import { useSessionClient } from "../session/SessionContext";
import type { SessionClient } from "../session/SessionClient";
import type {
  NotificationInbox,
  NotificationPreferences,
  NotificationRecord,
  NotificationState,
  UrgentAlertReceipt,
} from "./types";

type Json = Record<string, unknown>;
type Problem = { code?: string; detail?: string | { code?: string; detail?: string } };

const FORBIDDEN_FIELDS = [
  "recipient_id",
  "recipient_ids",
  "account_id",
  "device_id",
  "installation_id",
  "username",
  "password",
  "recovery_key",
  "refresh_token",
  "access_token",
  "push_token",
  "provider",
  "provider_ref",
  "provider_token",
  "latitude",
  "longitude",
  "coordinates",
  "radius",
  "radius_m",
  "distance",
  "distance_m",
  "bearing",
  "heading",
  "speed",
  "route",
  "corridor",
  "destination",
  "history",
] as const;

export class NotificationApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
  ) {
    super("The notification request could not be completed.");
    this.name = "NotificationApiError";
  }
}

export class NotificationApi {
  constructor(
    private readonly baseUrl: string,
    private readonly session: SessionClient,
    private readonly idempotencyKey: () => string = randomUUID,
  ) {}

  async preferences(): Promise<NotificationPreferences> {
    return this.parsePreferences(
      await this.request("/me/notification-preferences", { method: "GET" }),
    );
  }

  async updatePreferences(
    current: NotificationPreferences,
    update: Pick<
      NotificationPreferences,
      "channelActivityEnabled" | "urgentAlertEnabled"
    >,
  ): Promise<NotificationPreferences> {
    return this.parsePreferences(
      await this.request("/me/notification-preferences", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          channel_activity_enabled: update.channelActivityEnabled,
          urgent_alert_enabled: update.urgentAlertEnabled,
          expected_version: current.version,
        }),
      }),
    );
  }

  async inbox(): Promise<NotificationInbox> {
    const body = await this.request("/me/notifications", { method: "GET" });
    if (!Array.isArray(body.items)) throw this.invalidResponse();
    return { items: body.items.map((item) => this.parseRecord(item)) };
  }

  async updateState(
    notification: NotificationRecord,
    state: NotificationState,
  ): Promise<NotificationRecord> {
    return this.parseRecord(
      await this.request(
        `/me/notifications/${encodeURIComponent(notification.id)}/state`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            state,
            expected_version: notification.version,
          }),
        },
      ),
    );
  }

  async sendUrgentAlert(message: string): Promise<UrgentAlertReceipt> {
    const body = await this.request("/notifications/urgent-alerts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        idempotency_key: this.idempotencyKey(),
      }),
    });
    if (
      body.accepted !== true ||
      typeof body.recipient_count !== "number" ||
      !Number.isInteger(body.recipient_count) ||
      body.recipient_count < 0 ||
      !this.validDate(body.issued_at) ||
      !this.validDate(body.expires_at)
    ) {
      throw this.invalidResponse();
    }
    return {
      accepted: true,
      recipientCount: body.recipient_count,
      issuedAt: body.issued_at,
      expiresAt: body.expires_at,
    };
  }

  private async request(path: string, init: RequestInit): Promise<Json> {
    let response: Response;
    try {
      response = await this.session.authenticatedFetch(`${this.baseUrl}${path}`, {
        ...init,
        headers: { Accept: "application/json", ...init.headers },
      });
    } catch {
      throw new NotificationApiError(0, "NOTIFICATION_UNAVAILABLE");
    }
    if (!response.ok) {
      const problem = (await response.json().catch(() => ({}))) as Problem;
      const code =
        problem.code ??
        (typeof problem.detail === "object" ? problem.detail.code : undefined);
      throw new NotificationApiError(
        response.status,
        code ?? "NOTIFICATION_REQUEST_FAILED",
      );
    }
    try {
      const body: unknown = await response.json();
      if (typeof body !== "object" || body === null || Array.isArray(body)) {
        throw this.invalidResponse();
      }
      return body as Json;
    } catch (error) {
      if (error instanceof NotificationApiError) throw error;
      throw this.invalidResponse();
    }
  }

  private parsePreferences(body: Json): NotificationPreferences {
    if (
      typeof body.channel_activity_enabled !== "boolean" ||
      typeof body.urgent_alert_enabled !== "boolean" ||
      typeof body.version !== "number" ||
      !Number.isInteger(body.version) ||
      body.version < 1
    ) {
      throw this.invalidResponse();
    }
    return {
      channelActivityEnabled: body.channel_activity_enabled,
      urgentAlertEnabled: body.urgent_alert_enabled,
      version: body.version,
    };
  }

  private parseRecord(value: unknown): NotificationRecord {
    if (typeof value !== "object" || value === null || Array.isArray(value)) {
      throw this.invalidResponse();
    }
    const body = value as Json;
    for (const field of FORBIDDEN_FIELDS) {
      if (field in body) throw this.invalidResponse();
    }
    if (
      typeof body.id !== "string" ||
      !["account", "channel_activity", "urgent_alert"].includes(
        String(body.notification_class),
      ) ||
      !["normal", "high", "urgent"].includes(String(body.priority)) ||
      !["roadtalk_account", "roadtalk_channel", "user_generated_urgent"].includes(
        String(body.source),
      ) ||
      (body.title !== null && typeof body.title !== "string") ||
      typeof body.message !== "string" ||
      (body.channel_label !== null && typeof body.channel_label !== "string") ||
      !this.validDate(body.issued_at) ||
      !this.validDate(body.expires_at) ||
      !this.nullableDate(body.read_at) ||
      !this.nullableDate(body.dismissed_at) ||
      typeof body.version !== "number" ||
      !Number.isInteger(body.version) ||
      body.version < 1
    ) {
      throw this.invalidResponse();
    }

    const urgent = body.notification_class === "urgent_alert";
    if (
      urgent &&
      (body.priority !== "urgent" ||
        body.source !== "user_generated_urgent" ||
        body.verified !== false ||
        body.emergency_service !== false ||
        body.delivery_guaranteed !== false ||
        body.safety_not_emergency_service !== "RoadTalk is not an emergency service." ||
        body.safety_delivery_not_guaranteed !== "Delivery is not guaranteed." ||
        body.safety_emergency_services_guidance !==
          "Contact local emergency services directly when emergency assistance is needed." ||
        body.safety_unverified !== "This alert is user-generated and unverified.")
    ) {
      throw this.invalidResponse();
    }

    return {
      id: body.id,
      notificationClass: body.notification_class as NotificationRecord["notificationClass"],
      priority: body.priority as NotificationRecord["priority"],
      source: body.source as NotificationRecord["source"],
      title: body.title as string | null,
      message: body.message,
      channelLabel: body.channel_label as string | null,
      issuedAt: body.issued_at as string,
      expiresAt: body.expires_at as string,
      readAt: body.read_at as string | null,
      dismissedAt: body.dismissed_at as string | null,
      version: body.version,
      verified: urgent ? false : null,
      emergencyService: urgent ? false : null,
      deliveryGuaranteed: urgent ? false : null,
      safetyNotEmergencyService: urgent
        ? "RoadTalk is not an emergency service."
        : null,
      safetyDeliveryNotGuaranteed: urgent ? "Delivery is not guaranteed." : null,
      safetyEmergencyServicesGuidance: urgent
        ? "Contact local emergency services directly when emergency assistance is needed."
        : null,
      safetyUnverified: urgent
        ? "This alert is user-generated and unverified."
        : null,
    };
  }

  private validDate(value: unknown): value is string {
    return typeof value === "string" && Number.isFinite(Date.parse(value));
  }

  private nullableDate(value: unknown): value is string | null {
    return value === null || this.validDate(value);
  }

  private invalidResponse(): NotificationApiError {
    return new NotificationApiError(0, "NOTIFICATION_RESPONSE_INVALID");
  }
}

export function useNotificationApi(): NotificationApi {
  const session = useSessionClient();
  return useMemo(
    () => new NotificationApi(environment.apiBaseUrl, session),
    [session],
  );
}
