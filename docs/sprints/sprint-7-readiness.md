# Sprint 7 readiness

- Sprint: 7 — Route Awareness
- Status: APPROVED FOR LOCKED LOCAL/CI IMPLEMENTATION
- Planning date: 2026-08-22
- Current and incremental implementation cost: **$0 AWS + $0 LiveKit + $0 routing provider per month**

## Authorization boundary

Planning PR #164 records product-owner approval of the Sprint 7 specification. Tracker
#173 locks delivery issues #165–#172. This approval authorizes only local development and GitHub CI against deterministic route fixtures and
a fake provider. It does not activate a hosted routing API, the public OSRM demo
service, OpenStreetMap APIs/tiles, a regional dataset, a routing container, LiveKit
Cloud, AWS, a payment method, a paid plan, an always-on environment, field deployment,
or public beta.

## Scope readiness

- [x] Nearby remains the default accepted Sprints 5/6 behavior.
- [x] Same road is an explicit restrictive receive mode, not a broader audience.
- [x] No destination, address, navigation, ETA, route plan, trip history, map or marker
  is collected or displayed.
- [x] Requirements S07-R01–R12, tests S07-T01–T12 and deliverables S07-D01–D09 are
  defined with entry/exit criteria.
- [x] Sprint 8+ maps, Sprint 9 notifications, Sprint 12 moderation, Sprint 13 AI and
  production behavior remain out of scope.

## Architecture readiness

### Provider boundary

A typed backend interface accepts only one already-approved current location sample
plus accuracy/heading/speed/time needed for matching. It returns an opaque corridor
reference, coarse direction, confidence and expiry. Requests and responses are
validated, size/time bounded and excluded from routine logs.

Local/GitHub CI uses a deterministic fake and compact synthetic road fixtures. Real
provider configuration must remain disabled and absent. OSRM is only a candidate:
its documented Match service handles GPS traces, accuracy radiuses and confidence, and
its Nearest service finds nearby road segments. Provider selection, deployment, data
preparation and network access require a later dated decision.

### Authorization composition

The existing indexed PostGIS `ST_DWithin` proximity query remains the first spatial
bound. Same-road compatibility is applied only to candidates already authorized by
location consent/freshness/accuracy, session/device/account state, selected channel,
membership, receive grant and proximity. It cannot turn a prior denial into eligibility.

Exact keyed corridor equality and coarse compatible direction are required. Unknown,
stationary, ambiguous, stale, mismatched or failed context denies Same-road delivery.
Nearby users are unaffected by route-provider state.

### Persistence and lifecycle

One `current_route_context` row may contain only a keyed opaque corridor digest,
coarse direction/confidence, source location version, provider/policy version,
matched/expiry timestamps and row version. It contains no geometry, snapped coordinate,
road name, destination, route, trace or provider payload.

A newer accepted location replaces context atomically. Pause, consent withdrawal,
location expiry, mode change to Nearby, logout, account/device/session revocation and
deletion synchronously invalidate context and reconcile affected media authority.

## Privacy, security, and licensing readiness

- [x] Client submits no road, route, destination, provider or audience selector.
- [x] APIs return no corridor/provider reference, road name, direction, coordinate,
  distance, bearing, other-user identity or eligibility explanation.
- [x] Context is current-only, short-lived, source-bound, keyed and non-portable.
- [x] Logs/metrics/errors/evidence use allowlisted semantic outcomes only.
- [x] Provider failure is non-disclosing and fails Same-road closed.
- [x] Any future OSM-derived data use must record ODbL attribution/share-alike
  obligations before activation.
- [x] Public OSM APIs/tiles and the OSRM demo service are not treated as production
  infrastructure or used by CI.

## Reliability and evidence readiness

Synthetic evidence may prove exact contracts, provider minimization/disablement,
matching validation, source-version races, expiry/deletion, direction boundaries,
authorization composition, client state, privacy gates, and 100-account/25-receiver/
10-publisher control-plane performance.

It may not prove real-road match quality, map-data completeness/freshness, provider
availability/latency, licensing compliance for a chosen dataset distribution, physical
device behavior, live media delivery, cellular handoff, production capacity, or safety.
Those claims remain explicit exceptions.

## Cost readiness

| Decision | Status |
|---|---|
| Planning and local/CI implementation | **$0/month** |
| Deterministic provider fake/fixtures | Included |
| Hosted route/geocoding/map provider | None |
| OSM/OSRM network call or dataset download | None |
| New Docker routing service | None |
| AWS/LiveKit Cloud/managed service | None |
| Terraform | Disabled; zero resources |
| Existing incremental monthly ceiling | $10, unchanged and not authorization |

A real provider or self-hosted regional road graph would require a separate comparison
of license, attribution, data size/update process, latency, rate limits, privacy,
operations and recurring cost. No free tier is assumed to be permanent or sufficient.

## Locked implementation order

1. Specification/readiness approved in #164; tracker #173 and D02–D09 issues #165–#172 created.
2. Add route-mode persistence/API with Nearby default.
3. Add minimized provider boundary, deterministic fake and hard-disabled real config.
4. Add current context persistence, matching validation, expiry and deletion.
5. Compose Same-road filtering into proximity/channel/media authorization.
6. Add failure reconciliation, privacy-safe operations and observability.
7. Add accessible mobile/browser mode and lifecycle states.
8. Add security/privacy/licensing/performance/scope gates and synthetic evidence.
9. Complete traceability, review and product-owner acceptance.

Every implementation PR must identify its exact S07 deliverable, remain independently
reviewable, keep all prior gates green, and add no external call or dataset.

## Entry gate

- [x] Sprint 6 review is merged and Sprint 6 is accepted.
- [x] Local alpha stabilization through PR #163 is merged.
- [x] Objective, product decisions, APIs, data boundary and exclusions are specified.
- [x] Privacy/security/licensing/cost and evidence limits are explicit.
- [x] Product owner approved the specification and readiness record by merging PR #164.
- [x] Sprint 7 tracker #173 and exact work items #165–#172 are created and locked.

**Decision: READY TO CODE WITHIN THE LOCKED LOCAL/CI BOUNDARY.** Implementation must
follow #165 → #166 → #167 → #168 → #169 → #170 → #171 → #172. This decision does not
permit provider activation, external network calls, dataset downloads, cloud resources,
or spend.

## References

- [Sprint 7 specification](sprint-7-route-awareness.md)
- [Sprint 6 review](sprint-6-review.md)
- [PostGIS spatial-query guidance](https://postgis.net/docs/using_postgis_query.html)
- [OSRM API](https://project-osrm.org/docs/)
- [OpenStreetMap copyright and license](https://www.openstreetmap.org/copyright)
