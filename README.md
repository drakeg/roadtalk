# RoadTalk

RoadTalk is a location-aware, voice-first communication platform inspired by classic CB radio culture and designed for modern travelers.

## Project status

Sprint 0 — Planning & Architecture, Sprint 1 — Project Foundation, Sprint 2 —
Identity, and Sprint 3 — Location are complete. Sprint 1 is conditionally accepted
with named exceptions that must close before the first field test.

Sprint 4 — Push-to-Talk is complete and accepted. Sprint 5 — Proximity Engine is
approved for local/GitHub CI implementation through
[tracker #119](https://github.com/drakeg/roadtalk/issues/119). Its
[specification](docs/sprints/sprint-5-proximity.md),
[readiness gate](docs/sprints/sprint-5-readiness.md), $0 implementation policy, and
named evidence exceptions were approved on 2026-08-06. AWS or LiveKit activation,
paid plans, and recurring spend remain unauthorized.

## Repository layout

| Path | Purpose | Current boundary |
|---|---|---|
| `mobile/` | React Native, Expo development-build, and TypeScript mobile application | Sprint 4 synthetic receive-ready and hold-to-talk behavior is implemented; live/device evidence remains pending |
| `backend/` | FastAPI modular-monolith API, migrations, and backend tests | Sprint 4 metadata-only grants and the disabled provider boundary are implemented; no live adapter is active |
| `infrastructure/` | Terraform bootstrap, environment roots, and reusable modules | Remains disabled by default; Sprint 4 proposes no new AWS resource |
| `scripts/` | Cross-project developer and operational helper scripts | Added only with a traced requirement |
| `docs/` | Architecture, sprint records, ADRs, security, privacy, design, and runbooks | Sprint 4 is approved; documentation tracks implementation and evidence |
| `.github/` | Pull-request, issue, CI, quality, and security workflows | Existing gates remain; Sprint 4 changes require approved traced work |

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

Sprint 4 is complete and product-owner accepted by merged PR #108. Sprint 5 proximity
implementation is active through tracker #119; S05-D02–D04 (#111–#113) are complete
and S05-D05 (#114) is active. Only
local/GitHub CI implementation is authorized; cloud/provider activation and spend
remain blocked.

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
