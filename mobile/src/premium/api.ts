import { environment } from "../config";
import type { SessionClient } from "../session/SessionClient";

export type PremiumAvailability = "available" | "provider_disabled" | "provider_unavailable";
export type PremiumEntitlementState = "inactive" | "active" | "expired" | "revoked";

export type PremiumStatus = {
  availability: PremiumAvailability;
  provider_mode: "disabled" | "test";
  tier: "free" | "premium";
  entitlement_state: PremiumEntitlementState | null;
  premium_experience_allowed: boolean;
  reason: string;
  observed_at: string;
  valid_until: string;
  checkout_available: false;
  server_authoritative: true;
  communication_authorization_unchanged: true;
};

const STATUS_FIELDS = [
  "availability",
  "provider_mode",
  "tier",
  "entitlement_state",
  "premium_experience_allowed",
  "reason",
  "observed_at",
  "valid_until",
  "checkout_available",
  "server_authoritative",
  "communication_authorization_unchanged",
] as const;

const AVAILABILITY = new Set<unknown>(["available", "provider_disabled", "provider_unavailable"]);
const ENTITLEMENT = new Set<unknown>(["inactive", "active", "expired", "revoked", null]);

/** Maximum trust window the server grants a Premium observation (D05 gate). */
export const PREMIUM_STATUS_MAX_VALIDITY_MS = 5 * 60 * 1000;

export class PremiumStatusError extends Error {
  constructor() {
    super("Premium status unavailable.");
  }
}

function isTimestamp(value: unknown): value is string {
  return typeof value === "string" && Number.isFinite(Date.parse(value));
}

/**
 * Accept only the closed server contract. Anything unexpected is treated as no
 * status at all, so the app never infers Premium from a partial or widened payload.
 */
export function parsePremiumStatus(value: unknown): PremiumStatus {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new PremiumStatusError();
  const body = value as Record<string, unknown>;
  const keys = Object.keys(body).sort();
  if (keys.length !== STATUS_FIELDS.length || keys.join() !== [...STATUS_FIELDS].sort().join()) throw new PremiumStatusError();
  if (
    !AVAILABILITY.has(body.availability) ||
    (body.provider_mode !== "disabled" && body.provider_mode !== "test") ||
    (body.tier !== "free" && body.tier !== "premium") ||
    !ENTITLEMENT.has(body.entitlement_state) ||
    typeof body.premium_experience_allowed !== "boolean" ||
    typeof body.reason !== "string" ||
    !isTimestamp(body.observed_at) ||
    !isTimestamp(body.valid_until) ||
    body.checkout_available !== false ||
    body.server_authoritative !== true ||
    body.communication_authorization_unchanged !== true
  ) {
    throw new PremiumStatusError();
  }
  const validity = Date.parse(body.valid_until) - Date.parse(body.observed_at);
  if (!(validity > 0 && validity <= PREMIUM_STATUS_MAX_VALIDITY_MS)) throw new PremiumStatusError();
  // Premium is shown only when the server gate allowed it and the tier agrees.
  if ((body.tier === "premium") !== body.premium_experience_allowed) throw new PremiumStatusError();
  if (body.premium_experience_allowed && (body.availability !== "available" || body.entitlement_state !== "active")) {
    throw new PremiumStatusError();
  }
  return body as PremiumStatus;
}

export class PremiumApi {
  constructor(
    private readonly session: SessionClient,
    private readonly fetcher: typeof fetch = fetch,
  ) {}

  async status(): Promise<PremiumStatus> {
    let response: Response;
    try {
      response = await this.session.authenticatedFetch(
        `${environment.apiBaseUrl}/me/premium`,
        { method: "GET", headers: { Accept: "application/json", "Cache-Control": "no-store" } },
        this.fetcher,
      );
    } catch {
      throw new PremiumStatusError();
    }
    if (!response.ok) throw new PremiumStatusError();
    let body: unknown;
    try {
      body = await response.json();
    } catch {
      throw new PremiumStatusError();
    }
    return parsePremiumStatus(body);
  }
}
