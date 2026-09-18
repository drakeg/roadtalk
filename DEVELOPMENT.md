# RoadTalk Development Guide

## Active scope

RoadTalk has accepted Sprints 0–10. The current repository `main` branch is the source of truth for accepted behavior.

Sprint 11 implementation is not authorized merely because Sprint 10 is complete. A new sprint begins only after its specification/readiness gate is approved. Corrective or backlog work outside a new sprint must be tied to an existing approved issue or an explicit planning decision and must preserve accepted sprint privacy, authorization, provider, compatibility, and cost boundaries.

## Required workflow

1. Start from current `main`.
2. Select an approved sprint/tracker issue or separately approved corrective/backlog issue.
3. Confirm dependencies, acceptance criteria, privacy/security boundaries, and cost/provider constraints.
4. Create a focused branch.
5. Keep the change limited to one coherent deliverable or reviewable dependency slice.
6. Update implementation, automated tests, and affected documentation together.
7. Run every check documented by the affected component plus relevant regression/privacy/security gates.
8. Open a pull request that links the issue, requirements, tests, documentation, and evidence.
9. Merge only after required checks and review pass.
10. Update tracker/evidence records when applicable; do not close dependent work prematurely.

Do not begin a later sprint from roadmap position alone. The sprint-specific planning/readiness record controls authorization.

## Local dependencies

The local PostgreSQL/PostGIS service and optional Redis profile are documented in the [local development runbook](docs/runbooks/local-development.md).

Quick start:

```sh
make setup
make up
make verify-database
```

This builds the backend, migrates PostgreSQL/PostGIS, and starts the API at
`http://localhost:8000` without creating AWS resources. You may also run the same
stack directly with `docker compose up --build`; local-safe defaults make `.env`
optional for that command.

## Component guides

- [Mobile](mobile/README.md)
- [Backend](backend/README.md)
- [Infrastructure](infrastructure/README.md)
- [Scripts](scripts/README.md)
- [Documentation](docs/README.md)

## Secrets and configuration

- Never commit credentials, tokens, private keys, Terraform state, or populated environment files.
- Commit only redacted/example configuration.
- Mobile builds never contain server or media-provider secrets.
- Terraform references approved secret stores instead of receiving plaintext secrets.
- Logs and test fixtures must not contain real user, location, credential, or audio data.
- Local example credentials must never be reused outside a developer machine.

## Repository quality

All text uses UTF-8 and LF line endings. Formatters and linters must respect `.editorconfig`.

Generated dependencies, build output, local runtime data, reports, populated environment files, and Terraform state are excluded by `.gitignore`.

For every behavioral change, review the affected API/browser/mobile/operator documentation and regression tests. Update them in the same pull request whenever behavior, routes, contracts, configuration, operational steps, or acceptance evidence changed.

## Definition of done for a change

- linked approved sprint/tracker requirement or corrective/backlog issue
- scoped implementation
- acceptance and regression tests updated and passing
- affected documentation updated and checked for stale references
- security/privacy/provider/cost impact reviewed
- no unauthorized later-sprint feature leakage
- tracker/evidence updated when applicable
- pull request approved and merged
