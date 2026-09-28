import { act, fireEvent, render, waitFor } from "@testing-library/react-native";
import { Alert } from "react-native";

import { SafetyScreen } from "../screens/SafetyScreen";

const api = { restrictions: jest.fn(), report: jest.fn(), restrict: jest.fn(), revoke: jest.fn() };
const mockUseSession = jest.fn();
jest.mock("../session/SessionContext", () => ({
  useSessionClient: () => ({}),
  useSession: () => mockUseSession(),
}));

const props = { api: api as never, navigation: {} as never, route: { key: "safety", name: "Safety" as const } };

describe("mobile safety controls", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseSession.mockReturnValue({ snapshot: { status: "authenticated" } });
    api.restrictions.mockResolvedValue({ items: [] });
  });

  it("requires confirmation before report or block and sends no command on cancel", async () => {
    const alert = jest.spyOn(Alert, "alert").mockImplementation(jest.fn());
    const view = await render(<SafetyScreen {...props} />);
    await waitFor(() => expect(view.getByText("Current safety controls loaded.")).toBeOnTheScreen());
    fireEvent.changeText(view.getByLabelText("Account ID"), "00000000-0000-4000-8000-000000000001");
    await waitFor(() => expect(view.getByRole("button", { name: "Block account" })).not.toBeDisabled());
    await act(async () => { fireEvent.press(view.getByRole("button", { name: "Block account" })); });
    expect(alert).toHaveBeenCalledWith("Block account?", expect.any(String), expect.any(Array));
    expect(api.restrict).not.toHaveBeenCalled();
    await act(async () => { fireEvent.press(view.getByRole("button", { name: "Submit report" })); });
    expect(api.report).not.toHaveBeenCalled();
    await view.unmount();
  });

  it("clears cached restriction state on failed refresh", async () => {
    api.restrictions.mockResolvedValue({
      items: [{ restriction_id: "r1", subject_account_id: "a1", kind: "block" }],
    });
    const view = await render(<SafetyScreen {...props} />);
    expect(await view.findByText("Blocked account a1")).toBeOnTheScreen();

    api.restrictions.mockRejectedValue(new Error("offline"));
    await act(async () => { fireEvent.press(view.getByRole("button", { name: "Refresh safety controls" })); });

    await waitFor(() => expect(view.queryByText("Blocked account a1")).not.toBeOnTheScreen());
    expect(view.getByText(/Existing server-side restrictions remain enforced/)).toBeOnTheScreen();
    await view.unmount();
  });

  it("does not show stale controls or allow actions when signed out", async () => {
    mockUseSession.mockReturnValue({ snapshot: { status: "signed_out" } });
    const view = await render(<SafetyScreen {...props} />);
    await waitFor(() => expect(view.getByText(/No cached restrictions are shown/)).toBeOnTheScreen());
    expect(api.restrictions).not.toHaveBeenCalled();
    expect(view.getByRole("button", { name: "Block account" })).toBeDisabled();
    await view.unmount();
  });
});
