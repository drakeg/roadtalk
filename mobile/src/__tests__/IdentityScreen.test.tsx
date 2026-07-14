import {
  act,
  fireEvent,
  render,
  waitFor,
} from "@testing-library/react-native";

import {
  IdentityApiError,
  useIdentityApi,
} from "../identity/api";
import type { IdentityApi } from "../identity/api";
import type { CallsignAvailability, Profile } from "../identity/types";
import { IdentityScreen } from "../screens/IdentityScreen";

jest.mock("../identity/api", () => {
  const actual =
    jest.requireActual<typeof import("../identity/api")>("../identity/api");
  return { ...actual, useIdentityApi: jest.fn() };
});

const mockedUseIdentityApi = jest.mocked(useIdentityApi);

function incompleteProfile(): Profile {
  return {
    identity: { callsign: null, avatar_id: null },
    setup_completed: false,
    version: 0,
  };
}

function completeProfile(): Profile {
  return {
    identity: { callsign: "Road-Runner", avatar_id: "road-runner" },
    setup_completed: true,
    version: 3,
  };
}

function api() {
  return {
    getProfile: jest.fn(async () => incompleteProfile()),
    checkCallsign: jest.fn(
      async (): Promise<CallsignAvailability> => ({
        available: true,
        reason: "available",
      }),
    ),
    updateProfile: jest.fn(async () => completeProfile()),
  };
}

async function renderScreen() {
  return render(
    <IdentityScreen
      navigation={{} as never}
      route={{ key: "identity", name: "Identity" }}
    />,
  );
}

async function flushInteraction(interaction: () => void) {
  await act(async () => {
    interaction();
    await Promise.resolve();
    await Promise.resolve();
  });
}

describe("mobile identity experience", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("completes accessible callsign and avatar setup", async () => {
    const remote = api();
    mockedUseIdentityApi.mockReturnValue(remote as unknown as IdentityApi);
    const view = await renderScreen();

    expect(
      await view.findByRole("header", { name: "Set up your identity" }),
    ).toBeOnTheScreen();
    await flushInteraction(() =>
      fireEvent.changeText(view.getByLabelText("Callsign"), " Road-Runner "),
    );
    await flushInteraction(() =>
      fireEvent.press(
        view.getByRole("radio", { name: "Select Orange horizon avatar" }),
      ),
    );
    await flushInteraction(() =>
      fireEvent.press(
        view.getByRole("button", { name: "Check callsign availability" }),
      ),
    );
    expect(await view.findByText("This callsign is available.")).toBeOnTheScreen();

    await flushInteraction(() =>
      fireEvent.press(view.getByRole("button", { name: "Save identity" })),
    );

    await waitFor(() =>
      expect(remote.updateProfile).toHaveBeenCalledWith({
        version: 0,
        callsign: "Road-Runner",
        avatar_id: "road-runner",
      }),
    );
    expect(await view.findByText("Identity saved.")).toBeOnTheScreen();
    expect(view.getByText(/public pseudonym/i)).toBeOnTheScreen();
  });

  it("rejects malformed callsigns before a network availability request", async () => {
    const remote = api();
    mockedUseIdentityApi.mockReturnValue(remote as unknown as IdentityApi);
    const view = await renderScreen();
    await view.findByRole("header", { name: "Set up your identity" });

    await flushInteraction(() =>
      fireEvent.changeText(view.getByLabelText("Callsign"), "road talk"),
    );
    await flushInteraction(() =>
      fireEvent.press(
        view.getByRole("button", { name: "Check callsign availability" }),
      ),
    );

    expect(
      view.getByText(/ASCII letters, numbers, or single internal hyphens/i),
    ).toBeOnTheScreen();
    expect(remote.checkCallsign).not.toHaveBeenCalled();
  });

  it("shows unavailable server decisions without owner information", async () => {
    const remote = api();
    remote.checkCallsign.mockResolvedValue({
      available: false,
      reason: "taken",
    });
    mockedUseIdentityApi.mockReturnValue(remote as unknown as IdentityApi);
    const view = await renderScreen();
    await view.findByRole("header", { name: "Set up your identity" });

    await flushInteraction(() =>
      fireEvent.changeText(view.getByLabelText("Callsign"), "Night-Owl"),
    );
    await flushInteraction(() =>
      fireEvent.press(
        view.getByRole("button", { name: "Check callsign availability" }),
      ),
    );

    expect(
      await view.findByText("That callsign is unavailable."),
    ).toBeOnTheScreen();
    expect(JSON.stringify(view.toJSON())).not.toContain("account_id");
  });

  it("recovers from an offline load with an explicit retry", async () => {
    const remote = api();
    remote.getProfile
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce(incompleteProfile());
    mockedUseIdentityApi.mockReturnValue(remote as unknown as IdentityApi);
    const view = await renderScreen();

    expect(
      await view.findByText(/Identity is unavailable/i),
    ).toBeOnTheScreen();
    await flushInteraction(() =>
      fireEvent.press(
        view.getByRole("button", { name: "Retry loading identity" }),
      ),
    );

    expect(
      await view.findByRole("header", { name: "Set up your identity" }),
    ).toBeOnTheScreen();
    expect(remote.getProfile).toHaveBeenCalledTimes(2);
  });

  it("requires a reload after an optimistic concurrency conflict", async () => {
    const remote = api();
    remote.getProfile.mockResolvedValue(completeProfile());
    remote.updateProfile.mockRejectedValue(
      new IdentityApiError(
        409,
        "PROFILE_VERSION_CONFLICT",
        "The profile changed.",
      ),
    );
    mockedUseIdentityApi.mockReturnValue(remote as unknown as IdentityApi);
    const view = await renderScreen();
    await view.findByRole("header", { name: "Edit your identity" });

    await flushInteraction(() =>
      fireEvent.press(view.getByRole("button", { name: "Save identity" })),
    );

    expect(
      await view.findByText(/changed on another session/i),
    ).toBeOnTheScreen();
    await flushInteraction(() =>
      fireEvent.press(view.getByRole("button", { name: "Reload profile" })),
    );
    await waitFor(() => expect(remote.getProfile).toHaveBeenCalledTimes(2));
  });

  it("does not expose later-sprint permissions or features", async () => {
    const remote = api();
    mockedUseIdentityApi.mockReturnValue(remote as unknown as IdentityApi);
    const view = await renderScreen();
    await view.findByRole("header", { name: "Set up your identity" });

    expect(view.getByText(/never requests location, microphone/i)).toBeOnTheScreen();
    expect(view.queryByText(/push.to.talk/i)).not.toBeOnTheScreen();
    expect(view.queryByText(/nearby/i)).not.toBeOnTheScreen();
    expect(view.queryByText(/channel/i)).not.toBeOnTheScreen();
  });
});
