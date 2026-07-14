import { validateCallsignLocally } from "../identity/callsign";

describe("mobile callsign preflight", () => {
  it("matches the server-safe ASCII shape after NFKC normalization", () => {
    expect(validateCallsignLocally(" Ｒoad-Runner ")).toEqual({
      valid: true,
      display: "Road-Runner",
    });
  });

  it.each(["ab", "road talk", "road--talk", "-road", "rоad"])(
    "rejects %s before an availability request",
    (candidate) => {
      expect(validateCallsignLocally(candidate).valid).toBe(false);
    },
  );
});
