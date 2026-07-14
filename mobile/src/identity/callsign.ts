export type LocalCallsign =
  | { valid: true; display: string }
  | { valid: false; message: string };

export function validateCallsignLocally(value: string): LocalCallsign {
  const display = value.normalize("NFKC").trim();
  const normalized = display.toLocaleLowerCase("en-US");

  if (normalized.length < 3 || normalized.length > 24) {
    return {
      valid: false,
      message: "Use 3 to 24 letters, numbers, or single hyphens.",
    };
  }
  if (
    !/^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/.test(normalized) ||
    normalized.includes("--")
  ) {
    return {
      valid: false,
      message:
        "Use ASCII letters, numbers, or single internal hyphens; do not start or end with a hyphen.",
    };
  }
  return { valid: true, display };
}
