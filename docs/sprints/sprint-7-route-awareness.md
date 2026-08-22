# Sprint 7: Route Awareness

## Status

Proposed for product-owner review. This document defines a local/GitHub CI scope only.
Merging the planning pull request approves the specification and readiness record; it
does not itself authorize implementation until the Sprint 7 tracker is created and
locked. No routing provider, map dataset, cloud resource, or paid service is activated.

## Objective

Let an authenticated RoadTalk account explicitly choose a **Same road** receive mode
that limits otherwise-eligible Sprint 5/6 communication to confidently matched users
on the same server-derived road corridor with compatible travel direction, without
collecting a destination, retaining a trip, exposing a route, or changing the default
Nearby experience.

## Product decisions

- Nearby remains the default and preserves the accepted Sprint 5 proximity plus Sprint
  6 channel rules.
- Same road is an explicit account setting. It is a filter, never a way to broaden the
  eligible audience beyond current channel, consent, location, session, grant, and
  radius requirements.
- Sprint 7 does not ask for or infer a destination, planned route, address, trip name,
  stop, itinerary, ETA, navigation instruction, or route history.
- The server derives road context from the already-approved foreground location sample,
  horizontal accuracy, heading, speed, and observed time. Clients cannot submit a road,
  segment, direction, confidence, provider hint, route, or audience selector.
- A match contains only an opaque provider-scoped corridor reference, a coarse
  direction bucket, confidence state, source location version, policy version, and
  short expiry. Snapped coordinates, road names, geometries, traces, and raw provider
  payloads are neither persisted nor returned.
- Same-road delivery requires both endpoints to have fresh, confident context for the
  same normalized corridor and compatible direction. Missing, ambiguous, stale,
  conflicting, or provider-failed context denies Same-road delivery; it does not fall
  back silently to Nearby.
- Direction compatibility is coarse and wraparound-safe. Stationary/unknown direction
  is a distinct state and cannot be treated as traveling in both directions.
- Road matching sits behind a typed server provider boundary. Local/CI implementation
  uses deterministic fixtures and a fake provider; real map data, hosted routing APIs,
  and self-hosted regional datasets require a separate dated activation decision.
- OSRM is a candidate adapter because its Match service accepts timestamped GPS traces,
  accuracy radiuses, and reports confidence, while its Nearest service can snap to road
  segments. Candidate status is not provider approval.
- Any future OpenStreetMap-derived data use must satisfy ODbL attribution/share-alike
  obligations and may not assume the public OSM services are a free production API.
- No map is displayed. Sprint 8 retains map rendering and nearby-user visualization.
- Mobile and browser expose Nearby/Same road selection, clear unavailable/degraded
  states, and no road name, exact distance, bearing, other-user identity, or location.
- Route-context recomputation is bounded, rate-limited, cancelable, and tied to accepted
  foreground samples. Pause, consent withdrawal, logout, deletion, stale location, and
  session/device revocation remove or invalidate context and media authority.
- Current and incremental implementation cost remains $0. Terraform stays disabled and
  no external provider request is required for acceptance evidence.

PostGIS remains the final authorization engine. Its index-aware `ST_DWithin` predicate
continues to bound candidate rows before route filtering. Linear-referencing functions
such as `ST_LineLocatePoint` may be evaluated only inside deterministic fixtures; no
road-network geometry is approved for durable production storage in this sprint.

## Representative control flow

1. The account explicitly selects Nearby or Same road. Nearby behavior is unchanged.
2. RoadTalk accepts a foreground location through the existing Sprint 3 validation,
   consent, plausibility, accuracy, sequence, and freshness boundary.
3. For Same road, the backend submits a minimized typed sample to the configured route
   context provider and validates the result against confidence and policy limits.
4. The backend atomically replaces the account's short-lived route context, bound to
   the exact accepted location version. It stores no trace or provider response.
5. A receive/transmit/publication decision first applies every Sprint 5 proximity and
   Sprint 6 channel predicate.
6. If either endpoint selected Same road, both must have compatible fresh context for
   the same opaque corridor; otherwise delivery is denied without revealing why.
7. Provider timeout/failure leaves Nearby users unaffected and Same-road users in a
   clear unavailable state. It never reuses mismatched or expired context.
8. Pause, withdrawal, logout, account/device/session revocation, deletion, or location
   expiry clears route context and reconciles affected grants/subscriptions.

## API boundary

All routes remain under `/api/v1`:

- `GET /me/route-mode` returns only `nearby` or `same_road`, version, and semantic
  availability;
- `PUT /me/route-mode` accepts exactly the desired mode and expected version;
- existing location, channel, nearby-summary, and PTT routes keep their response shapes.

No route-matching endpoint is client callable. Requests accept no road/corridor,
geometry/polyline, coordinate beyond the existing location route, destination, address,
direction, distance, provider, confidence, audience, participant, channel, policy, or
TTL override. Responses expose no provider reference, road name, exact along-road
position, coordinate, heading, speed, identity, membership, or eligibility reason.

## Data boundary

Sprint 7 may add:

- `account_route_mode`: account ID, mode, selected timestamp, version;
- `current_route_context`: account ID, opaque keyed corridor digest, coarse direction,
  confidence class, source location version, provider/policy version, matched/expiry
  timestamps, and version.

The corridor value must be keyed or otherwise non-portable outside RoadTalk and must
not be reversible to a provider road identifier. One current row replaces the prior
row. No road geometry, snapped point, destination, address, route steps, trace,
itinerary, road name, provider hint/payload, location history, or route history is
stored. Account/location deletion and consent withdrawal cascade or synchronously
delete current route context.

## Requirements

- **S07-R01 — Explicit route mode:** Preserve Nearby as default and add versioned,
  authenticated Nearby/Same-road selection with exact over-posting denial.
- **S07-R02 — Provider boundary:** Add a typed, timeout-bounded route-context provider
  interface, deterministic fake, minimized request, validated response, and disabled
  real adapter configuration.
- **S07-R03 — Context minimization:** Derive only opaque corridor, coarse direction,
  confidence, source-version, policy, and expiry; retain one current row and no trace.
- **S07-R04 — Match integrity:** Bind context to an accepted current location and reject
  stale, inaccurate, low-confidence, implausible, mismatched, or replayed results.
- **S07-R05 — Composed authorization:** Apply Same-road compatibility only after every
  Sprint 5 proximity and Sprint 6 channel/session/grant predicate, never to broaden.
- **S07-R06 — Direction and corridor policy:** Require exact keyed corridor equality and
  deterministic compatible direction handling, including wraparound and unknown state.
- **S07-R07 — Failure and reconciliation:** Fail Same-road closed on timeout, provider
  error, expiry, mode change, pause, withdrawal, revocation, deletion, or race.
- **S07-R08 — Client experience:** Add accessible Nearby/Same-road controls and honest
  matching/unavailable/error states in mobile and browser without route disclosure.
- **S07-R09 — Privacy/security/licensing:** Prevent route, destination, provider,
  corridor, direction, location, eligibility, identity, and payload leakage; record any
  future dataset license/attribution before adapter activation.
- **S07-R10 — Reliability/performance:** Test match/update/race/failure matrices and the
  100-account/25-receiver/10-publisher synthetic state against 400 ms control p95.
- **S07-R11 — Cost controls:** Use local fixtures/fakes and existing PostGIS/media
  boundaries; create no external request, dataset download, AWS resource, or spend.
- **S07-R12 — Compatibility/scope:** Preserve Sprints 1–6 and exclude navigation,
  destinations, maps, presence/WebSockets, notifications, moderation, messaging,
  recording/transcription/AI, background/hands-free behavior, and production rollout.

## Acceptance tests

| Test ID | Requirement | Procedure | Expected result |
|---|---|---|---|
| S07-T01 | S07-R01 | Exercise defaults, versioning, replay/conflict, auth and over-posting for route mode. | Nearby remains default; only exact authorized mode transitions succeed. |
| S07-T02 | S07-R02 | Inspect fake/provider requests and inject timeout, malformed, oversized and unknown responses. | Only minimized inputs cross the boundary; invalid or unavailable providers fail closed. |
| S07-T03 | S07-R03 | Inspect schema, migrations, retention, deletion and marker scans. | Exactly one minimized current context exists; no route/trace/provider payload persists. |
| S07-T04 | S07-R04 | Vary location version, consent, freshness, accuracy, confidence, ordering and concurrent updates. | Context binds to one accepted sample and stale/ambiguous/replayed results cannot win. |
| S07-T05 | S07-R05 | Cross product proximity, channel, session, grant, mode and route state for sender/receivers. | Same-road can only reduce the already-authorized audience; no prior denial becomes eligible. |
| S07-T06 | S07-R06 | Test corridor equality, keyed isolation, direction boundaries/wraparound, stationary and unknown states. | Compatibility is deterministic, coarse and non-disclosing. |
| S07-T07 | S07-R07 | Inject provider/database/media failures plus pause, withdrawal, expiry, revocation and deletion races. | Context and subscriptions are removed/reconciled in bounded fail-closed order. |
| S07-T08 | S07-R08 | Drive fake mobile/browser mode, matching, unavailable, reconnect and accessibility states. | Controls are usable and reveal no road, route, identity, coordinate, distance or bearing. |
| S07-T09 | S07-R09 | Scan OpenAPI, database, config, dependencies, logs/errors/metrics/evidence and licensing markers. | No prohibited data/capability leaks and no unapproved provider/data use exists. |
| S07-T10 | S07-R10 | Run full regressions and route-aware 100/25/10 synthetic load with races/failures. | All prior suites pass and control-plane p95 remains at or below 400 ms. |
| S07-T11 | S07-R11 | Inspect network/provider calls, datasets, Compose, dependencies and disabled Terraform plans. | Zero external calls/downloads/resources and $0 current/incremental cost. |
| S07-T12 | S07-R01–R12 | Complete traceability, synthetic demo, privacy/cost/risk/limitations review and acceptance. | Every item has evidence or an approved exception before Sprint 8 planning. |

## Deliverables

- **S07-D01 — Specification, readiness, and tracker:** Approve this baseline and create
  one locked tracker with exact implementation work items.
- **S07-D02 — Route-mode contract and persistence:** Add mode schema/migration/APIs and
  Nearby-compatible defaults.
- **S07-D03 — Route-context provider boundary:** Add typed requests/results, fake,
  validation, timeout, configuration and real-adapter hard-disable.
- **S07-D04 — Current route-context lifecycle:** Add minimized persistence, source
  binding, replacement/expiry/deletion and concurrency handling.
- **S07-D05 — Route-aware authorization:** Compose corridor/direction compatibility with
  current proximity, channel, grant and selective-subscription logic.
- **S07-D06 — Failure reconciliation and operations:** Add bounded provider/context/media
  cleanup, metrics, runbooks and stable non-disclosing errors.
- **S07-D07 — Mobile and browser experience:** Add accessible mode selection and honest
  matching/unavailable lifecycle states.
- **S07-D08 — Security, privacy, licensing, performance, and evidence:** Add scope/leakage
  gates, synthetic matrices/load, provider hard-disable and cost evidence.
- **S07-D09 — Evidence and sprint review:** Finalize traceability, demo synthetic
  behavior, record limitations and obtain product-owner acceptance.

## Entry and exit criteria

Entry requires accepted Sprint 6, merged local alpha stabilizations through PR #163,
explicit product-owner approval of this specification/readiness/cost boundary, and a
locked Sprint 7 tracker. Until then, Sprint 7 implementation is not authorized.

Exit requires S07-R01–R12, S07-T01–T12 and S07-D01–D09 fully traced; green backend,
PostGIS, migration, mobile/browser, security, container and disabled-IaC suites; a
synthetic route-mode/matching/authorization demonstration; and honest provider,
dataset, physical-device and field-test exceptions.

## Cost posture and out of scope

Current and incremental recurring implementation cost is **$0 AWS + $0 LiveKit +
$0 routing provider per month**. Terraform remains disabled and plans zero resources.
No public OSRM endpoint, OSM API/tile service, hosted route API, dataset download,
routing container, credential, payment method, paid plan, or external request is
authorized.

Out of scope: destination/address entry, navigation, turn instructions, ETA, rerouting,
trip/route history, road-name display, route sharing, maps/tiles, nearby-user markers,
presence/WebSockets/Redis, notifications, block/mute/reporting/moderation, messaging,
background location/audio, hands-free mode, recording/egress/transcription/translation/
telephony/agents/AI, new AWS resources, production/public beta, and safety/emergency
claims.

## References

- [Sprint 7 readiness](sprint-7-readiness.md)
- [Sprint 6 review](sprint-6-review.md)
- [Sprint plan](../SPRINT_PLAN.md)
- [System architecture](../architecture/system-architecture.md)
- [Privacy model](../privacy/privacy-model.md)
- [Threat model](../security/threat-model.md)
- [PostGIS ST_DWithin](https://postgis.net/documentation/tips/st-dwithin/)
- [PostGIS linear referencing](https://postgis.net/docs/reference.html#Linear_Referencing)
- [OSRM API and Match service](https://project-osrm.org/docs/)
- [OpenStreetMap copyright and license](https://www.openstreetmap.org/copyright)
