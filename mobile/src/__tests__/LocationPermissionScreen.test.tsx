import { fireEvent, render } from "@testing-library/react-native";
import { Linking } from "react-native";

import type {
  LocationLifecycleControl,
  LocationLifecycleSnapshot,
} from "../location/types";
import { LocationPermissionScreen } from "../screens/LocationPermissionScreen";

jest.mock("../session/SessionContext", () => ({
  useSession: () => ({
    snapshot: {
      status: "authenticated",
      accountId: "account",
      deviceId: "device",
      sessionId: "session",
    },
  }),
  useSessionClient: () => ({}),
}));

function lifecycle(initial: LocationLifecycleSnapshot): LocationLifecycleControl & {
  enable: jest.Mock;
  pause: jest.Mock;
} {
  return {
    subscribe: jest.fn(() => () => undefined),
    getSnapshot: jest.fn(() => initial),
    enable: jest.fn(async () => undefined),
    pause: jest.fn(async () => undefined),
    setAppActive: jest.fn(async () => undefined),
    setScreenActive: jest.fn(async () => undefined),
    setAuthenticated: jest.fn(async () => undefined),
    dispose: jest.fn(async () => undefined),
  };
}

function navigation() {
  return {
    addListener: jest.fn(() => jest.fn()),
    goBack: jest.fn(),
    isFocused: jest.fn(() => true),
  };
}

describe("foreground location purpose screen", () => {
  it("explains purpose before invoking the explicit enable action", async () => {
    const control = lifecycle({ status: "purpose" });
    const nav = navigation();
    const view = await render(
      <LocationPermissionScreen
        lifecycle={control}
        navigation={nav as never}
        route={{ key: "location", name: "LocationPermission" }}
      />,
    );

    expect(
      view.getByRole("header", { name: "Foreground location" }),
    ).toBeOnTheScreen();
    expect(view.getByText(/nothing is collected until/i)).toBeOnTheScreen();
    expect(view.getByText(/does not request background access/i)).toBeOnTheScreen();
    expect(view.getByText(/approximate or reduced accuracy/i)).toBeOnTheScreen();
    expect(control.enable).not.toHaveBeenCalled();

    await fireEvent.press(
      view.getByRole("button", { name: "Enable foreground location" }),
    );
    expect(control.enable).toHaveBeenCalledTimes(1);

    await fireEvent.press(
      view.getByRole("button", { name: "Continue without location" }),
    );
    expect(nav.goBack).toHaveBeenCalledTimes(1);
  });

  it("offers settings for blocked permission and pause for active permission", async () => {
    const openSettings = jest
      .spyOn(Linking, "openSettings")
      .mockResolvedValue(undefined);
    const blocked = lifecycle({ status: "blocked" });
    const blockedView = await render(
      <LocationPermissionScreen
        lifecycle={blocked}
        navigation={navigation() as never}
        route={{ key: "blocked", name: "LocationPermission" }}
      />,
    );

    await fireEvent.press(
      blockedView.getByRole("button", {
        name: "Open device settings for location permission",
      }),
    );
    expect(openSettings).toHaveBeenCalledTimes(1);
    await blockedView.unmount();

    const active = lifecycle({
      status: "active",
      precision: "approximate",
      upload: "current",
      local: {
        status: "current",
        horizontalAccuracyM: 24.6,
        headingDeg: 91,
        speedMps: 4,
        observedAtMs: Date.parse("2026-07-16T12:00:00Z"),
      },
      nearby: {
        status: "current",
        bucket: "few",
        expiresAtMs: Date.parse("2026-07-16T12:02:00Z"),
      },
    });
    const activeView = await render(
      <LocationPermissionScreen
        lifecycle={active}
        navigation={navigation() as never}
        route={{ key: "active", name: "LocationPermission" }}
      />,
    );
    expect(activeView.getByText(/approximate permission is active/i)).toBeOnTheScreen();
    expect(activeView.getByText("About ±25 m")).toBeOnTheScreen();
    expect(activeView.getByText("91° E")).toBeOnTheScreen();
    expect(activeView.getByText("9 mph")).toBeOnTheScreen();
    expect(activeView.getByText(/some nearby roadtalk activity/i)).toBeOnTheScreen();
    expect(activeView.getByText(/never shows who, how many exactly/i)).toBeOnTheScreen();
    await fireEvent.press(
      activeView.getByRole("button", {
        name: "Pause and remove current location",
      }),
    );
    expect(active.pause).toHaveBeenCalledTimes(1);
    await fireEvent.press(
      activeView.getByRole("button", { name: "Open device location settings" }),
    );
    expect(openSettings).toHaveBeenCalledTimes(2);
  });

  it.each([
    { status: "checking" as const, message: /checking permission/i, button: null },
    {
      status: "unavailable" as const,
      message: /location services are unavailable/i,
      button: "Retry foreground location",
    },
    {
      status: "denied" as const,
      message: /permission not granted/i,
      button: "Retry foreground location",
    },
    {
      status: "error" as const,
      message: /location could not start/i,
      button: "Retry foreground location",
    },
  ])("renders an accessible $status state", async ({ status, message, button }) => {
    const control = lifecycle({ status });
    const view = await render(
      <LocationPermissionScreen
        lifecycle={control}
        navigation={navigation() as never}
        route={{ key: status, name: "LocationPermission" }}
      />,
    );

    expect(view.getByText(message)).toBeOnTheScreen();
    if (button !== null) {
      await fireEvent.press(view.getByRole("button", { name: button }));
      expect(control.enable).toHaveBeenCalledTimes(1);
    } else {
      expect(
        view.queryByRole("button", { name: "Retry foreground location" }),
      ).not.toBeOnTheScreen();
    }
    await view.unmount();
  });

  it.each([
    ["none" as const, /no nearby roadtalk activity/i],
    ["few" as const, /some nearby roadtalk activity/i],
    ["many" as const, /more nearby roadtalk activity/i],
  ])("renders only the semantic %s nearby bucket", async (bucket, message) => {
    const view = await render(
      <LocationPermissionScreen
        lifecycle={lifecycle({
          status: "active",
          precision: "precise",
          upload: "current",
          local: {
            status: "stale",
            horizontalAccuracyM: 50,
            headingDeg: null,
            speedMps: null,
            observedAtMs: Date.parse("2026-07-16T12:00:00Z"),
          },
          nearby: {
            status: "current",
            bucket,
            expiresAtMs: Date.parse("2026-07-16T12:02:00Z"),
          },
        })}
        navigation={navigation() as never}
        route={{ key: bucket, name: "LocationPermission" }}
      />,
    );

    expect(view.getByText(message)).toBeOnTheScreen();
    expect(view.getByText("Stale")).toBeOnTheScreen();
    expect(view.getAllByText("Unavailable")).toHaveLength(2);
    expect(view.queryByText(/callsign|avatar|bearing/i)).not.toBeOnTheScreen();
    await view.unmount();
  });
});
