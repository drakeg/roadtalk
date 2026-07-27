import {
  getRecordingPermissionsAsync,
  requestRecordingPermissionsAsync,
} from "expo-audio";
import { Platform } from "react-native";

import type {
  MicrophonePermission,
  MicrophonePermissionGateway,
} from "./types";

function normalize(
  permission: Awaited<ReturnType<typeof getRecordingPermissionsAsync>>,
): MicrophonePermission {
  return {
    status:
      permission.status === "granted"
        ? "granted"
        : permission.status === "undetermined"
          ? "undetermined"
          : "denied",
    canAskAgain: permission.canAskAgain,
  };
}

export const expoMicrophonePermission: MicrophonePermissionGateway = {
  isAvailable: () => Platform.OS === "android" || Platform.OS === "ios",
  getPermission: async () => normalize(await getRecordingPermissionsAsync()),
  requestPermission: async () =>
    normalize(await requestRecordingPermissionsAsync()),
};
