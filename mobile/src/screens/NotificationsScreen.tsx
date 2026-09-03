import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from "react-native";

import type { RootStackParamList } from "../AppNavigator";
import {
  NotificationApi,
  NotificationApiError,
  useNotificationApi,
} from "../notifications/api";
import type {
  NotificationPreferences,
  NotificationRecord,
  NotificationState,
} from "../notifications/types";
import { useSession } from "../session/SessionContext";
import { colors, spacing } from "../theme";

type Props = NativeStackScreenProps<RootStackParamList, "Notifications"> & {
  api?: NotificationApi;
};

type LoadState = "loading" | "ready" | "error";

function describeError(error: unknown): string {
  if (!(error instanceof NotificationApiError)) {
    return "Notifications are temporarily unavailable.";
  }
  switch (error.code) {
    case "REGISTERED_ACCOUNT_REQUIRED":
      return "A persistent registered account is required to send an urgent alert.";
    case "NOTIFICATION_PREFERENCES_VERSION_CONFLICT":
    case "NOTIFICATION_VERSION_CONFLICT":
      return "Notifications changed on another session. Refresh and try again.";
    case "NOTIFICATION_UNAVAILABLE":
      return "RoadTalk could not reach the notification service.";
    default:
      return "The notification request could not be completed.";
  }
}

function sourceLabel(notification: NotificationRecord): string {
  switch (notification.source) {
    case "roadtalk_account":
      return "RoadTalk account";
    case "roadtalk_channel":
      return "RoadTalk channel";
    case "user_generated_urgent":
      return "User-generated urgent alert";
  }
}

function ageLabel(issuedAt: string, now = Date.now()): string {
  const seconds = Math.max(0, Math.floor((now - Date.parse(issuedAt)) / 1000));
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hr ago`;
  return `${Math.floor(hours / 24)} days ago`;
}

function expiryLabel(expiresAt: string, now = Date.now()): string {
  const remaining = Date.parse(expiresAt) - now;
  if (remaining <= 0) return "Expired";
  const minutes = Math.max(1, Math.ceil(remaining / 60000));
  if (minutes < 60) return `Expires in ${minutes} min`;
  const hours = Math.ceil(minutes / 60);
  return `Expires in ${hours} hr`;
}

export function NotificationsScreen({ api: providedApi }: Props) {
  const hookApi = useNotificationApi();
  const api = providedApi ?? hookApi;
  const { snapshot } = useSession();
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [statusMessage, setStatusMessage] = useState("Loading notifications…");
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  const [items, setItems] = useState<NotificationRecord[]>([]);
  const [urgentMessage, setUrgentMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const authenticated = snapshot.status === "authenticated";

  const refresh = useCallback(async () => {
    if (!authenticated) {
      setLoadState("error");
      setStatusMessage("Connect to RoadTalk to view notifications.");
      setPreferences(null);
      setItems([]);
      return;
    }
    setLoadState("loading");
    setStatusMessage("Loading notifications…");
    try {
      const [nextPreferences, inbox] = await Promise.all([
        api.preferences(),
        api.inbox(),
      ]);
      setPreferences(nextPreferences);
      setItems(inbox.items.filter((item) => item.dismissedAt === null));
      setLoadState("ready");
      setStatusMessage(
        inbox.items.length === 0
          ? "No current notifications."
          : `${inbox.items.length} current notification${
              inbox.items.length === 1 ? "" : "s"
            } loaded.`,
      );
    } catch (error) {
      setLoadState("error");
      setStatusMessage(describeError(error));
    }
  }, [api, authenticated]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const visibleItems = useMemo(
    () => items.filter((item) => item.dismissedAt === null),
    [items],
  );

  async function changePreferences(
    field: "channelActivityEnabled" | "urgentAlertEnabled",
    value: boolean,
  ) {
    if (preferences === null || busy) return;
    setBusy(true);
    setStatusMessage("Saving notification preferences…");
    try {
      const next = await api.updatePreferences(preferences, {
        channelActivityEnabled:
          field === "channelActivityEnabled"
            ? value
            : preferences.channelActivityEnabled,
        urgentAlertEnabled:
          field === "urgentAlertEnabled" ? value : preferences.urgentAlertEnabled,
      });
      setPreferences(next);
      setStatusMessage("Notification preferences saved.");
    } catch (error) {
      setStatusMessage(describeError(error));
    } finally {
      setBusy(false);
    }
  }

  async function updateState(
    notification: NotificationRecord,
    state: NotificationState,
  ) {
    if (busy) return;
    setBusy(true);
    setStatusMessage(
      state === "read" ? "Marking notification read…" : "Dismissing notification…",
    );
    try {
      const updated = await api.updateState(notification, state);
      setItems((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      setStatusMessage(
        state === "read" ? "Notification marked read." : "Notification dismissed.",
      );
    } catch (error) {
      setStatusMessage(describeError(error));
    } finally {
      setBusy(false);
    }
  }

  async function sendUrgentAlert() {
    const message = urgentMessage.trim();
    if (busy || message.length === 0 || message.length > 280) return;
    setBusy(true);
    setStatusMessage("Sending urgent alert…");
    try {
      const receipt = await api.sendUrgentAlert(message);
      setUrgentMessage("");
      setStatusMessage(
        `Urgent alert accepted for ${receipt.recipientCount} currently eligible recipient${
          receipt.recipientCount === 1 ? "" : "s"
        }. Delivery, reading, and response are not guaranteed.`,
      );
      await refresh();
    } catch (error) {
      setStatusMessage(describeError(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      keyboardShouldPersistTaps="handled"
    >
      <Text accessibilityRole="header" style={styles.title}>
        Notifications
      </Text>
      <Text style={styles.body}>
        This mobile experience uses your RoadTalk account inbox. External push delivery is
        not active in this build.
      </Text>

      <View accessibilityLiveRegion="polite" style={styles.statusCard}>
        <Text style={styles.statusLabel}>Notification status</Text>
        <Text style={loadState === "error" ? styles.errorText : styles.statusValue}>
          {statusMessage}
        </Text>
      </View>

      <View style={styles.card}>
        <Text accessibilityRole="header" style={styles.sectionTitle}>
          Device presentation
        </Text>
        <Text style={styles.body}>
          In-app notifications are available while RoadTalk is open. OS push and background
          notification delivery are unavailable because no APNs, FCM, Expo Push, or other
          external notification provider is activated.
        </Text>
        <Text style={styles.muted}>
          RoadTalk does not request background location or background audio for notifications.
        </Text>
      </View>

      {preferences !== null ? (
        <View style={styles.card}>
          <Text accessibilityRole="header" style={styles.sectionTitle}>
            Preferences
          </Text>
          <View style={styles.preferenceRow}>
            <View style={styles.preferenceText}>
              <Text style={styles.preferenceTitle}>Channel activity</Text>
              <Text style={styles.muted}>Show currently authorized channel activity.</Text>
            </View>
            <Switch
              accessibilityLabel="Channel activity notifications"
              disabled={busy}
              onValueChange={(value) =>
                void changePreferences("channelActivityEnabled", value)
              }
              value={preferences.channelActivityEnabled}
            />
          </View>
          <View style={styles.preferenceRow}>
            <View style={styles.preferenceText}>
              <Text style={styles.preferenceTitle}>Urgent alerts</Text>
              <Text style={styles.muted}>Show eligible user-generated urgent alerts.</Text>
            </View>
            <Switch
              accessibilityLabel="Urgent alert notifications"
              disabled={busy}
              onValueChange={(value) => void changePreferences("urgentAlertEnabled", value)}
              value={preferences.urgentAlertEnabled}
            />
          </View>
        </View>
      ) : null}

      <View style={styles.card}>
        <Text accessibilityRole="header" style={styles.sectionTitle}>
          Send an urgent alert
        </Text>
        <Text style={styles.warning}>RoadTalk is not an emergency service.</Text>
        <Text style={styles.body}>
          This alert is user-generated and unverified. Delivery is not guaranteed. Contact
          local emergency services directly when emergency assistance is needed.
        </Text>
        <Text style={styles.muted}>
          The server selects currently eligible recipients from existing RoadTalk
          authorization. You cannot target a person, coordinate, radius, route, or
          destination.
        </Text>
        <TextInput
          accessibilityLabel="Urgent alert message"
          editable={!busy}
          maxLength={280}
          multiline
          onChangeText={setUrgentMessage}
          placeholder="Briefly describe the urgent situation"
          style={styles.input}
          value={urgentMessage}
        />
        <Text style={styles.counter}>{urgentMessage.length}/280</Text>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Send RoadTalk urgent alert"
          disabled={busy || urgentMessage.trim().length === 0}
          onPress={() => void sendUrgentAlert()}
          style={({ pressed }) => [
            styles.dangerButton,
            (pressed || busy || urgentMessage.trim().length === 0) && styles.buttonPressed,
          ]}
        >
          <Text style={styles.buttonText}>Send urgent alert</Text>
        </Pressable>
      </View>

      <View style={styles.sectionHeaderRow}>
        <Text accessibilityRole="header" style={styles.sectionTitle}>
          Inbox
        </Text>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Refresh notifications"
          disabled={busy}
          onPress={() => void refresh()}
          style={({ pressed }) => [styles.secondaryButton, pressed && styles.buttonPressed]}
        >
          <Text style={styles.secondaryButtonText}>Refresh</Text>
        </Pressable>
      </View>

      {loadState === "ready" && visibleItems.length === 0 ? (
        <Text style={styles.muted}>No current notifications.</Text>
      ) : null}

      {visibleItems.map((notification) => {
        const expired = Date.parse(notification.expiresAt) <= Date.now();
        const urgent = notification.notificationClass === "urgent_alert";
        return (
          <View
            accessibilityLabel={`${sourceLabel(notification)} notification`}
            key={notification.id}
            style={[styles.card, urgent && styles.urgentCard]}
          >
            <View style={styles.metaRow}>
              <Text style={styles.source}>{sourceLabel(notification)}</Text>
              <Text style={expired ? styles.errorText : styles.muted}>
                {expiryLabel(notification.expiresAt)}
              </Text>
            </View>
            <Text style={styles.muted}>{ageLabel(notification.issuedAt)}</Text>
            {notification.channelLabel !== null ? (
              <Text style={styles.muted}>Channel: {notification.channelLabel}</Text>
            ) : null}
            {notification.title !== null ? (
              <Text style={styles.notificationTitle}>{notification.title}</Text>
            ) : null}
            <Text style={styles.notificationMessage}>{notification.message}</Text>
            {urgent ? (
              <View style={styles.safetyBox}>
                <Text style={styles.warning}>User-generated and unverified</Text>
                <Text style={styles.muted}>RoadTalk is not an emergency service.</Text>
                <Text style={styles.muted}>Delivery is not guaranteed.</Text>
                <Text style={styles.muted}>
                  Contact local emergency services directly when emergency assistance is
                  needed.
                </Text>
              </View>
            ) : null}
            <View style={styles.actionRow}>
              {notification.readAt === null && !expired ? (
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Mark notification read"
                  disabled={busy}
                  onPress={() => void updateState(notification, "read")}
                  style={({ pressed }) => [
                    styles.secondaryButton,
                    pressed && styles.buttonPressed,
                  ]}
                >
                  <Text style={styles.secondaryButtonText}>Mark read</Text>
                </Pressable>
              ) : null}
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Dismiss notification"
                disabled={busy}
                onPress={() => void updateState(notification, "dismissed")}
                style={({ pressed }) => [
                  styles.secondaryButton,
                  pressed && styles.buttonPressed,
                ]}
              >
                <Text style={styles.secondaryButtonText}>Dismiss</Text>
              </Pressable>
            </View>
          </View>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.background,
    padding: spacing.large,
    gap: spacing.large,
  },
  title: { color: colors.text, fontSize: 32, fontWeight: "700" },
  sectionTitle: { color: colors.text, fontSize: 21, fontWeight: "700" },
  body: { color: colors.text, fontSize: 16, lineHeight: 23 },
  muted: { color: colors.muted, fontSize: 14, lineHeight: 20 },
  statusCard: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    gap: spacing.small,
    padding: spacing.medium,
  },
  statusLabel: { color: colors.muted, fontSize: 14 },
  statusValue: { color: colors.text, fontSize: 16, fontWeight: "600" },
  errorText: { color: colors.danger, fontSize: 14, fontWeight: "600" },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    gap: spacing.medium,
    padding: spacing.medium,
  },
  urgentCard: { borderColor: colors.danger, borderWidth: 2 },
  preferenceRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.medium,
    justifyContent: "space-between",
  },
  preferenceText: { flex: 1, gap: 4 },
  preferenceTitle: { color: colors.text, fontSize: 16, fontWeight: "600" },
  warning: { color: colors.danger, fontSize: 16, fontWeight: "700" },
  input: {
    borderColor: colors.border,
    borderRadius: 10,
    borderWidth: 1,
    color: colors.text,
    fontSize: 16,
    minHeight: 96,
    padding: spacing.medium,
    textAlignVertical: "top",
  },
  counter: { color: colors.muted, fontSize: 13, textAlign: "right" },
  dangerButton: {
    alignItems: "center",
    backgroundColor: colors.danger,
    borderRadius: 10,
    justifyContent: "center",
    minHeight: 48,
    paddingHorizontal: spacing.medium,
  },
  buttonText: { color: colors.surface, fontSize: 16, fontWeight: "700" },
  secondaryButton: {
    alignItems: "center",
    borderColor: colors.primary,
    borderRadius: 10,
    borderWidth: 1,
    justifyContent: "center",
    minHeight: 44,
    paddingHorizontal: spacing.medium,
  },
  secondaryButtonText: { color: colors.primary, fontSize: 15, fontWeight: "600" },
  buttonPressed: { opacity: 0.6 },
  sectionHeaderRow: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  metaRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.small,
    justifyContent: "space-between",
  },
  source: { color: colors.primary, fontSize: 14, fontWeight: "700" },
  notificationTitle: { color: colors.text, fontSize: 18, fontWeight: "700" },
  notificationMessage: { color: colors.text, fontSize: 16, lineHeight: 23 },
  safetyBox: {
    borderColor: colors.danger,
    borderRadius: 8,
    borderWidth: 1,
    gap: spacing.small,
    padding: spacing.medium,
  },
  actionRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.small },
});
