import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const source = readFileSync(
  resolve(__dirname, "../screens/MapAwarenessScreen.tsx"),
  "utf8",
);

describe("MapAwarenessScreen privacy contract", () => {
  it("keeps location foreground-only and explicitly pausable", () => {
    expect(source).toContain("foreground");
    expect(source).toContain("Pause map awareness");
    expect(source).not.toContain("background location");
  });

  it("renders only privacy-qualified coarse nearby activity", () => {
    expect(source).toContain("2 km privacy cell");
    expect(source).toContain("coarse RoadTalk activity");
    expect(source).not.toContain("distance_m");
    expect(source).not.toContain("bearing_deg");
    expect(source).not.toContain("callsign");
  });

  it("fails closed when awareness is stale or unavailable", () => {
    expect(source).toContain("Expired nearby activity is hidden until refreshed");
    expect(source).toContain("Prior nearby activity is hidden");
    expect(source).toContain("nearby activity is hidden rather than displayed with false precision");
  });
});
