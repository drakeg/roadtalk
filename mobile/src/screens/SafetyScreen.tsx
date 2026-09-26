import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import * as Crypto from "expo-crypto";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import type { RootStackParamList } from "../AppNavigator";
import { ModerationApi, type ReportReason, type RestrictionKind, type RestrictionSummary } from "../moderation/api";
import { useSession, useSessionClient } from "../session/SessionContext";
import { colors, spacing } from "../theme";

type Props = NativeStackScreenProps<RootStackParamList, "Safety"> & { api?: ModerationApi };
const reasons: ReportReason[] = ["harassment", "spam", "impersonation", "unsafe_content", "other"];
const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function SafetyScreen({ api: providedApi }: Props) {
  const client = useSessionClient();
  const { snapshot } = useSession();
  const api = useMemo(() => providedApi ?? new ModerationApi(client), [providedApi, client]);
  const [subject, setSubject] = useState("");
  const [reason, setReason] = useState<ReportReason>("harassment");
  const [items, setItems] = useState<RestrictionSummary[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("Loading safety controls…");
  const authenticated = snapshot.status === "authenticated";

  const refresh = useCallback(async () => {
    if (!authenticated) {
      setItems([]);
      setMessage("Sign in to manage safety controls. No cached restrictions are shown.");
      return;
    }
    setBusy(true);
    try {
      const response = await api.restrictions();
      setItems(response.items);
      setMessage("Current safety controls loaded.");
    } catch {
      setItems([]);
      setMessage("Safety controls are unavailable, offline, or revoked. Existing server-side restrictions remain enforced.");
    } finally {
      setBusy(false);
    }
  }, [api, authenticated]);

  useEffect(() => { void refresh(); }, [refresh]);

  async function perform(action: RestrictionKind | "report") {
    if (busy || !authenticated || !uuidPattern.test(subject.trim())) return;
    setBusy(true);
    try {
      if (action === "report") {
        await api.report(subject.trim(), reason, `mobile-${Crypto.randomUUID()}`);
        setMessage("Report submitted.");
      } else {
        await api.restrict(subject.trim(), action);
        setMessage(action === "block" ? "Account blocked." : "Account muted.");
        const response = await api.restrictions();
        setItems(response.items);
      }
      setSubject("");
    } catch {
      setItems([]);
      setMessage("Safety action is unavailable. No account status or restriction state is inferred.");
    } finally {
      setBusy(false);
    }
  }

  function confirm(action: RestrictionKind | "report") {
    if (!authenticated || busy || !uuidPattern.test(subject.trim())) return;
    Alert.alert(
      action === "report" ? "Submit report?" : action === "block" ? "Block account?" : "Mute account?",
      "This action uses only the account ID you entered. It does not reveal whether the account exists.",
      [
        { text: "Cancel", style: "cancel" },
        { text: action === "report" ? "Submit" : action === "block" ? "Block" : "Mute", onPress: () => void perform(action) },
      ],
    );
  }

  function confirmRevoke(item: RestrictionSummary) {
    if (busy || !authenticated) return;
    Alert.alert("Remove restriction?", "This removes your current mute or block control.", [
      { text: "Cancel", style: "cancel" },
      { text: "Remove", style: "destructive", onPress: () => void remove(item.restriction_id) },
    ]);
  }

  async function remove(id: string) {
    if (busy || !authenticated) return;
    setBusy(true);
    try {
      await api.revoke(id);
      const response = await api.restrictions();
      setItems(response.items);
      setMessage("Restriction removed.");
    } catch {
      setItems([]);
      setMessage("Safety action is unavailable. No cached restriction state is shown.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <Text accessibilityRole="header" style={styles.title}>Safety controls</Text>
      <Text style={styles.body}>Report, mute or block an account from an authorized RoadTalk interaction. No location, route, audio, background collection, or client-side authorization override is used.</Text>
      <View accessibilityLiveRegion="polite" style={styles.card}><Text style={styles.body}>{message}</Text></View>
      <View style={styles.card}>
        <Text accessibilityRole="header" style={styles.section}>Account action</Text>
        <TextInput accessibilityLabel="Account ID" autoCapitalize="none" autoCorrect={false} editable={authenticated && !busy} onChangeText={setSubject} placeholder="Account ID" placeholderTextColor={colors.muted} style={styles.input} value={subject} />
        <Text style={styles.muted}>Choose a report reason:</Text>
        {reasons.map((value) => (
          <Pressable key={value} accessibilityRole="radio" accessibilityState={{ selected: reason === value }} accessibilityLabel={value.replace("_", " ")} disabled={!authenticated || busy} onPress={() => setReason(value)} style={styles.secondaryButton}>
            <Text style={styles.secondaryText}>{reason === value ? "● " : "○ "}{value.replace("_", " ")}</Text>
          </Pressable>
        ))}
        <Pressable accessibilityRole="button" accessibilityLabel="Submit report" disabled={!authenticated || busy || !uuidPattern.test(subject.trim())} onPress={() => confirm("report")} style={styles.button}><Text style={styles.buttonText}>Report</Text></Pressable>
        <Pressable accessibilityRole="button" accessibilityLabel="Mute account" disabled={!authenticated || busy || !uuidPattern.test(subject.trim())} onPress={() => confirm("mute")} style={styles.button}><Text style={styles.buttonText}>Mute</Text></Pressable>
        <Pressable accessibilityRole="button" accessibilityLabel="Block account" disabled={!authenticated || busy || !uuidPattern.test(subject.trim())} onPress={() => confirm("block")} style={styles.dangerButton}><Text style={styles.buttonText}>Block</Text></Pressable>
      </View>
      <View style={styles.card}>
        <Text accessibilityRole="header" style={styles.section}>Your active restrictions</Text>
        <Pressable accessibilityRole="button" accessibilityLabel="Refresh safety controls" disabled={!authenticated || busy} onPress={() => void refresh()} style={styles.secondaryButton}><Text style={styles.secondaryText}>Refresh</Text></Pressable>
        {items.map((item) => (
          <View key={item.restriction_id} style={styles.item}>
            <Text style={styles.body}>{item.kind === "block" ? "Blocked" : "Muted"} account {item.subject_account_id}</Text>
            <Pressable accessibilityRole="button" accessibilityLabel={item.kind === "block" ? "Unblock account" : "Unmute account"} disabled={!authenticated || busy} onPress={() => confirmRevoke(item)} style={styles.secondaryButton}><Text style={styles.secondaryText}>{item.kind === "block" ? "Unblock" : "Unmute"}</Text></Pressable>
          </View>
        ))}
        {items.length === 0 ? <Text style={styles.muted}>No current restrictions are displayed.</Text> : null}
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
  input: { minHeight: 48, borderColor: colors.border, borderRadius: 10, borderWidth: 1, color: colors.text, paddingHorizontal: spacing.medium },
  item: { borderTopColor: colors.border, borderTopWidth: 1, paddingTop: spacing.small, gap: spacing.small },
  button: { minHeight: 48, alignItems: "center", justifyContent: "center", borderRadius: 10, backgroundColor: colors.primary },
  dangerButton: { minHeight: 48, alignItems: "center", justifyContent: "center", borderRadius: 10, backgroundColor: colors.danger },
  buttonText: { color: colors.surface, fontSize: 16, fontWeight: "700" },
  secondaryButton: { minHeight: 48, alignItems: "center", justifyContent: "center", borderRadius: 10, borderColor: colors.primary, borderWidth: 1 },
  secondaryText: { color: colors.primary, fontSize: 16, fontWeight: "600" },
});
