import { act, fireEvent, render, waitFor } from "@testing-library/react-native";
import { AppState, type AppStateStatus } from "react-native";

import type { PremiumStatus } from "../premium/api";
import { PremiumScreen } from "../screens/PremiumScreen";

let mockSessionStatus = "authenticated";
jest.mock("../session/SessionContext", () => ({
  useSessionClient: () => ({}),
  useSession: () => ({ snapshot: { status: mockSessionStatus } }),
}));

const api = { status: jest.fn<Promise<PremiumStatus>, []>() };
const props = { api, navigation: {} as never, route: { key: "premium", name: "Premium" as const } };

function active(validForMs = 5 * 60 * 1000): PremiumStatus {
  const now = Date.now();
  return {
    availability: "available",
    provider_mode: "test",
    tier: "premium",
    entitlement_state: "active",
    premium_experience_allowed: true,
    reason: "premium_entitled",
    observed_at: new Date(now).toISOString(),
    valid_until: new Date(now + validForMs).toISOString(),
    checkout_available: false,
    server_authoritative: true,
    communication_authorization_unchanged: true,
  };
}

describe("mobile Premium screen", () => {
  let appStateListener: ((state: AppStateStatus) => void) | undefined;

  beforeEach(() => {
    jest.clearAllMocks();
    mockSessionStatus = "authenticated";
    appStateListener = undefined;
    jest.spyOn(AppState, "addEventListener").mockImplementation((_type, listener) => {
      appStateListener = listener as (state: AppStateStatus) => void;
      return { remove: jest.fn() } as never;
    });
  });

  afterEach(() => jest.useRealTimers());

  it("shows server-confirmed status with provenance and states baseline preservation", async () => {
    api.status.mockResolvedValue(active());
    const view = await render(<PremiumScreen {...props} />);

    expect(await view.findByText("Premium is active for this account.")).toBeOnTheScreen();
    expect(view.getByText("Plan: Premium")).toBeOnTheScreen();
    expect(view.getByText(/deterministic test provider, no billing/)).toBeOnTheScreen();
    expect(view.getByText(/Premium never changes who you can hear or talk to/)).toBeOnTheScreen();
    expect(view.getByText(/Premium purchase is not available/)).toBeOnTheScreen();
    expect(view.getByRole("button", { name: "Check Premium status" })).toBeOnTheScreen();
    expect(view.queryByRole("button", { name: /buy|subscribe|upgrade|checkout|purchase/i })).not.toBeOnTheScreen();
  });

  it("reports the disabled provider without inferring Premium", async () => {
    api.status.mockResolvedValue({ ...active(), availability: "provider_disabled", provider_mode: "disabled", tier: "free", entitlement_state: null, premium_experience_allowed: false, reason: "premium_entitlement_required" });
    const view = await render(<PremiumScreen {...props} />);

    expect(await view.findByText(/not available in this RoadTalk environment/)).toBeOnTheScreen();
    expect(view.getByText("No server-confirmed Premium status is shown.")).toBeOnTheScreen();
    expect(view.queryByText("Plan: Premium")).not.toBeOnTheScreen();
  });

  it("clears status when a re-check fails", async () => {
    api.status.mockResolvedValueOnce(active()).mockRejectedValueOnce(new Error("offline"));
    const view = await render(<PremiumScreen {...props} />);
    expect(await view.findByText("Plan: Premium")).toBeOnTheScreen();

    await fireEvent.press(view.getByRole("button", { name: "Check Premium status" }));

    await waitFor(() => expect(view.queryByText("Plan: Premium")).not.toBeOnTheScreen());
    expect(view.getByText(/unavailable or offline. No cached Premium state/)).toBeOnTheScreen();
  });

  it("clears status when it reaches valid_until", async () => {
    jest.useFakeTimers();
    api.status.mockResolvedValue(active(1_000));
    const view = await render(<PremiumScreen {...props} />);
    expect(await view.findByText("Plan: Premium")).toBeOnTheScreen();

    await act(async () => {
      jest.advanceTimersByTime(1_001);
    });

    expect(view.queryByText("Plan: Premium")).not.toBeOnTheScreen();
    expect(view.getByText(/expired and was cleared/)).toBeOnTheScreen();
  });

  it("clears status when the app leaves the foreground and ignores the in-flight result", async () => {
    let resolveSecond: (value: PremiumStatus) => void = () => undefined;
    api.status
      .mockResolvedValueOnce(active())
      .mockImplementationOnce(() => new Promise((resolve) => { resolveSecond = resolve; }));
    const view = await render(<PremiumScreen {...props} />);
    expect(await view.findByText("Plan: Premium")).toBeOnTheScreen();

    await fireEvent.press(view.getByRole("button", { name: "Check Premium status" }));
    await act(async () => appStateListener?.("background"));
    await act(async () => resolveSecond(active()));

    expect(view.queryByText("Plan: Premium")).not.toBeOnTheScreen();
    expect(view.getByText(/not in the foreground/)).toBeOnTheScreen();
  });

  it("does not request status without an authenticated session", async () => {
    mockSessionStatus = "signed_out";
    const view = await render(<PremiumScreen {...props} />);

    expect(await view.findByText(/Connect to RoadTalk to check Premium status/)).toBeOnTheScreen();
    expect(api.status).not.toHaveBeenCalled();
  });
});
