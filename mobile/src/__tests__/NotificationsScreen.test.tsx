import { fireEvent, render, waitFor } from "@testing-library/react-native";

import type { NotificationApi } from "../notifications/api";
import { NotificationsScreen } from "../screens/NotificationsScreen";

jest.mock("../notifications/api", () => {
  const actual = jest.requireActual("../notifications/api");
  return {
    ...actual,
    useNotificationApi: () => ({}),
  };
});

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

const urgent = {
  id: "00000000-0000-4000-8000-000000000102",
  notificationClass: "urgent_alert" as const,
  priority: "urgent" as const,
  source: "user_generated_urgent" as const,
  title: null,
  message: "Disabled vehicle blocking the right lane.",
  channelLabel: "General",
  issuedAt: new Date(Date.now() - 60_000).toISOString(),
  expiresAt: new Date(Date.now() + 10 * 60_000).toISOString(),
  readAt: null,
  dismissedAt: null,
  version: 1,
  verified: false as const,
  emergencyService: false as const,
  deliveryGuaranteed: false as const,
  safetyNotEmergencyService: "RoadTalk is not an emergency service." as const,
  safetyDeliveryNotGuaranteed: "Delivery is not guaranteed." as const,
  safetyEmergencyServicesGuidance:
    "Contact local emergency services directly when emergency assistance is needed." as const,
  safetyUnverified: "This alert is user-generated and unverified." as const,
};

function api(): NotificationApi & {
  preferences: jest.Mock;
  inbox: jest.Mock;
  updatePreferences: jest.Mock;
  updateState: jest.Mock;
  sendUrgentAlert: jest.Mock;
} {
  return {
    preferences: jest.fn(async () => ({
      channelActivityEnabled: true,
      urgentAlertEnabled: true,
      version: 1,
    })),
    inbox: jest.fn(async () => ({ items: [urgent] })),
    updatePreferences: jest.fn(async (_current, update) => ({
      ...update,
      version: 2,
    })),
    updateState: jest.fn(async (notification, state) => ({
      ...notification,
      readAt: state === "read" ? new Date().toISOString() : notification.readAt,
      dismissedAt:
        state === "dismissed" ? new Date().toISOString() : notification.dismissedAt,
      version: notification.version + 1,
    })),
    sendUrgentAlert: jest.fn(async () => ({
      accepted: true,
      recipientCount: 2,
      issuedAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 10 * 60_000).toISOString(),
    })),
  } as unknown as NotificationApi & {
    preferences: jest.Mock;
    inbox: jest.Mock;
    updatePreferences: jest.Mock;
    updateState: jest.Mock;
    sendUrgentAlert: jest.Mock;
  };
}

describe("mobile notifications experience", () => {
  it("renders inbox safety, degraded provider state, and preferences", async () => {
    const client = api();
    const view = await render(
      <NotificationsScreen
        api={client}
        navigation={{} as never}
        route={{ key: "notifications", name: "Notifications" }}
      />,
    );

    await waitFor(() => expect(client.inbox).toHaveBeenCalledTimes(1));
    expect(view.getByRole("header", { name: "Notifications" })).toBeOnTheScreen();
    expect(view.getByText(/external push delivery is not active/i)).toBeOnTheScreen();
    expect(view.getByText(/os push and background notification delivery are unavailable/i)).toBeOnTheScreen();
    expect(view.getAllByText("RoadTalk is not an emergency service.").length).toBeGreaterThan(0);
    expect(view.getAllByText("Delivery is not guaranteed.").length).toBeGreaterThan(0);
    expect(view.getByText(/disabled vehicle blocking the right lane/i)).toBeOnTheScreen();
    expect(view.getByRole("switch", { name: "Channel activity notifications" })).toBeOnTheScreen();
    expect(view.getByRole("switch", { name: "Urgent alert notifications" })).toBeOnTheScreen();
  });

  it("updates a notification preference", async () => {
    const client = api();
    const view = await render(
      <NotificationsScreen
        api={client}
        navigation={{} as never}
        route={{ key: "notifications", name: "Notifications" }}
      />,
    );
    await waitFor(() => expect(client.preferences).toHaveBeenCalledTimes(1));

    fireEvent(
      view.getByRole("switch", { name: "Channel activity notifications" }),
      "valueChange",
      false,
    );
    await waitFor(() => expect(client.updatePreferences).toHaveBeenCalledTimes(1));
    await waitFor(() =>
      expect(view.getByText("Notification preferences saved.")).toBeOnTheScreen(),
    );
  });

  it("sends only the urgent message with server-side targeting semantics", async () => {
    const client = api();
    const view = await render(
      <NotificationsScreen
        api={client}
        navigation={{} as never}
        route={{ key: "notifications", name: "Notifications" }}
      />,
    );
    await waitFor(() =>
      expect(view.getByText("1 current notification loaded.")).toBeOnTheScreen(),
    );

    fireEvent.changeText(
      view.getByLabelText("Urgent alert message"),
      "Disabled vehicle ahead",
    );
    await waitFor(() => expect(view.getByText("22/280")).toBeOnTheScreen());
    fireEvent.press(
      view.getByRole("button", { name: "Send RoadTalk urgent alert" }),
    );
    await waitFor(() =>
      expect(client.sendUrgentAlert).toHaveBeenCalledWith("Disabled vehicle ahead"),
    );
    expect(view.getByText(/cannot target a person, coordinate, radius, route, or destination/i)).toBeOnTheScreen();
  });

  it("marks notifications read and dismisses them", async () => {
    const client = api();
    const view = await render(
      <NotificationsScreen
        api={client}
        navigation={{} as never}
        route={{ key: "notifications", name: "Notifications" }}
      />,
    );
    await waitFor(() => expect(client.inbox).toHaveBeenCalledTimes(1));

    fireEvent.press(view.getByRole("button", { name: "Mark notification read" }));
    await waitFor(() => expect(client.updateState).toHaveBeenCalledWith(urgent, "read"));
  });
});
