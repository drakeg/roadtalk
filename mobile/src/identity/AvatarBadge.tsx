import { StyleSheet, Text, View } from "react-native";

import { getAvatarAsset } from "./avatarCatalog";

type Props = {
  avatarId: string;
  size?: number;
};

export function AvatarBadge({ avatarId, size = 64 }: Props) {
  const avatar = getAvatarAsset(avatarId);
  if (avatar === undefined) {
    return null;
  }

  return (
    <View
      accessible
      accessibilityLabel={avatar.label}
      accessibilityRole="image"
      style={[
        styles.badge,
        {
          backgroundColor: avatar.background_color,
          borderRadius: size / 2,
          height: size,
          width: size,
        },
      ]}
    >
      <Text
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
        style={[
          styles.glyph,
          {
            color: avatar.foreground_color,
            fontSize: Math.max(14, Math.round(size * 0.3)),
          },
        ]}
      >
        {avatar.glyph}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignItems: "center",
    justifyContent: "center",
  },
  glyph: {
    fontWeight: "700",
    letterSpacing: 1,
  },
});
