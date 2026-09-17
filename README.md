# RoadTalk

RoadTalk is a location-aware, voice-first communication platform inspired by classic CB radio culture and designed for modern travelers.

## Project status

Sprint 0 — Planning & Architecture, Sprint 1 — Project Foundation, Sprint 2 —
Identity, and Sprint 3 — Location are complete. Sprint 1 is conditionally accepted
with named exceptions that must close before the first field test.

Sprints 4–10 are complete and accepted: Push-to-Talk, Proximity Engine, Channels,
Route Awareness, Map & Presence, Notifications, and Campgrounds. Sprint 10 acceptance
is recorded by merged PR #267. Sprint 11 implementation is not authorized without a
separate planning/readiness decision.

All accepted work remains within the local/GitHub-CI boundary. External data and
notification providers, AWS and LiveKit Cloud activation, production/public beta,
background location/audio, payment methods, and recurring spend remain unauthorized
unless a later written decision explicitly approves them.

## Repository layout

| Path | Purpose | Current boundary |
|---|---|---|
| `mobile/` | React Native, Expo development-build, and TypeScript mobile application | Accepted channel, route, map/presence, notification, and deterministic campground experiences; named physical-device/provider evidence remains pending |
| `backend/` | FastAPI modular-monolith API, migrations, and backend tests | Accepted identity through campground contracts and composition; external notification/campground providers remain disabled |
| `infrastructure/` | Terraform bootstrap, environment roots, and reusable modules | Disabled by default; no Sprint 7–10 AWS resource or recurring spend |
| `scripts/` | Cross-project developer and operational helper scripts | Privacy, hardening, scale, provider, and review gates through Sprint 10 |
| `docs/` | Architecture, sprint records, ADRs, security, privacy, design, evidence, and runbooks | Accepted sprint evidence through Sprint 10 and explicit named limitations |
| `.github/` | Pull-request, issue, CI, quality, and security workflows | Main CI plus route-awareness, map/presence, and notification boundary workflows |

## Start here

1. Read [DEVELOPMENT.md](DEVELOPMENT.md).
2. Read [repository guidance](AGENTS.md) and [contribution rules](CONTRIBUTING.md).
3. Confirm the issue belongs to the approved active-sprint tracker or separately documented planning decision.
4. Create a focused branch from `main`.
5. Implement only the linked requirement/deliverable.
6. Record tests, privacy impact, cost impact, and evidence in the pull request.

Current and incremental local/CI implementation cost remains $0 AWS and $0 LiveKit.
While RoadTalk earns $0, the operating target is $0 and the initial hard ceiling
is $10/month. LiveKit Build is free within hard limits. AWS is used only in separately
approved scheduled test windows, projected around $4–$6 in an active testing month,
and stopped or destroyed afterward. Always-on infrastructure, paid LiveKit, or any
projected recurring spend above $10/month requires a new written approval and
completed applicable Sprint 1 exceptions.

S04-D08 operations preserve lower controlled-test stops of 3,000 participant-minutes,
10 GB downstream transfer, 25 concurrent participants, and $10 incremental monthly
cost. Crossing any stop pauses testing; budgets, CI checks, and provider quotas never
authorize automatic upgrade or continued spend.

Sprint 4 is accepted by merged PR #108, Sprint 5 by PR #127, Sprint 6 by PR #149,
Sprint 7 by PR #185, Sprint 8 by PR #219, Sprint 9 by PR #244, and Sprint 10 by
PR #267. Field testing, cloud/provider activation, and spend remain blocked unless
separately approved.

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
