# RoadTalk

RoadTalk is a location-aware, voice-first communication platform inspired by classic CB radio culture and designed for modern travelers.

## Project status

Sprint 0 — Planning & Architecture and Sprint 1 — Project Foundation are complete.
Sprint 1 is conditionally accepted with named exceptions that must close before the
first field test. Sprint 2 — Identity is complete and approved. Sprint 3 — Location
implementation is complete and its final review is awaiting approval by merge.

The Sprint 3 decision is recorded in its [traceability](docs/sprints/sprint-3-traceability.md),
[synthetic evidence](docs/evidence/sprint-3/README.md), and
[review](docs/sprints/sprint-3-review.md). Sprint 4 planning begins only after the
review merge; coding requires a separately approved specification and readiness record.

## Repository layout

| Path | Purpose | Sprint 3 scope |
|---|---|---|
| `mobile/` | React Native, Expo development-build, and TypeScript mobile application | Foreground permission, short-lived sampling, heading/speed status, and coarse nearby awareness |
| `backend/` | FastAPI modular-monolith API, migrations, and backend tests | Consent, one current PostGIS row, validation, withdrawal, and coarse nearby summary |
| `infrastructure/` | Terraform bootstrap, environment roots, and reusable modules | No Sprint 3 expansion; remains disabled by default |
| `scripts/` | Cross-project developer and operational helper scripts | Added only with a traced requirement |
| `docs/` | Architecture, sprint records, ADRs, security, privacy, design, and runbooks | Specification, evidence, operations, and review |
| `.github/` | Pull-request, issue, CI, quality, and security workflows | Existing gates plus proposed location privacy/scope checks after approval |

## Start here

1. Read [DEVELOPMENT.md](DEVELOPMENT.md).
2. Read [repository guidance](AGENTS.md) and [contribution rules](CONTRIBUTING.md).
3. Confirm the issue belongs to the approved active-sprint tracker.
4. Create a focused branch from `main`.
5. Implement only the linked requirement/deliverable.
6. Record tests, privacy impact, cost impact, and evidence in the pull request.

Sprint 3 adds $0 incremental AWS cost. Terraform remains disabled; activating the
existing field-test design is projected at $20–$23/month without the temporary compute
promotion, and requires a separate approval and completed Sprint 1 exceptions.

## Source of truth

This repository is authoritative for:

- project and sprint plans
- requirements and acceptance tests
- sprint deliverables and reviews
- Agile/Kanban working agreements
- architecture decision records
- implementation and validation history

See [Project Governance](docs/PROJECT_GOVERNANCE.md), [Agile Workflow](docs/AGILE_WORKFLOW.md), and the [documentation index](docs/README.md).

## Scope rule

Keep changes scoped to the active sprint and linked work item. Changes to approved scope require a documented decision before implementation.
