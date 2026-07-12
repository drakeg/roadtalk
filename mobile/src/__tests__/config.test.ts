import { loadEnvironment } from "../config";

describe("mobile environment", () => {
  it("normalizes a valid API URL", () => {
    expect(loadEnvironment("http://10.0.2.2:8000/api/v1/").apiBaseUrl).toBe(
      "http://10.0.2.2:8000/api/v1",
    );
  });

  it("rejects non-HTTP endpoints", () => {
    expect(() => loadEnvironment("file:///tmp/api")).toThrow(
      "EXPO_PUBLIC_API_BASE_URL must use HTTP or HTTPS.",
    );
  });

  it("rejects relative endpoints", () => {
    expect(() => loadEnvironment("/api/v1")).toThrow(
      "EXPO_PUBLIC_API_BASE_URL must be an absolute HTTP(S) URL.",
    );
  });
});
