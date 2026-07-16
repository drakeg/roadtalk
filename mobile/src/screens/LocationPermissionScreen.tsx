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
import { environment } from "../config";
import { LocationApi } from "../location/api";
import { expoLocationGateway } from "../location/gateway";
import { LocationLifecycleController } from "../location/LocationLifecycleController";
import type { LocationLifecycleControl } from "../location/types";
import { useSession, useSessionClient } from "../session/SessionContext";
import { colors, spacing } from "../theme";

type Props = NativeStackScreenProps<RootStackParamList, "LocationPermission"> & {
  lifecycle?: LocationLifecycleControl;
};

export function LocationPermissionScreen({ lifecycle, navigation }: Props) {
  const session = useSession();
  const sessionClient = useSessionClient();
  const ownedLifecycle = useMemo(
    () =>
      lifecycle ??
      new LocationLifecycleController(
        expoLocationGateway,
        new LocationApi(environment.apiBaseUrl, sessionClient),
      ),
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

  const enable = () => void ownedLifecycle.enable();
  const pause = () => void ownedLifecycle.pause();

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      contentInsetAdjustmentBehavior="automatic"
    >
      <Text accessibilityRole="header" style={styles.title}>
        Foreground location
      </Text>
      <Text style={styles.body}>
        RoadTalk uses a short-lived location only while this screen is open to
        support coarse nearby awareness. Other users never receive your
        coordinates, exact distance, or identity from this feature.
      </Text>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>You stay in control</Text>
        <Text style={styles.body}>
          You can continue without location. RoadTalk does not request
          background access, build location history, show a map, or treat this
          as a safety or emergency service.
        </Text>
        <Text style={styles.body}>
          Approximate or reduced accuracy is accepted. Optional heading and
          speed may be sent as quality information only when your device
          provides them.
        </Text>
      </View>

      <View accessibilityLiveRegion="polite" style={styles.statusCard}>
        <Text style={styles.statusTitle}>{statusTitle(snapshot.status)}</Text>
        <Text style={styles.statusBody}>{statusBody(snapshot)}</Text>
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
              ? "Enable foreground location"
              : "Retry foreground location"
          }
          onPress={enable}
          style={({ pressed }) => [
            styles.primaryButton,
            pressed && styles.buttonPressed,
          ]}
        >
          <Text style={styles.primaryButtonText}>
            {snapshot.status === "purpose" ? "Enable location" : "Try again"}
          </Text>
        </Pressable>
      ) : null}

      {snapshot.status === "blocked" ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Open device settings for location permission"
          onPress={() => void Linking.openSettings()}
          style={({ pressed }) => [
            styles.primaryButton,
            pressed && styles.buttonPressed,
          ]}
        >
          <Text style={styles.primaryButtonText}>Open device settings</Text>
        </Pressable>
      ) : null}

      {snapshot.status === "active" ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Pause and remove current location"
          onPress={pause}
          style={({ pressed }) => [
            styles.secondaryButton,
            pressed && styles.buttonPressed,
          ]}
        >
          <Text style={styles.secondaryButtonText}>Pause location</Text>
        </Pressable>
      ) : null}

      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Continue without location"
        onPress={() => navigation.goBack()}
        style={({ pressed }) => [
          styles.textButton,
          pressed && styles.buttonPressed,
        ]}
      >
        <Text style={styles.textButtonText}>Continue without location</Text>
      </Pressable>
    </ScrollView>
  );
}

function statusTitle(status: ReturnType<LocationLifecycleControl["getSnapshot"]>["status"]): string {
  switch (status) {
    case "checking":
      return "Checking permission…";
    case "unavailable":
      return "Location services are unavailable";
    case "denied":
      return "Permission not granted";
    case "blocked":
      return "Permission is blocked";
    case "paused":
      return "Location is paused";
    case "active":
      return "Foreground location is on";
    case "error":
      return "Location could not start";
    default:
      return "Location is off";
  }
}

function statusBody(
  snapshot: ReturnType<LocationLifecycleControl["getSnapshot"]>,
): string {
  switch (snapshot.status) {
    case "checking":
      return "RoadTalk will show the system foreground-location prompt only if needed.";
    case "unavailable":
      return "Turn on device location services, then try again. You may continue without location.";
    case "denied":
      return "The request was declined. You may try again or continue without location.";
    case "blocked":
      return "Enable foreground location in device settings, or continue without it.";
    case "paused":
      return "Sampling stopped and the server was asked to remove your current location.";
    case "active":
      return `${snapshot.precision === "approximate" ? "Approximate" : "Precise"} permission is active. ${snapshot.upload === "current" ? "Your short-lived sample is current." : snapshot.upload === "retrying" ? "A private update will retry when another sample arrives." : "Waiting for a device sample."}`;
    case "error":
      return "Sampling is stopped. Check your connection or device settings and try again.";
    default:
      return "Nothing is collected until you choose Enable location.";
  }
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.background,
    flexGrow: 1,
    gap: spacing.large,
    padding: spacing.xlarge,
  },
  title: { color: colors.text, fontSize: 30, fontWeight: "700" },
  body: { color: colors.muted, fontSize: 17, lineHeight: 25 },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    gap: spacing.medium,
    padding: spacing.large,
  },
  cardTitle: { color: colors.text, fontSize: 19, fontWeight: "700" },
  statusCard: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    gap: spacing.small,
    padding: spacing.medium,
  },
  statusTitle: { color: colors.text, fontSize: 18, fontWeight: "700" },
  statusBody: { color: colors.muted, fontSize: 16, lineHeight: 23 },
  primaryButton: {
    alignItems: "center",
    backgroundColor: colors.primary,
    borderRadius: 12,
    justifyContent: "center",
    minHeight: 48,
    paddingHorizontal: spacing.large,
  },
  primaryButtonText: { color: colors.surface, fontSize: 17, fontWeight: "700" },
  secondaryButton: {
    alignItems: "center",
    borderColor: colors.primary,
    borderRadius: 12,
    borderWidth: 2,
    justifyContent: "center",
    minHeight: 48,
    paddingHorizontal: spacing.large,
  },
  secondaryButtonText: { color: colors.primary, fontSize: 17, fontWeight: "700" },
  textButton: { alignItems: "center", justifyContent: "center", minHeight: 48 },
  textButtonText: { color: colors.primary, fontSize: 16, fontWeight: "600" },
  buttonPressed: { opacity: 0.8 },
});
