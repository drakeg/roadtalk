import { environment } from "../config";
import type { SessionClient } from "../session/SessionClient";

export type CampgroundCategory =
  | "public"
  | "private"
  | "state_park"
  | "national_park"
  | "county_municipal"
  | "other";

export type CampgroundAmenity =
  | "electric"
  | "water"
  | "sewer"
  | "dump_station"
  | "wifi"
  | "showers"
  | "laundry"
  | "pet_friendly";

export type CampgroundRecord = {
  campground_id: string;
  name: string;
  category: CampgroundCategory;
  locality: string;
  region: string;
  country_code: string;
  latitude: number;
  longitude: number;
  public_location_precision: "campground_centroid";
  amenities: Record<CampgroundAmenity, boolean>;
  source: "deterministic_local";
  freshness: "deterministic";
};

export type CampgroundCatalogResponse = {
  source: "deterministic_local";
  freshness: "deterministic";
  live_directory: false;
  campgrounds: CampgroundRecord[];
};

export type CampgroundContextResponse = {
  state: "current" | "unavailable";
  context: { campground_id: string; name: string; state: "current" | "unavailable" } | null;
  expires_at: string | null;
};

export async function loadCampgroundCatalog(fetcher: typeof fetch = fetch): Promise<CampgroundCatalogResponse> {
  const response = await fetcher(`${environment.apiBaseUrl}/campgrounds/catalog`, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error("Campground catalog unavailable.");
  const data = (await response.json()) as CampgroundCatalogResponse;
  if (data.live_directory !== false || data.source !== "deterministic_local") {
    throw new Error("Unexpected campground catalog provenance.");
  }
  return data;
}

export async function loadCurrentCampgroundContext(
  session: SessionClient,
  fetcher: typeof fetch = fetch,
): Promise<CampgroundContextResponse> {
  const response = await session.authenticatedFetch(
    `${environment.apiBaseUrl}/campgrounds/context`,
    { headers: { Accept: "application/json" } },
    fetcher,
  );
  if (!response.ok) throw new Error("Current campground context unavailable.");
  return (await response.json()) as CampgroundContextResponse;
}

export function filterCampgrounds(
  rows: CampgroundRecord[],
  query: string,
  category: CampgroundCategory | "",
  amenity: CampgroundAmenity | "",
): CampgroundRecord[] {
  const normalized = query.trim().toLowerCase();
  return rows.filter((row) =>
    (!normalized || row.name.toLowerCase().includes(normalized) || row.locality.toLowerCase().includes(normalized)) &&
    (!category || row.category === category) &&
    (!amenity || row.amenities[amenity]),
  );
}
