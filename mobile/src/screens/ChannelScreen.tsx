import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import type { RootStackParamList } from "../AppNavigator";
import { useChannelApi } from "../channels/api";
import { ChannelController } from "../channels/ChannelController";
import type {
  ChannelControl,
  ChannelSnapshot,
  ChannelTransition,
} from "../channels/types";
import { useMediaLifecycle } from "../media/MediaLifecycleContext";
import { colors, spacing } from "../theme";

type Props = NativeStackScreenProps<RootStackParamList, "Channels"> & {
  control?: ChannelControl;
};

const inactiveTransition: ChannelTransition = {
  prepareChannelTransition: async () => undefined,
  completeChannelTransition: async () => undefined,
};

export function ChannelScreen({ control, navigation }: Props) {
  const api = useChannelApi();
  const media = useMediaLifecycle();
  const ownedControl = useMemo(
    () => control ?? new ChannelController(api, media ?? inactiveTransition),
    [api, control, media],
  );
  const snapshot = useSyncExternalStore(
    (listener) => ownedControl.subscribe(listener),
    () => ownedControl.getSnapshot(),
  );
  const [invite, setInvite] = useState("");
  const [channelName, setChannelName] = useState("");
  const [confirmation, setConfirmation] = useState<{
    kind: "rotate" | "close";
    channelId: string;
    label: string;
  } | null>(null);

  useEffect(() => {
    if (control === undefined) void ownedControl.load();
  }, [control, ownedControl]);

  const items = snapshot.status === "loading" ? [] : snapshot.items;
  const changing = snapshot.status === "switching";

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      contentInsetAdjustmentBehavior="automatic"
      keyboardShouldPersistTaps="handled"
    >
      <Text accessibilityRole="header" style={styles.title}>
        Channels
      </Text>
      <Text style={styles.body}>
        Choose General, RV, or one of your private channels. RoadTalk never
        shows who belongs to a private channel or how many people are there.
      </Text>

      <View accessibilityLiveRegion="polite" style={styles.statusCard}>
        <Text style={styles.cardTitle}>
          {snapshot.status === "loading"
            ? "Loading channels…"
            : changing
              ? "Switching safely…"
              : snapshot.status === "error"
                ? "Channel unavailable"
                : "Channel ready"}
        </Text>
        <Text style={styles.body}>
          {changing
            ? "Microphone capture and incoming audio are off while RoadTalk changes channels."
            : snapshot.status === "error"
              ? snapshot.message
              : "Only your current selection and channels available to you are shown."}
        </Text>
        {snapshot.status === "ready" && snapshot.notice !== undefined ? (
          <Text style={styles.notice}>
            {noticeText(snapshot.notice)}
          </Text>
        ) : null}
      </View>

      {snapshot.status === "error" ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Retry channel catalog"
          onPress={() => void ownedControl.load()}
          style={({ pressed }) => [styles.secondaryButton, pressed && styles.pressed]}
        >
          <Text style={styles.secondaryText}>Try again</Text>
        </Pressable>
      ) : null}

      {items.map((channel) => (
        <View key={channel.id} style={styles.channelCard}>
          <View style={styles.channelHeader}>
            <View style={styles.channelCopy}>
              <Text style={styles.cardTitle}>{channel.displayLabel}</Text>
              <Text style={styles.meta}>
                {channel.type === "public" ? "Public channel" : "Private channel"}
              </Text>
            </View>
            {channel.selected ? (
              <Text accessibilityLabel="Currently selected" style={styles.selected}>
                Selected
              </Text>
            ) : null}
          </View>
          {!channel.selected ? (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`Select ${channel.displayLabel} channel`}
              disabled={changing}
              onPress={() => void ownedControl.select(channel.id)}
              style={({ pressed }) => [
                styles.primaryButton,
                (pressed || changing) && styles.pressed,
              ]}
            >
              <Text style={styles.primaryText}>Select</Text>
            </Pressable>
          ) : null}
          {channel.type === "private" ? (
            <View style={styles.actions}>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={`Rotate invite for ${channel.displayLabel}`}
                disabled={changing}
                onPress={() =>
                  setConfirmation({
                    kind: "rotate",
                    channelId: channel.id,
                    label: channel.displayLabel,
                  })
                }
                style={({ pressed }) => [
                  styles.secondaryButton,
                  (pressed || changing) && styles.pressed,
                ]}
              >
                <Text style={styles.secondaryText}>Rotate invite</Text>
              </Pressable>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={`Leave ${channel.displayLabel} private channel`}
                disabled={changing}
                onPress={() => void ownedControl.leave(channel.id)}
                style={({ pressed }) => [
                  styles.secondaryButton,
                  (pressed || changing) && styles.pressed,
                ]}
              >
                <Text style={styles.secondaryText}>Leave private channel</Text>
              </Pressable>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={`Close ${channel.displayLabel} private channel`}
                disabled={changing}
                onPress={() =>
                  setConfirmation({
                    kind: "close",
                    channelId: channel.id,
                    label: channel.displayLabel,
                  })
                }
                style={({ pressed }) => [
                  styles.dangerButton,
                  (pressed || changing) && styles.pressed,
                ]}
              >
                <Text style={styles.dangerText}>Close private channel</Text>
              </Pressable>
            </View>
          ) : null}
        </View>
      ))}

      {snapshot.status === "ready" ? (
        <View style={styles.actions}>
          {snapshot.oneTimeInvite !== undefined ? (
            <View accessibilityLiveRegion="assertive" style={styles.inviteCard}>
              <Text accessibilityRole="header" style={styles.cardTitle}>
                Save this invite now
              </Text>
              <Text style={styles.body}>
                This secret is shown only once. Share it privately; RoadTalk cannot
                display it again after you dismiss it.
              </Text>
              <Text
                accessibilityLabel="One-time private channel invite"
                selectable
                style={styles.inviteValue}
              >
                {snapshot.oneTimeInvite.value}
              </Text>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Dismiss one-time private channel invite"
                onPress={() => ownedControl.dismissInvite()}
                style={({ pressed }) => [
                  styles.secondaryButton,
                  pressed && styles.pressed,
                ]}
              >
                <Text style={styles.secondaryText}>I saved it</Text>
              </Pressable>
            </View>
          ) : null}
          <View style={styles.joinCard}>
            <Text style={styles.cardTitle}>Create a private channel</Text>
            <TextInput
              accessibilityLabel="New private channel name"
              maxLength={64}
              onChangeText={setChannelName}
              placeholder="Channel name"
              style={styles.input}
              value={channelName}
            />
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Create private channel"
              onPress={() => {
                const submitted = channelName;
                setChannelName("");
                void ownedControl.create(submitted);
              }}
              style={({ pressed }) => [
                styles.primaryButton,
                pressed && styles.pressed,
              ]}
            >
              <Text style={styles.primaryText}>Create private channel</Text>
            </Pressable>
          </View>
          <View style={styles.joinCard}>
            <Text style={styles.cardTitle}>Join a private channel</Text>
            <Text style={styles.body}>
              Paste an invite shared with you. It is used only for this request
              and is cleared from the screen immediately.
            </Text>
            <TextInput
              accessibilityLabel="Private channel invite"
              autoCapitalize="none"
              autoCorrect={false}
              onChangeText={setInvite}
              placeholder="Private invite"
              secureTextEntry
              style={styles.input}
              value={invite}
            />
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Join private channel"
              onPress={() => {
                const submitted = invite;
                setInvite("");
                void ownedControl.join(submitted);
              }}
              style={({ pressed }) => [
                styles.primaryButton,
                pressed && styles.pressed,
              ]}
            >
              <Text style={styles.primaryText}>Join private channel</Text>
            </Pressable>
          </View>
        </View>
      ) : null}

      {confirmation !== null ? (
        <View accessibilityLiveRegion="assertive" style={styles.confirmCard}>
          <Text accessibilityRole="header" style={styles.cardTitle}>
            {confirmation.kind === "rotate"
              ? "Replace this invite?"
              : "Close this channel?"}
          </Text>
          <Text style={styles.body}>
            {confirmation.kind === "rotate"
              ? `The old invite for ${confirmation.label} will stop working.`
              : `${confirmation.label} will close for everyone and cannot be reopened.`}
          </Text>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={`Confirm ${confirmation.kind} for ${confirmation.label}`}
            onPress={() => {
              const pending = confirmation;
              setConfirmation(null);
              if (pending.kind === "rotate") {
                void ownedControl.rotate(pending.channelId);
              } else {
                void ownedControl.close(pending.channelId);
              }
            }}
            style={({ pressed }) => [
              styles.dangerButton,
              pressed && styles.pressed,
            ]}
          >
            <Text style={styles.dangerText}>
              {confirmation.kind === "rotate" ? "Replace invite" : "Close channel"}
            </Text>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Cancel private channel change"
            onPress={() => setConfirmation(null)}
            style={({ pressed }) => [
              styles.secondaryButton,
              pressed && styles.pressed,
            ]}
          >
            <Text style={styles.secondaryText}>Cancel</Text>
          </Pressable>
        </View>
      ) : null}

      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Return to RoadTalk home"
        onPress={() => navigation.goBack()}
        style={({ pressed }) => [styles.secondaryButton, pressed && styles.pressed]}
      >
        <Text style={styles.secondaryText}>Done</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.background,
    flexGrow: 1,
    gap: spacing.large,
    padding: spacing.xlarge,
  },
  title: { color: colors.text, fontSize: 32, fontWeight: "700" },
  body: { color: colors.muted, fontSize: 17, lineHeight: 25 },
  statusCard: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    gap: spacing.small,
    padding: spacing.medium,
  },
  channelCard: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    gap: spacing.medium,
    padding: spacing.medium,
  },
  actions: { gap: spacing.medium },
  joinCard: { gap: spacing.medium },
  channelHeader: { alignItems: "center", flexDirection: "row", gap: spacing.medium },
  channelCopy: { flex: 1, gap: 4 },
  cardTitle: { color: colors.text, fontSize: 18, fontWeight: "700" },
  meta: { color: colors.muted, fontSize: 15 },
  selected: { color: colors.primary, fontSize: 15, fontWeight: "700" },
  notice: { color: colors.primary, fontSize: 16, fontWeight: "600" },
  inviteCard: {
    backgroundColor: colors.surface,
    borderColor: colors.primary,
    borderRadius: 12,
    borderWidth: 2,
    gap: spacing.medium,
    padding: spacing.medium,
  },
  inviteValue: { color: colors.text, fontFamily: "monospace", fontSize: 15 },
  confirmCard: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    gap: spacing.medium,
    padding: spacing.medium,
  },
  primaryButton: {
    alignItems: "center",
    backgroundColor: colors.primary,
    borderRadius: 12,
    justifyContent: "center",
    minHeight: 48,
    paddingHorizontal: spacing.large,
  },
  primaryText: { color: colors.surface, fontSize: 17, fontWeight: "600" },
  secondaryButton: {
    alignItems: "center",
    borderColor: colors.primary,
    borderRadius: 12,
    borderWidth: 2,
    justifyContent: "center",
    minHeight: 48,
    paddingHorizontal: spacing.large,
  },
  secondaryText: { color: colors.primary, fontSize: 17, fontWeight: "600" },
  dangerButton: {
    alignItems: "center",
    borderColor: colors.danger,
    borderRadius: 12,
    borderWidth: 2,
    justifyContent: "center",
    minHeight: 48,
    paddingHorizontal: spacing.large,
  },
  dangerText: { color: colors.danger, fontSize: 17, fontWeight: "600" },
  input: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 10,
    borderWidth: 1,
    color: colors.text,
    fontSize: 17,
    minHeight: 48,
    paddingHorizontal: spacing.medium,
  },
  pressed: { opacity: 0.75 },
});

function noticeText(
  notice: NonNullable<Extract<ChannelSnapshot, { status: "ready" }>["notice"]>,
): string {
  const messages = {
    joined: "Private channel joined.",
    left: "Private channel left. General is selected when needed.",
    selected: "Channel selected. Live audio will use fresh authorization.",
    created: "Private channel created.",
    rotated: "Private channel invite replaced.",
    closed: "Private channel closed. General is selected when needed.",
  } as const;
  return messages[notice];
}
