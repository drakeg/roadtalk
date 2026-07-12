# RoadTalk Development Guide

## Active scope

Sprint 1 — Project Foundation is active. The approved specification is `docs/sprints/sprint-1-project-foundation.md`.

Do not implement profile/callsign, continuous location, PTT, proximity, channels, maps, notifications, or any later-sprint behavior.

## Required workflow

1. Select an open Sprint 1 issue from tracker #33.
2. Confirm dependencies and acceptance tests.
3. Branch from current `main` using `sprint/1-<description>`.
4. Keep the change limited to one coherent deliverable or reviewable dependency slice.
5. Run every check documented by the component.
6. Open a pull request that links the issue, requirements, tests, and evidence.
7. Merge only after required checks and review pass.
8. Update tracker/evidence; do not close dependent work prematurely.

## Component guides

- [Mobile](mobile/README.md)
- [Backend](backend/README.md)
- [Infrastructure](infrastructure/README.md)
- [Scripts](scripts/README.md)
- [Documentation](docs/README.md)

Each component guide currently describes ownership and boundaries. Executable setup commands arrive with the deliverable that creates the component; placeholders must not claim a working setup.

## Secrets and configuration

- Never commit credentials, tokens, private keys, Terraform state, or populated environment files.
- Commit only redacted/example configuration.
- Mobile builds never contain server or media-provider secrets.
- Terraform references approved secret stores instead of receiving plaintext secrets.
- Logs and test fixtures must not contain real user, location, credential, or audio data.

## Repository quality

All text uses UTF-8 and LF line endings. Formatters and linters introduced by later Sprint 1 deliverables must respect `.editorconfig`.

Generated dependencies, build output, local runtime data, reports, and Terraform state are excluded by `.gitignore`.

## Definition of done for a change

- linked Sprint 1 requirement and deliverable
- scoped implementation
- acceptance and regression tests
- documentation updated
- security/privacy impact reviewed
- no later-sprint feature leakage
- pull request approved and merged
