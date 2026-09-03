import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("provider-free mobile notification scope", () => {
  it("keeps push providers, background permissions, analytics, and sensitive targeting out", () => {
    const root = resolve(__dirname, "..");
    const source = [
      "notifications/api.ts",
      "notifications/types.ts",
      "screens/NotificationsScreen.tsx",
    ]
      .map((path) => readFileSync(resolve(root, path), "utf8"))
      .join("\n");
    const packageJson = readFileSync(resolve(root, "..", "package.json"), "utf8");
    const appConfig = readFileSync(resolve(root, "..", "app.config.ts"), "utf8");

    expect(packageJson).not.toMatch(
      /expo-notifications|firebase|@react-native-firebase|onesignal|pinpoint|sns/i,
    );
    expect(appConfig).not.toMatch(/remote-notification|UIBackgroundModes.*remote/i);
    expect(source).not.toMatch(/requestBackgroundPermissions|startLocationUpdates|TaskManager/i);
    expect(source).not.toMatch(/console\.|AsyncStorage|analytics/i);
    expect(source).not.toMatch(/recipientIds?|pushToken|providerToken|coordinates|radiusM/i);
  });
});
