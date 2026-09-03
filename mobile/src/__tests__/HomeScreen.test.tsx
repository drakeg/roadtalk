import { fireEvent, render } from "@testing-library/react-native";

import { HomeScreen } from "../screens/HomeScreen";

jest.mock("../session/SessionContext", () => ({
  useSession: () => ({
    snapshot: {
      status: "authenticated",
      accountId: "account",
      deviceId: "device",
      sessionId: "session",
    },
    logout: jest.fn(),
    reconnect: jest.fn(),
    revokeCurrentDevice: jest.fn(),
  }),
}));

describe("foundation screen", () => {
  it("provides accessible notifications, map, radio, audience, identity, and diagnostics navigation", async () => {
    const navigate = jest.fn();
    const view = await render(
      <HomeScreen
        navigation={{ navigate } as never}
        route={{ key: "foundation", name: "Foundation" }}
      />,
    );

    expect(view.getByRole("header", { name: "RoadTalk" })).toBeOnTheScreen();
    await fireEvent.press(view.getByRole("button", { name: "Open notifications" }));
    expect(navigate).toHaveBeenCalledWith("Notifications");
    await fireEvent.press(view.getByRole("button", { name: "Open map awareness" }));
    expect(navigate).toHaveBeenCalledWith("MapAwareness");
    await fireEvent.press(
      view.getByRole("button", { name: "Choose a RoadTalk channel" }),
    );
    expect(navigate).toHaveBeenCalledWith("Channels");
    await fireEvent.press(
      view.getByRole("button", { name: "Choose Nearby or Same road audience mode" }),
    );
    expect(navigate).toHaveBeenCalledWith("RouteMode");
    await fireEvent.press(
      view.getByRole("button", { name: "Set up or edit identity" }),
    );
    expect(navigate).toHaveBeenCalledWith("Identity");
    await fireEvent.press(
      view.getByRole("button", {
        name: "Create a recovery key or recover an account",
      }),
    );
    expect(navigate).toHaveBeenCalledWith("Recovery");
    await fireEvent.press(
      view.getByRole("button", { name: "Review foreground location privacy" }),
    );
    expect(navigate).toHaveBeenCalledWith("LocationPermission");
    await fireEvent.press(
      view.getByRole("button", {
        name: "Review microphone and live audio privacy",
      }),
    );
    expect(navigate).toHaveBeenCalledWith("MicrophonePermission");
    await fireEvent.press(
      view.getByRole("button", { name: "Open app diagnostics" }),
    );
    expect(navigate).toHaveBeenCalledWith("Diagnostics");
  });

  it("presents the current RoadTalk communication capabilities", async () => {
    const view = await render(
      <HomeScreen
        navigation={{ navigate: jest.fn() } as never}
        route={{ key: "foundation", name: "Foundation" }}
      />,
    );

    expect(view.getByText(/control who you can hear/i)).toBeOnTheScreen();
    expect(view.getByRole("button", { name: "Open notifications" })).toBeOnTheScreen();
    expect(view.getByRole("button", { name: "Open map awareness" })).toBeOnTheScreen();
    expect(
      view.getByRole("button", { name: "Choose Nearby or Same road audience mode" }),
    ).toBeOnTheScreen();
    expect(view.getByRole("button", { name: "Choose a RoadTalk channel" })).toBeOnTheScreen();
  });
});
