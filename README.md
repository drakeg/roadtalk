# RoadTalk

RoadTalk is a location-aware, voice-first communication platform inspired by classic CB radio culture and designed for modern travelers.

## Project status

Sprint 0 — Planning & Architecture, Sprint 1 — Project Foundation, Sprint 2 —
Identity, and Sprint 3 — Location are complete. Sprint 1 is conditionally accepted
with named exceptions that must close before the first field test.

Sprint 4 — Push-to-Talk and Sprint 5 — Proximity Engine are complete and accepted.
Sprint 5 completed through
[tracker #119](https://github.com/drakeg/roadtalk/issues/119). Its
[specification](docs/sprints/sprint-5-proximity.md),
[readiness gate](docs/sprints/sprint-5-readiness.md), $0 implementation policy, and
named evidence exceptions were approved on 2026-08-06, and merged PR #127 recorded
final acceptance. Sprint 6 channel planning is proposed; coding remains blocked until
its specification and readiness gate are approved. AWS or LiveKit activation, paid
plans, and recurring spend remain unauthorized.

## Repository layout

| Path | Purpose | Current boundary |
|---|---|---|
| `mobile/` | React Native, Expo development-build, and TypeScript mobile application | Sprint 5 synthetic selective receive is implemented; live/device evidence remains pending |
| `backend/` | FastAPI modular-monolith API, migrations, and backend tests | Sprint 5 proximity authorization and the disabled provider boundary are implemented; no live adapter is active |
| `infrastructure/` | Terraform bootstrap, environment roots, and reusable modules | Remains disabled by default; Sprint 5 adds no AWS resource |
| `scripts/` | Cross-project developer and operational helper scripts | Added only with a traced requirement |
| `docs/` | Architecture, sprint records, ADRs, security, privacy, design, and runbooks | Sprint 5 is accepted; Sprint 6 planning is proposed and not ready |
| `.github/` | Pull-request, issue, CI, quality, and security workflows | Existing gates remain; Sprint 6 coding requires approved traced work |

## Start here

1. Read [DEVELOPMENT.md](DEVELOPMENT.md).
2. Read [repository guidance](AGENTS.md) and [contribution rules](CONTRIBUTING.md).
3. Confirm the issue belongs to the approved active-sprint tracker.
4. Create a focused branch from `main`.
5. Implement only the linked requirement/deliverable.
6. Record tests, privacy impact, cost impact, and evidence in the pull request.

Sprint 5 local/CI implementation remains at $0 AWS and $0 LiveKit cost.
While RoadTalk earns $0, the operating target is $0 and the initial hard ceiling
is $10/month. LiveKit Build is free within hard limits. AWS is used only in separately
approved scheduled test windows, projected around $4–$6 in an active testing month,
and stopped or destroyed afterward. Always-on infrastructure, paid LiveKit, or any
projected recurring spend above $10/month requires a new written approval and
completed applicable Sprint 1 exceptions.

S04-D08 operations preserve those boundaries with lower controlled-test stops of
3,000 participant-minutes, 10 GB downstream transfer, 25 concurrent participants,
and $10 incremental monthly cost. Crossing any stop pauses testing; budgets and
provider quotas never authorize automatic upgrade or continued spend.

Sprint 4 is accepted by merged PR #108 and Sprint 5 by merged PR #127. Sprint 6
planning is proposed; implementation is not authorized. Only local/GitHub CI planning
evidence is authorized; field testing, cloud/provider activation, and spend remain
blocked.

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
