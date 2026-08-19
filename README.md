# RoadTalk

RoadTalk is a location-aware, voice-first communication platform inspired by classic CB radio culture and designed for modern travelers.

## Project status

Sprint 0 — Planning & Architecture, Sprint 1 — Project Foundation, Sprint 2 —
Identity, and Sprint 3 — Location are complete. Sprint 1 is conditionally accepted
with named exceptions that must close before the first field test.

Sprint 4 — Push-to-Talk and Sprint 5 — Proximity Engine are complete and accepted.
Sprint 6 — Channels implementation is complete through S06-D08 and merged PR #147.
Merging the S06-D09 review records final Sprint 6 product-owner acceptance, closes
[tracker #139](https://github.com/drakeg/roadtalk/issues/139), and permits the next
RoadTalk planning decision. It does not authorize Sprint 7 coding, AWS or LiveKit
activation, paid plans, recurring spend, production/public beta, or field-test claims.

## Repository layout

| Path | Purpose | Current boundary |
|---|---|---|
| `mobile/` | React Native, Expo development-build, and TypeScript mobile application | Sprint 6 channel catalog, switching, and private-channel management are implemented synthetically; physical-device/live evidence remains pending |
| `backend/` | FastAPI modular-monolith API, migrations, and backend tests | Sprint 6 channel, membership, invite, selection, proximity/media authorization, and reconciliation are implemented; no live adapter is active |
| `infrastructure/` | Terraform bootstrap, environment roots, and reusable modules | Remains disabled by default; Sprint 6 adds no AWS resource |
| `scripts/` | Cross-project developer and operational helper scripts | Sprint 6 privacy, hardening, and final-review gates are enforced |
| `docs/` | Architecture, sprint records, ADRs, security, privacy, design, evidence, and runbooks | Sprint 6 implementation/evidence is complete; acceptance is recorded by the D09 review merge |
| `.github/` | Pull-request, issue, CI, quality, and security workflows | Existing gates plus Sprint 6 channel/review gates remain enforced |

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

Sprint 4 is accepted by merged PR #108 and Sprint 5 by merged PR #127. Sprint 6 was
approved for implementation on 2026-08-14 through issue #129; D01–D08 are merged and
D09 is the acceptance review. Field testing, cloud/provider activation, and spend
remain blocked unless separately approved.

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
