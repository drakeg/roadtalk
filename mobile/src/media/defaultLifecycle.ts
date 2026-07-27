import { environment } from "../config";
import type { SessionClient } from "../session/SessionClient";
import { MediaGrantApi } from "./api";
import { LiveKitReceiveRoom } from "./liveKitRoom";
import { MediaLifecycleController } from "./MediaLifecycleController";
import { expoMicrophonePermission } from "./permission";

export function createDefaultMediaLifecycle(session: SessionClient) {
  return new MediaLifecycleController(
    expoMicrophonePermission,
    new MediaGrantApi(environment.apiBaseUrl, session),
    new LiveKitReceiveRoom(),
  );
}
