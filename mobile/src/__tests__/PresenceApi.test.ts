import { parseNearbyPresence } from "../presence/api";

describe("mobile nearby presence privacy contract", () => {
  it("accepts only approved coarse cells", () => {
    const parsed = parseNearbyPresence({
      availability: "available",
      policy_version: "presence-v1",
      privacy_min_accounts: 3,
      freshness: "fresh",
      expires_at: "2026-08-28T22:30:00Z",
      cells: [
        {
          approximate_latitude: 40.5,
          approximate_longitude: -77.8,
          cell_size_m: 2000,
          density: "several",
        },
      ],
    });

    expect(parsed.cells).toEqual([
      {
        approximateLatitude: 40.5,
        approximateLongitude: -77.8,
        cellSizeM: 2000,
        density: "several",
      },
    ]);
  });

  it.each([
    { density: "one" },
    { cell_size_m: 500 },
    { approximate_latitude: 91 },
    { approximate_longitude: 181 },
  ])("rejects privacy-contract drift %#", (override) => {
    expect(() =>
      parseNearbyPresence({
        availability: "available",
        policy_version: "presence-v1",
        privacy_min_accounts: 3,
        freshness: "fresh",
        expires_at: "2026-08-28T22:30:00Z",
        cells: [
          {
            approximate_latitude: 40.5,
            approximate_longitude: -77.8,
            cell_size_m: 2000,
            density: "few",
            ...override,
          },
        ],
      }),
    ).toThrow(/privacy contract|invalid/i);
  });

  it("rejects responses that lower the k-anonymity minimum", () => {
    expect(() =>
      parseNearbyPresence({
        availability: "available",
        policy_version: "presence-v1",
        privacy_min_accounts: 2,
        freshness: "fresh",
        expires_at: "2026-08-28T22:30:00Z",
        cells: [],
      }),
    ).toThrow(/privacy contract/i);
  });
});
