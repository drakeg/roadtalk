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
import type { ChannelControl, ChannelTransition } from "../channels/types";
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
            {snapshot.notice === "joined"
              ? "Private channel joined."
              : snapshot.notice === "left"
                ? "Private channel left. General is selected when needed."
                : "Channel selected. Live audio will use fresh authorization."}
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
          ) : null}
        </View>
      ))}

      {snapshot.status === "ready" ? (
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
            style={({ pressed }) => [styles.primaryButton, pressed && styles.pressed]}
          >
            <Text style={styles.primaryText}>Join private channel</Text>
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
  joinCard: { gap: spacing.medium },
  channelHeader: { alignItems: "center", flexDirection: "row", gap: spacing.medium },
  channelCopy: { flex: 1, gap: 4 },
  cardTitle: { color: colors.text, fontSize: 18, fontWeight: "700" },
  meta: { color: colors.muted, fontSize: 15 },
  selected: { color: colors.primary, fontSize: 15, fontWeight: "700" },
  notice: { color: colors.primary, fontSize: 16, fontWeight: "600" },
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
