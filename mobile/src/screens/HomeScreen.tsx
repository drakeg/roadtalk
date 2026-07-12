import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { Pressable, StyleSheet, Text, View } from "react-native";

import type { RootStackParamList } from "../AppNavigator";
import { colors, spacing } from "../theme";

type Props = NativeStackScreenProps<RootStackParamList, "Foundation">;

export function HomeScreen({ navigation }: Props) {
  return (
    <View style={styles.container}>
      <Text accessibilityRole="header" style={styles.title}>
        RoadTalk
      </Text>
      <Text style={styles.body}>
        The project foundation is installed. Communication features arrive in
        later approved sprints.
      </Text>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Open app diagnostics"
        onPress={() => navigation.navigate("Diagnostics")}
        style={({ pressed }) => [styles.button, pressed && styles.buttonPressed]}
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
  buttonPressed: {
    opacity: 0.8,
  },
  buttonText: {
    color: colors.surface,
    fontSize: 17,
    fontWeight: "600",
  },
});
