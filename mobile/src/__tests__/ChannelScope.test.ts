import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("mobile channel privacy and scope", () => {
  it("keeps channel state process-local, semantic, and non-disclosing", () => {
    const root = resolve(__dirname, "..");
    const source = [
      "channels/ChannelController.ts",
      "channels/types.ts",
      "screens/ChannelScreen.tsx",
    ]
      .map((path) => readFileSync(resolve(root, path), "utf8"))
      .join("\n");

    expect(source).toMatch(/prepareChannelTransition/);
    expect(source).toMatch(/completeChannelTransition/);
    expect(source).not.toMatch(
      /AsyncStorage|SecureStore|console\.|analytics|room_ref|participant_ref|member_count|owner_id/i,
    );
    expect(source).not.toMatch(/create_private|rotation|close_private/i);

    const api = readFileSync(resolve(root, "channels/api.ts"), "utf8");
    expect(api).toMatch(/"member_count"/);
    expect(api).toMatch(/"provider_room_ref"/);
    expect(api).not.toMatch(/AsyncStorage|SecureStore|console\.|analytics/i);
  });
});
