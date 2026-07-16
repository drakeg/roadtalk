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
  it("provides accessible identity and diagnostics navigation", async () => {
    const navigate = jest.fn();
    const view = await render(
      <HomeScreen
        navigation={{ navigate } as never}
        route={{ key: "foundation", name: "Foundation" }}
      />,
    );

    expect(view.getByRole("header", { name: "RoadTalk" })).toBeOnTheScreen();
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
      view.getByRole("button", { name: "Open app diagnostics" }),
    );
    expect(navigate).toHaveBeenCalledWith("Diagnostics");
  });

  it("does not expose later-sprint features", async () => {
    const view = await render(
      <HomeScreen
        navigation={{ navigate: jest.fn() } as never}
        route={{ key: "foundation", name: "Foundation" }}
      />,
    );

    expect(view.queryByText(/push.to.talk/i)).not.toBeOnTheScreen();
    expect(view.queryByText(/nearby/i)).not.toBeOnTheScreen();
    expect(view.queryByText(/channel/i)).not.toBeOnTheScreen();
  });
});
