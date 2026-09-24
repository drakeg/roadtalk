import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import type { RootStackParamList } from "../AppNavigator";
import { useSession } from "../session/SessionContext";
import { colors, spacing } from "../theme";

type Props = NativeStackScreenProps<RootStackParamList, "Foundation">;

export function HomeScreen({ navigation }: Props) {
  const { snapshot, logout, reconnect } = useSession();
  const authenticated = snapshot.status === "authenticated";
  const open = (route: keyof RootStackParamList, label: string, accessibilityLabel: string) =>
    authenticated ? (
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={accessibilityLabel}
        onPress={() => navigation.navigate(route as never)}
        style={({ pressed }) => [styles.button, pressed && styles.buttonPressed]}
      >
        <Text style={styles.buttonText}>{label}</Text>
      </Pressable>
    ) : null;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text accessibilityRole="header" style={styles.title}>RoadTalk</Text>
      <Text style={styles.body}>Choose a channel, control who you can hear, and use RoadTalk with a public pseudonymous identity.</Text>
      <View accessibilityLiveRegion="polite" style={styles.status}>
        <Text style={styles.statusLabel}>RoadTalk session</Text>
        <Text style={styles.statusValue}>{snapshot.status === "loading" ? "Connecting securely…" : authenticated ? "Connected" : "Not connected"}</Text>
        {snapshot.status === "signed_out" && snapshot.message !== undefined ? <Text style={styles.message}>{snapshot.message}</Text> : null}
      </View>
      {open("Campgrounds", "Campgrounds", "Browse deterministic campground discovery and current context")}
      {open("Convoys", "Convoys", "Open convoy controls")}
      {open("Notifications", "Notifications", "Open notifications")}
      {open("MapAwareness", "Map awareness", "Open map awareness")}
      {open("Channels", "Channels", "Choose a RoadTalk channel")}
      {open("RouteMode", "Audience mode", "Choose Nearby or Same road audience mode")}
      {open("MicrophonePermission", "Microphone and live audio", "Review microphone and live audio privacy")}
      {open("LocationPermission", "Location privacy", "Review foreground location privacy")}
      {open("Identity", "Identity settings", "Set up or edit identity")}
      {open("Recovery", "Account recovery", "Create a recovery key or recover an account")}
      <Pressable accessibilityRole="button" onPress={() => void (authenticated ? logout() : reconnect())} style={({ pressed }) => [styles.secondaryButton, pressed && styles.buttonPressed]}>
        <Text style={styles.secondaryButtonText}>{authenticated ? "Log out" : "Connect anonymously"}</Text>
      </Pressable>
      <Pressable accessibilityRole="button" accessibilityLabel="Open app diagnostics" onPress={() => navigation.navigate("Diagnostics")} style={({ pressed }) => [styles.button, pressed && styles.buttonPressed]}>
        <Text style={styles.buttonText}>View diagnostics</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, backgroundColor: colors.background, padding: spacing.xlarge, gap: spacing.large },
  title: { color: colors.text, fontSize: 36, fontWeight: "700" },
  body: { color: colors.muted, fontSize: 18, lineHeight: 27 },
  button: { alignItems: "center", backgroundColor: colors.primary, borderRadius: 12, minHeight: 48, justifyContent: "center", paddingHorizontal: spacing.large },
  secondaryButton: { alignItems: "center", borderColor: colors.primary, borderRadius: 12, borderWidth: 2, minHeight: 48, justifyContent: "center", paddingHorizontal: spacing.large },
  secondaryButtonText: { color: colors.primary, fontSize: 17, fontWeight: "600" },
  status: { backgroundColor: colors.surface, borderColor: colors.border, borderRadius: 12, borderWidth: 1, padding: spacing.medium, gap: spacing.small },
  statusLabel: { color: colors.muted, fontSize: 15 },
  statusValue: { color: colors.text, fontSize: 18, fontWeight: "600" },
  message: { color: colors.danger, fontSize: 15 },
  buttonPressed: { opacity: 0.8 },
  buttonText: { color: colors.surface, fontSize: 17, fontWeight: "600" },
});
