import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import type { RootStackParamList } from "../AppNavigator";
import { useMediaLifecycle } from "../media/MediaLifecycleContext";
import {
  RouteModeApiError,
  type RouteMode,
  type RouteModeReceipt,
  useRouteModeApi,
} from "../routeMode/api";
import { colors, spacing } from "../theme";

type Props = NativeStackScreenProps<RootStackParamList, "RouteMode">;

type ViewState =
  | { status: "loading" }
  | { status: "ready"; receipt: RouteModeReceipt }
  | { status: "changing"; receipt: RouteModeReceipt; target: RouteMode }
  | { status: "error"; message: string; receipt?: RouteModeReceipt };

export function RouteModeScreen(_: Props) {
  const api = useRouteModeApi();
  const media = useMediaLifecycle();
  const [state, setState] = useState<ViewState>({ status: "loading" });

  useEffect(() => {
    let active = true;
    void api
      .current()
      .then((receipt) => {
        if (active) setState({ status: "ready", receipt });
      })
      .catch(() => {
        if (active) {
          setState({
            status: "error",
            message: "Audience mode is unavailable right now.",
          });
        }
      });
    return () => {
      active = false;
    };
  }, [api]);

  const receipt = state.status === "loading" ? undefined : state.receipt;
  const changing = state.status === "changing";

  async function choose(mode: RouteMode) {
    if (receipt === undefined || changing || receipt.mode === mode) return;
    setState({ status: "changing", receipt, target: mode });
    try {
      await media?.prepareChannelTransition();
      const next = await api.update(mode, receipt.version);
      setState({ status: "ready", receipt: next });
    } catch (error) {
      const message =
        error instanceof RouteModeApiError && error.code === "ROUTE_MODE_VERSION_CONFLICT"
          ? "Audience mode changed elsewhere. Reload this screen and try again."
          : "RoadTalk could not update your audience mode.";
      setState({ status: "error", message, receipt });
    } finally {
      await media?.completeChannelTransition();
    }
  }

  const statusText =
    state.status === "loading"
      ? "Loading audience mode…"
      : state.status === "changing"
        ? state.target === "same_road"
          ? "Matching…"
          : "Switching to Nearby…"
        : state.status === "error"
          ? state.message
          : state.receipt.mode === "same_road" && state.receipt.availability === "unavailable"
            ? "Same road is unavailable right now."
            : state.receipt.mode === "same_road"
              ? "Same road is active."
              : "Nearby is active.";

  return (
    <View style={styles.container}>
      <Text accessibilityRole="header" style={styles.title}>
        Who should you hear?
      </Text>
      <Text style={styles.body}>
        Nearby is the default. Same road only narrows the nearby audience when RoadTalk
        can safely match current route context. RoadTalk does not show road names,
        directions, exact distance, or who did not match.
      </Text>

      <View accessibilityLiveRegion="polite" style={styles.statusCard}>
        <Text style={styles.statusTitle}>{statusText}</Text>
        <Text style={styles.body}>
          If Same road is unavailable, RoadTalk fails closed instead of widening your
          audience back to Nearby.
        </Text>
      </View>

      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Use Nearby audience mode"
        accessibilityState={{ selected: receipt?.mode === "nearby", disabled: changing }}
        disabled={changing || receipt === undefined}
        onPress={() => void choose("nearby")}
        style={({ pressed }) => [
          styles.option,
          receipt?.mode === "nearby" && styles.selected,
          (pressed || changing || receipt === undefined) && styles.pressed,
        ]}
      >
        <Text style={styles.optionTitle}>Nearby</Text>
        <Text style={styles.body}>Hear eligible RoadTalk users nearby on your channel.</Text>
      </Pressable>

      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Use Same road audience mode"
        accessibilityState={{ selected: receipt?.mode === "same_road", disabled: changing }}
        disabled={changing || receipt === undefined}
        onPress={() => void choose("same_road")}
        style={({ pressed }) => [
          styles.option,
          receipt?.mode === "same_road" && styles.selected,
          (pressed || changing || receipt === undefined) && styles.pressed,
        ]}
      >
        <Text style={styles.optionTitle}>Same road</Text>
        <Text style={styles.body}>
          Restrict eligible nearby audio to users RoadTalk can safely match to your
          current road context.
        </Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    padding: spacing.xlarge,
    gap: spacing.large,
  },
  title: {
    color: colors.text,
    fontSize: 30,
    fontWeight: "700",
  },
  body: {
    color: colors.muted,
    fontSize: 16,
    lineHeight: 24,
  },
  statusCard: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    padding: spacing.large,
    gap: spacing.small,
  },
  statusTitle: {
    color: colors.text,
    fontSize: 18,
    fontWeight: "700",
  },
  option: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 2,
    padding: spacing.large,
    gap: spacing.small,
  },
  selected: {
    borderColor: colors.primary,
  },
  optionTitle: {
    color: colors.text,
    fontSize: 20,
    fontWeight: "700",
  },
  pressed: {
    opacity: 0.72,
  },
});
