import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import type { ConfigContext } from "expo/config";

import appConfig from "../../app.config";

describe("foreground-only location scope", () => {
  it("configures only foreground permission with accurate purpose text", () => {
    const config = appConfig({ config: {} } as ConfigContext);
    const plugin = config.plugins?.find(
      (candidate) => Array.isArray(candidate) && candidate[0] === "expo-location",
    );

    expect(plugin).toBeDefined();
    expect(plugin?.[1]).toEqual(
      expect.objectContaining({
        isIosBackgroundLocationEnabled: false,
        isAndroidBackgroundLocationEnabled: false,
        locationWhenInUsePermission: expect.stringMatching(/only while.*screen is open/i),
      }),
    );
  });

  it("contains no background task, persistent coordinate, analytics, or logging path", () => {
    const root = resolve(__dirname, "..");
    const locationSource = [
      "location/api.ts",
      "location/gateway.ts",
      "location/LocationLifecycleController.ts",
      "location/types.ts",
      "screens/LocationPermissionScreen.tsx",
    ]
      .map((path) => readFileSync(resolve(root, path), "utf8"))
      .join("\n");
    const packageJson = readFileSync(resolve(root, "..", "package.json"), "utf8");

    expect(locationSource).not.toMatch(
      /requestBackgroundPermissions|startLocationUpdates|TaskManager|Geofenc/i,
    );
    expect(locationSource).not.toMatch(/console\.|AsyncStorage|analytics/i);
    expect(packageJson).not.toMatch(/async-storage|task-manager|analytics/i);
  });
});
