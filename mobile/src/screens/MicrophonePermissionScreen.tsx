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
        <Text style={styles.cardTitle}>Release always means microphone off</Text>
        <Text style={styles.body}>
          Enabling live audio joins receive-only. RoadTalk requests a separate,
          short-lived server authorization only after you press and hold the
          control below. Releasing, leaving this screen, or reaching 30 seconds
          turns capture off before cleanup.
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

      {isPushToTalkVisible(snapshot) ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={pushToTalkLabel(snapshot)}
          accessibilityHint="Double tap and continue holding to request microphone transmission. Release to stop."
          onPressIn={() => void ownedLifecycle.pressToTalk()}
          onPressOut={() => void ownedLifecycle.releaseToTalk()}
          style={({ pressed }) => [
            styles.pushToTalkButton,
            snapshot.status === "transmitting" &&
              styles.pushToTalkButtonActive,
            pressed && styles.buttonPressed,
          ]}
        >
          <Text
            style={[
              styles.pushToTalkCue,
              snapshot.status === "transmitting" &&
                styles.pushToTalkTextActive,
            ]}
          >
            {pushToTalkCue(snapshot)}
          </Text>
          <Text
            style={[
              styles.pushToTalkText,
              snapshot.status === "transmitting" &&
                styles.pushToTalkTextActive,
            ]}
          >
            {pushToTalkText(snapshot)}
          </Text>
        </Pressable>
      ) : null}

      {snapshot.status === "ready" ||
      snapshot.status === "receiving" ||
      snapshot.status === "authorizing" ||
      snapshot.status === "transmitting" ||
      snapshot.status === "busy" ||
      snapshot.status === "degraded" ||
      snapshot.status === "transmit_error" ||
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
    receiving: "Receiving remote audio · microphone off",
    authorizing: "Authorizing · microphone off",
    transmitting: "Transmitting · release to stop",
    busy: "Channel busy · microphone off",
    degraded: "Transmission temporarily unavailable · microphone off",
    transmit_error: "Transmission failed · microphone off",
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
    if (snapshot.reason === "maximum") {
      return "The 30-second maximum was reached. Release, then press and hold again for a new authorization.";
    }
    return "Remote audio can play while this screen is active. Microphone capture is off.";
  }
  if (snapshot.status === "receiving") {
    return "Another participant is speaking. You can listen now; hold the control when the channel is available.";
  }
  if (snapshot.status === "authorizing") {
    return "Keep holding. RoadTalk is requesting a short-lived microphone-only authorization; capture is still off.";
  }
  if (snapshot.status === "transmitting") {
    return "Your microphone is live. Release now to stop; RoadTalk also stops automatically at 30 seconds.";
  }
  if (snapshot.status === "busy") {
    return "Another transmission has priority. Nothing was captured; release and try again.";
  }
  if (snapshot.status === "degraded") {
    return "The live-audio provider is temporarily unavailable or rate limited. Nothing was captured.";
  }
  if (snapshot.status === "transmit_error") {
    return "RoadTalk stopped capture and released the transmission authorization. Release and try again.";
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

function isPushToTalkVisible(snapshot: MediaLifecycleSnapshot): boolean {
  return [
    "ready",
    "receiving",
    "authorizing",
    "transmitting",
    "busy",
    "degraded",
    "transmit_error",
  ].includes(snapshot.status);
}

function pushToTalkLabel(snapshot: MediaLifecycleSnapshot): string {
  if (snapshot.status === "transmitting") {
    return "Transmitting. Release to stop";
  }
  if (snapshot.status === "authorizing") {
    return "Authorizing microphone transmission. Keep holding";
  }
  return "Hold to talk. Microphone off";
}

function pushToTalkCue(snapshot: MediaLifecycleSnapshot): string {
  if (snapshot.status === "transmitting") {
    return "● LIVE";
  }
  if (snapshot.status === "authorizing") {
    return "… WAIT";
  }
  return "○ OFF";
}

function pushToTalkText(snapshot: MediaLifecycleSnapshot): string {
  if (snapshot.status === "transmitting") {
    return "RELEASE TO STOP";
  }
  if (snapshot.status === "authorizing") {
    return "KEEP HOLDING";
  }
  return "HOLD TO TALK";
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
  pushToTalkButton: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.primary,
    borderRadius: 18,
    borderWidth: 3,
    gap: spacing.small,
    justifyContent: "center",
    minHeight: 112,
    padding: spacing.large,
  },
  pushToTalkButtonActive: {
    backgroundColor: colors.primary,
  },
  pushToTalkCue: {
    color: colors.text,
    fontSize: 18,
    fontWeight: "700",
  },
  pushToTalkText: {
    color: colors.text,
    fontSize: 22,
    fontWeight: "700",
    letterSpacing: 0.8,
  },
  pushToTalkTextActive: {
    color: colors.surface,
  },
  textButton: { alignItems: "center", justifyContent: "center", minHeight: 44 },
  textButtonText: { color: colors.primary, fontSize: 16, fontWeight: "600" },
  buttonPressed: { opacity: 0.8 },
});
