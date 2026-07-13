# RoadTalk

RoadTalk is a location-aware, voice-first communication platform inspired by classic CB radio culture and designed for modern travelers.

## Project status

Sprint 0 — Planning & Architecture and Sprint 1 — Project Foundation are complete.
Sprint 1 is conditionally accepted with named exceptions that must close before the
first field test. Sprint 2 — Identity is the sole active implementation sprint after
its specification pull request is merged.

Current work must follow the [Sprint 2 Identity specification](docs/sprints/sprint-2-identity.md)
and [Sprint 2 readiness record](docs/sprints/sprint-2-readiness.md). The tracker and
deliverable issues are created from the approved wording after merge.

## Repository layout

| Path | Purpose | Sprint 2 scope |
|---|---|---|
| `mobile/` | React Native, Expo development-build, and TypeScript mobile application | Identity setup, avatar selection, and optional recovery experience |
| `backend/` | FastAPI modular-monolith API, migrations, and backend tests | Profile, callsign, catalog, and recovery services |
| `infrastructure/` | Terraform bootstrap, environment roots, and reusable modules | No Sprint 2 expansion; remains disabled by default |
| `scripts/` | Cross-project developer and operational helper scripts | Added only with a traced requirement |
| `docs/` | Architecture, sprint records, ADRs, security, privacy, design, and runbooks | Specification, evidence, operations, and review |
| `.github/` | Pull-request, issue, CI, quality, and security workflows | Existing gates plus traced identity checks |

## Start here

1. Read [DEVELOPMENT.md](DEVELOPMENT.md).
2. Read [repository guidance](AGENTS.md) and [contribution rules](CONTRIBUTING.md).
3. Confirm the issue belongs to the approved Sprint 2 tracker.
4. Create a focused branch from `main`.
5. Implement only the linked requirement/deliverable.
6. Record tests, privacy impact, cost impact, and evidence in the pull request.

Sprint 2 must not enable AWS resources or add location, audio, channel, notification,
moderation, or later-sprint behavior.

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
