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
const privateReceipt = {
  ...general,
  id: "00000000-0000-4000-8000-000000000003",
  slug: null,
  display_label: "Camp Friends",
  type: "private",
  selected: false,
  created_at: "2026-08-15T12:00:00Z",
  invite: "rtc1." + "b".repeat(43),
  replayed: false,
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

describe("caller-scoped channel transport", () => {
  it("maps exact catalog, selection, join, leave, and management contracts", async () => {
    const client = session([
      { items: [general] },
      { ...general, selected_at: "2026-08-15T12:00:00Z", selection_version: 2 },
      {
        channel_id: general.id,
        state: "joined",
        changed_at: "2026-08-15T12:00:00Z",
        replayed: false,
      },
      {
        channel_id: general.id,
        state: "left",
        changed_at: "2026-08-15T12:00:00Z",
        replayed: false,
      },
      privateReceipt,
      privateReceipt,
      {
        channel_id: privateReceipt.id,
        state: "closed",
        changed_at: "2026-08-15T12:00:00Z",
        replayed: false,
      },
    ]);
    const api = new ChannelApi(
      "https://roadtalk.test/api/v1",
      client,
      () => "private-operation-key-0001",
    );

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
    await expect(api.create("Camp Friends")).resolves.toEqual(
      expect.objectContaining({ invite: privateReceipt.invite, type: "private" }),
    );
    await expect(api.rotate(privateReceipt.id)).resolves.toEqual(
      expect.objectContaining({ invite: privateReceipt.invite }),
    );
    await expect(api.close(privateReceipt.id)).resolves.toEqual(
      expect.objectContaining({ state: "closed" }),
    );

    const fetcher = client.authenticatedFetch as jest.Mock;
    expect(fetcher.mock.calls[2]?.[1]?.body).toBe(
      JSON.stringify({ invite: "rtc1." + "a".repeat(43) }),
    );
    expect(fetcher.mock.calls[3]?.[0]).toContain(
      `/channels/${general.id}/membership`,
    );
    expect(fetcher.mock.calls[4]?.[1]).toEqual(
      expect.objectContaining({
        body: JSON.stringify({ display_label: "Camp Friends" }),
        headers: expect.objectContaining({
          "Idempotency-Key": "private-operation-key-0001",
        }),
      }),
    );
    expect(fetcher.mock.calls[5]?.[0]).toContain("/invite/rotation");
    expect(fetcher.mock.calls[6]?.[1]?.method).toBe("DELETE");
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

  it("reads only the stable nested problem code and discards server detail", async () => {
    const api = new ChannelApi(
      "https://roadtalk.test/api/v1",
      failedSession(409, {
        detail: {
          code: "CHANNEL_NOT_AVAILABLE",
          detail: "secret ownership detail",
        },
      }),
    );

    await expect(api.rotate(privateReceipt.id)).rejects.toEqual(
      expect.objectContaining<Partial<ChannelApiError>>({
        code: "CHANNEL_NOT_AVAILABLE",
        message: "The channel request could not be completed.",
      }),
    );
  });
});
