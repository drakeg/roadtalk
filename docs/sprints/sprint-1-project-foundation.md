# Sprint 1: Project Foundation

## Status

Approved — Ready for Implementation

## Approved roadmap scope

> Mobile app, backend, CI/CD, Terraform, monitoring, authentication.

This specification operationalizes the approved Sprint 1 wording without adding Sprint 2–15 functionality.

## Objective

Create a reproducible, tested, observable RoadTalk foundation in which the mobile development build and backend can run locally, authenticate an anonymous device session, pass CI, and deploy the controlled field-test infrastructure through Terraform.

## In scope

- repository/application scaffolding
- React Native/Expo development-build foundation
- FastAPI modular-monolith foundation
- PostgreSQL/PostGIS and Alembic baseline
- device-bound anonymous account/session authentication foundation
- access-token issue/validation
- rotating refresh credentials, logout, and device/session revocation
- local Docker Compose development environment
- CI quality/security gates
- field-test Terraform implementation from the accepted design
- container build and controlled deployment workflow
- health, readiness, version, structured logging, metrics, alarms, and runbooks
- automated tests and documentation

## Out of scope

- profile, callsign, avatar, or account-recovery user experience (Sprint 2)
- continuous location collection or nearby discovery (Sprint 3)
- push-to-talk/media feature implementation (Sprint 4)
- proximity delivery engine (Sprint 5)
- general/RV/private channel feature implementation (Sprint 6)
- maps, notifications, campgrounds, convoys, moderation, AI, premium, or production launch
- self-hosted LiveKit
- production Multi-AZ deployment
- audio recording, transcription, or storage

A dependency may be wired as an inert adapter/configuration boundary, but later-sprint user behavior must not be implemented.

## Requirements

- **S01-R01 — Repository foundation:** Establish the approved mobile, backend, infrastructure, documentation, and shared-tooling structure with reproducible setup commands.
- **S01-R02 — Mobile foundation:** Create an installable Expo development build for iOS and Android with navigation shell, environment configuration, accessibility baseline, error boundary, and test framework.
- **S01-R03 — Backend foundation:** Create the FastAPI modular-monolith shell with versioned routing, configuration, dependency boundaries, problem-details errors, correlation IDs, and health/readiness/version endpoints.
- **S01-R04 — Database foundation:** Provide PostgreSQL/PostGIS local service, SQLAlchemy data access, Alembic migration baseline, account/device/session tables, and migration validation.
- **S01-R05 — Anonymous authentication:** Create a new anonymous account and registered device without collecting profile/location/audio data.
- **S01-R06 — Session lifecycle:** Issue short-lived access tokens; securely hash/rotate refresh credentials; support refresh, logout, device revocation, and replay-family revocation.
- **S01-R07 — Mobile credential security:** Store refresh credentials using supported platform-secure storage; never persist access/refresh credentials in ordinary application storage, logs, URLs, or analytics.
- **S01-R08 — Local development:** Provide Docker Compose and documented commands for backend, PostgreSQL/PostGIS, optional Redis profile, migrations, tests, and mobile-to-local-API configuration.
- **S01-R09 — CI/CD foundation:** Enforce formatting, linting, types, unit/integration tests, migration tests, schema checks, dependency/container/IaC scanning, and build validation.
- **S01-R10 — Terraform field-test foundation:** Implement the accepted bootstrap/state and controlled field-test AWS design with separate module `variables.tf` and `outputs.tf`, no NAT Gateway, no public database/cache ports, and no embedded secrets.
- **S01-R11 — Deployment foundation:** Build immutable backend images, publish through the approved registry workflow, deploy/rollback the field-test backend reproducibly, and document database migration ordering.
- **S01-R12 — Monitoring:** Implement privacy-filtered structured logs, request correlation, baseline service metrics, health checks, resource/error alarms, budget alerts, and operational contact routing.
- **S01-R13 — Documentation/runbooks:** Document clean setup, configuration, authentication behavior, CI, deployment, rollback, restore, credential rotation, and known limitations.
- **S01-R14 — Scope protection:** Demonstrate that no Sprint 2–15 user feature is present and no audio/location data is collected.

## Acceptance tests

| Test ID | Requirements | Procedure | Expected result |
|---|---|---|---|
| S01-T01 | R01, R08 | Follow setup documentation from a clean checkout. | Required local services start, migrations complete, tests run, and mobile can reach backend without undocumented steps. |
| S01-T02 | R02 | Build/install development builds and run the navigation/error/accessibility smoke suite on iOS and Android targets. | Both platforms launch, display the foundation shell, handle configured API state, and expose no later-sprint feature. |
| S01-T03 | R03 | Exercise health, readiness, version, unknown route, invalid request, and correlation behavior. | Stable versioned responses/problem details are returned; readiness reflects dependencies; correlation IDs propagate without sensitive data. |
| S01-T04 | R04 | Run migrations on empty and previous-baseline databases; inspect PostGIS availability, constraints, and downgrade/forward-fix behavior. | Schema is reproducible and account/device/session integrity rules pass. |
| S01-T05 | R05, R06 | Create anonymous session, authenticate, refresh repeatedly, logout, revoke device, and attempt use afterward. | Valid lifecycle succeeds; revoked/expired credentials fail closed. |
| S01-T06 | R06 | Replay a rotated refresh credential and then use another credential from the same family. | Replay is detected and the affected credential family is revoked. |
| S01-T07 | R07 | Inspect application storage, backups, logs, errors, URLs, and analytics during auth flows. | No raw credential appears outside platform-secure storage/in-memory use. |
| S01-T08 | R09 | Run CI on compliant code and controlled format/type/test/migration/security failures. | Compliant pipeline passes; every injected defect fails the intended required check. |
| S01-T09 | R10 | Run Terraform formatting, initialization, validation, lint/security scans, and reviewed plan for field test. | Plan matches architecture, exposes no secret, creates no prohibited public data service/NAT Gateway, and module contracts follow the file rules. |
| S01-T10 | R11 | Deploy field-test backend, apply migration, verify health, deploy a second image, and roll back. | Deployment and rollback complete from documented commands with service/data integrity preserved. |
| S01-T11 | R12 | Trigger health, error-rate, resource, and budget test conditions. | Logs/metrics are privacy-safe and each actionable alarm reaches the configured destination. |
| S01-T12 | R13 | Execute rollback, restore rehearsal, and credential-rotation runbook review. | Steps are complete, bounded, and produce recorded evidence. |
| S01-T13 | R14 | Inspect routes, mobile screens, permissions, schemas, database, and dependencies for later-sprint behavior. | No profile/callsign, continuous location, PTT, proximity, channel, or later feature is implemented or collected. |
| S01-T14 | All | Run the full automated suite and Sprint 1 demonstration. | All requirements and tests pass; documentation and tracker are complete; repository is deployable. |

## Deliverables

- **S01-D01:** Approved repository scaffold and root development documentation.
- **S01-D02:** `mobile/` Expo/React Native/TypeScript development-build foundation.
- **S01-D03:** `backend/` FastAPI modular-monolith foundation.
- **S01-D04:** PostgreSQL/PostGIS Compose service, models, and Alembic baseline.
- **S01-D05:** Anonymous-account and device/session authentication API.
- **S01-D06:** Mobile secure-session client and logout/revocation behavior.
- **S01-D07:** Docker Compose local environment and clean-setup scripts.
- **S01-D08:** Required CI workflows and pinned quality/security tooling.
- **S01-D09:** `infrastructure/` Terraform bootstrap and field-test roots/modules.
- **S01-D10:** Container build, registry, deployment, migration, and rollback workflow.
- **S01-D11:** Monitoring, alarms, budgets, dashboards/queries, and privacy filters.
- **S01-D12:** Setup, authentication, deployment, rollback, restore, and rotation runbooks.
- **S01-D13:** Sprint 1 traceability and automated/manual test evidence.
- **S01-D14:** Sprint 1 review, demonstration, approval, and retrospective record.

## Implementation order

1. D01 repository scaffold
2. D07 local development foundation
3. D03 backend shell and D04 database baseline
4. D05 authentication backend
5. D02 mobile shell and D06 secure session client
6. D08 CI gates
7. D09 Terraform field-test foundation
8. D10 deployment/rollback
9. D11 monitoring/budgets
10. D12 runbooks
11. D13 evidence and D14 review

Parallel work is allowed only when dependencies and the active work-in-progress limit permit it.

## Entry criteria

- Sprint 0 status is Complete.
- Sprint 0 tracker and all deliverable issues are closed.
- Sprint 1 readiness decision is READY.
- Accepted ADR-0001 through ADR-0005 are on `main`.
- This Sprint 1 specification is committed and indexed.
- Code/infrastructure work returns to branch and pull-request workflow.

## Exit criteria

- All S01-R01 through S01-R14 requirements are implemented.
- All S01-T01 through S01-T14 tests pass.
- All S01-D01 through S01-D14 deliverables are committed and reviewed.
- CI and deployment/rollback are reproducible.
- Field-test cost and security controls are active before resources remain running.
- No later-sprint functionality was implemented.
- Sprint 1 demonstration is approved.
- Sprint 2 does not begin until its specification is approved.
