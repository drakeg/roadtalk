import type {
  AnonymousSessionResponse,
  RecoverySessionResponse,
  TokenPair,
} from "./types";

type Fetch = typeof fetch;
type Problem = {
  code?: string;
  detail?: string | { code?: string; detail?: string };
};

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly retryAfter?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class AuthApi {
  constructor(
    private readonly baseUrl: string,
    private readonly fetcher: Fetch = fetch,
  ) {}

  private async request<T>(
    path: string,
    init: RequestInit,
    accessToken?: string,
  ): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");
    if (init.body !== undefined) {
      headers.set("Content-Type", "application/json");
    }
    if (accessToken !== undefined) {
      headers.set("Authorization", `Bearer ${accessToken}`);
    }
    const response = await this.fetcher(`${this.baseUrl}${path}`, {
      ...init,
      headers,
    });
    if (!response.ok) {
      const problem = (await response.json().catch(() => ({}))) as Problem;
      const nested =
        typeof problem.detail === "object" ? problem.detail : undefined;
      const retryAfterHeader = response.headers.get("Retry-After");
      const parsedRetryAfter =
        retryAfterHeader === null ? Number.NaN : Number(retryAfterHeader);
      throw new ApiError(
        response.status,
        nested?.code ?? problem.code ?? "REQUEST_FAILED",
        nested?.detail ??
          (typeof problem.detail === "string"
            ? problem.detail
            : "The request could not be completed."),
        Number.isFinite(parsedRetryAfter) ? parsedRetryAfter : undefined,
      );
    }
    return (await response.json()) as T;
  }

  register(installationId: string, platform: "android" | "ios") {
    return this.request<AnonymousSessionResponse>("/auth/anonymous", {
      method: "POST",
      body: JSON.stringify({
        installation_id: installationId,
        platform,
      }),
    });
  }

  recover(
    recoveryKey: string,
    installationId: string,
    platform: "android" | "ios",
  ) {
    return this.request<RecoverySessionResponse>("/sessions/recover", {
      method: "POST",
      body: JSON.stringify({
        recovery_key: recoveryKey,
        installation_id: installationId,
        platform,
      }),
    });
  }

  refresh(refreshToken: string) {
    return this.request<TokenPair>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  }

  logout(accessToken: string) {
    return this.request<{ status: "logged_out" }>(
      "/auth/logout",
      { method: "POST" },
      accessToken,
    );
  }

  revokeDevice(accessToken: string, deviceId: string) {
    return this.request<{ device_id: string; revoked_sessions: number }>(
      `/auth/devices/${deviceId}`,
      { method: "DELETE" },
      accessToken,
    );
  }
}
