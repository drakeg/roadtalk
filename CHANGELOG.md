# Changelog

All notable RoadTalk changes are recorded here. The repository history and sprint review records remain the detailed source of truth.

## Unreleased — Sprint 3: Location planning

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
