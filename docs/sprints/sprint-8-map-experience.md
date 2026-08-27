# Sprint 8: Map Experience

## Status

Planning candidate dated 2026-08-26. Sprint 8 implementation is not authorized until this specification and the companion readiness record are accepted by product-owner merge of the planning PR. Current and incremental implementation cost remains $0.

## Objective

Give an authenticated RoadTalk user useful geographic awareness of their current communication environment on mobile and browser without turning RoadTalk into a people-tracking, navigation, or trip-history product.

The user's own accepted foreground location may be rendered precisely for orientation. Other RoadTalk users must be represented only through privacy-preserving approximate presence that cannot reveal another account's exact coordinate, route, destination, heading, exact distance/bearing, location history, or route-context identifier.

## Product decisions

- Map rendering and nearby-presence visualization are Sprint 8 scope; navigation, routing, destination/address search, ETA, itinerary, trip history, geofencing, automatic subscription, emergency tracking, and background tracking are not.
- Nearby remains the default communication mode. Same road remains an explicit server-authoritative narrowing filter from Sprint 7.
- The map is an awareness surface, not an authorization engine. Existing consent, current-location, PostGIS proximity, channel, session/grant, and Same-road authorization remain authoritative.
- The current user's own accepted foreground location may be shown at normal client precision. Other-user presence is server-derived and privacy-preserving.
- No API may return another user's raw coordinate, exact distance/bearing, heading/speed, route/corridor/direction, destination, provider identifier, callsign-to-coordinate association, or location history.
- Nearby presence must use an explicitly documented coarse representation such as privacy cells, aggregate/density markers, or another deterministic abstraction. The exact abstraction and minimum anonymity/precision policy are locked before UI implementation.
- Sparse populations must fail closed or reduce precision rather than expose a near-unique person's position.
- Presence is short-lived and current-only. No map history, breadcrumb, replay, trail, heat-history, or durable other-user map location is introduced.
- Map/tile access sits behind a client/server provider boundary. Local/CI acceptance uses deterministic fixtures or local static test assets; no public tile endpoint is treated as free production infrastructure.
- A production map/tile provider or dataset requires a separate dated decision covering license/attribution, privacy, terms, quotas/rate limits, caching/offline rules, geographic scope, update process, operational ownership, recurring cost, and rollback.
- No AWS resource, LiveKit Cloud resource, paid mapping API, payment method, paid plan, recurring service, or production/public-beta deployment is authorized by Sprint 8 planning.
- Browser/mobile microphone and foreground-location compatibility remain release blockers. Sprint 8 includes explicit physical-system compatibility evidence and diagnostics work, but does not authorize background location/audio.
- Accessibility includes keyboard/screen-reader semantics for map controls and a non-map textual summary so core awareness is not map-only.

## Architecture boundary

Sprint 8 may introduce:

1. a typed map/presence policy boundary;
2. a privacy-preserving current nearby-presence response derived from already-authorized current location/proximity state;
3. deterministic/local map fixture assets or a fake tile/provider adapter for CI;
4. mobile and browser map components plus a text-equivalent nearby summary;
5. bounded foreground refresh/reconciliation tied to existing location consent and freshness;
6. diagnostics/evidence tooling for physical browser/mobile microphone and location compatibility.

Sprint 8 must not make the map provider authoritative for communication eligibility, send raw location to a new external service, persist other-user map history, or add a continuously running location worker.

## Requirements

- **S08-R01 — Own-location map:** Render the authenticated user's accepted foreground location and semantic freshness/permission state without introducing background tracking.
- **S08-R02 — Privacy-preserving presence contract:** Return only coarse current nearby-presence information with exact over-posting denial and no raw other-user coordinates or identity/location association.
- **S08-R03 — Sparse-population protection:** Enforce a deterministic minimum privacy policy that reduces precision, aggregates, or suppresses presence when a representation could identify a near-unique user.
- **S08-R04 — Authorization separation:** Map/presence discovery cannot broaden communication eligibility and must consume only already-authorized current location/proximity/channel/route state.
- **S08-R05 — Current-only lifecycle:** Expiry, pause, consent withdrawal, logout, deletion, stale location, and session/device revocation remove or invalidate map presence within bounded time; no history is retained.
- **S08-R06 — Map provider boundary:** Add a typed deterministic/local provider or fixture boundary; production/public map/tile endpoints remain disabled until separately approved.
- **S08-R07 — Browser experience:** Provide a responsive Web Radio map/awareness surface with navigation to Radio, Audience, and Operations and actionable secure-context/location diagnostics.
- **S08-R08 — Mobile experience:** Provide an equivalent mobile awareness surface with permission/freshness/degraded states and no privacy-sensitive detail leakage.
- **S08-R09 — Accessible equivalent:** Map controls are keyboard/screen-reader operable and a textual nearby summary communicates the same essential awareness without requiring visual map use.
- **S08-R10 — Compatibility evidence:** Establish a repeatable physical-system matrix for browser/mobile microphone plus foreground location across representative supported environments, recording pass/fail/limitations without collecting unnecessary personal data.
- **S08-R11 — Hardening and performance:** Add privacy/schema/log/provider/cost gates and synthetic scale evidence for presence lookup/aggregation/refresh at the accepted Sprint 5–7 population matrix or stricter.
- **S08-R12 — Evidence and review:** Produce bidirectional requirements/tests/deliverables/PR/evidence traceability and final privacy, security, accessibility, licensing, reliability, performance, compatibility, cost, risk, limitation, and retrospective review.

## Acceptance tests

- **S08-T01:** Own-location UI renders accepted foreground location and clearly distinguishes unavailable, denied, stale, and active states; no background permission is requested.
- **S08-T02:** Presence API schema rejects unexpected client selectors and never exposes another user's coordinate, exact distance/bearing, heading/speed, route context, identity-location association, or history.
- **S08-T03:** Deterministic sparse-population cases prove suppression/coarsening and cannot yield a single-user exact/near-exact position.
- **S08-T04:** Integration tests prove map presence cannot create a receiver/publisher/channel/session/grant eligibility path that existing authorization denied.
- **S08-T05:** Lifecycle tests prove current presence expires/clears on freshness, consent, pause, logout, deletion, and revocation boundaries with no durable history rows.
- **S08-T06:** Fake/local map provider fixtures are deterministic and CI requires all real/public provider/network configuration to remain disabled.
- **S08-T07:** Browser tests cover map/summary navigation, secure-context/location diagnostics, degraded states, and privacy-safe rendering.
- **S08-T08:** Mobile tests cover map/summary navigation, foreground permission/freshness/degraded states, and privacy-safe rendering.
- **S08-T09:** Accessibility tests cover semantic labels/roles, keyboard focus/control where applicable, live status, and text-equivalent awareness.
- **S08-T10:** Named physical compatibility evidence covers representative browser/OS/mobile combinations for microphone acquisition, speaker/receive path where feasible, foreground location acquisition, permission denial/recovery, and secure-origin requirements; unsupported/unperformed cases remain explicit exceptions.
- **S08-T11:** Synthetic scale/hardening gates prove bounded presence lookup/aggregation/refresh, privacy/log/schema/provider/cost boundaries, and no regression of Sprint 5–7 authorization/performance controls.
- **S08-T12:** Final review maps S08-R01–R12 to S08-T01–T12 and delivery/evidence records and is accepted by product-owner merge.

## Locked delivery sequence

- **S08-D01 — Planning and readiness baseline.** This specification, readiness gate, cost/activation boundary, issues, and tracker.
- **S08-D02 — Presence privacy contract and policy.** Define coarse representation, sparse-population policy, API/schema, and lifecycle contract before any map UI.
- **S08-D03 — Map/provider boundary.** Deterministic/local provider or fixture abstraction with all real/public providers disabled.
- **S08-D04 — Presence lifecycle and authorization composition.** Server derivation, current-only expiry/cleanup, and proof that presence cannot broaden communication authorization.
- **S08-D05 — Browser map experience.** Web awareness surface, text summary, navigation, diagnostics, and privacy-safe states.
- **S08-D06 — Mobile map experience.** Mobile awareness surface, text summary, permission/freshness states, and privacy-safe states.
- **S08-D07 — Accessibility and degraded/offline experience.** Keyboard/screen-reader semantics, non-map equivalent, bounded stale/offline behavior, no false precision.
- **S08-D08 — Physical mic/location compatibility evidence.** Representative real-system matrix, diagnostics, fixes that remain within approved foreground scope, and explicit unresolved exceptions.
- **S08-D09 — Map/presence hardening and scale evidence.** Privacy/provider/license/cost gates plus synthetic performance/reliability evidence.
- **S08-D10 — Sprint evidence and review.** Traceability, final review, retrospective, and product-owner acceptance.

Execution order is strictly D02 → D03 → D04 → D05 → D06 → D07 → D08 → D09 → D10 after D01 planning acceptance. A later deliverable may not be used to bypass an unmet earlier acceptance criterion.

## Cost and activation boundary

Approved planning/implementation ceiling: **$0 incremental recurring cost**.

Allowed for acceptance evidence:

- local Docker Compose and existing local HTTPS gateway;
- existing Postgres/PostGIS and local media development components;
- deterministic fixtures/fakes/static test assets;
- GitHub CI already used by the repository;
- local browser/mobile simulator or physical-device testing that does not activate a paid service.

Not authorized:

- AWS resource creation or billing;
- LiveKit Cloud activation;
- public/hosted map, tile, geocoding, routing, traffic, or location APIs;
- paid/free-tier accounts that require payment methods or create recurring-spend exposure;
- production/public-beta deployment;
- production road/map dataset download/distribution unless separately approved;
- background location/audio or always-on tracking infrastructure.

Budgets, quotas, alerts, CI checks, or free-tier labels are not automatic shutdown controls and do not authorize spend.

## Named evidence exceptions

Sprint 8 planning does not claim the following evidence exists yet:

- production map/tile provider selection, licensing compliance, attribution placement, quota/caching behavior, availability, or latency;
- production road/map dataset selection/distribution/update operations;
- broad physical-device/browser microphone, speaker, Bluetooth, GPS, permission, interruption, battery, and data behavior;
- background location/audio behavior;
- live LiveKit Cloud media, NAT/TURN/cellular handoff, or multi-region behavior;
- AWS deployment/billing/destroy evidence;
- public-beta/production capacity;
- driver-distraction, emergency, navigation, safety, hands-free, or regulatory claims.

D08 is specifically intended to reduce the foreground microphone/location compatibility exception, but any unsupported or untested combinations remain named limitations rather than inferred passes.

## Readiness decision

Implementation remains blocked until the companion `sprint-8-readiness.md` record is accepted with this specification and the planning tracker locks the sequence. Merge of the planning PR is the product-owner approval event for Sprint 8 implementation under these boundaries only.