import { environment } from "../config";
import type { SessionClient } from "../session/SessionClient";

export type ConvoyRole = "leader" | "member";

export type ConvoyStatus = {
  convoy_id: string;
  membership_id: string;
  display_name: string;
  role: ConvoyRole;
  state: "active";
};

export type ConvoyAwarenessMember = {
  account_id: string;
  callsign: string;
  role: ConvoyRole;
  availability: "current";
  expires_at: string;
};

export type ConvoyAwareness = {
  convoy_id: string;
  freshness: "current";
  expires_at: string;
  members: ConvoyAwarenessMember[];
};

export class ConvoyApi {
  constructor(
    private readonly session: SessionClient,
    private readonly fetcher: typeof fetch = fetch,
  ) {}

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await this.session.authenticatedFetch(
      `${environment.apiBaseUrl}/convoys${path}`,
      {
        ...init,
        headers: { Accept: "application/json", "Content-Type": "application/json", ...init?.headers },
      },
      this.fetcher,
    );
    if (!response.ok) throw new Error("Convoy state unavailable.");
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  }

  status(): Promise<ConvoyStatus | null> {
    return this.request<ConvoyStatus | null>("/me");
  }

  awareness(): Promise<ConvoyAwareness | null> {
    return this.request<ConvoyAwareness | null>("/awareness");
  }

  create(displayName: string): Promise<ConvoyStatus> {
    return this.request<ConvoyStatus>("", {
      method: "POST",
      body: JSON.stringify({ display_name: displayName }),
    });
  }

  join(convoyId: string): Promise<ConvoyStatus> {
    return this.request<ConvoyStatus>("/join", {
      method: "POST",
      body: JSON.stringify({ convoy_id: convoyId }),
    });
  }

  leave(): Promise<void> {
    return this.request<void>("/leave", { method: "POST", body: "{}" });
  }

  disband(): Promise<void> {
    return this.request<void>("/disband", { method: "POST", body: "{}" });
  }
}
