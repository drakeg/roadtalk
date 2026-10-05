import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import {
  AppState,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import type { RootStackParamList } from "../AppNavigator";
import { MobileAiController } from "../ai/MobileAiController";
import type {
  AiLanguage,
  AuthorizedAiSource,
  MobileAiActionHandler,
} from "../ai/types";
import { colors, spacing } from "../theme";

type Props = NativeStackScreenProps<RootStackParamList, "AiTools"> & {
  controller?: MobileAiController;
  source?: AuthorizedAiSource | null;
  online?: boolean;
  providerMode?: "disabled" | "test";
};

const disabledAction: MobileAiActionHandler = async () => {
  throw new Error("AI provider unavailable");
};

const languageLabels: Readonly<Record<AiLanguage, string>> = {
  en: "English",
  es: "Spanish",
  fr: "French",
  de: "German",
};

export function AiToolsScreen({
  controller,
  source = null,
  online = false,
  providerMode = "disabled",
}: Props) {
  const ownedController = useMemo(
    () => controller ?? new MobileAiController(disabledAction),
    [controller],
  );
  const snapshot = useSyncExternalStore(
    ownedController.subscribe,
    ownedController.getSnapshot,
  );
  const [targetLanguage, setTargetLanguage] = useState<AiLanguage>("es");

  useEffect(() => {
    ownedController.setAuthorizedSource(source);
  }, [ownedController, source]);

  useEffect(() => {
    ownedController.setOnline(online);
  }, [online, ownedController]);

  useEffect(() => {
    ownedController.setProviderMode(providerMode);
  }, [ownedController, providerMode]);

  useEffect(() => {
    ownedController.setAppActive(AppState.currentState === "active");
    const subscription = AppState.addEventListener("change", (state) => {
      ownedController.setAppActive(state === "active");
    });
    return () => subscription.remove();
  }, [ownedController]);

  const controlsDisabled =
    snapshot.status !== "ready" && snapshot.status !== "result";

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text accessibilityRole="header" style={styles.title}>
        AI tools
      </Text>
      <Text style={styles.body}>
        AI can only transform content already authorized in RoadTalk. Nothing here
        creates a new audience, channel, proximity decision, or microphone permission.
      </Text>

      <View accessibilityLiveRegion="polite" style={styles.statusCard}>
        <Text style={styles.cardTitle}>AI status</Text>
        <Text style={styles.body}>{snapshot.message}</Text>
      </View>

      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Summarize authorized RoadTalk text"
        disabled={controlsDisabled}
        onPress={() => void ownedController.run("summary")}
        style={({ pressed }) => [
          styles.primaryButton,
          (pressed || controlsDisabled) && styles.pressed,
        ]}
      >
        <Text style={styles.primaryText}>Summarize authorized text</Text>
      </Pressable>

      <View style={styles.card}>
        <Text accessibilityRole="header" style={styles.cardTitle}>
          Translate authorized text
        </Text>
        <View style={styles.languageGrid}>
          {(Object.keys(languageLabels) as AiLanguage[]).map((language) => (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={"Translate target " + languageLabels[language]}
              accessibilityState={{ selected: targetLanguage === language }}
              disabled={controlsDisabled}
              key={language}
              onPress={() => setTargetLanguage(language)}
              style={({ pressed }) => [
                styles.secondaryButton,
                targetLanguage === language && styles.selectedButton,
                (pressed || controlsDisabled) && styles.pressed,
              ]}
            >
              <Text style={styles.secondaryText}>{languageLabels[language]}</Text>
            </Pressable>
          ))}
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={
            "Translate authorized RoadTalk text to " +
            languageLabels[targetLanguage]
          }
          disabled={controlsDisabled}
          onPress={() =>
            void ownedController.run("translation", targetLanguage)
          }
          style={({ pressed }) => [
            styles.primaryButton,
            (pressed || controlsDisabled) && styles.pressed,
          ]}
        >
          <Text style={styles.primaryText}>Translate authorized text</Text>
        </Pressable>
      </View>

      <View style={styles.card}>
        <Text accessibilityRole="header" style={styles.cardTitle}>
          Foreground transcription
        </Text>
        <Text style={styles.body}>
          Transcription requires an explicit foreground action. This screen does not
          start microphone capture, background recording, or durable audio storage.
        </Text>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Request foreground transcription"
          disabled={controlsDisabled}
          onPress={() => void ownedController.run("transcription")}
          style={({ pressed }) => [
            styles.primaryButton,
            (pressed || controlsDisabled) && styles.pressed,
          ]}
        >
          <Text style={styles.primaryText}>Request foreground transcription</Text>
        </Pressable>
      </View>

      {snapshot.status === "result" ? (
        <View accessibilityLiveRegion="polite" style={styles.resultCard}>
          <Text accessibilityRole="header" style={styles.cardTitle}>
            AI result
          </Text>
          <Text style={styles.meta}>
            Source: {snapshot.source.sourceKind} · {snapshot.source.sourceLanguage}
            {snapshot.result.targetLanguage !== undefined
              ? " → " + snapshot.result.targetLanguage
              : ""}
          </Text>
          <Text selectable style={styles.resultText}>
            {snapshot.result.text}
          </Text>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Clear AI result"
            onPress={() => ownedController.clearResult()}
            style={({ pressed }) => [
              styles.secondaryButton,
              pressed && styles.pressed,
            ]}
          >
            <Text style={styles.secondaryText}>Clear result</Text>
          </Pressable>
        </View>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.background,
    flexGrow: 1,
    gap: spacing.large,
    padding: spacing.xlarge,
  },
  title: { color: colors.text, fontSize: 32, fontWeight: "700" },
  body: { color: colors.muted, fontSize: 17, lineHeight: 25 },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    gap: spacing.medium,
    padding: spacing.medium,
  },
  statusCard: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    gap: spacing.small,
    padding: spacing.medium,
  },
  resultCard: {
    backgroundColor: colors.surface,
    borderColor: colors.primary,
    borderRadius: 12,
    borderWidth: 2,
    gap: spacing.medium,
    padding: spacing.medium,
  },
  cardTitle: { color: colors.text, fontSize: 18, fontWeight: "700" },
  meta: { color: colors.muted, fontSize: 14 },
  resultText: { color: colors.text, fontSize: 17, lineHeight: 25 },
  languageGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.small,
  },
  primaryButton: {
    alignItems: "center",
    backgroundColor: colors.primary,
    borderRadius: 12,
    justifyContent: "center",
    minHeight: 48,
    paddingHorizontal: spacing.large,
  },
  primaryText: { color: colors.surface, fontSize: 17, fontWeight: "600" },
  secondaryButton: {
    alignItems: "center",
    borderColor: colors.primary,
    borderRadius: 12,
    borderWidth: 2,
    justifyContent: "center",
    minHeight: 48,
    minWidth: 96,
    paddingHorizontal: spacing.medium,
  },
  selectedButton: { borderWidth: 4 },
  secondaryText: { color: colors.primary, fontSize: 16, fontWeight: "600" },
  pressed: { opacity: 0.65 },
});
