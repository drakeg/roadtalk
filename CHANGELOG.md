# Changelog

All notable RoadTalk changes are recorded here. The repository history and sprint review records remain the detailed source of truth.

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

### Cost controls

- Local development creates no AWS resources.
- Managed AWS database/cache services remain disabled until their approved implementation and cost decision.

### Not yet implemented

- CI/CD workflows.
- Terraform infrastructure.
- Deployment and monitoring.
