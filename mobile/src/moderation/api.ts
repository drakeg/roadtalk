import { environment } from "../config";
import type { SessionClient } from "../session/SessionClient";

export type ReportReason = "harassment" | "spam" | "impersonation" | "unsafe_content" | "other";
export type RestrictionKind = "mute" | "block";
export type RestrictionSummary = { restriction_id: string; subject_account_id: string; kind: RestrictionKind };

export class ModerationApi {
  constructor(
    private readonly session: SessionClient,
    private readonly fetcher: typeof fetch = fetch,
  ) {}

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await this.session.authenticatedFetch(
      `${environment.apiBaseUrl}/moderation${path}`,
      { ...init, headers: { Accept: "application/json", "Content-Type": "application/json", ...init?.headers } },
      this.fetcher,
    );
    if (!response.ok) throw new Error("Safety action is unavailable.");
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  }

  restrictions(): Promise<{ items: RestrictionSummary[] }> {
    return this.request("/restrictions");
  }

  report(subjectAccountId: string, reason: ReportReason, idempotencyKey: string): Promise<void> {
    return this.request("/reports", {
      method: "POST",
      body: JSON.stringify({ subject_account_id: subjectAccountId, reason, idempotency_key: idempotencyKey }),
    });
  }

  restrict(subjectAccountId: string, kind: RestrictionKind): Promise<RestrictionSummary> {
    return this.request("/restrictions", {
      method: "POST",
      body: JSON.stringify({ subject_account_id: subjectAccountId, kind }),
    });
  }

  revoke(restrictionId: string): Promise<void> {
    return this.request(`/restrictions/${encodeURIComponent(restrictionId)}`, { method: "DELETE" });
  }
}
