import type { SessionClient } from "../session/SessionClient";

export type PresenceDensity = "few" | "several" | "many";

export type PresenceCell = {
  approximateLatitude: number;
  approximateLongitude: number;
  cellSizeM: 2000;
  density: PresenceDensity;
};

export type NearbyPresence = {
  expiresAtMs: number;
  cells: PresenceCell[];
};

type RawPresenceCell = {
  approximate_latitude?: unknown;
  approximate_longitude?: unknown;
  cell_size_m?: unknown;
  density?: unknown;
};

type RawPresenceResponse = {
  availability?: unknown;
  policy_version?: unknown;
  privacy_min_accounts?: unknown;
  freshness?: unknown;
  expires_at?: unknown;
  cells?: unknown;
};

const ALLOWED_DENSITIES = new Set<PresenceDensity>([
  "few",
  "several",
  "many",
]);

export class PresenceApi {
  constructor(
    private readonly baseUrl: string,
    private readonly session: SessionClient,
  ) {}

  async nearby(): Promise<NearbyPresence> {
    const response = await this.session.authenticatedFetch(
      `${this.baseUrl}/api/v1/presence/nearby`,
      { method: "GET" },
    );
    if (!response.ok) {
      throw new Error(`Presence request failed with HTTP ${response.status}.`);
    }
    return parseNearbyPresence((await response.json()) as RawPresenceResponse);
  }
}

export function parseNearbyPresence(raw: RawPresenceResponse): NearbyPresence {
  if (
    raw.availability !== "available" ||
    raw.policy_version !== "presence-v1" ||
    raw.privacy_min_accounts !== 3 ||
    raw.freshness !== "fresh" ||
    typeof raw.expires_at !== "string" ||
    !Array.isArray(raw.cells) ||
    raw.cells.length > 32
  ) {
    throw new Error("Presence response violated the approved privacy contract.");
  }
  const expiresAtMs = Date.parse(raw.expires_at);
  if (!Number.isFinite(expiresAtMs)) {
    throw new Error("Presence response freshness was invalid.");
  }
  return {
    expiresAtMs,
    cells: raw.cells.map(parseCell),
  };
}

function parseCell(raw: unknown): PresenceCell {
  if (typeof raw !== "object" || raw === null) {
    throw new Error("Presence cell was invalid.");
  }
  const cell = raw as RawPresenceCell;
  if (
    typeof cell.approximate_latitude !== "number" ||
    !Number.isFinite(cell.approximate_latitude) ||
    cell.approximate_latitude < -85.051129 ||
    cell.approximate_latitude > 85.051129 ||
    typeof cell.approximate_longitude !== "number" ||
    !Number.isFinite(cell.approximate_longitude) ||
    cell.approximate_longitude < -180 ||
    cell.approximate_longitude > 180 ||
    cell.cell_size_m !== 2000 ||
    typeof cell.density !== "string" ||
    !ALLOWED_DENSITIES.has(cell.density as PresenceDensity)
  ) {
    throw new Error("Presence cell violated the approved privacy contract.");
  }
  return {
    approximateLatitude: cell.approximate_latitude,
    approximateLongitude: cell.approximate_longitude,
    cellSizeM: 2000,
    density: cell.density as PresenceDensity,
  };
}
