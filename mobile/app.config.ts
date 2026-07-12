import type { ExpoConfig, ConfigContext } from "expo/config";

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: "RoadTalk",
  slug: "roadtalk",
  version: "0.1.0",
  orientation: "portrait",
  userInterfaceStyle: "automatic",
  newArchEnabled: true,
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
  plugins: ["expo-dev-client"],
  extra: {
    apiBaseUrl: process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1",
  },
});
