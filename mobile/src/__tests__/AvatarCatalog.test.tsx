import { render } from "@testing-library/react-native";

import { AvatarBadge } from "../identity/AvatarBadge";
import {
  AVATAR_CATALOG,
  SELECTABLE_AVATARS,
  getAvatarAsset,
} from "../identity/avatarCatalog";

describe("bundled avatar catalog", () => {
  it("has a version, unique identifiers, and active choices", () => {
    const ids = AVATAR_CATALOG.avatars.map((avatar) => avatar.id);

    expect(AVATAR_CATALOG.version).toBe("2026.1");
    expect(new Set(ids).size).toBe(ids.length);
    expect(SELECTABLE_AVATARS).toHaveLength(6);
    expect(SELECTABLE_AVATARS.every((avatar) => avatar.status === "active")).toBe(
      true,
    );
  });

  it("renders active and retained retired avatars accessibly", async () => {
    const active = await render(<AvatarBadge avatarId="road-runner" />);
    expect(
      active.getByRole("image", { name: "Orange horizon avatar" }),
    ).toBeOnTheScreen();

    const retired = await render(<AvatarBadge avatarId="classic-rig" />);
    expect(
      retired.getByRole("image", { name: "Brown classic rig avatar" }),
    ).toBeOnTheScreen();
  });

  it("fails closed for an unknown identifier", async () => {
    expect(getAvatarAsset("unknown")).toBeUndefined();
    const view = await render(<AvatarBadge avatarId="unknown" />);
    expect(view.toJSON()).toBeNull();
  });
});
