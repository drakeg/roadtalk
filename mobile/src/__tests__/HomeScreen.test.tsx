import { fireEvent, render, screen } from "@testing-library/react-native";

import { HomeScreen } from "../screens/HomeScreen";

describe("foundation screen", () => {
  it("provides an accessible foundation shell and navigates to diagnostics", () => {
    const navigate = jest.fn();
    render(
      <HomeScreen
        navigation={{ navigate } as never}
        route={{ key: "foundation", name: "Foundation" }}
      />,
    );

    expect(screen.getByRole("header", { name: "RoadTalk" })).toBeOnTheScreen();
    fireEvent.press(screen.getByRole("button", { name: "Open app diagnostics" }));
    expect(navigate).toHaveBeenCalledWith("Diagnostics");
  });

  it("does not expose later-sprint features", () => {
    render(
      <HomeScreen
        navigation={{ navigate: jest.fn() } as never}
        route={{ key: "foundation", name: "Foundation" }}
      />,
    );

    expect(screen.queryByText(/push.to.talk/i)).not.toBeOnTheScreen();
    expect(screen.queryByText(/nearby/i)).not.toBeOnTheScreen();
    expect(screen.queryByText(/channel/i)).not.toBeOnTheScreen();
  });
});
