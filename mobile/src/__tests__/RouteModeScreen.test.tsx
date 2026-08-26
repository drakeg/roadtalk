import { fireEvent, render, waitFor } from "@testing-library/react-native";

import { RouteModeScreen } from "../screens/RouteModeScreen";

const mockCurrent = jest.fn();
const mockUpdate = jest.fn();
const mockPrepareChannelTransition = jest.fn();
const mockCompleteChannelTransition = jest.fn();

jest.mock("../routeMode/api", () => {
  const actual = jest.requireActual("../routeMode/api");
  return {
    ...actual,
    useRouteModeApi: () => ({ current: mockCurrent, update: mockUpdate }),
  };
});

jest.mock("../media/MediaLifecycleContext", () => ({
  useMediaLifecycle: () => ({
    prepareChannelTransition: mockPrepareChannelTransition,
    completeChannelTransition: mockCompleteChannelTransition,
  }),
}));

describe("Same-road mobile experience", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCurrent.mockResolvedValue({
      mode: "nearby",
      version: 1,
      selectedAt: "2026-08-26T03:30:00Z",
      availability: "available",
    });
    mockUpdate.mockResolvedValue({
      mode: "same_road",
      version: 2,
      selectedAt: "2026-08-26T03:31:00Z",
      availability: "unavailable",
    });
  });

  it("keeps Nearby as the default and safely transitions into unavailable Same road", async () => {
    const view = await render(
      <RouteModeScreen
        navigation={{} as never}
        route={{ key: "route-mode", name: "RouteMode" }}
      />,
    );

    await waitFor(() => expect(view.getByText("Nearby is active.")).toBeOnTheScreen());
    const nearbyButton = view.getByRole("button", {
      name: "Use Nearby audience mode",
    });
    expect(nearbyButton.props.accessibilityState?.selected).toBe(true);

    await fireEvent.press(
      view.getByRole("button", { name: "Use Same road audience mode" }),
    );

    await waitFor(() =>
      expect(view.getByText("Same road is unavailable right now.")).toBeOnTheScreen(),
    );
    expect(mockPrepareChannelTransition).toHaveBeenCalledTimes(1);
    expect(mockUpdate).toHaveBeenCalledWith("same_road", 1);
    expect(mockCompleteChannelTransition).toHaveBeenCalledTimes(1);
  });

  it("does not expose route details in user-visible copy", async () => {
    const view = await render(
      <RouteModeScreen
        navigation={{} as never}
        route={{ key: "route-mode", name: "RouteMode" }}
      />,
    );

    await waitFor(() => expect(view.getByText("Nearby is active.")).toBeOnTheScreen());
    expect(view.queryByText(/provider/i)).not.toBeOnTheScreen();
    expect(view.queryByText(/corridor/i)).not.toBeOnTheScreen();
    expect(view.queryByText(/bearing/i)).not.toBeOnTheScreen();
  });
});
