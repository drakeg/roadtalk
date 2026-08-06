# Changelog

All notable RoadTalk changes are recorded here. The repository history and sprint review records remain the detailed source of truth.

## Unreleased — Sprint 5: Proximity Engine

### Planning

- Approved S05-R01–R12, S05-T01–T12, S05-D01–D09, readiness, the $0
  local/GitHub CI implementation policy, and named live/device/cloud exceptions on
  2026-08-06 through issue #109.
- Created deliverable issues #110–#118 and tracker #119; implementation begins with
  S05-D02 (#111).
- AWS and LiveKit activation, provider calls, paid plans, payment methods, always-on
  operation, and recurring spend remain unauthorized.

### Added

- Versioned, server-controlled proximity policy with a 5,000-meter planning default
  and a configuration invariant requiring location usability to cover the complete
  transmit window.
- Private indexed eligibility query joining current same-device locations to active
  accounts, sessions, consent, and controlled-room receive grants through delivery
  expiry using inclusive PostGIS `ST_DWithin`.
- Exact transient opaque receiver result shape, boundary/high-latitude/antimeridian
  database fixtures, GiST plan evidence, and a dedicated proximity privacy/scope gate.
- No new database object, API, provider dependency/call, AWS resource, managed service,
  or recurring cost.
- Nearby-scoped transmit authorization now requires a usable sender location and a
  non-empty server-derived audience before transmit persistence or microphone
  promotion. Stable `PTT_LOCATION_UNAVAILABLE` and `PTT_NO_NEARBY_LISTENERS`
  denials disclose no membership details.
- Recipient eligibility remains transient in process memory; transmit request and
  response schemas, provider behavior, persistence, infrastructure, and recurring
  cost are unchanged.

## Unreleased — Sprint 4: Push-to-Talk

### Planning

- Proposed an audio-only, hold-to-talk foundation using LiveKit Cloud behind a typed,
  disabled-by-default provider boundary.
- Separated a receive-only room join from server-authorized microphone-only
  publication for an already-connected participant, preserving the low-latency target
  without granting standing publish permission.
- Limited the sprint to one opaque, server-assigned controlled test room; proximity
  and user channels remain assigned to Sprints 5 and 6.
- Proposed metadata-only grants, explicit expiry/release, one-publisher concurrency,
  capture-off-first lifecycle handling, stable failure states, and no audio/token/
  secret persistence or logging.
- Approved S04-R01–R12, S04-T01–T12, S04-D01–D09, readiness gates, evidence limits,
  and zero-revenue cost policy on 2026-07-23 through planning issue #90.
- Created implementation issues #91–#99 and tracker #100; implementation begins with
  S04-D02.
- No cloud project, live secret, AWS resource, payment method, paid plan, or recurring
  spend above $10/month is authorized.

### Added

- Metadata-only `media_grant` persistence with account/device ownership, receive/
  transmit parentage, opaque provider references, scoped actions, policy, expiry,
  revocation, stable outcomes, fail-closed constraints, and authorization indexes.
- Disabled-by-default PTT media configuration that rejects stray provider credentials,
  plus a typed no-network provider protocol and deterministic CI fake.
- Authenticated receive-only grant creation and release endpoints with server-derived
  ownership and provider references, hashed idempotency keys, bounded process-local
  rate controls, one-time synthetic participant tokens, and replay responses that
  never reissue or persist a token.
- Synthetic LiveKit claim tests that allow room join/subscribe while explicitly
  denying media/data publication, room administration, recording, and egress-related
  capabilities.
- Nested transmit authorization for an active caller-owned receive grant, with
  microphone-only provider promotion, one active publisher, 30-second expiry,
  idempotent revocation, receive-release cascade, and failure-closed reconciliation.
- Logout and owned-device revocation synchronously invalidate local media grants.
- Pinned Expo 57-compatible LiveKit native dependencies, an audio-only config plugin,
  purpose-before-permission microphone states, receive-only room/audio adapters, and
  deterministic cleanup on background, screen exit, logout/revocation, failure, and
  unmount.
- Receive-ready explicitly keeps microphone capture off, validates join/subscribe-only
  credentials, and exposes stable connecting, ready, reconnecting, blocked, unavailable,
  and retry states through a fake-tested mobile lifecycle.
- Accessible foreground hold-to-talk requests a nested server transmit grant before
  enabling capture, accepts only microphone publication scope, and serializes native
  capture operations so release cannot be overtaken by an in-flight enable.
- Receiving, authorizing, transmitting, busy, provider-degraded, transmit-error,
  reconnecting, permission-revoked, and 30-second-maximum states use dynamic
  screen-reader labels, non-color text/symbol cues, and a 112-point control.
- Fake-clock and cancellation tests cover maximum duration, rapid press/release,
  denied authorization, incoming audio, reconnect, background, screen exit, logout,
  and capture-off-before-cleanup ordering.
- Ambiguous promotion or delayed release now revokes affected local media authority,
  records metadata-only provider-cleanup state, and attempts microphone denial plus
  participant removal without reauthorizing uncertain state.
- Refresh replay, logout, and device revocation invalidate all active media grants for
  the affected device, with a bounded unscheduled reconciliation helper for expired or
  cleanup-pending participants.
- A dedicated Sprint 4 CI gate rejects live provider configuration/network paths,
  paid/background media capabilities, sensitive logging/evidence, non-metadata grant
  columns, and later-sprint proximity/channel drift while preserving prior gates.
- Refreshed the test-tool and transitive mobile dependency resolutions for current
  security advisories without adding runtime packages or changing approved scope.
- Added the S04-D08 PTT operator runbook, provider activation/rotation/revocation
  procedures, scheduled AWS pre-cost and destroy checks, synthetic evidence, and
  privacy-safe physical-device/cloud test templates.
- Enforced 3,000 participant-minute, 10 GB, 25-connection, and $10 stops in a dedicated
  operations gate; Terraform's disabled field-test budget now defaults to and rejects
  activation above the approved $10 ceiling.
- Added the S04-D09 requirement/test/deliverable traceability, synthetic PTT
  demonstration, security/privacy/cost review, limitations, retrospective, and
  merge-bound product-owner decision.
- Added a migrated-PostgreSQL grant-service measurement at 100 registered accounts,
  25 connected receivers, and 10 publishers with eligible/denied p95 assertions at
  the approved 250 ms target, plus a final-review integrity gate.
- Recorded Sprint 4 product-owner acceptance by merged PR #108 and tracker closure.
- Added the proposed Sprint 5 proximity specification/readiness gate: indexed
  server-authoritative eligibility, default-deny selective subscription, verified
  publication, no recipient-membership persistence, $0 implementation, and explicit
  live/device/cloud exceptions. Sprint 5 coding remains unapproved.
- No LiveKit project, live provider call, token/secret/audio storage, AWS resource,
  managed service, payment method, or incremental recurring cost.

### Cost controls

- Planning and proposed local/GitHub CI implementation remain **$0 AWS + $0 LiveKit**.
- Adopted a zero-revenue policy: $0/month is the default operating target and
  $10/month is the initial hard ceiling requiring explicit approval to exceed.
- LiveKit Build is currently $0/month with hard caps of 5,000 WebRTC participant-
  minutes, 50 GB downstream transfer, and 100 concurrent connections.
- Controlled-test stops are lower: 3,000 participant-minutes, 10 GB, and 25 concurrent
  connections; crossing a stop pauses testing rather than upgrading.
- Physical-device media testing keeps AWS off where practical. Scheduled AWS test
  windows are planned around $4–$6 in an active month and are stopped or destroyed
  afterward; a fully destroyed inactive month targets $0.
- Always-on AWS, LiveKit Ship, spend above $10/month, automatic scaling/upgrades,
  payment methods, RDS, managed Redis, NAT Gateway, ALB, Fargate, recording, egress,
  transcription, telephony, agents, enhanced paid processing, and self-hosting all
  require separate written approval.
- The prior $35/$85 default-budget language is withdrawn; those amounts are scenario
  references only if always-on Build or Ship is approved later.

## Unreleased — Sprint 3: Location

### Planning

- Proposed foreground-only location consent, one-row PostGIS persistence, validated
  GPS/heading/speed samples, and privacy-preserving coarse nearby awareness.
- Explicit exclusions for background tracking, maps/geocoding, history, WebSockets,
  PTT/channels, external SDKs, managed services, and AWS resources.
- Proposed S03-R01–R12, S03-T01–T12, S03-D01–D09, readiness gates, risks, privacy
  controls, and zero-incremental-AWS-cost posture.
- Product-owner approval, READY determination, tracker #81, and scoped implementation
  issues #72–#80; S03-D02 is the first code deliverable.

### Added

- Append-only foreground-location consent events with versioned policy/disclosure,
  account/device ownership, platform, decision, and timestamp metadata.
- One current PostGIS `geography(Point,4326)` row per account with source-device,
  accuracy, optional heading/speed, sequence, expiry, consent, quality, and version
  constraints plus explicit GiST/effective-state indexes.
- Backward-compatible location migration and model/live-PostGIS invariant tests with
  no location history, API, mobile permission, AWS resource, or managed service.
- Versioned foreground-location validation for coordinate, accuracy, observation
  time, heading, speed, consent, device ownership, sequencing, cross-device races,
  plausible movement, quality state, and bounded expiry.
- Privacy-safe metadata-only write receipts, stable non-disclosing policy failures,
  and idempotent explicit/expired current-location deletion helpers.
- Bounded process-local mutation and nearby-read controls across peer, account, and
  device dimensions for the approved single-worker design, with no cache, new AWS
  resource, or incremental AWS cost.
- Expo SDK 57 patch dependencies refreshed to the compatibility set required by Expo
  Doctor, preserving the existing mobile feature scope while restoring the CI gate.
- Authenticated owner-scoped foreground-consent grant and withdrawal endpoints with
  exact version checks, idempotent decisions, and atomic current-location deletion.
- Authenticated current-location upsert and pause endpoints with forbidden extra
  fields, session-derived ownership, metadata-only acknowledgements, stable private
  errors, and bounded peer/account/device mutation limits.
- Indexed caller-relative PostGIS nearby evaluation over fresh, usable, actively
  consented current rows, returning only availability, a semantic bucket, freshness,
  and the caller's expiry boundary.
- Boundary, fail-closed, rate-limit, OpenAPI, privacy, and live query-plan evidence
  for the nearby summary, with no identity, exact count, coordinate, distance,
  bearing, AWS resource, or paid service.
- Accessible purpose-before-permission mobile onboarding for foreground location,
  including precise, approximate/reduced, denied, blocked/settings, unavailable,
  retry, pause, and continue-without-location states.
- Foreground-only Expo location lifecycle control with conservative native sampling,
  bounded JSON uploads, in-memory monotonic sequencing, and mandatory stops on pause,
  background, screen exit, logout, and unmount.
- Mobile configuration and scope tests that prohibit background location/tasks,
  persistent coordinate storage, analytics, paid providers, and new AWS resources;
  expected incremental AWS cost remains $0.
- Owner-only, non-authoritative local accuracy, heading, speed, and freshness status
  with explicit unavailable and stale states.
- Accessible coarse nearby awareness limited to semantic none/few/many buckets, with
  no identity, exact count, coordinate, distance, or bearing disclosure.
- Bounded foreground nearby polling with fail-closed unavailable/retry/expiry states
  and deterministic cancellation on pause, background, screen exit, logout, and
  unmount; no new dependency, paid provider, or AWS resource.
- Dedicated location privacy/scope CI gate rejecting background tasks/permissions,
  coordinate persistence/logging, maps/geocoding, analytics, history, unapproved
  providers, managed services, and later-sprint drift.
- Foreground-location operator runbook plus expanded privacy, threat, leakage,
  OpenAPI, deletion/expiry, and prior-sprint regression coverage.
- Sprint 3 requirement/test/deliverable traceability, synthetic lifecycle evidence,
  cost/privacy audit, known limitations, retrospective, and merge-bound review.

### Cost controls

- Sprint 3 creates no AWS resource and adds $0 incremental monthly cost.
- Terraform remains disabled; the existing enabled field-test design is projected at
  $20–$23/month without the temporary compute promotion.
- A $30 monthly planning budget is recommended before activation because the current
  $20 notification threshold is too close to the recurring floor.

## Unreleased — Sprint 2: Identity

### Planning

- Sprint 2 Identity requirements, acceptance tests, deliverables, readiness, security,
  privacy, compatibility, and scope boundaries.
- Bundled avatar catalog and PII-free optional recovery-key decisions.
- Zero-incremental-AWS-cost gate; no avatar upload/storage/CDN or email/SMS service.

### Added

- Optional one-to-one profile persistence with nullable callsign/avatar state for
  existing anonymous accounts.
- Backward-compatible profile migration with account ownership, normalized callsign
  uniqueness, setup-state, version, and cascade constraints.
- Profile model invariant tests with no new AWS resources.

- Deterministic NFKC/ASCII callsign policy with reserved system names and
  confusable rejection.
- Authenticated, non-enumerating callsign availability endpoint with bounded
  per-account/device rate limiting.
- Unit, route, service, and PostgreSQL uniqueness tests for identity policy.
- Owner-scoped private profile read and conditional callsign update endpoints.
- Minimal public identity DTO limited to display callsign and bundled-avatar ID.
- Optimistic version conflicts, configurable callsign cooldown, over-posting guards,
  and database lifecycle tests with no new AWS resources.
- Versioned bundled avatar catalog endpoint with active and retained-retired metadata.
- Backend profile validation that rejects unknown and retired avatar selections.
- Accessible code-native mobile avatar assets with backend/mobile contract tests.
- Atomic callsign/avatar profile updates and setup-completion state.
- Accessible mobile identity setup and settings flow with callsign preflight and
  authenticated availability checks.
- Bundled-avatar selection, optimistic conflict reload, explicit offline retry, and
  retained retired-avatar rendering.
- Session-bound identity transport with one refresh retry and no new credential storage.
- Optional 256-bit anonymous recovery keys with salted, versioned scrypt hashing and
  a separately configured application pepper.
- One-time recovery-key creation/rotation and atomic account transfer that rotates the
  key, revokes old sessions, prevents replay, and establishes a replacement session.
- Constant-shape recovery failures and bounded peer/device/selector/account mutation
  limits using the existing single-worker API and PostgreSQL database.
- Accessible mobile recovery-key creation and rotation with explicit one-time display.
- Newly registered-device recovery that replaces the temporary session, surfaces the
  rotated key once, and preserves constant-shape failure messaging.
- Recovery keys transient by default, with device-only SecureStore persistence only
  after explicit user opt-in and no clipboard, URL, analytics, or ordinary storage.
- Closed-field structured logging with route templates, result classes, stable problem
  codes, and regression tests that reject synthetic callsign/recovery-key leakage.
- Exact Sprint 2 OpenAPI/scope, non-enumeration, and bounded rate-limit gates.
- Identity and anonymous-recovery operator runbook covering lost keys, compromise,
  pepper rotation, privacy-safe evidence, and the single-worker limiter boundary.
- Sprint 2 requirement, acceptance-test, and deliverable traceability with a complete
  green CI baseline and privacy-safe synthetic identity lifecycle evidence.
- Sprint 2 cost/privacy review, known limitations, retrospective, and merge-bound
  product-owner approval decision.

## Unreleased — Sprint 1: Project Foundation

### Added

- Top-level implementation repository scaffold.
- Shared editor and ignore rules.
- Development workflow and component boundary documentation.
- GitHub pull-request and issue templates.
- Local PostgreSQL/PostGIS Docker Compose service.
- Optional Redis Compose profile.
- Safe local environment example, prerequisite checks, lifecycle commands, and local-development runbook.
- FastAPI backend foundation with typed configuration.
- Versioned system API plus liveness, readiness, and version endpoints.
- Request correlation, privacy-safe JSON logging, problem-details errors, and foundation tests.
- SQLAlchemy account, device, and session persistence models.
- Alembic baseline migration with PostGIS enablement, schema constraints, and indexes.
- Database readiness checks and local migration commands.
- Anonymous account/device registration with no profile, location, or audio collection.
- Device-bound access tokens, hashed rotating refresh credentials, logout, device revocation, and replay-family revocation.
- Expo/React Native iOS and Android development-build foundation.
- Accessible navigation shell, typed public configuration, error boundary, and mobile smoke tests.
- Mobile anonymous-session bootstrap with refresh rotation and fail-closed recovery.
- Platform SecureStore persistence for refresh credentials and in-memory-only access tokens.
- Mobile logout and current-device revocation handling.
- Pull-request CI for backend, PostGIS migrations, mobile quality, and security scans.
- Immutable action pins, read-only permissions, concurrency cancellation, caching, and job timeouts.
- Disabled-by-default Terraform bootstrap and controlled field-test roots.
- Low-cost VPC, ARM EC2/SSM, encrypted gp3, and encrypted S3 backup modules.
- Terraform formatting, validation, disabled-plan, TFLint, Trivy, cost, network, and module-contract gates.
- Immutable ARM backend image, minimal ECR registry, SSM deployment, and application rollback workflow.
- Migration-before-replacement ordering and field-test deployment rehearsal runbook.
- Opt-in three-day API logs, two essential EC2 alarms, operational routing, and a small monthly budget.
- Operator runbooks for clean setup, authentication, CI, deployment, rollback,
  backup/restore, credential rotation, monitoring, and low-cost shutdown.
- Sprint 1 requirement/test/deliverable traceability, automated evidence baseline,
  and privacy-safe manual evidence template.
- Sprint 1 review, acceptance results, known limitations, cost decision,
  retrospective, and approval-withheld decision pending manual evidence.
- Conditional Sprint 1 approval with named device, CI-rehearsal, and AWS exceptions
  that must close before the first field test.

### Cost controls

- Local development creates no AWS resources.
- Managed AWS database/cache services remain disabled until their approved implementation and cost decision.
- Field-test Terraform defaults to zero resources and excludes NAT Gateway, RDS, managed Redis, ALB, and Fargate.
- Detailed monitoring, custom metrics, paid dashboards, tracing, and high-volume logs remain disabled.

### Not yet implemented
