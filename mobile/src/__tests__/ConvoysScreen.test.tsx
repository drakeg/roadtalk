import { fireEvent, render, waitFor } from "@testing-library/react-native";
import { Alert } from "react-native";

import { ConvoysScreen } from "../screens/ConvoysScreen";

const api = {
  status: jest.fn(),
  awareness: jest.fn(),
  create: jest.fn(),
  join: jest.fn(),
  leave: jest.fn(),
  disband: jest.fn(),
};

jest.mock("../session/SessionContext", () => ({
  useSessionClient: () => ({}),
  useSession: () => ({ snapshot: { status: "authenticated" } }),
}));

describe("mobile convoy screen", () => {
  beforeEach(() => jest.clearAllMocks());

  it("shows only server-returned bounded awareness", async () => {
    api.status.mockResolvedValue({ convoy_id: "c1", membership_id: "m1", display_name: "Road Crew", role: "member", state: "active" });
    api.awareness.mockResolvedValue({ convoy_id: "c1", freshness: "current", expires_at: "2030-01-01T00:00:00Z", members: [{ account_id: "a1", callsign: "Mallard", role: "member", availability: "current", expires_at: "2030-01-01T00:00:00Z" }] });
    const view = render(<ConvoysScreen api={api as never} navigation={{} as never} route={{ key: "convoys", name: "Convoys" }} />);
    expect(await view.findByText("Mallard · member · current")).toBeOnTheScreen();
    expect(view.queryByText(/latitude|longitude|route history/i)).not.toBeOnTheScreen();
    expect(view.getByRole("button", { name: "Leave convoy" })).toBeOnTheScreen();
  });

  it("clears stale member state when refresh fails", async () => {
    api.status.mockResolvedValueOnce({ convoy_id: "c1", membership_id: "m1", display_name: "Road Crew", role: "member", state: "active" }).mockRejectedValueOnce(new Error("offline"));
    api.awareness.mockResolvedValue({ convoy_id: "c1", freshness: "current", expires_at: "2030-01-01T00:00:00Z", members: [{ account_id: "a1", callsign: "Mallard", role: "member", availability: "current", expires_at: "2030-01-01T00:00:00Z" }] });
    const view = render(<ConvoysScreen api={api as never} navigation={{} as never} route={{ key: "convoys", name: "Convoys" }} />);
    expect(await view.findByText("Mallard · member · current")).toBeOnTheScreen();
    await fireEvent.press(view.getByRole("button", { name: "Refresh convoy state" }));
    await waitFor(() => expect(view.queryByText("Mallard · member · current")).not.toBeOnTheScreen());
    expect(view.getByText(/offline, stale, permission-denied, or revoked/i)).toBeOnTheScreen();
  });

  it("requires destructive confirmation", async () => {
    api.status.mockResolvedValue({ convoy_id: "c1", membership_id: "m1", display_name: "Road Crew", role: "leader", state: "active" });
    api.awareness.mockResolvedValue({ convoy_id: "c1", freshness: "current", expires_at: "2030-01-01T00:00:00Z", members: [] });
    const alert = jest.spyOn(Alert, "alert").mockImplementation(jest.fn());
    const view = render(<ConvoysScreen api={api as never} navigation={{} as never} route={{ key: "convoys", name: "Convoys" }} />);
    await fireEvent.press(await view.findByRole("button", { name: "Disband convoy" }));
    expect(alert).toHaveBeenCalledWith("Disband convoy?", expect.any(String), expect.any(Array));
    expect(api.disband).not.toHaveBeenCalled();
  });
});
