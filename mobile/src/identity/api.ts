import { useMemo } from "react";

import { environment } from "../config";
import { useSessionClient } from "../session/SessionContext";
import type { SessionClient } from "../session/SessionClient";
import type {
  CallsignAvailability,
  Profile,
  ProfileUpdate,
} from "./types";

type Problem = {
  code?: string;
  detail?: string;
};

export class IdentityApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly retryAfter?: number,
  ) {
    super(message);
    this.name = "IdentityApiError";
  }
}

export class IdentityApi {
  constructor(
    private readonly baseUrl: string,
    private readonly session: SessionClient,
  ) {}

  private async request<T>(path: string, init: RequestInit): Promise<T> {
    let response: Response;
    try {
      response = await this.session.authenticatedFetch(
        `${this.baseUrl}${path}`,
        init,
      );
    } catch (error) {
      if (error instanceof IdentityApiError) {
        throw error;
      }
      throw new IdentityApiError(
        0,
        "NETWORK_ERROR",
        "RoadTalk could not reach the identity service.",
      );
    }

    if (!response.ok) {
      const problem = (await response.json().catch(() => ({}))) as Problem;
      const retryAfterHeader = response.headers.get("Retry-After");
      const parsedRetryAfter =
        retryAfterHeader === null ? Number.NaN : Number(retryAfterHeader);
      throw new IdentityApiError(
        response.status,
        problem.code ?? "REQUEST_FAILED",
        problem.detail ?? "The identity request could not be completed.",
        Number.isFinite(parsedRetryAfter) ? parsedRetryAfter : undefined,
      );
    }
    return (await response.json()) as T;
  }

  getProfile(): Promise<Profile> {
    return this.request<Profile>("/me/profile", {
      method: "GET",
      headers: { Accept: "application/json" },
    });
  }

  checkCallsign(callsign: string): Promise<CallsignAvailability> {
    return this.request<CallsignAvailability>(
      `/callsigns/availability?callsign=${encodeURIComponent(callsign)}`,
      {
        method: "GET",
        headers: { Accept: "application/json" },
      },
    );
  }

  updateProfile(update: ProfileUpdate): Promise<Profile> {
    return this.request<Profile>("/me/profile", {
      method: "PATCH",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(update),
    });
  }
}

export function useIdentityApi(): IdentityApi {
  const session = useSessionClient();
  return useMemo(
    () => new IdentityApi(environment.apiBaseUrl, session),
    [session],
  );
}
