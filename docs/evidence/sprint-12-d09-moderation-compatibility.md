# Sprint 12 D09 — Moderation compatibility and evidence

Issue: #303

## Deterministic compatibility profile

Sprint 12 moderation is validated using repository-local code, PostgreSQL/PostGIS-backed CI, React Native unit tests, Compose validation, dependency auditing, Terraform validation, Trivy scanning, and the existing RoadTalk privacy/authorization regression suites.

The D09 compatibility gate verifies that:

- report and restriction contracts remain closed and continue to name prohibited sensitive fields;
- moderation remains restrictive-only and cannot add recipients that upstream RoadTalk authorization rejected;
- active mute/block state remains server-enforced in the existing PTT authorization pipeline;
- concurrent report and restriction creation retains generic rollback/replay behavior;
- browser/mobile moderation clients remain bounded and fail closed;
- moderation implementation code does not introduce an external network/provider client;
- backend/mobile dependency manifests do not add an external moderation or AI SDK;
- Terraform does not introduce moderation/AI cloud resources.

## Privacy and abuse evidence

Existing Sprint 12 tests cover bounded report reasons, closed schemas, no arbitrary audience targeting, server-enforced mute/block behavior, rate/replay limits, concurrent uniqueness races, generic anti-enumeration failures, and safe mobile/browser degraded states.

No report payload accepts raw location, route history, audio recording/content, transcripts, credentials, provider secrets, unrelated-user presence, arbitrary evidence, or authorization overrides.

## Cost and provider evidence

Incremental recurring implementation cost remains $0.

No external moderation or AI provider is activated. Sprint 12 uses the existing local application/PostgreSQL/PostGIS stack and GitHub CI only. No AWS moderation service, hosted AI moderation endpoint, new external account/API key, or paid moderation dependency is introduced.

## Existing compatibility gates reused

The repository CI continues to enforce:

- backend formatting, lint, type-checking and full tests;
- PostgreSQL/PostGIS migration upgrade, drift, downgrade and forward migration;
- mobile locked dependency install, Expo validation, type-checking and tests;
- Compose configuration validation including LAN configuration;
- Python and mobile dependency audits;
- historical RoadTalk privacy/scope gates;
- Terraform validation;
- Trivy dependency, secret, container and IaC scanning;
- backend container build and image scan.

## Named evidence exceptions

Physical-device moderation behavior: **not performed**.

Production/public-beta moderation behavior: **not performed**.

External moderation/AI provider behavior, quotas, privacy terms, latency, billing and outage handling: **not performed**, because no such provider is authorized or activated.

AWS/LiveKit Cloud production evidence: **not performed**.

These exceptions are intentional and must not be represented as completed evidence.
