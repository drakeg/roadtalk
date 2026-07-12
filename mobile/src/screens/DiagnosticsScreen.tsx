import { StyleSheet, Text, View } from "react-native";

import { environment } from "../config";
import { colors, spacing } from "../theme";

export function DiagnosticsScreen() {
  return (
    <View style={styles.container}>
      <Text accessibilityRole="header" style={styles.title}>
        Development diagnostics
      </Text>
      <Text style={styles.label}>Configured API</Text>
      <Text accessibilityLabel="Configured API address" selectable style={styles.value}>
        {environment.apiBaseUrl}
      </Text>
      <Text style={styles.note}>
        This screen contains configuration status only. It does not collect device,
        profile, location, or audio data.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    padding: spacing.large,
    gap: spacing.medium,
  },
  title: {
    color: colors.text,
    fontSize: 28,
    fontWeight: "700",
  },
  label: {
    color: colors.muted,
    fontSize: 16,
    fontWeight: "600",
  },
  value: {
    color: colors.text,
    fontSize: 16,
  },
  note: {
    color: colors.muted,
    fontSize: 16,
    lineHeight: 24,
  },
});
