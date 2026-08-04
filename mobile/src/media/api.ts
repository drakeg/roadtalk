import { randomUUID } from "expo-crypto";

import type { SessionClient } from "../session/SessionClient";
import type {
  ReceiveGrant,
  ReceiveGrantTransport,
  TransmitGrant,
} from "./types";

type ReceiveGrantResponse = {
  grant_id: string;
  mode: "receive";
  allowed_actions: ["join", "subscribe"] | readonly ("join" | "subscribe")[];
  allowed_track_sources: readonly string[];
  server_url: string | null;
  participant_token: string | null;
};

type TransmitGrantResponse = {
  grant_id: string;
  receive_grant_id: string;
  mode: "transmit";
  allowed_actions: readonly string[];
  allowed_track_sources: readonly string[];
  expires_at: string;
};

type Problem = {
  code?: string;
  detail?: string | { code?: string; detail?: string };
};

export class MediaGrantError extends Error {
  constructor(readonly code: string) {
    super("The media authorization could not be completed.");
    this.name = "MediaGrantError";
  }
}

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

  async createTransmitGrant(receiveGrantId: string): Promise<TransmitGrant> {
    const response = await this.session.authenticatedFetch(
      `${this.baseUrl}/ptt/grants/${encodeURIComponent(receiveGrantId)}/transmit`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": this.idempotencyKey(),
        },
        body: JSON.stringify({}),
      },
    );
    if (!response.ok) {
      const problem = (await response.json().catch(() => ({}))) as Problem;
      const nested =
        typeof problem.detail === "object" ? problem.detail : undefined;
      throw new MediaGrantError(
        nested?.code ?? problem.code ?? "PTT_TRANSMIT_FAILED",
      );
    }
    const body = (await response.json()) as TransmitGrantResponse;
    if (
      typeof body.grant_id !== "string" ||
      body.grant_id.length === 0 ||
      typeof body.receive_grant_id !== "string" ||
      body.mode !== "transmit" ||
      body.receive_grant_id !== receiveGrantId ||
      typeof body.expires_at !== "string" ||
      !Number.isFinite(Date.parse(body.expires_at)) ||
      !Array.isArray(body.allowed_actions) ||
      body.allowed_actions.length !== 1 ||
      body.allowed_actions[0] !== "publish" ||
      !Array.isArray(body.allowed_track_sources) ||
      body.allowed_track_sources.length !== 1 ||
      body.allowed_track_sources[0] !== "microphone"
    ) {
      throw new MediaGrantError("PTT_TRANSMIT_SCOPE_INVALID");
    }
    return {
      grantId: body.grant_id,
      receiveGrantId: body.receive_grant_id,
      expiresAt: body.expires_at,
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
