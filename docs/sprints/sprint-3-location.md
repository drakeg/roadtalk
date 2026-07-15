# Sprint 3: Location

## Status

Approved — product owner approved on 2026-07-14.

## Objective

Allow an authenticated RoadTalk user to explicitly enable foreground location,
publish one short-lived validated current sample containing optional heading and
speed, and see privacy-preserving coarse nearby awareness without exposing any
person's coordinates, identity, exact distance, or location history.

## Product decisions

- Sprint 3 is foreground-only. Collection starts from an explicit in-app action and
  stops when the location experience is no longer active, the app leaves the
  foreground, consent is withdrawn, the user pauses it, or authentication ends.
- RoadTalk requests OS foreground/when-in-use location only after a separate purpose
  explanation and affirmative choice. Denial leaves identity and account management
  usable and does not trigger a coercive prompt loop.
- Approximate or inaccurate OS results may support a stable degraded/unavailable UI,
  but only samples meeting server policy are eligible for nearby awareness.
- The server stores one current row per account, not a trip or breadcrumb history.
  Accepted samples replace the prior row and expire quickly.
- Heading and speed are optional quality fields from the OS sample. The app does not
  infer driving, advertise a driving mode, or collect motion/activity data.
- Nearby discovery returns a semantic bucket such as `none`, `few`, or `many`; it
  never returns identities, callsigns, avatars, coordinates, bearings, exact counts,
  or distances. Exact bucket and radius thresholds remain server policy.
- PostgreSQL/PostGIS remains the only data platform. Redis, RDS, maps, geocoding,
  external location SDKs, and new AWS resources are unnecessary for this sprint.

These choices satisfy the Sprint 3 roadmap's GPS, heading, speed, and nearby-discovery
scope while keeping the first implementation testable locally and in GitHub CI at
zero incremental AWS cost.

## Requirements

- **S03-R01 — Foreground consent:** Record versioned, authenticated foreground-
  location consent separately from OS permission. Grant and withdrawal are explicit,
  idempotent, auditable without coordinates, and scoped to the current policy and
  disclosure versions.
- **S03-R02 — Current-location persistence:** Add one account-owned current-location
  row using PostGIS `geography(Point, 4326)` with source device, observed/received
  times, horizontal accuracy, optional heading/speed, client sequence, expiry,
  consent version, quality state, and optimistic version. Add a GiST point index and
  expiry/effective-state indexes without creating historical location storage.
- **S03-R03 — Location quality policy:** Validate coordinate, accuracy, time,
  sequence, device/session ownership, consent, heading, speed, expiry, and plausible
  movement using versioned server configuration. Reject stale, future, inaccurate,
  out-of-order, malformed, and implausible samples with stable problems.
- **S03-R04 — Private location API:** Provide authenticated consent grant/withdrawal,
  current-sample upsert, and location withdrawal endpoints. Responses acknowledge
  sequence, quality, expiry, and policy version but never echo coordinates.
- **S03-R05 — Expiry and deletion:** Exclude expired or unusable rows immediately,
  remove the current row when consent is withdrawn or the user pauses location, and
  cascade it on account deletion. Cleanup must be idempotent and require no background
  worker or managed scheduler for correctness.
- **S03-R06 — Coarse nearby discovery:** Use indexed PostGIS distance evaluation over
  fresh, consented, usable samples to return only the caller's semantic nearby bucket
  and freshness state. Exclude the caller and fail closed when the caller's location
  is missing, stale, inaccurate, or withdrawn.
- **S03-R07 — Foreground mobile permission flow:** Add a purpose screen and explicit
  enable action before requesting foreground permission. Handle unavailable services,
  approximate/reduced accuracy, denied, blocked/settings, loading, and retry states
  accessibly without requesting background, motion, microphone, or notification
  permission.
- **S03-R08 — Foreground sampling:** Use the platform location API only while the
  location experience is foreground-active. Send bounded, deduplicated updates with
  monotonic sequence and stop the subscription on pause, background, logout, screen
  exit, or unmount. Never persist coordinates in ordinary or secure device storage.
- **S03-R09 — Heading, speed, and nearby UX:** Show the owner non-authoritative local
  heading/speed/accuracy when available, clearly distinguish unavailable/stale data,
  and show only the server's coarse nearby status. Do not add a map, route, nearby
  profile list, exact count, distance, or bearing to another user.
- **S03-R10 — Privacy and abuse controls:** Rate-limit consent, mutation, and nearby
  reads across existing account/device/network dimensions; keep coordinates and
  derived movement out of logs, analytics, URLs, errors, crash fields, and evidence;
  and reject over-posted or later-sprint fields.
- **S03-R11 — Compatibility and cost:** Preserve Sprint 1 authentication/operations
  and Sprint 2 identity/recovery behavior, use the existing PostgreSQL/PostGIS and CI
  foundation, keep Terraform disabled, and introduce no AWS or paid third-party
  service.
- **S03-R12 — Quality and evidence:** Extend migration, domain, API, PostGIS-query,
  mobile permission/lifecycle, OpenAPI, privacy, scope, security, and regression
  tests; update privacy/security/runbook documentation; and record traceability,
  synthetic demonstration evidence, limitations, and the review decision.

## Out of scope

- background or always-on location, iOS `Always`, Android
  `ACCESS_BACKGROUND_LOCATION`, foreground services, geofencing, or headless tasks
- maps, tiles, routing, roads, geocoding, reverse geocoding, places, trip history,
  breadcrumbs, geofences, or downloadable location content
- exact nearby counts, profile/callsign/avatar lists, coordinates, exact distances,
  bearings to other users, or public location APIs
- Redis/GEO, RDS, DynamoDB, OpenSearch, S3, CloudFront, Lambda, EventBridge, queues,
  managed schedulers, analytics SDKs, advertising SDKs, or another location provider
- WebSockets, durable presence, channels, PTT grants, audio, delivery eligibility,
  block/mute, notifications, maps, moderation, or other Sprint 4+ behavior
- motion/activity recognition, driving detection, navigation, emergency/safety claims,
  anti-spoof guarantees, or background battery optimization
- enabling Terraform, deploying AWS, or executing S01-E01 through S01-E03 rehearsals

## API baseline

All endpoints are versioned under `/api/v1` and require an active bearer session.

| Endpoint | Method | Purpose |
|---|---|---|
| `/me/location-consent` | PUT | Grant the current foreground-location policy/disclosure version. |
| `/me/location-consent` | DELETE | Withdraw foreground consent and remove current location. |
| `/me/location` | PUT | Submit a current foreground sample. |
| `/me/location` | DELETE | Pause/withdraw the current sample without deleting consent history. |
| `/nearby/summary` | GET | Read caller-relative coarse status with no user or coordinate disclosure. |

Location sample input contains only:

- `observed_at`
- `latitude` and `longitude`
- `horizontal_accuracy_m`
- optional `heading_deg`
- optional `speed_mps`
- monotonic `client_sequence`
- `consent_policy_version`

The acknowledgement contains only accepted sequence, quality state, expiry,
effective policy version, and resource version. It does not echo coordinates,
movement values, source identifiers, or internal thresholds.

Nearby summary contains only a stable availability state, semantic nearby bucket,
and expiry/freshness boundary. Missing or unusable caller location returns a stable
problem; candidate data is never returned.

## Persistence baseline

### Foreground consent

- append-only grant/revoke events with account, policy/disclosure version, platform,
  source device, decision, and timestamp
- one derived effective state per account or a deterministic latest-event query
- no coordinate, heading, speed, IP, or free-text reason in the consent record

### Current location

- primary/foreign key: account ID with cascade deletion
- PostGIS geography point in SRID 4326
- source device ID; no raw installation or session credential
- client observed/server received timestamps
- horizontal accuracy; optional heading and speed
- client sequence, expiry, quality state, consent policy version, resource version
- GiST point index plus B-tree expiry/effective-state indexes
- no history table, event stream, audit copy, cache, analytics export, or location log

Same-device updates require a strictly increasing sequence and observed time.
Cross-device replacement requires an active authenticated source and a materially
newer observation. Server receipt order resolves an otherwise equal race. Thresholds
are tested policy, not public promises.

## Mobile baseline

- Add `expo-location` only; review and pin the dependency.
- Configure foreground purpose text and only the Android coarse/fine and iOS
  when-in-use permissions produced by the supported Expo configuration.
- Do not enable Expo background-location flags, Android background permission or
  location foreground service, iOS location background mode, TaskManager, geofencing,
  or persistent coordinate storage.
- Explain purpose before the OS dialog and request permission only from an explicit
  user action. Android approximate and iOS reduced-accuracy states are handled as
  real user choices, not errors to bypass.
- A foreground subscription uses conservative accuracy/distance/time behavior and a
  bounded upload/poll schedule. Exact tuning is configuration and must be covered by
  fake-clock/lifecycle tests rather than exposed as an API promise.
- App-state, navigation, pause, consent withdrawal, logout, and unmount transitions
  stop sampling and nearby polling before clearing UI state.

Official implementation constraints:

- [Expo Location](https://docs.expo.dev/versions/latest/sdk/location/)
- [Apple when-in-use authorization](https://developer.apple.com/documentation/corelocation/requesting-authorization-to-use-location-services)
- [Android foreground and accuracy choices](https://developer.android.com/develop/sensors-and-location/location/permissions)
- [Android runtime permission guidance](https://developer.android.com/develop/sensors-and-location/location/permissions/runtime)

## Acceptance tests

| Test ID | Requirements | Procedure | Expected result |
|---|---|---|---|
| S03-T01 | R01, R02, R11 | Upgrade empty and Sprint 2 databases; inspect consent/location constraints and indexes; downgrade/forward where safe. | Existing accounts gain no consent/location row, PostGIS invariants hold, and migration gates pass. |
| S03-T02 | R01, R04, R05 | Grant/replay/replace/withdraw consent as owner and attempt missing auth, stale policy, unknown fields, or another account. | Owner decisions are idempotent and versioned; unauthorized/over-posted/stale requests fail; withdrawal removes location. |
| S03-T03 | R03, R04 | Submit boundary coordinates, accuracy, times, sequences, heading, speed, same/cross-device races, and implausible movement. | Only policy-valid newest samples replace the row; stable problems expose no submitted values or thresholds. |
| S03-T04 | R02, R05 | Exercise replacement, expiry, pause, consent withdrawal, account deletion, and cleanup with a migrated PostGIS database. | At most one current row exists; stale/withdrawn/deleted data is immediately ineligible and cleanup is idempotent. |
| S03-T05 | R06 | Use deterministic PostGIS fixtures at inside/outside boundary, stale, inaccurate, withdrawn, self, and empty cases; inspect query plan. | Indexed distance logic returns only the correct coarse bucket; no candidate field or exact count escapes. |
| S03-T06 | R04, R06, R10 | Validate authentication, exact OpenAPI schemas, over-posting, rate limits, and response/log/error serialization. | Contracts expose only approved fields; stable 401/409/422/429 problems and Retry-After leak no location. |
| S03-T07 | R07 | Test purpose-before-permission, granted precise/approximate, denied, blocked/settings, unavailable services, loading, retry, and accessibility. | Permission is contextual and non-coercive; limited states remain usable; only foreground permission is configured. |
| S03-T08 | R08, R09 | Drive fake location/AppState/navigation/logout clocks through update, dedupe, retry, pause, background, stale, and unmount paths. | Sampling/polling is bounded and always stops; coordinates are not persisted/logged; heading/speed and coarse status degrade safely. |
| S03-T09 | R09, R10 | Inspect mobile UI, transport, storage, URLs, logs, dependencies, configuration, and screenshots generated by tests. | No map, nearby identity, exact count/distance, coordinate persistence, analytics, background task, or later-sprint behavior exists. |
| S03-T10 | R10, R12 | Inject synthetic coordinates/callsigns/identifiers into failures and scan allowlisted logs, artifacts, OpenAPI, and CI output. | Sensitive values are absent; route templates/stable codes remain; privacy/scope gate fails on prohibited additions. |
| S03-T11 | R11 | Re-run all Sprint 1 and Sprint 2 backend/PostGIS, migration, mobile, security, container, dependency, and zero-resource Terraform gates. | Authentication, identity, recovery, operations, and zero-cost defaults remain green. |
| S03-T12 | R01–R12 | Demonstrate synthetic consent, foreground sample, heading/speed quality, nearby bucket, expiry, pause, withdrawal, and denied/stale paths; review traceability/cost/limitations. | The repository/CI lifecycle passes without real location evidence, and the product owner records the sprint decision. |

Physical-device permission, battery, native storage, and foreground lifecycle behavior
must be recorded as pending rather than passed until S01-E01 is closed and hardware
evidence is performed.

## Deliverables

- **S03-D01:** Approved Location specification, readiness record, tracker, and scoped
  implementation issues.
- **S03-D02:** Foreground-consent and current-location schema/model with backward-
  compatible PostGIS migration.
- **S03-D03:** Versioned location quality, sequencing, plausibility, expiry, and rate-
  limit domain controls.
- **S03-D04:** Authenticated consent/current-location API and privacy-safe contracts.
- **S03-D05:** Indexed coarse nearby-summary query/service/API with boundary and query-
  plan evidence.
- **S03-D06:** Mobile foreground permission/onboarding and lifecycle controller.
- **S03-D07:** Mobile location status, heading/speed, pause/settings, and coarse nearby
  experience.
- **S03-D08:** Privacy/security hardening, exact scope gates, deletion/expiry behavior,
  regression coverage, and location operator documentation.
- **S03-D09:** Traceability, synthetic demonstration evidence, sprint review, cost/
  privacy audit, limitations, retrospective, and product-owner decision.

## Implementation order

1. D01 specification/readiness/tracker
2. D02 consent and current-location persistence
3. D03 quality/sequencing/expiry controls
4. D04 private consent/location API
5. D05 coarse nearby summary
6. D06 mobile permission and lifecycle
7. D07 mobile location/nearby experience
8. D08 hardening, regressions, and operations
9. D09 evidence and sprint review

Only one code deliverable is active unless a dependency makes independent work
explicit. Every code branch starts from the latest merged deliverable.

## Dependencies

- Sprint 2 approval merge `106c3670413d697689934b00afe6f5d3c1cc8c9d`.
- Existing FastAPI, SQLAlchemy/Alembic, PostgreSQL 17/PostGIS 3.5, Expo development
  build, authenticated session client, profile setup state, CI, container, and
  disabled Terraform foundations.
- ADR-0003's PostgreSQL/PostGIS geography and `ST_DWithin` decision.
- Approved privacy model, threat model, API/data-model baselines, and NFR-08/NFR-11/
  NFR-16/NFR-18.
- S01-E01 through S01-E03 remain hard blockers for field testing, but not for local/
  CI Sprint 3 implementation.
- No AWS, external map/location API, or paid service dependency is required.

## Entry criteria

- Sprint 2 issue #60 and tracker #61 are closed as completed.
- This specification and readiness record are reviewed and explicitly approved.
- Planning issue #71 is closed after approval is recorded.
- D01 creates the tracker and implementation issues from the exact approved wording.
- Repository/documentation status makes Sprint 3 the sole active implementation
  sprint after approval.
- The first code branch starts from the approval baseline.
- No AWS resource is enabled and no Sprint 1 exception is represented as closed.

## Exit criteria

- S03-R01 through S03-R12 are implemented and traced.
- S03-T01 through S03-T12 pass for the approved repository/CI scope, with physical-
  device evidence honestly pending where blocked.
- S03-D01 through S03-D09 are merged and the tracker is complete.
- Synthetic foreground consent, current location, heading/speed quality, coarse
  nearby awareness, expiry, pause, withdrawal, and denial are demonstrated.
- No coordinate, movement value, candidate identity, exact count/distance, or location
  history leaks through public responses, logs, errors, URLs, storage, or evidence.
- No background permission/task, map/geocoder, location history, later-sprint feature,
  AWS resource, or recurring infrastructure cost is introduced.
- Sprint 1 and Sprint 2 regressions remain green.
- Sprint 3 review is approved before Sprint 4 planning begins.

## Cost posture

Expected incremental AWS cost is **$0**. Development and acceptance use the existing
local PostgreSQL/PostGIS service and GitHub CI. The mobile app uses the platform
location service through the existing Expo development build. Nearby summary uses
the existing PostGIS database and one current row per account.

Terraform remains disabled and must plan zero resources by default. RDS, Redis,
DynamoDB, OpenSearch, S3, CloudFront, Lambda, EventBridge, queues, paid map/geocoding,
analytics, or additional compute is not authorized. If measured field-test load later
justifies another service, it requires a separate architecture and cost decision.

## Security and privacy constraints

- Exact coordinates, accuracy, heading, speed, device source, and derived movement
  are private inputs and never enter routine logs, analytics, URLs, errors, evidence,
  public profile output, or nearby output.
- Only an active authenticated account with current foreground consent may update or
  withdraw its location and read caller-relative nearby status.
- No client-supplied account/device selector is accepted; ownership comes from the
  verified session.
- Freshness, accuracy, sequence, plausibility, rate, consent, and expiry checks fail
  closed. Consumer GPS is not treated as cryptographically trustworthy.
- Nearby query results are reduced to a semantic bucket before serialization.
- Denial and withdrawal remain usable, non-coercive paths and remove eligibility
  promptly.
- Mobile stores no coordinate history and stops collection on every foreground-
  lifecycle exit.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Precise-location disclosure | Physical safety and privacy harm | Private DTOs, no coordinate reads, semantic nearby buckets, closed logs, synthetic leakage corpus |
| Spoofed or implausible samples | False nearby awareness | freshness/accuracy/sequence/plausibility policy and explicit residual-risk language |
| Nearby bucket enables inference | Repeated probing may reveal presence | coarse buckets, no identity/distance, caller-location requirement, rate limits, expiry |
| Permission coercion or store rejection | User harm and distribution risk | contextual foreground-only request, denial path, no background permission/task, accurate disclosures |
| Battery/data drain | Poor mobile experience | foreground lifecycle stop rules, conservative sampling/polling, dedupe, fake-clock tests, later device evidence |
| Location history appears accidentally | Privacy/scope violation | one-row schema, replacement semantics, no event/cache/analytics sink, schema and dependency gates |
| High write/query rate | Database load | bounded client updates, server mutation/read limits, GiST index, query-plan test; scale only from measurements |
| Multi-device races | Stale or incorrect current sample | device-aware sequence and newer-observation rules with server receipt tie-break |
| PostGIS adds managed-service pressure | Recurring cost | reuse local/existing PostgreSQL/PostGIS; no RDS authorization |
| Sprint 4–8 behavior leaks in | Unreviewed audio/proximity/channel/map scope | exact route/schema/screen/dependency/permission allowlists |

## Approval boundary

Product-owner approval on 2026-07-14 locks this baseline and authorizes Sprint 3
implementation through tracker #81. Changes to requirements, acceptance tests,
deliverables, cost, permissions, privacy, or scope require documented change control.
