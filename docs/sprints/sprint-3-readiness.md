# Sprint 3 readiness

- Sprint: 3 — Location
- Status: NOT READY — specification approval pending
- Planning issue: #71
- Readiness date: 2026-07-14
- Proposed baseline: Sprint 2 approval merge `106c3670413d697689934b00afe6f5d3c1cc8c9d`

## Decision

Sprint 3 has no unresolved architecture or cost dependency for local/GitHub CI
implementation, but it is not authorized to begin until the product owner approves
the proposed Location specification. Planning on `main` does not itself authorize
code, dependency, permission, schema, or API changes.

## Definition of Ready

- [x] Sprint 2 review is merged and tracker #61 is closed.
- [x] Roadmap objective is explicit: GPS, heading, speed, nearby discovery.
- [x] Foreground-only collection and coarse nearby output are defined.
- [x] Requirements, acceptance tests, deliverables, order, and exit criteria are
  proposed in `sprint-3-location.md`.
- [x] Consent, retention, deletion, sequencing, accuracy, freshness, plausibility,
  rate-limit, and multi-device boundaries are specified.
- [x] PostgreSQL/PostGIS persistence and indexed query architecture is already
  approved by ADR-0003.
- [x] Mobile permission states and lifecycle stop conditions are explicit.
- [x] Background location, maps, history, WebSockets, PTT, channels, and later-sprint
  scope are excluded.
- [x] Exact coordinates, nearby identities, exact counts/distances, and movement
  values are excluded from public output and logs.
- [x] Sprint 1 and Sprint 2 regressions remain acceptance gates.
- [x] No new AWS resource, managed service, or paid third-party API is authorized.
- [x] Planning approval and implementation authorization are separated.
- [ ] Product owner approves the proposed Sprint 3 baseline.
- [ ] D01 tracker and implementation issues are created from the approved wording.

## Cost gate

The default and expected incremental AWS cost for Sprint 3 is **$0**. Development
uses the existing local PostgreSQL/PostGIS service and GitHub CI. Mobile location uses
the OS provider through `expo-location`; no paid map, geocoder, analytics, or external
location provider is required.

Terraform remains disabled. RDS, Redis, DynamoDB, OpenSearch, Lambda, EventBridge,
queues, schedulers, maps, tiles, geocoding, background workers, or extra compute is a
scope change requiring a written architecture and cost decision before implementation.

## Permission and platform gate

The proposal follows current official platform boundaries:

- Expo distinguishes foreground and background permission APIs and supports a
  foreground subscription while the app is active.
- Apple when-in-use authorization is the Sprint 3 ceiling; `Always` is excluded.
- Android foreground access may be precise or approximate; both choices require a
  stable product state. `ACCESS_BACKGROUND_LOCATION` is excluded.
- Permission is requested in context after user action, never at launch.

The implementation must pin the supported Expo dependency and add a CI configuration
gate that rejects background permissions, background modes, TaskManager/geofencing,
motion/activity, maps, and unrelated sensitive permissions.

## Privacy and data gate

- Server stores one expiring current row per account and versioned consent events.
- No trip/location history, coordinate read API, client persistence, analytics export,
  cache, event stream, or evidence copy is allowed.
- Nearby discovery returns only a semantic bucket and freshness state.
- Withdrawal removes current data and eligibility immediately.
- Logs and errors retain only route template, result class, duration, request ID, and
  stable problem code under the existing allowlist.

## Sprint 1 exception boundary

S01-E01 through S01-E03 remain open. Sprint 3 local/CI implementation may proceed
after approval, but no physical-device behavior, battery target, native permission
flow, enabled AWS plan, deployment, or field-test operation may be represented as
passed until its prerequisite exception is closed and evidence is recorded.

## Preconditions before the first code change

1. Product owner explicitly approves `sprint-3-location.md` and this readiness record.
2. Close planning issue #71 as completed.
3. Create one Sprint 3 tracker and S03-D01 through S03-D09 issues from the exact
   approved wording.
4. Update repository and documentation status to make Sprint 3 the sole active
   implementation sprint.
5. Record the approval commit as the implementation baseline.
6. Start S03-D01 from that baseline using the feature-branch/PR workflow.
7. Keep Terraform disabled and Sprint 1 exceptions open.

## Readiness conclusion

**NOT READY — approval pending.** The proposal is technically and financially bounded
for local/CI delivery, with expected incremental AWS cost of $0. Approval is the only
remaining entry gate; until then, no location dependency, permission, database, API,
or mobile implementation change is authorized.
