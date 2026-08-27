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

The client presence-query contract is intentionally empty. A caller cannot request or override an account/device, coordinate, radius, privacy cell, route, provider, audience, channel, precision, threshold, or TTL. Unexpected fields are rejected by schema validation.

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

`presence-v1` accepts only server-selected candidate points. It does not decide whether an account is eligible to communicate, receive, publish, join a channel, satisfy proximity, or satisfy Same-road. D04 must compose presence only after existing consent/current-location/proximity/channel/session/grant/route authorization and must prove presence cannot broaden those decisions.

## Lifecycle boundary

This deliverable defines no durable presence-history table. D04 must derive current presence only from accepted current location state, bound its expiry to authoritative freshness, and ensure pause, consent withdrawal, stale location, logout, deletion, and device/session revocation remove eligibility within bounded time.

## Provider independence

The 2 km cell policy is independent of any map/tile provider. D03 may add only a deterministic/local rendering/provider boundary under the approved $0 policy. Changing providers must not change the privacy cell or anonymity semantics without a new versioned privacy-policy decision.

## Known limitation

Three accounts within the same 2 km cell provide coarse k-anonymity, not a guarantee against an observer with substantial external knowledge. RoadTalk therefore avoids identity-location association, exact counts, adaptive sparse-cell merging, history, and precise other-user coordinates. D09 must review this residual risk before Sprint 8 acceptance.