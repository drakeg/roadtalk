import { fireEvent, render, waitFor } from "@testing-library/react-native";

import type { ChannelControl } from "../channels/types";
import { ChannelScreen } from "../screens/ChannelScreen";

jest.mock("../channels/api", () => ({ useChannelApi: () => ({}) }));
jest.mock("../media/MediaLifecycleContext", () => ({
  useMediaLifecycle: () => null,
}));

function control(): ChannelControl & {
  select: jest.Mock;
  join: jest.Mock;
  leave: jest.Mock;
} {
  const snapshot = {
    status: "ready" as const,
    selectedId: "general-id",
    items: [
      {
        id: "general-id",
        slug: "general" as const,
        displayLabel: "General",
        type: "public" as const,
        selected: true,
        enabled: true,
        version: 1,
      },
      {
        id: "private-id",
        slug: null,
        displayLabel: "Camp Friends",
        type: "private" as const,
        selected: false,
        enabled: true,
        version: 1,
      },
    ],
  };
  return {
    subscribe: jest.fn(() => () => undefined),
    getSnapshot: jest.fn(() => snapshot),
    load: jest.fn(async () => undefined),
    select: jest.fn(async () => undefined),
    join: jest.fn(async () => undefined),
    leave: jest.fn(async () => undefined),
  };
}

describe("accessible channel catalog", () => {
  it("supports select, leave, and private invite submission without disclosure", async () => {
    const remote = control();
    const view = await render(
      <ChannelScreen
        control={remote}
        navigation={{ goBack: jest.fn() } as never}
        route={{ key: "channels", name: "Channels" }}
      />,
    );

    expect(view.getByRole("header", { name: "Channels" })).toBeOnTheScreen();
    expect(view.getByLabelText("Currently selected")).toBeOnTheScreen();
    await fireEvent.press(
      view.getByRole("button", { name: "Select Camp Friends channel" }),
    );
    expect(remote.select).toHaveBeenCalledWith("private-id");
    await fireEvent.press(
      view.getByRole("button", {
        name: "Leave Camp Friends private channel",
      }),
    );
    expect(remote.leave).toHaveBeenCalledWith("private-id");

    const input = view.getByLabelText("Private channel invite");
    const invite = "rtc1." + "a".repeat(43);
    fireEvent.changeText(input, invite);
    await waitFor(() => {
      expect(view.getByLabelText("Private channel invite").props.value).toBe(invite);
    });
    await fireEvent.press(
      view.getByRole("button", { name: "Join private channel" }),
    );
    expect(remote.join).toHaveBeenCalledWith(invite);
    await waitFor(() => {
      expect(view.getByLabelText("Private channel invite").props.value).toBe("");
    });

    const rendered = view.toJSON();
    expect(JSON.stringify(rendered)).not.toMatch(
      /member_count|owner_id|provider_room|participant_ref|fingerprint/i,
    );
  });
});
