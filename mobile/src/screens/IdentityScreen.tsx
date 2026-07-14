import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import type { RootStackParamList } from "../AppNavigator";
import { IdentityApiError, useIdentityApi } from "../identity/api";
import { AvatarBadge } from "../identity/AvatarBadge";
import { SELECTABLE_AVATARS, getAvatarAsset } from "../identity/avatarCatalog";
import { validateCallsignLocally } from "../identity/callsign";
import type {
  CallsignAvailability,
  Profile,
  ProfileUpdate,
} from "../identity/types";
import { colors, spacing } from "../theme";

type Props = NativeStackScreenProps<RootStackParamList, "Identity">;
type AvailabilityState =
  | "unchecked"
  | "checking"
  | CallsignAvailability["reason"];

function errorMessage(error: unknown, fallback: string): string {
  if (error instanceof IdentityApiError) {
    if (error.code === "PROFILE_VERSION_CONFLICT") {
      return "Your profile changed on another session. Reload it before saving.";
    }
    if (error.code === "CALLSIGN_CHANGE_COOLDOWN") {
      return "That callsign cannot be changed yet. Try again later.";
    }
    if (error.code === "AVATAR_UNAVAILABLE") {
      return "That avatar is no longer available. Choose another avatar.";
    }
  }
  return fallback;
}

export function IdentityScreen(_props: Props) {
  const api = useIdentityApi();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [callsign, setCallsign] = useState("");
  const [selectedAvatar, setSelectedAvatar] = useState<string | null>(null);
  const [availability, setAvailability] =
    useState<AvailabilityState>("unchecked");
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const localCallsign = useMemo(
    () => validateCallsignLocally(callsign),
    [callsign],
  );

  const applyProfile = useCallback((next: Profile) => {
    setProfile(next);
    setCallsign(next.identity.callsign ?? "");
    const currentAvatar = next.identity.avatar_id;
    const selectable =
      currentAvatar !== null &&
      SELECTABLE_AVATARS.some((avatar) => avatar.id === currentAvatar);
    setSelectedAvatar(selectable ? currentAvatar : null);
    setAvailability(
      next.identity.callsign === null ? "unchecked" : "available",
    );
  }, []);

  const loadProfile = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    setSaved(false);
    try {
      applyProfile(await api.getProfile());
    } catch {
      setLoadError(
        "Identity is unavailable. Check your connection and try again.",
      );
    } finally {
      setLoading(false);
    }
  }, [api, applyProfile]);

  useEffect(() => {
    void loadProfile();
  }, [loadProfile]);

  const checkAvailability = useCallback(async () => {
    setSaved(false);
    setSaveError(null);
    if (!localCallsign.valid) {
      setAvailability("invalid");
      return;
    }
    setChecking(true);
    setAvailability("checking");
    try {
      const result = await api.checkCallsign(localCallsign.display);
      setAvailability(result.reason);
    } catch {
      setAvailability("unchecked");
      setSaveError(
        "Callsign availability could not be checked. Check your connection and retry.",
      );
    } finally {
      setChecking(false);
    }
  }, [api, localCallsign]);

  const saveProfile = useCallback(async () => {
    if (profile === null || !localCallsign.valid) {
      return;
    }
    const existingAvatar = profile.identity.avatar_id;
    if (selectedAvatar === null && existingAvatar === null) {
      return;
    }

    const update: ProfileUpdate = {
      version: profile.version,
      callsign: localCallsign.display,
    };
    if (selectedAvatar !== null && selectedAvatar !== existingAvatar) {
      update.avatar_id = selectedAvatar;
    }

    setSaving(true);
    setSaveError(null);
    setSaved(false);
    try {
      const updated = await api.updateProfile(update);
      applyProfile(updated);
      setSaved(true);
    } catch (error) {
      setSaveError(
        errorMessage(
          error,
          "Your identity could not be saved. Check your connection and try again.",
        ),
      );
    } finally {
      setSaving(false);
    }
  }, [api, applyProfile, localCallsign, profile, selectedAvatar]);

  if (loading) {
    return (
      <View
        accessibilityLabel="Loading identity"
        accessibilityRole="progressbar"
        style={styles.centered}
      >
        <ActivityIndicator color={colors.primary} size="large" />
        <Text style={styles.body}>Loading identity…</Text>
      </View>
    );
  }

  if (loadError !== null || profile === null) {
    return (
      <View style={styles.centered}>
        <Text accessibilityRole="alert" style={styles.error}>
          {loadError ?? "Identity is unavailable."}
        </Text>
        <ActionButton label="Retry loading identity" onPress={loadProfile} />
      </View>
    );
  }

  const existingAvatar = profile.identity.avatar_id;
  const retainedAvatar =
    existingAvatar === null ? undefined : getAvatarAsset(existingAvatar);
  const avatarReady =
    selectedAvatar !== null ||
    (profile.setup_completed && retainedAvatar !== undefined);
  const canSave =
    localCallsign.valid &&
    availability === "available" &&
    avatarReady &&
    !saving &&
    !checking;

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      keyboardShouldPersistTaps="handled"
    >
      <Text accessibilityRole="header" style={styles.title}>
        {profile.setup_completed
          ? "Edit your identity"
          : "Set up your identity"}
      </Text>
      <Text style={styles.body}>
        Your callsign is a public pseudonym. Do not use a real name or contact
        information.
      </Text>

      {retainedAvatar?.status === "retired" ? (
        <View style={styles.currentIdentity}>
          <AvatarBadge avatarId={retainedAvatar.id} size={48} />
          <Text style={styles.body}>
            Your current avatar is retained but retired. It remains visible
            until you choose a replacement.
          </Text>
        </View>
      ) : null}

      <View style={styles.section}>
        <Text style={styles.label}>Callsign</Text>
        <TextInput
          accessibilityLabel="Callsign"
          accessibilityHint="Enter a public callsign using 3 to 24 letters, numbers, or single hyphens."
          autoCapitalize="none"
          autoCorrect={false}
          maxLength={128}
          onChangeText={(value) => {
            setCallsign(value);
            setAvailability("unchecked");
            setSaveError(null);
            setSaved(false);
          }}
          returnKeyType="done"
          style={styles.input}
          value={callsign}
        />
        {!localCallsign.valid && callsign.length > 0 ? (
          <Text accessibilityRole="alert" style={styles.error}>
            {localCallsign.message}
          </Text>
        ) : null}
        <ActionButton
          disabled={checking}
          label={checking ? "Checking callsign" : "Check callsign availability"}
          onPress={checkAvailability}
          secondary
        />
        <View accessibilityLiveRegion="polite">
          {availability === "available" ? (
            <Text style={styles.success}>This callsign is available.</Text>
          ) : null}
          {availability === "taken" || availability === "reserved" ? (
            <Text accessibilityRole="alert" style={styles.error}>
              That callsign is unavailable.
            </Text>
          ) : null}
          {availability === "invalid" ? (
            <Text accessibilityRole="alert" style={styles.error}>
              Enter a valid callsign before checking availability.
            </Text>
          ) : null}
        </View>
      </View>

      <View style={styles.section}>
        <Text accessibilityRole="header" style={styles.sectionTitle}>
          Choose an avatar
        </Text>
        <View accessibilityRole="radiogroup" style={styles.avatarGrid}>
          {SELECTABLE_AVATARS.map((avatar) => {
            const selected = selectedAvatar === avatar.id;
            return (
              <Pressable
                accessibilityLabel={`Select ${avatar.label}`}
                accessibilityRole="radio"
                accessibilityState={{ selected }}
                key={avatar.id}
                onPress={() => {
                  setSelectedAvatar(avatar.id);
                  setSaveError(null);
                  setSaved(false);
                }}
                style={[
                  styles.avatarChoice,
                  selected && styles.avatarChoiceSelected,
                ]}
              >
                <AvatarBadge avatarId={avatar.id} size={56} />
                <Text style={styles.avatarLabel}>
                  {avatar.label.replace(/ avatar$/, "")}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      <View accessibilityLiveRegion="polite">
        {saveError !== null ? (
          <Text accessibilityRole="alert" style={styles.error}>
            {saveError}
          </Text>
        ) : null}
        {saved ? (
          <Text accessibilityRole="status" style={styles.success}>
            Identity saved.
          </Text>
        ) : null}
      </View>

      <ActionButton
        disabled={!canSave}
        label={saving ? "Saving identity" : "Save identity"}
        onPress={saveProfile}
      />
      {saveError?.includes("another session") ? (
        <ActionButton
          label="Reload profile"
          onPress={loadProfile}
          secondary
        />
      ) : saveError !== null ? (
        <ActionButton
          label="Try saving again"
          onPress={saveProfile}
          secondary
        />
      ) : null}

      <Text style={styles.scope}>
        Identity setup never requests location, microphone, contacts, photos,
        or notification permission.
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
  centered: {
    alignItems: "center",
    backgroundColor: colors.background,
    flex: 1,
    gap: spacing.medium,
    justifyContent: "center",
    padding: spacing.large,
  },
  title: {
    color: colors.text,
    fontSize: 30,
    fontWeight: "700",
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
  section: {
    gap: spacing.medium,
  },
  label: {
    color: colors.text,
    fontSize: 17,
    fontWeight: "600",
  },
  input: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    color: colors.text,
    fontSize: 18,
    minHeight: 52,
    paddingHorizontal: spacing.medium,
  },
  avatarGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.medium,
  },
  avatarChoice: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 2,
    gap: spacing.small,
    minHeight: 112,
    padding: spacing.medium,
    width: "47%",
  },
  avatarChoiceSelected: {
    borderColor: colors.primary,
  },
  avatarLabel: {
    color: colors.text,
    fontSize: 14,
    textAlign: "center",
  },
  currentIdentity: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    flexDirection: "row",
    gap: spacing.medium,
    padding: spacing.medium,
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
