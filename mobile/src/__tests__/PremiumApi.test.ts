import { parsePremiumStatus, PremiumApi, PremiumStatusError } from "../premium/api";

const observed = "2026-10-29T12:00:00Z";
const valid = "2026-10-29T12:05:00Z";

function status(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    availability: "available",
    provider_mode: "test",
    tier: "premium",
    entitlement_state: "active",
    premium_experience_allowed: true,
    reason: "premium_entitled",
    observed_at: observed,
    valid_until: valid,
    checkout_available: false,
    server_authoritative: true,
    communication_authorization_unchanged: true,
    ...overrides,
  };
}

describe("mobile Premium API", () => {
  it("reads only the caller's server status endpoint without a request body", async () => {
    const authenticatedFetch = jest.fn().mockResolvedValue(new Response(JSON.stringify(status()), { status: 200 }));
    const api = new PremiumApi({ authenticatedFetch } as never);

    await expect(api.status()).resolves.toMatchObject({ tier: "premium" });
    expect(authenticatedFetch).toHaveBeenCalledTimes(1);
    const [url, init] = authenticatedFetch.mock.calls[0];
    expect(url).toMatch(/\/me\/premium$/);
    expect(init.method).toBe("GET");
    expect(init.body).toBeUndefined();
    expect(String(url)).not.toMatch(/account_id|tier|entitlement/);
  });

  it.each([
    ["HTTP failure", () => Promise.resolve(new Response("{}", { status: 503 }))],
    ["network failure", () => Promise.reject(new Error("offline"))],
    ["invalid JSON", () => Promise.resolve(new Response("not json", { status: 200 }))],
  ])("fails generically on %s", async (_label, outcome) => {
    const api = new PremiumApi({ authenticatedFetch: jest.fn().mockImplementation(outcome) } as never);
    await expect(api.status()).rejects.toThrow(new PremiumStatusError());
  });

  it("accepts the closed disabled-provider status", () => {
    expect(
      parsePremiumStatus(
        status({ availability: "provider_disabled", provider_mode: "disabled", tier: "free", entitlement_state: null, premium_experience_allowed: false, reason: "premium_entitlement_required" }),
      ).tier,
    ).toBe("free");
  });

  it.each([
    ["an unknown field", status({ card_number: "4242" })],
    ["a missing field", (() => { const s = status(); delete s.reason; return s; })()],
    ["checkout claimed available", status({ checkout_available: true })],
    ["non-authoritative status", status({ server_authoritative: false })],
    ["tier disagreeing with the gate", status({ tier: "premium", premium_experience_allowed: false })],
    ["Premium without an active entitlement", status({ entitlement_state: "revoked" })],
    ["Premium from an unavailable provider", status({ availability: "provider_unavailable" })],
    ["an unknown entitlement state", status({ entitlement_state: "lifetime" })],
    ["a validity window over five minutes", status({ valid_until: "2026-10-29T12:05:01Z" })],
    ["a validity window ending before observation", status({ valid_until: "2026-10-29T11:59:59Z" })],
    ["an invalid timestamp", status({ observed_at: "yesterday" })],
    ["a non-object", ["premium"]],
  ])("rejects %s", (_label, body) => {
    expect(() => parsePremiumStatus(body)).toThrow(PremiumStatusError);
  });
});
