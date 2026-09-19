# Sprint 11 specification: Convoys

- Planning issue: #283
- Implementation tracker: #284
- Delivery issues: #274–#282
- Baseline: Sprints 0–10 accepted; corrective issue #208 completed.

## Objective

Deliver privacy-safe convoy membership, current convoy awareness, and convoy-scoped communication context without turning convoy membership into a new authorization source or creating durable movement tracking.

## Requirements

- **S11-R01 — Domain:** Define convoy identity, lifecycle, membership roles/states and bounded metadata.
- **S11-R02 — Authorization:** Convoy state may only narrow or label behavior already authorized by account/session, location consent/current state, proximity/Same-road, channel and media rules.
- **S11-R03 — Membership lifecycle:** Create/join/leave/revoke/disband transitions are deterministic, bounded and fail closed.
- **S11-R04 — Privacy:** Do not expose or persist raw/durable location or route history, unrelated-user presence, cross-convoy enumeration, private credentials, recovery material or provider secrets.
- **S11-R05 — Current awareness:** Any convoy awareness is derived from already-authorized current state, expires with it, and does not add background collection.
- **S11-R06 — Communication:** Convoy communication cannot override channel, proximity/Same-road or media-grant authorization.
- **S11-R07 — Browser:** Provide accessible create/join/leave/status UX with explicit destructive-action confirmation and safe degraded states.
- **S11-R08 — Mobile:** Provide equivalent mobile lifecycle/awareness behavior without client-side authorization broadening or background location/audio.
- **S11-R09 — Abuse/reliability:** Bound enumeration, rate/size and concurrent lifecycle behavior; stale/revoked state fails closed.
- **S11-R10 — Compatibility:** Preserve accepted Sprint 0–10 API/privacy/provider behavior and document degraded/offline limitations.
- **S11-R11 — Cost/provider:** Incremental recurring cost is $0 using local Docker/PostgreSQL/PostGIS and GitHub CI; no external provider/cloud activation.
- **S11-R12 — Evidence:** Maintain bidirectional requirements/tests/deliverables/PR/evidence traceability and distinguish deterministic CI evidence from unperformed physical/production/provider evidence.

## Acceptance tests

- **S11-T01:** Contract/schema tests reject sensitive/unknown fields and prove bounded convoy metadata.
- **S11-T02:** Authorization composition proves convoy state never broadens upstream eligibility.
- **S11-T03:** Membership lifecycle, revocation, deletion and concurrency tests fail closed.
- **S11-T04:** Privacy/enumeration tests prove no raw/durable location/history or cross-convoy leakage.
- **S11-T05:** Current-awareness staleness/consent/revocation tests prove authoritative expiry.
- **S11-T06:** Channel/PTT/media regressions cover convoy transitions during receive/transmit eligibility.
- **S11-T07:** Browser accessibility, confirmation, over-posting and degraded-state tests.
- **S11-T08:** Mobile permission/stale/offline/revoked-state and accessibility regressions.
- **S11-T09:** Abuse/rate/bounds and race-condition hardening tests.
- **S11-T10:** Full backend/mobile/security/migration/schema-drift/Compose/IaC compatibility gates.
- **S11-T11:** Automated dependency/provider/cost gates prove zero external activation and zero Terraform resources.
- **S11-T12:** Final traceability/evidence review covers S11-R01–R12 and named exceptions.

## Delivery order

D01 planning/readiness (#283), then strictly #274 → #275 → #276 → #277 → #278 → #279 → #280 → #281 → #282.

## Explicit exclusions

Sprint 11 does not authorize AWS or LiveKit Cloud, external map/location/messaging providers, production/public beta, payment methods, background location/audio, durable convoy movement history, tracking analytics, marketing profiles, or Sprint 12 implementation.
