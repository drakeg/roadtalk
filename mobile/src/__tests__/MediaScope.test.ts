import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import type { ConfigContext } from "expo/config";

import appConfig from "../../app.config";

describe("audio-only foreground media scope", () => {
  it("pins native development-build dependencies and disables background features", () => {
    const config = appConfig({ config: {} } as ConfigContext);
    const audio = config.plugins?.find(
      (candidate) => Array.isArray(candidate) && candidate[0] === "expo-audio",
    );
    const liveKit = config.plugins?.find(
      (candidate) =>
        Array.isArray(candidate) &&
        candidate[0] === "@livekit/react-native-expo-plugin",
    );

    expect(audio?.[1]).toEqual(
      expect.objectContaining({
        recordAudioAndroid: true,
        enableBackgroundRecording: false,
        enableBackgroundPlayback: false,
        microphonePermission: expect.stringMatching(/only while.*hold/i),
      }),
    );
    expect(liveKit?.[1]).toEqual(
      expect.objectContaining({
        android: expect.objectContaining({ enableScreenShareService: false }),
        ios: expect.objectContaining({
          enableMultitaskingCameraAccess: false,
        }),
      }),
    );
    expect(config.android?.blockedPermissions).toEqual(
      expect.arrayContaining([
        "android.permission.CAMERA",
        "android.permission.SYSTEM_ALERT_WINDOW",
        "android.permission.WAKE_LOCK",
      ]),
    );
  });

  it("limits capture to the server-authorized controller path", () => {
    const root = resolve(__dirname, "..");
    const paths = [
      "media/api.ts",
      "media/liveKitRoom.ts",
      "media/MediaLifecycleController.ts",
      "media/permission.ts",
      "media/types.ts",
    ];
    const files = paths.map((path) => ({
      path,
      source: readFileSync(resolve(root, path), "utf8"),
    }));
    const source = files.map(({ source: contents }) => contents).join("\n");
    const captureEnablers = files.filter(({ source: contents }) =>
      /setMicrophoneEnabled\(\s*true/.test(contents),
    );

    expect(source).toMatch(/setMicrophoneEnabled\(false\)/);
    expect(source).toMatch(/createTransmitGrant\(receiveGrantId\)/);
    expect(source).toMatch(/publishTransmitTrack/);
    expect(source).toMatch(/autoSubscribe:\s*false/);
    expect(captureEnablers.map(({ path }) => path)).toEqual([
      "media/liveKitRoom.ts",
    ]);
    expect(source.match(/setMicrophoneEnabled\(\s*true/g)).toHaveLength(1);
    expect(source).not.toMatch(
      /setCameraEnabled|startRecording|transcri|console\./i,
    );
  });
});
