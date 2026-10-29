import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AppState, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import type { RootStackParamList } from "../AppNavigator";
import { PremiumApi, type PremiumStatus } from "../premium/api";
import { useSession, useSessionClient } from "../session/SessionContext";
import { colors, spacing } from "../theme";

type Props = NativeStackScreenProps<RootStackParamList, "Premium"> & { api?: Pick<PremiumApi, "status"> };

const ENTITLEMENT_TEXT: Record<string, string> = {
  active: "Active",
  inactive: "Not active",
  expired: "Expired",
  revoked: "Revoked",
};

function time(value: string): string {
  return new Date(value).toLocaleTimeString();
}

export function PremiumScreen({ api: providedApi }: Props) {
  const session = useSessionClient();
  const { snapshot } = useSession();
  const api = useMemo(() => providedApi ?? new PremiumApi(session), [providedApi, session]);
  const [status, setStatus] = useState<PremiumStatus | null>(null);
  const [message, setMessage] = useState("Checking Premium status…");
  const [busy, setBusy] = useState(false);
  // Every clear bumps the generation so an in-flight response can never
  // repopulate status that was cleared for staleness, backgrounding or sign-out.
  const generation = useRef(0);
  const expiry = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clear = useCallback((nextMessage: string, supersede = true) => {
    if (supersede) generation.current += 1;
    if (expiry.current !== null) {
      clearTimeout(expiry.current);
      expiry.current = null;
    }
    setStatus(null);
    setMessage(nextMessage);
  }, []);

  const check = useCallback(async () => {
    if (snapshot.status !== "authenticated") {
      clear("Connect to RoadTalk to check Premium status. No Premium state is inferred.");
      return;
    }
    const request = ++generation.current;
    setBusy(true);
    setMessage("Checking Premium status…");
    try {
      const next = await api.status();
      if (request !== generation.current) return;
      if (next.availability === "provider_disabled") {
        clear("Premium is not available in this RoadTalk environment. Your existing RoadTalk features are unchanged.", false);
        return;
      }
      if (next.availability === "provider_unavailable") {
        clear("Premium status could not be confirmed right now. Nothing has changed; try again later.", false);
        return;
      }
      const remaining = Date.parse(next.valid_until) - Date.now();
      if (!(remaining > 0)) {
        clear("That Premium status is already out of date. Check again.", false);
        return;
      }
      if (expiry.current !== null) clearTimeout(expiry.current);
      expiry.current = setTimeout(() => clear("Premium status expired and was cleared. Check again to confirm it."), remaining);
      setStatus(next);
      setMessage(next.premium_experience_allowed ? "Premium is active for this account." : "This account does not have active Premium.");
    } catch {
      if (request === generation.current) {
        clear("Premium status is unavailable or offline. No cached Premium state is shown.", false);
      }
    } finally {
      setBusy(false);
    }
  }, [api, clear, snapshot.status]);

  useEffect(() => {
    void check();
  }, [check]);

  useEffect(() => {
    const subscription = AppState.addEventListener("change", (state) => {
      if (state !== "active") {
        clear("Premium status was cleared while RoadTalk was not in the foreground. Check again to confirm it.");
      }
    });
    return () => {
      subscription.remove();
      generation.current += 1;
      if (expiry.current !== null) clearTimeout(expiry.current);
    };
  }, [clear]);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text accessibilityRole="header" style={styles.title}>Premium</Text>
      <Text style={styles.body}>Premium never changes who you can hear or talk to. Radio, channels, convoys, the map, notifications, and every other feature you use today stay available without Premium.</Text>
      <View accessibilityLiveRegion="polite" style={styles.card}>
        <Text style={styles.body}>{message}</Text>
      </View>
      <View style={styles.card}>
        <Text accessibilityRole="header" style={styles.section}>Your entitlement</Text>
        {status === null ? (
          <Text style={styles.muted}>No server-confirmed Premium status is shown.</Text>
        ) : (
          <>
            <Text accessibilityLabel={`Plan: ${status.tier === "premium" ? "Premium" : "Free"}`} style={styles.body}>Plan: {status.tier === "premium" ? "Premium" : "Free"}</Text>
            <Text style={styles.body}>Entitlement: {status.entitlement_state === null ? "None" : ENTITLEMENT_TEXT[status.entitlement_state]}</Text>
            <Text style={styles.body}>Premium experience: {status.premium_experience_allowed ? "Available" : "Not available"}</Text>
            <Text style={styles.muted}>Confirmed by the RoadTalk server at {time(status.observed_at)}{status.provider_mode === "test" ? " (deterministic test provider, no billing)" : ""}.</Text>
            <Text style={styles.muted}>Valid until {time(status.valid_until)}.</Text>
          </>
        )}
        <Pressable accessibilityRole="button" accessibilityLabel="Check Premium status" accessibilityState={{ disabled: busy, busy }} disabled={busy} onPress={() => void check()} style={styles.button}>
          <Text style={styles.buttonText}>Check Premium status</Text>
        </Pressable>
      </View>
      <View style={styles.card}>
        <Text accessibilityRole="header" style={styles.section}>Purchasing</Text>
        <Text style={styles.body}>Premium purchase is not available. RoadTalk does not offer checkout, collect payment details, or connect to an app store or payment provider.</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, backgroundColor: colors.background, padding: spacing.large, gap: spacing.large },
  title: { color: colors.text, fontSize: 32, fontWeight: "700" },
  section: { color: colors.text, fontSize: 20, fontWeight: "700" },
  body: { color: colors.text, fontSize: 16, lineHeight: 23 },
  muted: { color: colors.muted, fontSize: 14, lineHeight: 20 },
  card: { backgroundColor: colors.surface, borderColor: colors.border, borderRadius: 12, borderWidth: 1, gap: spacing.medium, padding: spacing.medium },
  button: { minHeight: 48, alignItems: "center", justifyContent: "center", borderRadius: 10, backgroundColor: colors.primary },
  buttonText: { color: colors.surface, fontSize: 16, fontWeight: "700" },
});
