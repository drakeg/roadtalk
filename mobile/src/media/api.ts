import { randomUUID } from "expo-crypto";

import type { SessionClient } from "../session/SessionClient";
import type {
  ReceiveGrant,
  ReceiveGrantTransport,
  PublicationDelivery,
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

type PublicationResponse = {
  transmit_grant_id: string;
  delivery_state: "ready" | "no_nearby_listeners" | "reconciling" | "ended";
  proximity_policy_version: string;
  evaluated_at: string;
  expires_at: string;
  replayed: boolean;
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

  async publishTransmitTrack(
    transmitGrantId: string,
    trackRef: string,
  ): Promise<PublicationDelivery> {
    const response = await this.session.authenticatedFetch(
      `${this.baseUrl}/ptt/grants/${encodeURIComponent(transmitGrantId)}/publication`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ track_ref: trackRef }),
      },
    );
    if (!response.ok) {
      const problem = (await response.json().catch(() => ({}))) as Problem;
      const nested =
        typeof problem.detail === "object" ? problem.detail : undefined;
      const code = nested?.code ?? problem.code ?? "PTT_PUBLICATION_FAILED";
      throw new MediaGrantError(
        code === "PTT_PROVIDER_UNAVAILABLE"
          ? "PTT_DELIVERY_RECONCILING"
          : code,
      );
    }
    const body = (await response.json()) as PublicationResponse;
    const allowedStates = new Set([
      "ready",
      "no_nearby_listeners",
      "reconciling",
      "ended",
    ]);
    const exactKeys = [
      "delivery_state",
      "evaluated_at",
      "expires_at",
      "proximity_policy_version",
      "replayed",
      "transmit_grant_id",
    ];
    if (
      Object.keys(body).sort().join("|") !== exactKeys.join("|") ||
      body.transmit_grant_id !== transmitGrantId ||
      !allowedStates.has(body.delivery_state) ||
      typeof body.proximity_policy_version !== "string" ||
      body.proximity_policy_version.length === 0 ||
      !Number.isFinite(Date.parse(body.evaluated_at)) ||
      !Number.isFinite(Date.parse(body.expires_at)) ||
      typeof body.replayed !== "boolean"
    ) {
      throw new MediaGrantError("PTT_PUBLICATION_SCOPE_INVALID");
    }
    return {
      transmitGrantId: body.transmit_grant_id,
      deliveryState: body.delivery_state,
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
