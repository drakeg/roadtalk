import { ChannelApi, ChannelApiError } from "../channels/api";
import type { SessionClient } from "../session/SessionClient";

const general = {
  id: "00000000-0000-4000-8000-000000000001",
  slug: "general",
  display_label: "General",
  type: "public",
  selected: true,
  enabled: true,
  version: 1,
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

describe("caller-scoped channel transport", () => {
  it("maps exact catalog, selection, join, and leave contracts", async () => {
    const client = session([
      { items: [general] },
      { ...general, selected_at: "2026-08-15T12:00:00Z", selection_version: 2 },
      { channel_id: general.id, state: "joined", changed_at: "2026-08-15T12:00:00Z", replayed: false },
      { channel_id: general.id, state: "left", changed_at: "2026-08-15T12:00:00Z", replayed: false },
    ]);
    const api = new ChannelApi("https://roadtalk.test/api/v1", client);

    await expect(api.list()).resolves.toEqual({
      items: [expect.objectContaining({ displayLabel: "General", selected: true })],
    });
    await expect(api.current()).resolves.toEqual(
      expect.objectContaining({ selectionVersion: 2 }),
    );
    await expect(api.join("rtc1." + "a".repeat(43))).resolves.toEqual(
      expect.objectContaining({ state: "joined" }),
    );
    await expect(api.leave(general.id)).resolves.toEqual(
      expect.objectContaining({ state: "left" }),
    );

    const fetcher = client.authenticatedFetch as jest.Mock;
    expect(fetcher.mock.calls[2]?.[1]?.body).toBe(
      JSON.stringify({ invite: "rtc1." + "a".repeat(43) }),
    );
    expect(fetcher.mock.calls[3]?.[0]).toContain(
      `/channels/${general.id}/membership`,
    );
  });

  it("rejects malformed or disclosing catalog responses generically", async () => {
    const api = new ChannelApi(
      "https://roadtalk.test/api/v1",
      session([{ items: [{ ...general, member_count: 4, type: "private" }] }]),
    );

    await expect(api.list()).rejects.toEqual(
      expect.objectContaining<Partial<ChannelApiError>>({
        code: "CHANNEL_RESPONSE_INVALID",
      }),
    );
  });
});
