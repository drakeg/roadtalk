# Sprint 10: Campgrounds

## Status

Planning candidate dated 2026-09-06. Sprint 10 implementation is **not authorized** until this specification and the companion readiness record are accepted by product-owner merge of the planning PR. Current and incremental recurring implementation cost remains **$0**.

## Objective

Add campground-specific discovery and communication context for authenticated RoadTalk users without creating campsite-level tracking, occupancy surveillance, a new communication authorization source, reservation/commerce functionality, or an external campground/place-data dependency.

## Product decisions

- Campground context is descriptive/current context, **not an authorization engine**. Existing account/session, location consent/current location, proximity, channel, Same-road, media and notification rules remain authoritative.
- Campground logic may narrow or label an already-authorized result; it may never restore a recipient, publisher, listener or notification that an upstream rule denied.
- Sprint 10 supports a bounded campground catalog: stable campground identity, coarse public geography, public descriptive metadata, amenity/category fields and explicit source/provenance/freshness context.
- Local/GitHub CI acceptance uses deterministic catalog data. It must never be presented as a live or complete campground directory.
- No external campground/place/map/reservation provider, API key, provider account, network call, scraping or payment method is authorized.
- No booking, reservation inventory, campsite selection, availability, pricing transaction or payment workflow is Sprint 10 scope.
- RoadTalk must not expose or persist campsite/lot/unit-level user presence, exact campground member lists, exact occupancy counts, arrival/departure logs or durable visit history.
- Current campground context, where available, is server-derived from already-authorized current state and expires with that state. Clients cannot assert arbitrary campground presence to obtain communication access.
- Leaving context, stale location, consent withdrawal, logout, account/device revocation or deletion must fail closed.
- Campground communication entry points compose with existing channel/proximity/media rules. A campground is not a shortcut around private-channel membership, proximity or publication authorization.
- No background location/audio, tracking analytics, marketing profile or cross-user campground engagement graph is introduced.
- Browser and mobile experiences must make deterministic/stale/degraded source state clear and must not imply live occupancy or live provider freshness.
- Sprint 11 Convoys, Sprint 12 Moderation, Sprint 13 AI, Sprint 14 Premium and Sprint 15 Production remain out of scope.

## Requirements

- **S10-R01 — Campground domain/privacy contract:** Define the closed public campground contract and reject user-sensitive, authorization, recipient, provider and campsite-level fields.
- **S10-R02 — Bounded persistence:** Persist campground catalog records independently from user movement/history/authentication data with migrations, deletion and provenance semantics.
- **S10-R03 — Deterministic catalog discovery:** Provide bounded search/filter/detail behavior using deterministic local/CI data and coarse campground geography/metadata without live-provider claims.
- **S10-R04 — Current-context derivation:** Derive current campground context server-side only from existing authorized current state; stale/revoked/withdrawn state fails closed.
- **S10-R05 — Presence privacy:** Campground context exposes no campsite/unit presence, exact membership/occupancy, durable visit history, arrival/departure history or person-at-campground enumeration.
- **S10-R06 — Communication composition:** Campground communication context may only narrow/label existing channel/proximity/media authorization and cannot broaden recipient/publisher/listener eligibility.
- **S10-R07 — Browser experience:** Provide accessible campground browse/search/filter/detail/current-context and communication-entry UX with explicit deterministic/degraded state.
- **S10-R08 — Mobile experience:** Provide equivalent mobile UX without new background location/audio permissions or external data-provider activation.
- **S10-R09 — Lifecycle/reliability:** Handle stale/replayed context, consent withdrawal, logout/revocation/deletion, concurrent updates and malformed requests safely and idempotently.
- **S10-R10 — Security/privacy hardening:** Non-enumerating failures and CI gates reject person-campground history, occupancy enumeration, sensitive logs, client-selected authorization and later-sprint drift.
- **S10-R11 — Performance/provider/compatibility/cost:** Add synthetic scale evidence, provider/dependency/cost gates and explicit real-data/physical/production evidence limitations under the $0 boundary.
- **S10-R12 — Evidence/review:** Produce bidirectional R/T/D/PR/evidence traceability and final privacy/security/accessibility/provider/reliability/performance/compatibility/cost/risk/retrospective review.

## Acceptance tests

- **S10-T01:** Schema/API tests accept only approved campground fields and reject exact user/campsite/occupancy/history/recipient/auth/provider overrides.
- **S10-T02:** Migration/persistence tests prove campground catalog storage contains no user movement/history/authentication linkage and has bounded deletion/provenance semantics.
- **S10-T03:** Search/filter/detail tests are deterministic, bounded and explicit about source/freshness; CI makes zero external campground/place/map/reservation calls.
- **S10-T04:** Context tests prove only server-derived current authorized state can establish campground context and stale/withdrawn/revoked state fails closed.
- **S10-T05:** Privacy tests prove APIs/logs/evidence expose no campsite/unit presence, exact occupancy/member list, visit/arrival/departure history or person-at-campground enumeration.
- **S10-T06:** Integration tests prove campground context cannot turn any existing proximity/channel/Same-road/media/notification denial into authorization.
- **S10-T07:** Browser tests cover browse/search/filter/detail/current-context/communication entry, accessibility and deterministic/stale/degraded states.
- **S10-T08:** Mobile tests cover equivalent flows, permission/no-location/offline/degraded states and absence of new background location/audio permissions.
- **S10-T09:** Lifecycle tests cover replay/staleness, consent withdrawal, logout/revocation/deletion, concurrency and malformed/over-posted requests.
- **S10-T10:** Hardening tests/gates reject sensitive campground presence/history/occupancy leakage, enumeration, external provider activation, scraping, analytics and spend-enabling dependencies.
- **S10-T11:** Synthetic evidence uses at least 100 accounts / 25 current-context users / 10 campground communication publishers plus a representative catalog, with p95 targets locked before the named run and real-provider/physical/production cases explicit as unperformed.
- **S10-T12:** Final review maps S10-R01–R12 to S10-T01–T12 and D01–D10 evidence and is accepted by product-owner merge.

## Locked delivery sequence

- **S10-D01 — Planning/readiness baseline:** specification, readiness, tracker and issues.
- **S10-D02 — Campground domain and privacy contract:** #246.
- **S10-D03 — Campground persistence and deterministic catalog:** #247.
- **S10-D04 — Campground presence composition:** #248.
- **S10-D05 — Campground channels and communication context:** #249.
- **S10-D06 — Browser campground experience:** #250.
- **S10-D07 — Mobile campground experience:** #251.
- **S10-D08 — Reliability and privacy hardening:** #252.
- **S10-D09 — Scale, provider and compatibility evidence:** #253.
- **S10-D10 — Sprint evidence and review:** #254.

Execution after D01 acceptance is strictly #246 → #247 → #248 → #249 → #250 → #251 → #252 → #253 → #254.

## Cost and activation boundary

Allowed for Sprint 10 acceptance: existing local Docker/Postgres/PostGIS/media components, deterministic campground fixtures/catalog, existing browser/mobile app surfaces and GitHub CI. Current and incremental recurring cost is **$0**.

Not authorized: AWS or LiveKit Cloud activation; external campground/place/map/reservation provider account/key/network use; scraping; payment method or recurring service; booking/reservation/payment workflow; production/public beta; background location/audio; analytics/marketing tracking; campsite-level presence; exact occupancy/member lists or durable visit history.

A nominally free provider does not authorize activation. Selecting a real campground data source later requires a separate review of licensing, attribution, privacy, freshness, quota and cost before credentials or network calls are added.

## Named evidence exceptions

Sprint 10 planning does not claim real campground/place/reservation data completeness/freshness/licensing behavior, physical-device campground detection, suspended/offline/roaming behavior, external provider latency/quota/terms/cost, production capacity/failover, AWS deployment/billing/destroy, background location/audio behavior, or accuracy of campground boundaries/amenities beyond deterministic test data.

## Approval statement

Merging the Sprint 10 planning PR means the product owner approves this specification, companion readiness gate, locked D01–D10 order, $0 implementation policy and named evidence exceptions. It authorizes local/GitHub-CI Sprint 10 implementation only. It does not authorize an external data provider, payment/recurring spend, production/public beta, background tracking/audio, reservation/commerce integration, Sprint 11 implementation, or claims of live campground data freshness/completeness.