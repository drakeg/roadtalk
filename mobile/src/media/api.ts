import { randomUUID } from "expo-crypto";

import type { SessionClient } from "../session/SessionClient";
import type { ReceiveGrant, ReceiveGrantTransport } from "./types";

type ReceiveGrantResponse = {
  grant_id: string;
  mode: "receive";
  allowed_actions: ["join", "subscribe"] | readonly ("join" | "subscribe")[];
  allowed_track_sources: readonly string[];
  server_url: string | null;
  participant_token: string | null;
};

export class MediaGrantApi implements ReceiveGrantTransport {
  constructor(
    private readonly baseUrl: string,
    private readonly session: SessionClient,
    private readonly idempotencyKey: () => string = randomUUID,
  ) {}

  async createReceiveGrant(): Promise<ReceiveGrant> {
    const response = await this.session.authenticatedFetch(
      `${this.baseUrl}/ptt/grants`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": this.idempotencyKey(),
        },
        body: JSON.stringify({ mode: "receive" }),
      },
    );
    if (!response.ok) {
      throw new Error("Receive media is not available.");
    }
    const body = (await response.json()) as ReceiveGrantResponse;
    if (
      body.mode !== "receive" ||
      body.server_url === null ||
      body.participant_token === null ||
      body.allowed_track_sources.length !== 0 ||
      body.allowed_actions.length !== 2 ||
      !body.allowed_actions.includes("join") ||
      !body.allowed_actions.includes("subscribe")
    ) {
      throw new Error("The receive grant was not safely scoped.");
    }
    return {
      grantId: body.grant_id,
      serverUrl: body.server_url,
      participantToken: body.participant_token,
    };
  }

  async releaseGrant(grantId: string): Promise<void> {
    const response = await this.session.authenticatedFetch(
      `${this.baseUrl}/ptt/grants/${encodeURIComponent(grantId)}`,
      {
        method: "DELETE",
        headers: { "Idempotency-Key": this.idempotencyKey() },
      },
    );
    if (!response.ok) {
      throw new Error("The receive grant could not be released.");
    }
  }
}
