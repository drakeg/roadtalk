import { fireEvent, render } from "@testing-library/react-native";

import type {
  MediaLifecycleControl,
  MediaLifecycleSnapshot,
} from "../media/types";
import { MicrophonePermissionScreen } from "../screens/MicrophonePermissionScreen";

jest.mock("../media/defaultLifecycle", () => ({
  createDefaultMediaLifecycle: jest.fn(),
}));

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

function lifecycle(
  snapshot: MediaLifecycleSnapshot,
): MediaLifecycleControl & {
  pressToTalk: jest.Mock;
  releaseToTalk: jest.Mock;
} {
  return {
    subscribe: jest.fn(() => () => undefined),
    getSnapshot: jest.fn(() => snapshot),
    enable: jest.fn(async () => undefined),
    pressToTalk: jest.fn(async () => undefined),
    releaseToTalk: jest.fn(async () => undefined),
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

function screen(control: MediaLifecycleControl) {
  return (
    <MicrophonePermissionScreen
      lifecycle={control}
      navigation={navigation() as never}
      route={{ key: "microphone", name: "MicrophonePermission" }}
    />
  );
}

describe("accessible hold-to-talk screen", () => {
  it("starts authorization on press and stops on release", async () => {
    const control = lifecycle({ status: "ready" });
    const view = await render(screen(control));
    const button = view.getByRole("button", {
      name: "Hold to talk. Microphone off",
    });

    expect(view.getByText("○ OFF")).toBeOnTheScreen();
    expect(view.getByText("HOLD TO TALK")).toBeOnTheScreen();
    expect(button).toHaveStyle({ minHeight: 112 });

    await fireEvent(button, "pressIn");
    expect(control.pressToTalk).toHaveBeenCalledTimes(1);

    await fireEvent(button, "pressOut");
    expect(control.releaseToTalk).toHaveBeenCalledTimes(1);
  });

  it.each([
    [
      { status: "authorizing" } as const,
      "Authorizing microphone transmission. Keep holding",
      "… WAIT",
      "KEEP HOLDING",
    ],
    [
      { status: "transmitting" } as const,
      "Transmitting. Release to stop",
      "● LIVE",
      "RELEASE TO STOP",
    ],
  ])(
    "uses screen-reader and non-color cues for $snapshot.status",
    async (snapshot, label, cue, instruction) => {
      const view = await render(screen(lifecycle(snapshot)));

      expect(view.getByRole("button", { name: label })).toBeOnTheScreen();
      expect(view.getByText(cue)).toBeOnTheScreen();
      expect(view.getByText(instruction)).toBeOnTheScreen();
    },
  );

  it("explains the mandatory maximum without implying capture remains on", async () => {
    const view = await render(
      screen(lifecycle({ status: "ready", reason: "maximum" })),
    );

    expect(view.getByText(/30-second maximum was reached/i)).toBeOnTheScreen();
    expect(
      view.getByRole("button", { name: "Hold to talk. Microphone off" }),
    ).toBeOnTheScreen();
  });

  it.each([
    ["receiving", /another participant is speaking/i],
    ["busy", /nothing was captured/i],
    ["degraded", /temporarily unavailable or rate limited/i],
    ["transmit_error", /stopped capture and released/i],
    ["reconnecting", /restoring receive-only audio/i],
  ] as const)("renders a non-color %s state", async (status, copy) => {
    const view = await render(screen(lifecycle({ status })));

    expect(view.getByText(copy)).toBeOnTheScreen();
  });
});
