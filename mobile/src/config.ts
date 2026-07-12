type PublicEnvironment = {
  apiBaseUrl: string;
};

function requireHttpUrl(name: string, value: string): string {
  let parsed: URL;
  try {
    parsed = new URL(value);
  } catch {
    throw new Error(`${name} must be an absolute HTTP(S) URL.`);
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error(`${name} must use HTTP or HTTPS.`);
  }
  return value.replace(/\/$/, "");
}

export function loadEnvironment(
  apiBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL ??
    "http://localhost:8000/api/v1",
): PublicEnvironment {
  return {
    apiBaseUrl: requireHttpUrl("EXPO_PUBLIC_API_BASE_URL", apiBaseUrl),
  };
}

export const environment = loadEnvironment();
