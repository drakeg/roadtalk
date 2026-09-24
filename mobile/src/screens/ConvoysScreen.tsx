import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import type { RootStackParamList } from "../AppNavigator";
import { ConvoyApi, type ConvoyAwareness, type ConvoyStatus } from "../convoys/api";
import { useSession, useSessionClient } from "../session/SessionContext";
import { colors, spacing } from "../theme";

type Props = NativeStackScreenProps<RootStackParamList, "Convoys"> & { api?: ConvoyApi };

export function ConvoysScreen({ api: providedApi }: Props) {
  const session = useSessionClient();
  const { snapshot } = useSession();
  const api = useMemo(() => providedApi ?? new ConvoyApi(session), [providedApi, session]);
  const [current, setCurrent] = useState<ConvoyStatus | null>(null);
  const [awareness, setAwareness] = useState<ConvoyAwareness | null>(null);
  const [name, setName] = useState("");
  const [convoyId, setConvoyId] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("Loading current convoy state…");

  const clearUnavailable = useCallback((nextMessage: string) => {
    setCurrent(null);
    setAwareness(null);
    setMessage(nextMessage);
  }, []);

  const refresh = useCallback(async () => {
    if (snapshot.status !== "authenticated") {
      clearUnavailable("Connect to RoadTalk to use convoys. No convoy state is inferred.");
      return;
    }
    setBusy(true);
    try {
      const status = await api.status();
      setCurrent(status);
      if (status === null) {
        setAwareness(null);
        setMessage("You are not currently in an active convoy.");
        return;
      }
      const nextAwareness = await api.awareness();
      if (nextAwareness === null || nextAwareness.convoy_id !== status.convoy_id) {
        clearUnavailable("Current convoy awareness is unavailable. No stale member state is shown.");
        return;
      }
      setAwareness(nextAwareness);
      setMessage("Current server-authorized convoy state loaded.");
    } catch {
      clearUnavailable("Convoy state is unavailable, offline, stale, permission-denied, or revoked. No cached member state is shown.");
    } finally {
      setBusy(false);
    }
  }, [api, clearUnavailable, snapshot.status]);

  useEffect(() => { void refresh(); }, [refresh]);

  async function create() {
    const value = name.trim();
    if (!value || busy) return;
    setBusy(true);
    try {
      await api.create(value);
      setName("");
      await refresh();
    } catch {
      clearUnavailable("Convoy creation failed. No convoy state is inferred.");
    } finally { setBusy(false); }
  }

  async function join() {
    const value = convoyId.trim();
    if (!value || busy) return;
    setBusy(true);
    try {
      await api.join(value);
      setConvoyId("");
      await refresh();
    } catch {
      clearUnavailable("Convoy join failed. No convoy state is inferred.");
    } finally { setBusy(false); }
  }

  async function leaveOrDisband(action: "leave" | "disband") {
    if (busy) return;
    setBusy(true);
    try {
      if (action === "leave") await api.leave(); else await api.disband();
      clearUnavailable(action === "leave" ? "You left the convoy." : "Convoy disbanded.");
    } catch {
      clearUnavailable("Convoy membership changed or is unavailable. No stale member state is shown.");
    } finally { setBusy(false); }
  }

  const confirmAction = (action: "leave" | "disband") => {
    const disband = action === "disband";
    Alert.alert(
      disband ? "Disband convoy?" : "Leave convoy?",
      disband ? "This ends the convoy for every member and cannot be undone." : "You will lose this convoy context.",
      [
        { text: "Cancel", style: "cancel" },
        { text: disband ? "Disband" : "Leave", style: "destructive", onPress: () => void leaveOrDisband(action) },
      ],
    );
  };

  return (
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <Text accessibilityRole="header" style={styles.title}>Convoys</Text>
      <Text style={styles.body}>Travel together using server-authorized current context. Membership never grants communication access. Mobile does not collect background location or audio for convoys.</Text>
      <View accessibilityLiveRegion="polite" style={styles.card}><Text style={styles.body}>{message}</Text></View>
      {current === null ? (
        <>
          <View style={styles.card}>
            <Text accessibilityRole="header" style={styles.section}>Create convoy</Text>
            <TextInput accessibilityLabel="Convoy name" editable={!busy} maxLength={64} onChangeText={setName} placeholder="Convoy name" placeholderTextColor={colors.muted} style={styles.input} value={name} />
            <Pressable accessibilityRole="button" accessibilityLabel="Create convoy" disabled={busy || !name.trim()} onPress={() => void create()} style={styles.button}><Text style={styles.buttonText}>Create</Text></Pressable>
          </View>
          <View style={styles.card}>
            <Text accessibilityRole="header" style={styles.section}>Join convoy</Text>
            <TextInput accessibilityLabel="Convoy ID" autoCapitalize="none" editable={!busy} onChangeText={setConvoyId} placeholder="Convoy ID" placeholderTextColor={colors.muted} style={styles.input} value={convoyId} />
            <Pressable accessibilityRole="button" accessibilityLabel="Join convoy" disabled={busy || !convoyId.trim()} onPress={() => void join()} style={styles.button}><Text style={styles.buttonText}>Join</Text></Pressable>
          </View>
        </>
      ) : (
        <View style={styles.card}>
          <Text accessibilityRole="header" style={styles.section}>{current.display_name}</Text>
          <Text style={styles.muted}>{current.role === "leader" ? "You lead this convoy." : "You are a convoy member."}</Text>
          <Text style={styles.muted}>Only members with eligible foreground current state appear below. No coordinates, routes, or movement history are shown.</Text>
          {awareness?.members.map((member) => <Text accessibilityLabel={`${member.callsign}, ${member.role}, current`} key={member.account_id} style={styles.member}>{member.callsign} · {member.role} · current</Text>)}
          {awareness !== null && awareness.members.length === 0 ? <Text style={styles.muted}>No members currently have eligible foreground current state.</Text> : null}
          <Pressable accessibilityRole="button" accessibilityLabel="Refresh convoy state" disabled={busy} onPress={() => void refresh()} style={styles.secondaryButton}><Text style={styles.secondaryText}>Refresh</Text></Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel={current.role === "leader" ? "Disband convoy" : "Leave convoy"} disabled={busy} onPress={() => confirmAction(current.role === "leader" ? "disband" : "leave")} style={styles.dangerButton}><Text style={styles.buttonText}>{current.role === "leader" ? "Disband convoy" : "Leave convoy"}</Text></Pressable>
        </View>
      )}
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
  member: { color: colors.text, fontSize: 16, borderTopColor: colors.border, borderTopWidth: 1, paddingTop: spacing.small },
  button: { minHeight: 48, alignItems: "center", justifyContent: "center", borderRadius: 10, backgroundColor: colors.primary },
  dangerButton: { minHeight: 48, alignItems: "center", justifyContent: "center", borderRadius: 10, backgroundColor: colors.danger },
  buttonText: { color: colors.surface, fontSize: 16, fontWeight: "700" },
  secondaryButton: { minHeight: 48, alignItems: "center", justifyContent: "center", borderRadius: 10, borderColor: colors.primary, borderWidth: 1 },
  secondaryText: { color: colors.primary, fontSize: 16, fontWeight: "600" },
});
