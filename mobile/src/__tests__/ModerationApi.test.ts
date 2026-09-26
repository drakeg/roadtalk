import { ModerationApi } from "../moderation/api";

describe("mobile moderation API", () => {
  it("uses authenticated endpoints with only bounded payload fields", async () => {
    const authenticatedFetch = jest.fn().mockResolvedValue(new Response(JSON.stringify({ items: [] }), { status: 200 }));
    const api = new ModerationApi({ authenticatedFetch } as never);
    await api.report("00000000-0000-4000-8000-000000000001", "spam", "mobile-00000000-0000-4000-8000-000000000002");
    await api.restrict("00000000-0000-4000-8000-000000000001", "block");
    await api.restrictions();
    expect(authenticatedFetch.mock.calls.map((call) => call[0])).toEqual([
      expect.stringMatching(/\/moderation\/reports$/),
      expect.stringMatching(/\/moderation\/restrictions$/),
      expect.stringMatching(/\/moderation\/restrictions$/),
    ]);
    expect(JSON.parse(authenticatedFetch.mock.calls[0][1].body)).toEqual({
      subject_account_id: "00000000-0000-4000-8000-000000000001",
      reason: "spam",
      idempotency_key: "mobile-00000000-0000-4000-8000-000000000002",
    });
    expect(JSON.parse(authenticatedFetch.mock.calls[1][1].body)).toEqual({
      subject_account_id: "00000000-0000-4000-8000-000000000001", kind: "block",
    });
    for (const forbidden of ["latitude", "longitude", "route_history", "audio", "background_location", "enforcement_override"]) {
      expect(JSON.stringify(authenticatedFetch.mock.calls).toLowerCase()).not.toContain(forbidden);
    }
  });

  it("fails closed on unavailable moderation endpoints", async () => {
    const authenticatedFetch = jest.fn().mockResolvedValue(new Response("{}", { status: 403 }));
    const api = new ModerationApi({ authenticatedFetch } as never);
    await expect(api.restrictions()).rejects.toThrow("Safety action is unavailable.");
  });
});
