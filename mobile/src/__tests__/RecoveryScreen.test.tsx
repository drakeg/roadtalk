import {
  act,
  fireEvent,
  render,
  waitFor,
} from "@testing-library/react-native";

import {
  RecoveryApiError,
  useRecoveryApi,
} from "../recovery/api";
import type { RecoveryApi } from "../recovery/api";
import type { RecoveryKeyStorage } from "../recovery/storage";
import { RecoveryScreen } from "../screens/RecoveryScreen";

jest.mock("../recovery/api", () => {
  const actual =
    jest.requireActual<typeof import("../recovery/api")>("../recovery/api");
  return { ...actual, useRecoveryApi: jest.fn() };
});

const mockedUseRecoveryApi = jest.mocked(useRecoveryApi);

function api() {
  return {
    createRecoveryKey: jest.fn(async () => ({
      recovery_key: "rtk1.created.secret",
      key_version: "rtk1" as const,
    })),
    recover: jest.fn(async () => ({
      recoveryKey: "rtk1.rotated.secret",
      recoveryKeyVersion: "rtk1" as const,
    })),
  };
}

function storage(): RecoveryKeyStorage {
  return {
    writeRecoveryKey: jest.fn(async () => undefined),
    clearRecoveryKey: jest.fn(async () => undefined),
  };
}

async function renderScreen(recoveryStorage = storage()) {
  return render(
    <RecoveryScreen
      navigation={{} as never}
      route={{ key: "recovery", name: "Recovery" }}
      storage={recoveryStorage}
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

describe("mobile recovery experience", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("displays a created key once without storing it by default", async () => {
    const remote = api();
    const secure = storage();
    mockedUseRecoveryApi.mockReturnValue(remote as unknown as RecoveryApi);
    const view = await renderScreen(secure);

    await flushInteraction(() =>
      fireEvent.press(
        view.getByRole("button", { name: "Create or rotate recovery key" }),
      ),
    );

    expect(await view.findByText("rtk1.created.secret")).toBeOnTheScreen();
    expect(view.getByText(/Not saved by RoadTalk/i)).toBeOnTheScreen();
    expect(secure.clearRecoveryKey).toHaveBeenCalled();
    expect(secure.writeRecoveryKey).not.toHaveBeenCalled();

    await flushInteraction(() =>
      fireEvent.press(view.getByRole("button", { name: "I saved the key" })),
    );
    expect(view.queryByText("rtk1.created.secret")).not.toBeOnTheScreen();
  });

  it("uses SecureStore only after explicit user opt-in", async () => {
    const remote = api();
    const secure = storage();
    mockedUseRecoveryApi.mockReturnValue(remote as unknown as RecoveryApi);
    const view = await renderScreen(secure);

    fireEvent(
      view.getByLabelText("Save recovery key in secure storage"),
      "valueChange",
      true,
    );
    await flushInteraction(() =>
      fireEvent.press(
        view.getByRole("button", { name: "Create or rotate recovery key" }),
      ),
    );

    await waitFor(() =>
      expect(secure.writeRecoveryKey).toHaveBeenCalledWith(
        "rtk1.created.secret",
      ),
    );
    expect(view.getByText("Saved securely on this device.")).toBeOnTheScreen();
  });

  it("recovers the session, clears the submitted key, and shows the rotation once", async () => {
    const remote = api();
    mockedUseRecoveryApi.mockReturnValue(remote as unknown as RecoveryApi);
    const view = await renderScreen();

    fireEvent.changeText(
      view.getByLabelText("Recovery key"),
      "rtk1.original.secret",
    );
    await flushInteraction(() =>
      fireEvent.press(view.getByRole("button", { name: "Recover account" })),
    );

    await waitFor(() =>
      expect(remote.recover).toHaveBeenCalledWith("rtk1.original.secret"),
    );
    expect(
      view.getByText("Account recovered. Older sessions were signed out."),
    ).toBeOnTheScreen();
    expect(view.getByText("rtk1.rotated.secret")).toBeOnTheScreen();
    expect(view.getByLabelText("Recovery key").props.value).toBe("");
    expect(JSON.stringify(view.toJSON())).not.toContain(
      "rtk1.original.secret",
    );
  });

  it.each(["invalid", "unknown", "replayed"])(
    "uses one non-enumerating error for %s keys",
    async () => {
      const remote = api();
      remote.recover.mockRejectedValue(
        new RecoveryApiError(
          401,
          "RECOVERY_FAILED",
          "The account could not be recovered with that key.",
        ),
      );
      mockedUseRecoveryApi.mockReturnValue(remote as unknown as RecoveryApi);
      const view = await renderScreen();

      fireEvent.changeText(view.getByLabelText("Recovery key"), "candidate");
      await flushInteraction(() =>
        fireEvent.press(view.getByRole("button", { name: "Recover account" })),
      );

      expect(
        await view.findByText("Recovery could not be completed with that key."),
      ).toBeOnTheScreen();
    },
  );

  it("does not expose later-sprint permissions or clipboard behavior", async () => {
    const remote = api();
    mockedUseRecoveryApi.mockReturnValue(remote as unknown as RecoveryApi);
    const view = await renderScreen();

    expect(view.getByText(/never requests contacts, photos, location/i)).toBeOnTheScreen();
    expect(view.queryByText(/copy to clipboard/i)).not.toBeOnTheScreen();
    expect(view.queryByText(/push.to.talk/i)).not.toBeOnTheScreen();
    expect(view.queryByText(/nearby/i)).not.toBeOnTheScreen();
  });
});
