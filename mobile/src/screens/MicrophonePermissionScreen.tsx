import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useEffect, useMemo, useSyncExternalStore } from "react";
import {
  AppState,
  Linking,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import type { RootStackParamList } from "../AppNavigator";
import { createDefaultMediaLifecycle } from "../media/defaultLifecycle";
import type {
  MediaLifecycleControl,
  MediaLifecycleSnapshot,
} from "../media/types";
import { useSession, useSessionClient } from "../session/SessionContext";
import { colors, spacing } from "../theme";

type Props = NativeStackScreenProps<
  RootStackParamList,
  "MicrophonePermission"
> & {
  lifecycle?: MediaLifecycleControl;
};

export function MicrophonePermissionScreen({ lifecycle, navigation }: Props) {
  const session = useSession();
  const sessionClient = useSessionClient();
  const ownedLifecycle = useMemo(
    () => lifecycle ?? createDefaultMediaLifecycle(sessionClient),
    [lifecycle, sessionClient],
  );
  const snapshot = useSyncExternalStore(
    (listener) => ownedLifecycle.subscribe(listener),
    () => ownedLifecycle.getSnapshot(),
  );

  useEffect(() => {
    void ownedLifecycle.setAuthenticated(
      session.snapshot.status === "authenticated",
    );
  }, [ownedLifecycle, session.snapshot.status]);

  useEffect(() => {
    void ownedLifecycle.setAppActive(AppState.currentState === "active");
    const subscription = AppState.addEventListener("change", (state) => {
      void ownedLifecycle.setAppActive(state === "active");
    });
    return () => subscription.remove();
  }, [ownedLifecycle]);

  useEffect(() => {
    if (navigation.isFocused()) {
      void ownedLifecycle.setScreenActive(true);
    }
    const removeFocus = navigation.addListener("focus", () => {
      void ownedLifecycle.setScreenActive(true);
    });
    const removeBlur = navigation.addListener("blur", () => {
      void ownedLifecycle.setScreenActive(false);
    });
    return () => {
      removeFocus();
      removeBlur();
      void ownedLifecycle.setScreenActive(false);
    };
  }, [navigation, ownedLifecycle]);

  useEffect(
    () => () => {
      if (lifecycle === undefined) {
        void ownedLifecycle.dispose();
      }
    },
    [lifecycle, ownedLifecycle],
  );

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      contentInsetAdjustmentBehavior="automatic"
    >
      <Text accessibilityRole="header" style={styles.title}>
        Microphone and live audio
      </Text>
      <Text style={styles.body}>
        RoadTalk needs microphone access only when you explicitly hold the
        push-to-talk control. Audio is sent live to the current ephemeral room;
        RoadTalk does not record, transcribe, or store it.
      </Text>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Receive-ready is microphone-off</Text>
        <Text style={styles.body}>
          Enabling this foundation joins receive-only with automatic remote
          audio subscription. It never starts microphone capture. Publishing
          remains unavailable until the separate hold-to-talk flow is added and
          the server authorizes it.
        </Text>
      </View>
      <View accessibilityLiveRegion="polite" style={styles.statusCard}>
        <Text style={styles.statusTitle}>{statusTitle(snapshot)}</Text>
        <Text style={styles.body}>{statusBody(snapshot)}</Text>
      </View>

      {snapshot.status === "purpose" ||
      snapshot.status === "paused" ||
      snapshot.status === "denied" ||
      snapshot.status === "unavailable" ||
      snapshot.status === "error" ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={
            snapshot.status === "purpose"
              ? "Enable microphone and live audio"
              : "Retry microphone and live audio"
          }
          onPress={() => void ownedLifecycle.enable()}
          style={({ pressed }) => [
            styles.primaryButton,
            pressed && styles.buttonPressed,
          ]}
        >
          <Text style={styles.primaryButtonText}>
            {snapshot.status === "purpose" ? "Enable live audio" : "Try again"}
          </Text>
        </Pressable>
      ) : null}

      {snapshot.status === "blocked" ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Open device microphone settings"
          onPress={() => void Linking.openSettings()}
          style={({ pressed }) => [
            styles.primaryButton,
            pressed && styles.buttonPressed,
          ]}
        >
          <Text style={styles.primaryButtonText}>Open device settings</Text>
        </Pressable>
      ) : null}

      {snapshot.status === "ready" ||
      snapshot.status === "reconnecting" ||
      snapshot.status === "connecting" ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Disconnect live audio"
          onPress={() => void ownedLifecycle.pause()}
          style={({ pressed }) => [
            styles.secondaryButton,
            pressed && styles.buttonPressed,
          ]}
        >
          <Text style={styles.secondaryButtonText}>Disconnect live audio</Text>
        </Pressable>
      ) : null}

      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Continue without microphone or live audio"
        onPress={() => navigation.goBack()}
        style={({ pressed }) => [
          styles.textButton,
          pressed && styles.buttonPressed,
        ]}
      >
        <Text style={styles.textButtonText}>Continue without live audio</Text>
      </Pressable>
    </ScrollView>
  );
}

function statusTitle(snapshot: MediaLifecycleSnapshot): string {
  const labels: Record<MediaLifecycleSnapshot["status"], string> = {
    purpose: "Not enabled",
    checking: "Checking microphone access",
    denied: "Microphone access denied",
    blocked: "Microphone access blocked",
    unavailable: "Microphone unavailable",
    connecting: "Connecting receive-only",
    ready: "Receive-ready · microphone off",
    reconnecting: "Reconnecting · microphone off",
    paused: "Disconnected",
    error: "Live audio unavailable",
  };
  return labels[snapshot.status];
}

function statusBody(snapshot: MediaLifecycleSnapshot): string {
  if (snapshot.status === "blocked") {
    return "RoadTalk cannot ask again. You can change microphone access in device settings.";
  }
  if (snapshot.status === "ready") {
    return "Remote audio can play while this screen is active. Microphone capture is off.";
  }
  if (snapshot.status === "reconnecting") {
    return "The network changed. RoadTalk is restoring receive-only audio without starting the microphone.";
  }
  if (snapshot.status === "denied") {
    return "You can continue without audio or choose Try again.";
  }
  if (snapshot.status === "unavailable") {
    return "This device or build cannot provide microphone access.";
  }
  if (snapshot.status === "error") {
    return "RoadTalk disconnected and released local audio resources. You can try again.";
  }
  return "You can continue without granting access.";
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: colors.background,
    padding: spacing.xlarge,
    gap: spacing.large,
  },
  title: { color: colors.text, fontSize: 30, fontWeight: "700" },
  body: { color: colors.muted, fontSize: 17, lineHeight: 25 },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    padding: spacing.large,
    gap: spacing.small,
  },
  cardTitle: { color: colors.text, fontSize: 18, fontWeight: "600" },
  statusCard: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    padding: spacing.large,
    gap: spacing.small,
  },
  statusTitle: { color: colors.text, fontSize: 18, fontWeight: "600" },
  primaryButton: {
    alignItems: "center",
    backgroundColor: colors.primary,
    borderRadius: 12,
    justifyContent: "center",
    minHeight: 48,
  },
  primaryButtonText: {
    color: colors.surface,
    fontSize: 17,
    fontWeight: "600",
  },
  secondaryButton: {
    alignItems: "center",
    borderColor: colors.primary,
    borderRadius: 12,
    borderWidth: 2,
    justifyContent: "center",
    minHeight: 48,
  },
  secondaryButtonText: {
    color: colors.primary,
    fontSize: 17,
    fontWeight: "600",
  },
  textButton: { alignItems: "center", justifyContent: "center", minHeight: 44 },
  textButtonText: { color: colors.primary, fontSize: 16, fontWeight: "600" },
  buttonPressed: { opacity: 0.8 },
});
