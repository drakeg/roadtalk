import type { ExpoConfig, ConfigContext } from "expo/config";

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: "RoadTalk",
  slug: "roadtalk",
  version: "0.1.0",
  orientation: "portrait",
  userInterfaceStyle: "automatic",
  ios: {
    supportsTablet: true,
    bundleIdentifier: "com.roadtalk.mobile",
  },
  android: {
    package: "com.roadtalk.mobile",
    adaptiveIcon: {
      backgroundColor: "#10212b",
    },
  },
  plugins: [
    "expo-dev-client",
    [
      "expo-secure-store",
      {
        configureAndroidBackup: true,
      },
    ],
    [
      "expo-location",
      {
        locationWhenInUsePermission:
          "RoadTalk uses your location only while the location screen is open to provide coarse nearby awareness. Your coordinates are never shown to other users or stored as history.",
        isIosBackgroundLocationEnabled: false,
        isAndroidBackgroundLocationEnabled: false,
      },
    ],
  ],
  extra: {
    apiBaseUrl: process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1",
  },
});
