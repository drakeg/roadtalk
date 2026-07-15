import { ApiError, AuthApi } from "../session/api";

function response(
  body: unknown,
  status = 200,
  headers: Record<string, string> = {},
): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers(headers),
    json: jest.fn(async () => body),
  } as unknown as Response;
}

describe("anonymous recovery transport", () => {
  it("sends recovery material only in a JSON request body", async () => {
    const fetcher = jest.fn(async () =>
      response({
        access_token: "access",
        refresh_token: "refresh",
        token_type: "bearer",
        expires_in: 900,
        account_id: "account",
        device_id: "device",
        session_id: "session",
        recovery_key: "rtk1.rotated.secret",
        recovery_key_version: "rtk1",
      }),
    );
    const api = new AuthApi(
      "https://roadtalk.test/api/v1",
      fetcher as unknown as typeof fetch,
    );

    await api.recover("rtk1.original.secret", "installation-id-1234", "ios");

    const [url, init] = fetcher.mock.calls[0] ?? [];
    expect(url).toBe("https://roadtalk.test/api/v1/sessions/recover");
    expect(url).not.toContain("rtk1.");
    expect(init?.method).toBe("POST");
    expect(JSON.parse(String(init?.body))).toEqual({
      recovery_key: "rtk1.original.secret",
      installation_id: "installation-id-1234",
      platform: "ios",
    });
  });

  it("reads nested stable errors and Retry-After without key content", async () => {
    const fetcher = jest.fn(async () =>
      response(
        {
          detail: {
            code: "RECOVERY_RATE_LIMITED",
            detail: "Recovery requests are temporarily limited.",
          },
        },
        429,
        { "Retry-After": "45" },
      ),
    );
    const api = new AuthApi(
      "https://roadtalk.test/api/v1",
      fetcher as unknown as typeof fetch,
    );

    await expect(
      api.recover("candidate", "installation-id-1234", "android"),
    ).rejects.toEqual(
      expect.objectContaining<Partial<ApiError>>({
        status: 429,
        code: "RECOVERY_RATE_LIMITED",
        retryAfter: 45,
      }),
    );
  });
});
