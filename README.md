# RoadTalk

RoadTalk is a location-aware, voice-first communication platform inspired by classic CB radio culture and designed for modern travelers.

## Project status

Sprint 0 — Planning & Architecture, Sprint 1 — Project Foundation, Sprint 2 —
Identity, and Sprint 3 — Location are complete. Sprint 1 is conditionally accepted
with named exceptions that must close before the first field test.

Sprint 4 — Push-to-Talk is in planning only. Its proposed
[specification](docs/sprints/sprint-4-push-to-talk.md) and
[readiness gate](docs/sprints/sprint-4-readiness.md) await product-owner approval in
[issue #90](https://github.com/drakeg/roadtalk/issues/90). No Sprint 4 code, cloud
provider, AWS activation, or paid plan is authorized yet.

## Repository layout

| Path | Purpose | Current boundary |
|---|---|---|
| `mobile/` | React Native, Expo development-build, and TypeScript mobile application | Sprint 3 location is complete; proposed Sprint 4 adds receive-ready audio and hold-to-talk only after approval |
| `backend/` | FastAPI modular-monolith API, migrations, and backend tests | Sprint 3 location is complete; proposed Sprint 4 adds metadata-only grants and a disabled provider boundary |
| `infrastructure/` | Terraform bootstrap, environment roots, and reusable modules | Remains disabled by default; Sprint 4 proposes no new AWS resource |
| `scripts/` | Cross-project developer and operational helper scripts | Added only with a traced requirement |
| `docs/` | Architecture, sprint records, ADRs, security, privacy, design, and runbooks | Sprint 4 planning and approval are the current documentation activity |
| `.github/` | Pull-request, issue, CI, quality, and security workflows | Existing gates remain; Sprint 4 changes require approved traced work |

## Start here

1. Read [DEVELOPMENT.md](DEVELOPMENT.md).
2. Read [repository guidance](AGENTS.md) and [contribution rules](CONTRIBUTING.md).
3. Confirm the issue belongs to the approved active-sprint tracker.
4. Create a focused branch from `main`.
5. Implement only the linked requirement/deliverable.
6. Record tests, privacy impact, cost impact, and evidence in the pull request.

Sprint 4 planning and proposed local/CI implementation add $0 AWS and $0 LiveKit
cost. LiveKit Build is currently $0/month with hard usage caps; combining it with the
existing enabled AWS field-test design is projected at $20–$23/month without the
temporary compute promotion. LiveKit Ship would raise the combined floor to
$70–$73/month. Every cloud activation or paid-plan change requires separate approval,
a current price check, and completed applicable Sprint 1 exceptions.

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
