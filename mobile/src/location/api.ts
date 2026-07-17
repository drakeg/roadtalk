import type { SessionClient } from "../session/SessionClient";
import type {
  LocationTransport,
  NearbyBucket,
  NearbySummary,
  PublishedLocationSample,
} from "./types";

export const LOCATION_POLICY_VERSION = "location-v1";
export const LOCATION_DISCLOSURE_VERSION = "location-disclosure-v1";

export class LocationApi implements LocationTransport {
  constructor(
    private readonly baseUrl: string,
    private readonly session: SessionClient,
  ) {}

  async grantConsent(): Promise<void> {
    await this.request("/me/location-consent", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        policy_version: LOCATION_POLICY_VERSION,
        disclosure_version: LOCATION_DISCLOSURE_VERSION,
      }),
    });
  }

  async publish(sample: PublishedLocationSample): Promise<void> {
    await this.request("/me/location", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(sample),
    });
  }

  async pause(): Promise<void> {
    await this.request("/me/location", { method: "DELETE" });
  }

  async nearby(): Promise<NearbySummary | null> {
    const response = await this.session.authenticatedFetch(
      `${this.baseUrl}/nearby/summary`,
      { method: "GET" },
    );
    if (response.status === 409) {
      return null;
    }
    if (!response.ok) {
      throw new Error("Nearby status is temporarily unavailable.");
    }

    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      throw new Error("Nearby status is temporarily unavailable.");
    }
    if (
      typeof payload !== "object" ||
      payload === null ||
      Array.isArray(payload)
    ) {
      throw new Error("Nearby status is temporarily unavailable.");
    }
    const body = payload as Record<string, unknown>;
    const expiresAtMs =
      typeof body.expires_at === "string" ? Date.parse(body.expires_at) : NaN;
    if (
      body.availability !== "available" ||
      !isNearbyBucket(body.bucket) ||
      body.freshness !== "fresh" ||
      !Number.isFinite(expiresAtMs)
    ) {
      throw new Error("Nearby status is temporarily unavailable.");
    }
    return {
      availability: "available",
      bucket: body.bucket,
      freshness: "fresh",
      expiresAtMs,
    };
  }

  private async request(path: string, init: RequestInit): Promise<void> {
    const response = await this.session.authenticatedFetch(
      `${this.baseUrl}${path}`,
      init,
    );
    if (!response.ok) {
      throw new Error("The location service is temporarily unavailable.");
    }
  }
}

function isNearbyBucket(value: unknown): value is NearbyBucket {
  return value === "none" || value === "few" || value === "many";
}
