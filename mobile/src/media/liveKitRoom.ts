import {
  AndroidAudioTypePresets,
  AudioSession,
  registerGlobals,
} from "@livekit/react-native";
import { Room, RoomEvent, Track } from "livekit-client";

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
  private readonly authorizedAudioTrackRefs = new Set<string>();

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
      room.on(RoomEvent.TrackSubscribed, (track, publication) => {
        if (
          track.kind === Track.Kind.Audio &&
          track.source === Track.Source.Microphone
        ) {
          this.authorizedAudioTrackRefs.add(publication.trackSid);
          handlers.authorizedReceiveChanged(true);
        }
      });
      room.on(RoomEvent.TrackUnsubscribed, (_track, publication) => {
        this.authorizedAudioTrackRefs.delete(publication.trackSid);
        handlers.authorizedReceiveChanged(
          this.authorizedAudioTrackRefs.size > 0,
        );
      });
      this.room = room;
      await room.connect(grant.serverUrl, grant.participantToken, {
        autoSubscribe: false,
      });
      // Receive-ready must never create or enable a local microphone track.
      await room.localParticipant.setMicrophoneEnabled(false);
    } catch (error) {
      await this.disconnect();
      throw error;
    }
  }

  async publishMicrophone(): Promise<string> {
    if (this.room === null) {
      throw new Error("The receive room is not connected.");
    }
    const publication = await this.room.localParticipant.setMicrophoneEnabled(
      true,
    );
    if (publication === undefined || publication.trackSid.length === 0) {
      await this.room.localParticipant.setMicrophoneEnabled(false);
      throw new Error("The microphone publication has no opaque track reference.");
    }
    return publication.trackSid;
  }

  async stopMicrophone(): Promise<void> {
    if (this.room !== null) {
      await this.room.localParticipant.setMicrophoneEnabled(false);
    }
  }

  async disconnect(): Promise<void> {
    const room = this.room;
    this.room = null;
    this.authorizedAudioTrackRefs.clear();
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
