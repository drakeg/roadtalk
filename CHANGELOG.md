# Changelog

All notable RoadTalk changes are recorded here. The repository history and sprint review records remain the detailed source of truth.

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
