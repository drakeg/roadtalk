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

### Cost controls

- Local development creates no AWS resources.
- Managed AWS database/cache services remain disabled until their approved implementation and cost decision.

### Not yet implemented

- Mobile application foundation.
- Anonymous device/session authentication.
- CI/CD workflows.
- Terraform infrastructure.
- Deployment and monitoring.
