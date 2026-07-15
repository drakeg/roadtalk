import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useCallback, useState } from "react";
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from "react-native";

import type { RootStackParamList } from "../AppNavigator";
import { RecoveryApiError, useRecoveryApi } from "../recovery/api";
import {
  secureRecoveryKeyStorage,
  type RecoveryKeyStorage,
} from "../recovery/storage";
import type { OneTimeRecoveryKey } from "../recovery/types";
import { colors, spacing } from "../theme";

type Props = NativeStackScreenProps<RootStackParamList, "Recovery">;

function recoveryError(error: unknown): string {
  if (error instanceof RecoveryApiError) {
    if (error.code === "RECOVERY_FAILED") {
      return "Recovery could not be completed with that key.";
    }
    if (error.code === "RECOVERY_RATE_LIMITED") {
      return "Recovery attempts are temporarily limited. Try again later.";
    }
  }
  return "Recovery is unavailable. Check your connection and try again.";
}

function creationError(error: unknown): string {
  if (
    error instanceof RecoveryApiError &&
    error.code === "RECOVERY_RATE_LIMITED"
  ) {
    return "Recovery-key changes are temporarily limited. Try again later.";
  }
  return "A recovery key could not be created. Check your connection and try again.";
}

export function RecoveryScreen({
  storage = secureRecoveryKeyStorage,
}: Props & { storage?: RecoveryKeyStorage }) {
  const api = useRecoveryApi();
  const [saveOnDevice, setSaveOnDevice] = useState(false);
  const [oneTimeKey, setOneTimeKey] = useState<OneTimeRecoveryKey | null>(null);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [storageWarning, setStorageWarning] = useState<string | null>(null);
  const [recoveryKey, setRecoveryKey] = useState("");
  const [recovering, setRecovering] = useState(false);
  const [recoverError, setRecoverError] = useState<string | null>(null);
  const [recovered, setRecovered] = useState(false);

  const revealKey = useCallback(
    async (value: string, version: "rtk1") => {
      setOneTimeKey({ value, version, savedOnDevice: false });
      setStorageWarning(null);
      if (saveOnDevice) {
        try {
          await storage.writeRecoveryKey(value);
          setOneTimeKey({ value, version, savedOnDevice: true });
        } catch {
          setStorageWarning(
            "The key could not be saved securely. Write it down before leaving this screen.",
          );
        }
        return;
      }
      try {
        await storage.clearRecoveryKey();
      } catch {
        setStorageWarning(
          "An older device-saved key could not be removed. The new key is shown only here.",
        );
      }
    },
    [saveOnDevice, storage],
  );

  const createKey = useCallback(async () => {
    setCreating(true);
    setCreateError(null);
    setStorageWarning(null);
    setRecovered(false);
    setOneTimeKey(null);
    try {
      const issued = await api.createRecoveryKey();
      await revealKey(issued.recovery_key, issued.key_version);
    } catch (error) {
      setCreateError(creationError(error));
    } finally {
      setCreating(false);
    }
  }, [api, revealKey]);

  const recoverAccount = useCallback(async () => {
    const submitted = recoveryKey.trim();
    setRecoverError(null);
    setRecovered(false);
    if (submitted.length === 0) {
      setRecoverError("Enter a recovery key.");
      return;
    }
    setRecovering(true);
    setOneTimeKey(null);
    setStorageWarning(null);
    try {
      const result = await api.recover(submitted);
      setRecoveryKey("");
      setRecovered(true);
      await revealKey(result.recoveryKey, result.recoveryKeyVersion);
    } catch (error) {
      setRecoverError(recoveryError(error));
    } finally {
      setRecovering(false);
    }
  }, [api, recoveryKey, revealKey]);

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      keyboardShouldPersistTaps="handled"
    >
      <Text accessibilityRole="header" style={styles.title}>
        Account recovery
      </Text>
      <Text style={styles.body}>
        Recovery is optional and does not use email, phone numbers, passwords,
        or support overrides.
      </Text>

      <View style={styles.section}>
        <Text accessibilityRole="header" style={styles.sectionTitle}>
          Create or rotate a key
        </Text>
        <Text style={styles.body}>
          Creating a key invalidates any previous key. RoadTalk shows the new
          key once, so write it down and keep it somewhere private.
        </Text>
        <View style={styles.switchRow}>
          <View style={styles.switchText}>
            <Text style={styles.label}>Save in secure storage</Text>
            <Text style={styles.hint}>
              Off by default. This device-only copy does not transfer to a new
              phone.
            </Text>
          </View>
          <Switch
            accessibilityLabel="Save recovery key in secure storage"
            accessibilityHint="Stores the next recovery key in platform-secure storage on this device only."
            onValueChange={setSaveOnDevice}
            value={saveOnDevice}
          />
        </View>
        <ActionButton
          disabled={creating}
          label={creating ? "Creating recovery key" : "Create or rotate recovery key"}
          onPress={createKey}
        />
        {createError !== null ? (
          <Text accessibilityRole="alert" style={styles.error}>
            {createError}
          </Text>
        ) : null}
      </View>

      <View style={styles.section}>
        <Text accessibilityRole="header" style={styles.sectionTitle}>
          Recover on this device
        </Text>
        <Text style={styles.body}>
          Enter a key on a newly registered device. Success signs out older
          sessions and replaces the key.
        </Text>
        <TextInput
          accessibilityLabel="Recovery key"
          accessibilityHint="Enter the complete recovery key."
          autoCapitalize="none"
          autoComplete="off"
          autoCorrect={false}
          maxLength={512}
          onChangeText={(value) => {
            setRecoveryKey(value);
            setRecoverError(null);
            setRecovered(false);
          }}
          secureTextEntry
          style={styles.input}
          value={recoveryKey}
        />
        <ActionButton
          disabled={recovering}
          label={recovering ? "Recovering account" : "Recover account"}
          onPress={recoverAccount}
          secondary
        />
        {recoverError !== null ? (
          <Text accessibilityRole="alert" style={styles.error}>
            {recoverError}
          </Text>
        ) : null}
        {recovered ? (
          <Text accessibilityLiveRegion="polite" style={styles.success}>
            Account recovered. Older sessions were signed out.
          </Text>
        ) : null}
      </View>

      {oneTimeKey !== null ? (
        <View accessibilityLiveRegion="assertive" style={styles.keyCard}>
          <Text accessibilityRole="header" style={styles.sectionTitle}>
            Save this recovery key now
          </Text>
          <Text style={styles.body}>
            It will not be shown again. Do not put it in a URL, message, or
            support request.
          </Text>
          <Text selectable style={styles.keyValue}>
            {oneTimeKey.value}
          </Text>
          <Text style={oneTimeKey.savedOnDevice ? styles.success : styles.hint}>
            {oneTimeKey.savedOnDevice
              ? "Saved securely on this device."
              : "Not saved by RoadTalk. Keep your own private copy."}
          </Text>
          {storageWarning !== null ? (
            <Text accessibilityRole="alert" style={styles.error}>
              {storageWarning}
            </Text>
          ) : null}
          <ActionButton
            label="I saved the key"
            onPress={() => {
              setOneTimeKey(null);
              setStorageWarning(null);
            }}
            secondary
          />
        </View>
      ) : null}

      <Text style={styles.scope}>
        Recovery never requests contacts, photos, location, microphone, or
        notification permission. Keys are not copied, logged, analyzed, placed
        in URLs, or saved outside SecureStore by this screen.
      </Text>
    </ScrollView>
  );
}

function ActionButton({
  disabled = false,
  label,
  onPress,
  secondary = false,
}: {
  disabled?: boolean;
  label: string;
  onPress: () => void | Promise<void>;
  secondary?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={() => void onPress()}
      style={({ pressed }) => [
        styles.button,
        secondary && styles.secondaryButton,
        disabled && styles.buttonDisabled,
        pressed && styles.buttonPressed,
      ]}
    >
      <Text
        style={secondary ? styles.secondaryButtonText : styles.buttonText}
      >
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.background,
    gap: spacing.large,
    padding: spacing.large,
  },
  title: {
    color: colors.text,
    fontSize: 30,
    fontWeight: "700",
  },
  section: {
    gap: spacing.medium,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 20,
    fontWeight: "700",
  },
  body: {
    color: colors.muted,
    fontSize: 17,
    lineHeight: 25,
  },
  label: {
    color: colors.text,
    fontSize: 17,
    fontWeight: "600",
  },
  hint: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 20,
  },
  switchRow: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    flexDirection: "row",
    gap: spacing.medium,
    justifyContent: "space-between",
    minHeight: 64,
    padding: spacing.medium,
  },
  switchText: {
    flex: 1,
    gap: spacing.small,
  },
  input: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    color: colors.text,
    fontSize: 17,
    minHeight: 52,
    paddingHorizontal: spacing.medium,
  },
  button: {
    alignItems: "center",
    backgroundColor: colors.primary,
    borderColor: colors.primary,
    borderRadius: 12,
    borderWidth: 2,
    justifyContent: "center",
    minHeight: 48,
    paddingHorizontal: spacing.large,
  },
  secondaryButton: {
    backgroundColor: colors.surface,
  },
  buttonText: {
    color: colors.surface,
    fontSize: 17,
    fontWeight: "600",
  },
  secondaryButtonText: {
    color: colors.primary,
    fontSize: 17,
    fontWeight: "600",
  },
  buttonDisabled: {
    opacity: 0.45,
  },
  buttonPressed: {
    opacity: 0.8,
  },
  keyCard: {
    backgroundColor: colors.surface,
    borderColor: colors.primary,
    borderRadius: 12,
    borderWidth: 2,
    gap: spacing.medium,
    padding: spacing.medium,
  },
  keyValue: {
    backgroundColor: colors.background,
    borderRadius: 8,
    color: colors.text,
    fontFamily: "monospace",
    fontSize: 15,
    lineHeight: 22,
    padding: spacing.medium,
  },
  error: {
    color: colors.danger,
    fontSize: 15,
    lineHeight: 22,
  },
  success: {
    color: colors.primary,
    fontSize: 15,
    fontWeight: "600",
  },
  scope: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 21,
  },
});
