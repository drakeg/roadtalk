import type { AnonymousSessionResponse, TokenPair } from "./types";

type Fetch = typeof fetch;
type Problem = { code?: string; detail?: string };

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
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
      throw new ApiError(
        response.status,
        problem.code ?? "REQUEST_FAILED",
        problem.detail ?? "The request could not be completed.",
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
