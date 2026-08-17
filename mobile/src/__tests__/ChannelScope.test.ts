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
    expect(source).toMatch(/oneTimeInvite/);
    expect(source).toMatch(/dismissInvite/);
    expect(source).toMatch(/async create/);
    expect(source).toMatch(/async rotate/);
    expect(source).toMatch(/async close/);

    const api = readFileSync(resolve(root, "channels/api.ts"), "utf8");
    expect(api).toMatch(/"member_count"/);
    expect(api).toMatch(/"provider_room_ref"/);
    expect(api).toMatch(/"Idempotency-Key"/);
    expect(api).toMatch(/invite\/rotation/);
    expect(api).not.toMatch(/AsyncStorage|SecureStore|console\.|analytics/i);
  });
});
