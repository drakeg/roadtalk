import { useMemo } from "react";

import { environment } from "../config";
import { useSessionClient } from "../session/SessionContext";
import type { SessionClient } from "../session/SessionClient";

export type RouteMode = "nearby" | "same_road";
export type RouteModeAvailability = "available" | "unavailable";

export type RouteModeReceipt = {
  mode: RouteMode;
  version: number;
  selectedAt: string;
  availability: RouteModeAvailability;
};

type Json = Record<string, unknown>;

type Problem = {
  code?: string;
  detail?: string | { code?: string; detail?: string };
};

export class RouteModeApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
  ) {
    super("RoadTalk could not update your audience mode.");
    this.name = "RouteModeApiError";
  }
}

export class RouteModeApi {
  constructor(
    private readonly baseUrl: string,
    private readonly session: SessionClient,
  ) {}

  async current(): Promise<RouteModeReceipt> {
    return this.receipt(await this.request("GET"));
  }

  async update(mode: RouteMode, expectedVersion: number): Promise<RouteModeReceipt> {
    return this.receipt(
      await this.request("PUT", {
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode, expected_version: expectedVersion }),
      }),
    );
  }

  private async request(method: "GET" | "PUT", init: RequestInit = {}): Promise<Json> {
    let response: Response;
    try {
      response = await this.session.authenticatedFetch(
        `${this.baseUrl}/me/route-mode`,
        { ...init, method, headers: { Accept: "application/json", ...init.headers } },
      );
    } catch {
      throw new RouteModeApiError(0, "ROUTE_MODE_UNAVAILABLE");
    }

    if (!response.ok) {
      const problem = (await response.json().catch(() => ({}))) as Problem;
      const code =
        problem.code ??
        (typeof problem.detail === "object" ? problem.detail.code : undefined);
      throw new RouteModeApiError(
        response.status,
        code ?? "ROUTE_MODE_REQUEST_FAILED",
      );
    }

    const body: unknown = await response.json().catch(() => null);
    if (typeof body !== "object" || body === null || Array.isArray(body)) {
      throw new RouteModeApiError(response.status, "ROUTE_MODE_INVALID_RESPONSE");
    }
    return body as Json;
  }

  private receipt(body: Json): RouteModeReceipt {
    for (const forbidden of [
      "road_name",
      "route",
      "provider",
      "provider_corridor_ref",
      "corridor_digest",
      "direction",
      "latitude",
      "longitude",
      "distance_m",
      "bearing",
      "account_id",
      "device_id",
      "participant_ref",
      "eligibility_reason",
    ]) {
      if (forbidden in body) {
        throw new RouteModeApiError(200, "ROUTE_MODE_INVALID_RESPONSE");
      }
    }

    if (
      (body.mode !== "nearby" && body.mode !== "same_road") ||
      typeof body.version !== "number" ||
      !Number.isInteger(body.version) ||
      body.version < 1 ||
      typeof body.selected_at !== "string" ||
      !Number.isFinite(Date.parse(body.selected_at)) ||
      (body.availability !== "available" && body.availability !== "unavailable")
    ) {
      throw new RouteModeApiError(200, "ROUTE_MODE_INVALID_RESPONSE");
    }

    return {
      mode: body.mode,
      version: body.version,
      selectedAt: body.selected_at,
      availability: body.availability,
    };
  }
}

export function useRouteModeApi(): RouteModeApi {
  const session = useSessionClient();
  return useMemo(() => new RouteModeApi(environment.apiBaseUrl, session), [session]);
}
