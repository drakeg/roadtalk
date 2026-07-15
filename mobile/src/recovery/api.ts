import { useMemo } from "react";

import { environment } from "../config";
import { ApiError } from "../session/api";
import { useSessionClient } from "../session/SessionContext";
import type { SessionClient } from "../session/SessionClient";
import type { RecoveryResult } from "../session/types";
import type { RecoveryKeyResponse } from "./types";

type Problem = {
  code?: string;
  detail?: string | { code?: string; detail?: string };
};

export class RecoveryApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly retryAfter?: number,
  ) {
    super(message);
    this.name = "RecoveryApiError";
  }
}

function retryAfter(response: Response): number | undefined {
  const header = response.headers.get("Retry-After");
  const parsed = header === null ? Number.NaN : Number(header);
  return Number.isFinite(parsed) ? parsed : undefined;
}

async function responseError(response: Response): Promise<RecoveryApiError> {
  const problem = (await response.json().catch(() => ({}))) as Problem;
  const nested = typeof problem.detail === "object" ? problem.detail : undefined;
  return new RecoveryApiError(
    response.status,
    nested?.code ?? problem.code ?? "REQUEST_FAILED",
    nested?.detail ??
      (typeof problem.detail === "string"
        ? problem.detail
        : "The recovery request could not be completed."),
    retryAfter(response),
  );
}

function normalizeError(error: unknown): RecoveryApiError {
  if (error instanceof RecoveryApiError) {
    return error;
  }
  if (error instanceof ApiError) {
    return new RecoveryApiError(
      error.status,
      error.code,
      error.message,
      error.retryAfter,
    );
  }
  return new RecoveryApiError(
    0,
    "NETWORK_ERROR",
    "RoadTalk could not reach the recovery service.",
  );
}

export class RecoveryApi {
  constructor(
    private readonly baseUrl: string,
    private readonly session: SessionClient,
  ) {}

  async createRecoveryKey(): Promise<RecoveryKeyResponse> {
    let response: Response;
    try {
      response = await this.session.authenticatedFetch(
        `${this.baseUrl}/me/recovery-key`,
        {
          method: "POST",
          headers: { Accept: "application/json" },
        },
      );
    } catch (error) {
      throw normalizeError(error);
    }
    if (!response.ok) {
      throw await responseError(response);
    }
    return (await response.json()) as RecoveryKeyResponse;
  }

  async recover(recoveryKey: string): Promise<RecoveryResult> {
    try {
      return await this.session.recover(recoveryKey);
    } catch (error) {
      throw normalizeError(error);
    }
  }
}

export function useRecoveryApi(): RecoveryApi {
  const session = useSessionClient();
  return useMemo(
    () => new RecoveryApi(environment.apiBaseUrl, session),
    [session],
  );
}
