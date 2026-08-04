import {
  AndroidAudioTypePresets,
  AudioSession,
  registerGlobals,
} from "@livekit/react-native";
import { Room, RoomEvent } from "livekit-client";

import type {
  ReceiveGrant,
  ReceiveRoomAdapter,
  RoomConnectionHandlers,
} from "./types";

let globalsRegistered = false;

function ensureGlobals(): void {
  if (!globalsRegistered) {
    registerGlobals();
    globalsRegistered = true;
  }
}

export class LiveKitReceiveRoom implements ReceiveRoomAdapter {
  private room: Room | null = null;
  private audioSessionStarted = false;

  async connectReceiveOnly(
    grant: ReceiveGrant,
    handlers: RoomConnectionHandlers,
  ): Promise<void> {
    await this.disconnect();
    ensureGlobals();
    await AudioSession.configureAudio({
      android: {
        audioTypeOptions: AndroidAudioTypePresets.communication,
      },
      ios: { defaultOutput: "speaker" },
    });
    await AudioSession.startAudioSession();
    this.audioSessionStarted = true;
    try {
      const room = new Room({
        adaptiveStream: true,
        dynacast: false,
      });
      room.on(RoomEvent.Reconnecting, handlers.reconnecting);
      room.on(RoomEvent.Reconnected, handlers.reconnected);
      room.on(RoomEvent.Disconnected, handlers.disconnected);
      room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
        handlers.receivingChanged(
          speakers.some(
            (participant) =>
              participant.identity !== room.localParticipant.identity,
          ),
        );
      });
      this.room = room;
      await room.connect(grant.serverUrl, grant.participantToken, {
        autoSubscribe: true,
      });
      // Receive-ready must never create or enable a local microphone track.
      await room.localParticipant.setMicrophoneEnabled(false);
    } catch (error) {
      await this.disconnect();
      throw error;
    }
  }

  async setMicrophoneEnabled(enabled: boolean): Promise<void> {
    if (this.room === null) {
      if (enabled) {
        throw new Error("The receive room is not connected.");
      }
      return;
    }
    await this.room.localParticipant.setMicrophoneEnabled(enabled);
  }

  async disconnect(): Promise<void> {
    const room = this.room;
    this.room = null;
    const audioSessionStarted = this.audioSessionStarted;
    this.audioSessionStarted = false;
    try {
      if (room !== null) {
        await room.localParticipant.setMicrophoneEnabled(false);
        await room.disconnect();
        room.removeAllListeners();
      }
    } finally {
      if (audioSessionStarted) {
        await AudioSession.stopAudioSession().catch(() => undefined);
      }
    }
  }
}
