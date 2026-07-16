import type { SessionClient } from "../session/SessionClient";
import type { LocationTransport, PublishedLocationSample } from "./types";

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
