import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
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
import { PresenceApi, type NearbyPresence, type PresenceCell } from "../presence/api";
import { useSession, useSessionClient } from "../session/SessionContext";
import { colors, spacing } from "../theme";

type Props = NativeStackScreenProps<RootStackParamList, "MapAwareness"> & {
  lifecycle?: LocationLifecycleControl;
};

type PresenceState =
  | { status: "waiting" | "unavailable" }
  | { status: "current"; value: NearbyPresence }
  | { status: "stale"; value: NearbyPresence };

export function MapAwarenessScreen({ lifecycle, navigation }: Props) {
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
  const presenceApi = useMemo(
    () => new PresenceApi(environment.apiBaseUrl, sessionClient),
    [sessionClient],
  );
  const snapshot = useSyncExternalStore(
    (listener) => ownedLifecycle.subscribe(listener),
    () => ownedLifecycle.getSnapshot(),
  );
  const [presence, setPresence] = useState<PresenceState>({ status: "waiting" });

  useEffect(() => {
    void ownedLifecycle.setAuthenticated(session.snapshot.status === "authenticated");
  }, [ownedLifecycle, session.snapshot.status]);

  useEffect(() => {
    void ownedLifecycle.setAppActive(AppState.currentState === "active");
    const subscription = AppState.addEventListener("change", (state) => {
      void ownedLifecycle.setAppActive(state === "active");
    });
    return () => subscription.remove();
  }, [ownedLifecycle]);

  useEffect(() => {
    if (navigation.isFocused()) void ownedLifecycle.setScreenActive(true);
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
      if (lifecycle === undefined) void ownedLifecycle.dispose();
    },
    [lifecycle, ownedLifecycle],
  );

  useEffect(() => {
    if (
      snapshot.status !== "active" ||
      snapshot.upload !== "current" ||
      snapshot.local.status === "waiting"
    ) {
      setPresence({ status: "waiting" });
      return;
    }
    let cancelled = false;
    const refresh = async () => {
      try {
        const value = await presenceApi.nearby();
        if (!cancelled) {
          setPresence(
            value.expiresAtMs > Date.now()
              ? { status: "current", value }
              : { status: "stale", value },
          );
        }
      } catch {
        if (!cancelled) setPresence({ status: "unavailable" });
      }
    };
    void refresh();
    const timer = setInterval(() => void refresh(), 30_000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [presenceApi, snapshot]);

  const enable = () => void ownedLifecycle.enable();
  const pause = () => void ownedLifecycle.pause();
  const local = snapshot.status === "active" ? snapshot.local : null;
  const cells = presence.status === "current" ? presence.value.cells : [];

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text accessibilityRole="header" style={styles.title}>Map awareness</Text>
      <Text style={styles.body}>
        This local awareness view shows your own foreground device position and only
        privacy-approved coarse RoadTalk activity cells for everyone else.
      </Text>
      <View style={styles.notice}>
        <Text style={styles.noticeTitle}>Awareness, not navigation</Text>
        <Text style={styles.body}>
          No public map provider, route, destination, exact other-user position,
          distance, bearing, heading, speed, or identity is shown here. Location stops
          when this screen/app is no longer active.
        </Text>
      </View>

      <View accessibilityLabel="RoadTalk local awareness grid" style={styles.map}>
        <View style={[styles.gridLine, styles.vertical]} />
        <View style={[styles.gridLine, styles.horizontal]} />
        {local !== null && local.status !== "waiting" ? (
          <>
            <View accessibilityLabel="Your current foreground location" style={styles.youMarker} />
            <Text style={styles.youLabel}>You</Text>
            {cells.map((cell, index) => (
              <PresenceMarker
                cell={cell}
                index={index}
                key={`${cell.approximateLatitude}:${cell.approximateLongitude}`}
                latitude={local.latitude}
                longitude={local.longitude}
              />
            ))}
          </>
        ) : null}
      </View>

      <View accessibilityLiveRegion="polite" style={styles.statusCard}>
        <Text style={styles.statusTitle}>{statusTitle(snapshot.status)}</Text>
        <Text style={styles.body}>{statusText(snapshot, presence)}</Text>
      </View>

      {snapshot.status === "purpose" || snapshot.status === "paused" ||
      snapshot.status === "denied" || snapshot.status === "unavailable" ||
      snapshot.status === "error" ? (
        <Pressable accessibilityRole="button" onPress={enable} style={styles.primaryButton}>
          <Text style={styles.primaryText}>Enable foreground map awareness</Text>
        </Pressable>
      ) : null}
      {snapshot.status === "blocked" ? (
        <Pressable accessibilityRole="button" onPress={() => void Linking.openSettings()} style={styles.primaryButton}>
          <Text style={styles.primaryText}>Open location settings</Text>
        </Pressable>
      ) : null}
      {snapshot.status === "active" ? (
        <Pressable accessibilityRole="button" onPress={pause} style={styles.secondaryButton}>
          <Text style={styles.secondaryText}>Pause map awareness</Text>
        </Pressable>
      ) : null}
    </ScrollView>
  );
}

function PresenceMarker({
  cell,
  index,
  latitude,
  longitude,
}: {
  cell: PresenceCell;
  index: number;
  latitude: number;
  longitude: number;
}) {
  const x = clamp(50 + (cell.approximateLongitude - longitude) * 850, 8, 92);
  const y = clamp(50 - (cell.approximateLatitude - latitude) * 650, 8, 92);
  return (
    <View
      accessibilityLabel={`${cell.density} coarse RoadTalk activity cell`}
      style={[styles.presenceMarker, { left: `${x}%`, top: `${y}%` }]}
    >
      <Text style={styles.presenceText}>{densityLabel(cell.density, index)}</Text>
    </View>
  );
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(maximum, Math.max(minimum, value));
}

function densityLabel(density: PresenceCell["density"], index: number): string {
  switch (density) {
    case "few": return `Few ${index + 1}`;
    case "several": return `Several ${index + 1}`;
    case "many": return `Many ${index + 1}`;
  }
}

function statusTitle(status: string): string {
  switch (status) {
    case "active": return "Foreground awareness active";
    case "checking": return "Checking location permission";
    case "blocked": return "Location permission blocked";
    case "denied": return "Location permission denied";
    case "unavailable": return "Location services unavailable";
    case "error": return "Map awareness unavailable";
    case "paused": return "Map awareness paused";
    default: return "Map awareness off";
  }
}

function statusText(
  snapshot: ReturnType<LocationLifecycleControl["getSnapshot"]>,
  presence: PresenceState,
): string {
  if (snapshot.status !== "active") {
    return "Enable foreground location to display your position and request coarse nearby presence.";
  }
  if (snapshot.local.status === "waiting") return "Waiting for a foreground location sample.";
  if (snapshot.local.status === "stale") return "Your last foreground location is stale; nearby cells are hidden.";
  if (snapshot.upload === "retrying") return "Your location could not be refreshed; nearby cells are hidden until it succeeds.";
  if (presence.status === "unavailable") return "Coarse nearby presence is temporarily unavailable.";
  if (presence.status === "stale") return "Coarse nearby presence expired and is hidden until refreshed.";
  if (presence.status === "current") {
    return presence.value.cells.length === 0
      ? "Your location is current. No privacy-qualified nearby cells are visible."
      : `Your location is current. ${presence.value.cells.length} privacy-qualified coarse cells are visible.`;
  }
  return "Your location is current. Loading privacy-qualified nearby presence.";
}

const styles = StyleSheet.create({
  container: { backgroundColor: colors.background, flexGrow: 1, gap: spacing.large, padding: spacing.xlarge },
  title: { color: colors.text, fontSize: 32, fontWeight: "700" },
  body: { color: colors.muted, fontSize: 16, lineHeight: 24 },
  notice: { backgroundColor: colors.surface, borderColor: colors.border, borderRadius: 12, borderWidth: 1, gap: spacing.small, padding: spacing.medium },
  noticeTitle: { color: colors.text, fontSize: 17, fontWeight: "700" },
  map: { backgroundColor: colors.surface, borderColor: colors.border, borderRadius: 18, borderWidth: 1, height: 340, overflow: "hidden", position: "relative" },
  gridLine: { backgroundColor: colors.border, opacity: 0.55, position: "absolute" },
  vertical: { bottom: 0, left: "50%", top: 0, width: 1 },
  horizontal: { height: 1, left: 0, right: 0, top: "50%" },
  youMarker: { backgroundColor: colors.primary, borderRadius: 9, height: 18, left: "50%", marginLeft: -9, marginTop: -9, position: "absolute", top: "50%", width: 18 },
  youLabel: { color: colors.text, fontSize: 13, fontWeight: "700", left: "50%", marginLeft: 12, marginTop: 7, position: "absolute", top: "50%" },
  presenceMarker: { alignItems: "center", backgroundColor: colors.background, borderColor: colors.primary, borderRadius: 10, borderWidth: 2, minWidth: 58, padding: 5, position: "absolute", transform: [{ translateX: -29 }, { translateY: -14 }] },
  presenceText: { color: colors.primary, fontSize: 11, fontWeight: "700" },
  statusCard: { backgroundColor: colors.surface, borderColor: colors.border, borderRadius: 12, borderWidth: 1, gap: spacing.small, padding: spacing.medium },
  statusTitle: { color: colors.text, fontSize: 18, fontWeight: "700" },
  primaryButton: { alignItems: "center", backgroundColor: colors.primary, borderRadius: 12, minHeight: 48, justifyContent: "center", paddingHorizontal: spacing.large },
  primaryText: { color: colors.surface, fontSize: 16, fontWeight: "700" },
  secondaryButton: { alignItems: "center", borderColor: colors.primary, borderRadius: 12, borderWidth: 2, minHeight: 48, justifyContent: "center", paddingHorizontal: spacing.large },
  secondaryText: { color: colors.primary, fontSize: 16, fontWeight: "700" },
});
