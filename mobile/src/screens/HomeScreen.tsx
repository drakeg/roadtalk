import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { Pressable, StyleSheet, Text, View } from "react-native";

import type { RootStackParamList } from "../AppNavigator";
import { useSession } from "../session/SessionContext";
import { colors, spacing } from "../theme";

type Props = NativeStackScreenProps<RootStackParamList, "Foundation">;

export function HomeScreen({ navigation }: Props) {
  const { snapshot, logout, reconnect } = useSession();
  const authenticated = snapshot.status === "authenticated";

  return (
    <View style={styles.container}>
      <Text accessibilityRole="header" style={styles.title}>
        RoadTalk
      </Text>
      <Text style={styles.body}>
        Set up a public pseudonymous identity now. Communication features arrive
        in later approved sprints.
      </Text>
      <View accessibilityLiveRegion="polite" style={styles.status}>
        <Text style={styles.statusLabel}>Anonymous session</Text>
        <Text style={styles.statusValue}>
          {snapshot.status === "loading"
            ? "Connecting securely…"
            : authenticated
              ? "Connected"
              : "Not connected"}
        </Text>
        {snapshot.status === "signed_out" && snapshot.message !== undefined ? (
          <Text style={styles.message}>{snapshot.message}</Text>
        ) : null}
      </View>
      {authenticated ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Review foreground location privacy"
          onPress={() => navigation.navigate("LocationPermission")}
          style={({ pressed }) => [
            styles.button,
            pressed && styles.buttonPressed,
          ]}
        >
          <Text style={styles.buttonText}>Location privacy</Text>
        </Pressable>
      ) : null}
      {authenticated ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Set up or edit identity"
          onPress={() => navigation.navigate("Identity")}
          style={({ pressed }) => [
            styles.button,
            pressed && styles.buttonPressed,
          ]}
        >
          <Text style={styles.buttonText}>Identity settings</Text>
        </Pressable>
      ) : null}
      {authenticated ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Create a recovery key or recover an account"
          onPress={() => navigation.navigate("Recovery")}
          style={({ pressed }) => [
            styles.button,
            pressed && styles.buttonPressed,
          ]}
        >
          <Text style={styles.buttonText}>Account recovery</Text>
        </Pressable>
      ) : null}
      <Pressable
        accessibilityRole="button"
        onPress={() => void (authenticated ? logout() : reconnect())}
        style={({ pressed }) => [
          styles.secondaryButton,
          pressed && styles.buttonPressed,
        ]}
      >
        <Text style={styles.secondaryButtonText}>
          {authenticated ? "Log out" : "Connect anonymously"}
        </Text>
      </Pressable>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Open app diagnostics"
        onPress={() => navigation.navigate("Diagnostics")}
        style={({ pressed }) => [
          styles.button,
          pressed && styles.buttonPressed,
        ]}
      >
        <Text style={styles.buttonText}>View diagnostics</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    justifyContent: "center",
    padding: spacing.xlarge,
    gap: spacing.large,
  },
  title: {
    color: colors.text,
    fontSize: 36,
    fontWeight: "700",
  },
  body: {
    color: colors.muted,
    fontSize: 18,
    lineHeight: 27,
  },
  button: {
    alignItems: "center",
    backgroundColor: colors.primary,
    borderRadius: 12,
    minHeight: 48,
    justifyContent: "center",
    paddingHorizontal: spacing.large,
  },
  secondaryButton: {
    alignItems: "center",
    borderColor: colors.primary,
    borderRadius: 12,
    borderWidth: 2,
    minHeight: 48,
    justifyContent: "center",
    paddingHorizontal: spacing.large,
  },
  secondaryButtonText: {
    color: colors.primary,
    fontSize: 17,
    fontWeight: "600",
  },
  status: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    padding: spacing.medium,
    gap: spacing.small,
  },
  statusLabel: {
    color: colors.muted,
    fontSize: 15,
  },
  statusValue: {
    color: colors.text,
    fontSize: 18,
    fontWeight: "600",
  },
  message: {
    color: colors.danger,
    fontSize: 15,
  },
  buttonPressed: {
    opacity: 0.8,
  },
  buttonText: {
    color: colors.surface,
    fontSize: 17,
    fontWeight: "600",
  },
});
