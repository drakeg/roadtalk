# RoadTalk

RoadTalk is a location-aware, voice-first communication platform inspired by classic CB radio culture and designed for modern travelers.

## Project status

Sprint 0 — Planning & Architecture is complete. Sprint 1 — Project Foundation is the sole active sprint.

Current implementation work must follow the [approved Sprint 1 specification](docs/sprints/sprint-1-project-foundation.md) and [Sprint 1 tracker](https://github.com/drakeg/roadtalk/issues/33).

## Repository layout

| Path | Purpose | Current Sprint 1 owner |
|---|---|---|
| `mobile/` | React Native, Expo development-build, and TypeScript mobile application | S01-D02, S01-D06 |
| `backend/` | FastAPI modular-monolith API, migrations, and backend tests | S01-D03–S01-D05 |
| `infrastructure/` | Terraform bootstrap, environment roots, and reusable modules | S01-D09 |
| `scripts/` | Cross-project developer and operational helper scripts | Added only with a traced requirement |
| `docs/` | Architecture, sprint records, ADRs, security, privacy, design, and runbooks | All sprints |
| `.github/` | Pull-request and issue workflow templates; later CI workflows | S01-D01, S01-D08 |

## Start here

1. Read [DEVELOPMENT.md](DEVELOPMENT.md).
2. Read [repository guidance](AGENTS.md) and [contribution rules](CONTRIBUTING.md).
3. Confirm the issue belongs to Sprint 1 and appears on the tracker.
4. Create a focused branch from `main`.
5. Implement only the linked requirement/deliverable.
6. Record tests and evidence in the pull request.

Executable mobile, backend, local-environment, and Terraform setup commands will be added by their specific Sprint 1 deliverables. S01-D01 intentionally does not invent commands before those implementations exist.

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
