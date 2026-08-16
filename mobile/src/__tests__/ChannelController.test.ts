import { ChannelController } from "../channels/ChannelController";
import type { ChannelSummary, ChannelTransport, ChannelTransition } from "../channels/types";

const general: ChannelSummary = {
  id: "general-id",
  slug: "general",
  displayLabel: "General",
  type: "public",
  selected: true,
  enabled: true,
  version: 1,
};
const privateChannel: ChannelSummary = {
  id: "private-id",
  slug: null,
  displayLabel: "Camp Friends",
  type: "private",
  selected: false,
  enabled: true,
  version: 1,
};

function transport(): jest.Mocked<ChannelTransport> {
  return {
    list: jest.fn(async () => ({ items: [general, privateChannel] })),
    current: jest.fn(async () => ({
      ...general,
      selected: true as const,
      selectedAt: "2026-08-15T12:00:00Z",
      selectionVersion: 1,
    })),
    select: jest.fn(async (_channelId: string) => ({
      ...privateChannel,
      selected: true as const,
      selectedAt: "2026-08-15T12:01:00Z",
      selectionVersion: 2,
    })),
    join: jest.fn(async (_invite: string) => ({
      channelId: privateChannel.id,
      state: "joined" as const,
      changedAt: "2026-08-15T12:00:00Z",
      replayed: false,
    })),
    leave: jest.fn(async (_channelId: string) => ({
      channelId: privateChannel.id,
      state: "left" as const,
      changedAt: "2026-08-15T12:00:00Z",
      replayed: false,
    })),
  };
}

function transition(events: string[]): jest.Mocked<ChannelTransition> {
  return {
    prepareChannelTransition: jest.fn(async () => {
      events.push("media-stopped");
    }),
    completeChannelTransition: jest.fn(async () => {
      events.push("media-reconnected");
    }),
  };
}

describe("channel catalog and safe switching controller", () => {
  it("loads only semantic catalog state and switches after media cleanup", async () => {
    const events: string[] = [];
    const remote = transport();
    remote.select.mockImplementationOnce(async () => {
      events.push("server-selected");
      return {
        ...privateChannel,
        selected: true,
        selectedAt: "2026-08-15T12:01:00Z",
        selectionVersion: 2,
      };
    });
    const controller = new ChannelController(remote, transition(events));
    await controller.load();
    await controller.select(privateChannel.id);

    expect(events).toEqual(["media-stopped", "server-selected", "media-reconnected"]);
    expect(controller.getSnapshot()).toEqual(
      expect.objectContaining({ status: "ready", selectedId: privateChannel.id }),
    );
  });

  it("cleans media before leaving and falls back to the server selection", async () => {
    const events: string[] = [];
    const remote = transport();
    remote.current
      .mockResolvedValueOnce({
        ...privateChannel,
        selected: true,
        selectedAt: "2026-08-15T12:00:00Z",
        selectionVersion: 2,
      })
      .mockResolvedValueOnce({
        ...general,
        selected: true,
        selectedAt: "2026-08-15T12:01:00Z",
        selectionVersion: 3,
      });
    remote.list
      .mockResolvedValueOnce({ items: [{ ...general, selected: false }, { ...privateChannel, selected: true }] })
      .mockResolvedValueOnce({ items: [general] });
    remote.leave.mockImplementationOnce(async () => {
      events.push("server-left");
      return {
        channelId: privateChannel.id,
        state: "left",
        changedAt: "2026-08-15T12:01:00Z",
        replayed: false,
      };
    });
    const controller = new ChannelController(remote, transition(events));
    await controller.load();
    await controller.leave(privateChannel.id);

    expect(events).toEqual(["media-stopped", "server-left", "media-reconnected"]);
    expect(controller.getSnapshot()).toEqual(
      expect.objectContaining({ status: "ready", selectedId: general.id, notice: "left" }),
    );
  });

  it("uses a non-disclosing error and reconnects after switch failure", async () => {
    const events: string[] = [];
    const remote = transport();
    remote.select.mockRejectedValueOnce(new Error("provider room secret"));
    const reconnect = transition(events);
    const controller = new ChannelController(remote, reconnect);
    await controller.load();
    await controller.select(privateChannel.id);

    expect(reconnect.completeChannelTransition).toHaveBeenCalled();
    expect(controller.getSnapshot()).toEqual({
      status: "error",
      items: [general, privateChannel],
      selectedId: general.id,
      message: "The channel could not be changed. Your prior channel remains selected.",
    });
    expect(JSON.stringify(controller.getSnapshot())).not.toContain("provider room secret");
  });
});
