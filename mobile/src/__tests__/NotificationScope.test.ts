import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("provider-free mobile notification scope", () => {
  it("keeps push providers, background permissions, analytics, and client targeting out", () => {
    const root = resolve(__dirname, "..");
    const apiSource = readFileSync(resolve(root, "notifications/api.ts"), "utf8");
    const screenSource = readFileSync(
      resolve(root, "screens/NotificationsScreen.tsx"),
      "utf8",
    );
    const source = [apiSource, screenSource].join("\n");
    const packageJson = readFileSync(resolve(root, "..", "package.json"), "utf8");
    const appConfig = readFileSync(resolve(root, "..", "app.config.ts"), "utf8");

    expect(packageJson).not.toMatch(
      /expo-notifications|firebase|@react-native-firebase|onesignal|pinpoint|sns/i,
    );
    expect(appConfig).not.toMatch(/remote-notification|UIBackgroundModes.*remote/i);
    expect(source).not.toMatch(/requestBackgroundPermissions|startLocationUpdates|TaskManager/i);
    expect(source).not.toMatch(/console\.|AsyncStorage|analytics/i);

    // These names exist only in the response deny-list; they are not mobile compose inputs.
    expect(apiSource).toContain('"recipient_ids"');
    expect(apiSource).toContain('"push_token"');
    expect(apiSource).toContain('"coordinates"');
    expect(apiSource).toContain('"radius_m"');
    expect(screenSource).not.toMatch(/recipient[_A-Z]?ids?\s*[:=]/i);
    expect(screenSource).not.toMatch(/push[_A-Z]?token\s*[:=]/i);
    expect(screenSource).not.toMatch(/coordinates\s*[:=]|radius[_A-Z]?m\s*[:=]/i);
  });
});
