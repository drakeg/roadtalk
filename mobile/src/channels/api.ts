import { useMemo } from "react";
import { randomUUID } from "expo-crypto";

import { environment } from "../config";
import { useSessionClient } from "../session/SessionContext";
import type { SessionClient } from "../session/SessionClient";
import type {
  ChannelCatalog,
  ChannelLifecycle,
  ChannelSelection,
  ChannelSummary,
  ChannelTransport,
  PrivateChannelReceipt,
} from "./types";

type Problem = {
  code?: string;
  detail?: string | { code?: string; detail?: string };
};
type Json = Record<string, unknown>;

export class ChannelApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
  ) {
    super("The channel request could not be completed.");
    this.name = "ChannelApiError";
  }
}

export class ChannelApi implements ChannelTransport {
  constructor(
    private readonly baseUrl: string,
    private readonly session: SessionClient,
    private readonly idempotencyKey: () => string = randomUUID,
  ) {}

  async list(): Promise<ChannelCatalog> {
    const body = await this.request("/channels", { method: "GET" });
    if (!Array.isArray(body.items)) {
      throw this.invalidResponse();
    }
    return { items: body.items.map((item) => this.channel(item)) };
  }

  async current(): Promise<ChannelSelection> {
    return this.selection(
      await this.request("/me/channel", { method: "GET" }),
    );
  }

  async select(channelId: string): Promise<ChannelSelection> {
    return this.selection(
      await this.request(`/channels/${encodeURIComponent(channelId)}/select`, {
        method: "POST",
      }),
    );
  }

  async join(invite: string): Promise<ChannelLifecycle> {
    return this.lifecycle(
      await this.request("/channels/private/join", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ invite }),
      }),
      "joined",
    );
  }

  async leave(channelId: string): Promise<ChannelLifecycle> {
    return this.lifecycle(
      await this.request(
        `/channels/${encodeURIComponent(channelId)}/membership`,
        { method: "DELETE" },
      ),
      "left",
    );
  }

  async create(displayLabel: string): Promise<PrivateChannelReceipt> {
    return this.privateReceipt(
      await this.request("/channels/private", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": this.idempotencyKey(),
        },
        body: JSON.stringify({ display_label: displayLabel }),
      }),
    );
  }

  async rotate(channelId: string): Promise<PrivateChannelReceipt> {
    return this.privateReceipt(
      await this.request(
        `/channels/${encodeURIComponent(channelId)}/invite/rotation`,
        { method: "POST", headers: { "Idempotency-Key": this.idempotencyKey() } },
      ),
    );
  }

  async close(channelId: string): Promise<ChannelLifecycle> {
    return this.lifecycle(
      await this.request(`/channels/${encodeURIComponent(channelId)}`, {
        method: "DELETE",
      }),
      "closed",
    );
  }

  private async request(path: string, init: RequestInit): Promise<Json> {
    let response: Response;
    try {
      response = await this.session.authenticatedFetch(
        `${this.baseUrl}${path}`,
        { ...init, headers: { Accept: "application/json", ...init.headers } },
      );
    } catch {
      throw new ChannelApiError(0, "CHANNEL_UNAVAILABLE");
    }
    if (!response.ok) {
      const problem = (await response.json().catch(() => ({}))) as Problem;
      const code =
        problem.code ??
        (typeof problem.detail === "object" ? problem.detail.code : undefined);
      throw new ChannelApiError(
        response.status,
        code ?? "CHANNEL_REQUEST_FAILED",
      );
    }
    try {
      const body: unknown = await response.json();
      if (typeof body !== "object" || body === null || Array.isArray(body)) {
        throw this.invalidResponse();
      }
      return body as Json;
    } catch (error) {
      if (error instanceof ChannelApiError) {
        throw error;
      }
      throw this.invalidResponse();
    }
  }

  private channel(value: unknown): ChannelSummary {
    if (typeof value !== "object" || value === null || Array.isArray(value)) {
      throw this.invalidResponse();
    }
    const body = value as Json;
    for (const forbidden of [
      "member_count",
      "members",
      "owner_id",
      "creator_account_id",
      "provider_room_ref",
      "participant_ref",
      "invite",
      "fingerprint",
    ]) {
      if (forbidden in body) throw this.invalidResponse();
    }
    if (
      typeof body.id !== "string" ||
      (body.slug !== null && body.slug !== "general" && body.slug !== "rv") ||
      typeof body.display_label !== "string" ||
      (body.type !== "public" && body.type !== "private") ||
      typeof body.selected !== "boolean" ||
      typeof body.enabled !== "boolean" ||
      typeof body.version !== "number" ||
      !Number.isInteger(body.version) ||
      body.version < 1
    ) {
      throw this.invalidResponse();
    }
    if (
      (body.type === "public" && body.slug === null) ||
      (body.type === "private" && body.slug !== null)
    ) {
      throw this.invalidResponse();
    }
    return {
      id: body.id,
      slug: body.slug,
      displayLabel: body.display_label,
      type: body.type,
      selected: body.selected,
      enabled: body.enabled,
      version: body.version,
    };
  }

  private selection(body: Json): ChannelSelection {
    const channel = this.channel(body);
    if (
      channel.selected !== true ||
      typeof body.selected_at !== "string" ||
      !Number.isFinite(Date.parse(body.selected_at)) ||
      typeof body.selection_version !== "number" ||
      !Number.isInteger(body.selection_version) ||
      body.selection_version < 1
    ) {
      throw this.invalidResponse();
    }
    return {
      ...channel,
      selected: true,
      selectedAt: body.selected_at,
      selectionVersion: body.selection_version,
    };
  }

  private lifecycle(
    body: Json,
    state: "joined" | "left" | "closed",
  ): ChannelLifecycle {
    if (
      typeof body.channel_id !== "string" ||
      body.state !== state ||
      typeof body.changed_at !== "string" ||
      !Number.isFinite(Date.parse(body.changed_at)) ||
      typeof body.replayed !== "boolean"
    ) {
      throw this.invalidResponse();
    }
    return {
      channelId: body.channel_id,
      state,
      changedAt: body.changed_at,
      replayed: body.replayed,
    };
  }

  private privateReceipt(body: Json): PrivateChannelReceipt {
    const semanticBody = { ...body };
    delete semanticBody.invite;
    delete semanticBody.created_at;
    delete semanticBody.replayed;
    const channel = this.channel(semanticBody);
    if (
      channel.type !== "private" ||
      typeof body.created_at !== "string" ||
      !Number.isFinite(Date.parse(body.created_at)) ||
      (body.invite !== null &&
        (typeof body.invite !== "string" ||
          body.invite.length < 40 ||
          body.invite.length > 128)) ||
      typeof body.replayed !== "boolean"
    ) {
      throw this.invalidResponse();
    }
    return {
      ...channel,
      createdAt: body.created_at,
      invite: body.invite,
      replayed: body.replayed,
    };
  }

  private invalidResponse(): ChannelApiError {
    return new ChannelApiError(0, "CHANNEL_RESPONSE_INVALID");
  }
}

export function useChannelApi(): ChannelApi {
  const session = useSessionClient();
  return useMemo(
    () => new ChannelApi(environment.apiBaseUrl, session),
    [session],
  );
}
