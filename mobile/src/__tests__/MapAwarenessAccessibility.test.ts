import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const source = readFileSync(
  resolve(__dirname, "../screens/MapAwarenessScreen.tsx"),
  "utf8",
);

describe("MapAwarenessScreen accessibility contract", () => {
  it("provides a semantic text equivalent for the visual awareness grid", () => {
    expect(source).toContain('accessibilityRole="image"');
    expect(source).toContain("Text awareness summary");
    expect(source).toContain('accessibilityLiveRegion="polite"');
    expect(source).toContain("privacy-qualified coarse RoadTalk activity area");
    expect(source).toContain("precision is limited to a 2 km privacy cell");
  });

  it("labels controls and explains their effects", () => {
    expect(source).toContain('accessibilityLabel="Enable foreground map awareness"');
    expect(source).toContain('accessibilityLabel="Open location settings"');
    expect(source).toContain('accessibilityLabel="Pause map awareness"');
    expect(source).toContain("Requests foreground location only while RoadTalk map awareness is active");
    expect(source).toContain("Stops foreground map awareness and hides nearby activity");
  });

  it("fails closed for stale and unavailable awareness", () => {
    expect(source).toContain("nearby activity is hidden rather than displayed with false precision");
    expect(source).toContain("Expired nearby activity is hidden until refreshed");
    expect(source).toContain("Prior nearby activity is hidden");
    expect(source).not.toContain("distance_m");
    expect(source).not.toContain("bearing_deg");
    expect(source).not.toContain("callsign");
    expect(source).toContain("distance, bearing, heading, speed, or identity is shown here");
  });
});
