import catalog from "./avatarCatalog.json";

export type AvatarStatus = "active" | "retired";

export type AvatarAsset = {
  id: string;
  label: string;
  glyph: string;
  background_color: string;
  foreground_color: string;
  status: AvatarStatus;
};

type AvatarCatalog = {
  version: string;
  avatars: AvatarAsset[];
};

export const AVATAR_CATALOG = catalog as AvatarCatalog;
export const SELECTABLE_AVATARS = AVATAR_CATALOG.avatars.filter(
  (avatar) => avatar.status === "active",
);

export function getAvatarAsset(avatarId: string): AvatarAsset | undefined {
  return AVATAR_CATALOG.avatars.find((avatar) => avatar.id === avatarId);
}
