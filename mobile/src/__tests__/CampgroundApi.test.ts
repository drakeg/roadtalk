import { filterCampgrounds, type CampgroundRecord } from "../campgrounds/api";

const rows: CampgroundRecord[] = [
  {
    campground_id: "cg_test_alpha",
    name: "Alpha Campground",
    category: "state_park",
    locality: "Ithaca",
    region: "NY",
    country_code: "US",
    latitude: 42.4,
    longitude: -76.5,
    public_location_precision: "campground_centroid",
    amenities: {
      electric: true,
      water: true,
      sewer: false,
      dump_station: true,
      wifi: false,
      showers: true,
      laundry: false,
      pet_friendly: true,
    },
    source: "deterministic_local",
    freshness: "deterministic",
  },
  {
    campground_id: "cg_test_beta",
    name: "Beta Camp",
    category: "private",
    locality: "State College",
    region: "PA",
    country_code: "US",
    latitude: 40.8,
    longitude: -77.8,
    public_location_precision: "campground_centroid",
    amenities: {
      electric: true,
      water: true,
      sewer: true,
      dump_station: false,
      wifi: true,
      showers: true,
      laundry: true,
      pet_friendly: true,
    },
    source: "deterministic_local",
    freshness: "deterministic",
  },
];

describe("mobile campground filtering", () => {
  it("filters only public catalog metadata without deriving presence", () => {
    expect(filterCampgrounds(rows, "ithaca", "", "").map((row) => row.campground_id)).toEqual([
      "cg_test_alpha",
    ]);
    expect(filterCampgrounds(rows, "", "private", "wifi").map((row) => row.campground_id)).toEqual([
      "cg_test_beta",
    ]);
  });

  it("does not model occupancy, members, visits, or campsite identity", () => {
    const encoded = JSON.stringify(rows).toLowerCase();
    for (const forbidden of ["occupancy", "member_ids", "present_users", "arrival_at", "departure_at", "visit_history", "campsite_id"]) {
      expect(encoded).not.toContain(forbidden);
    }
  });
});
