# Map Presence Privacy Policy

Sprint 8 map presence is an awareness aid, not a people-tracking or authorization system.

## Locked `presence-v1` policy

- The authenticated user's own accepted foreground location is outside this aggregation policy and may be rendered to that same user at normal client precision.
- Other-user presence is aggregated into fixed **2,000 meter Web Mercator privacy cells**.
- A cell is visible only when it contains at least **3 distinct eligible accounts**.
- One or two accounts in a cell are suppressed completely; adjacent sparse cells are not merged dynamically because adaptive merging can itself leak population shape. A later policy version may introduce a reviewed hierarchical scheme.
- A visible cell exposes only its fixed coarse center, fixed cell size, and a density bucket:
  - `few`: 3–5 distinct accounts;
  - `several`: 6–10 distinct accounts;
  - `many`: 11 or more distinct accounts.
- Exact account counts are not part of the client response.
- At most **32 visible cells** are returned in one response. Ordering is deterministic by density and cell index, not by account identity.
- Multiple samples for the same account count once toward the anonymity threshold.
- Invalid/non-finite coordinates fail closed and cannot generate presence.

## Prohibited client selectors

`GET /api/v1/presence/nearby` accepts no query parameters or request body. A caller cannot request or override an account/device, coordinate, radius, privacy cell, route, provider, audience, channel, precision, threshold, or TTL. Any query parameter is rejected before the presence query executes.

## Prohibited response data

A client presence response must not expose another user's:

- account/device/session/participant identifier or callsign association;
- raw coordinate or snapped coordinate;
- exact distance or bearing;
- heading or speed;
- Same-road corridor/direction/provider context;
- destination, route, itinerary, history, breadcrumb, or trail;
- exact population count for a cell.

The coarse cell center is an aggregate policy artifact and must never be described as a person's location.

## Authorization separation

Presence is read-only derived awareness. It does not create, refresh, broaden, or alter receiver eligibility, publisher eligibility, media grants, channel membership/selection, sessions, proximity eligibility, or Same-road eligibility. The presence service does not call PTT, channel, proximity, route-mode, or media-provider authorization code. Existing communication authorization remains authoritative and independent of whether a presence cell is visible.

## Current-only lifecycle

There is no presence table, history row, breadcrumb, replay record, or presence-specific coordinate persistence. Every response is derived from the existing authoritative `current_location` row at read time.

A candidate is eligible only while all of the following remain true:

- the account is active;
- its current location is `usable`, unexpired, and on the current location-policy version;
- the latest foreground-location consent decision is `granted` for that policy version;
- the device that supplied the current location still has an active, unrevoked, unexpired session.

The authenticated viewer is excluded from other-user aggregation. Response expiry is bounded by the earliest contributing current-location expiry. If fewer than three eligible accounts remain in a cell, the cell disappears completely.

Existing lifecycle operations therefore fail closed without a new retention surface: pausing location deletes `current_location`; consent withdrawal deletes it and records revoked consent; stale location fails the expiry predicate; logout/session revocation invalidates a source with no active source-device session; device revocation invalidates that device's source session; account deletion cascades current location; disabled/deleted accounts are excluded. No fabricated or last-known position is substituted.

## Provider independence

The 2 km cell policy is independent of any map/tile provider. D03's deterministic local provider does not receive presence data. Changing providers must not change the privacy cell or anonymity semantics without a new versioned privacy-policy decision.

## Known limitation

Three accounts within the same 2 km cell provide coarse k-anonymity, not a guarantee against an observer with substantial external knowledge. RoadTalk therefore avoids identity-location association, exact counts, adaptive sparse-cell merging, history, and precise other-user coordinates. D09 must review this residual risk before Sprint 8 acceptance.
