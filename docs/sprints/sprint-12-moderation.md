# Sprint 12 specification: Moderation

- Planning issue: #305
- Implementation tracker: #306
- Delivery issues: #296–#304
- Baseline: Sprints 0–11 accepted.

## Objective

Deliver privacy-safe reporting, server-enforced mute/block behavior and spam prevention without making moderation state a new authorization source or introducing sensitive evidence collection.

## Requirements

- **S12-R01 — Domain:** Define bounded report, mute/block and enforcement state with deterministic lifecycle semantics.
- **S12-R02 — Authorization:** Moderation state may deny/narrow behavior only; existing account/session, location/current-state, proximity/Same-road, channel, convoy and media authorization remain authoritative.
- **S12-R03 — Reporting:** Reports use bounded reason categories/metadata, ownership, idempotency and retention/deletion rules; no arbitrary sensitive evidence payload.
- **S12-R04 — Mute/block:** Server-enforced mute/block decisions fail closed and cannot be bypassed by client state, channel, convoy or media grants.
- **S12-R05 — Spam prevention:** Apply bounded multidimensional rate/replay/concurrency controls appropriate to the existing local/single-worker evidence environment.
- **S12-R06 — Privacy:** No raw/durable location/route history, audio recording/content, credentials/recovery material, provider secrets, unrelated-user presence, tracking analytics or marketing profile.
- **S12-R07 — Browser:** Accessible report/mute/block UX with confirmation, closed schemas and safe degraded states.
- **S12-R08 — Mobile:** Equivalent mobile moderation UX without background collection or client-side authorization broadening.
- **S12-R09 — Reliability/abuse:** Concurrent/stale/revoked transitions and enumeration attempts fail safely with privacy-preserving errors.
- **S12-R10 — Compatibility:** Preserve accepted Sprint 0–11 API/privacy/provider behavior and document degraded/offline limitations.
- **S12-R11 — Cost/provider:** Incremental recurring cost $0 using local Docker/PostgreSQL/PostGIS and GitHub CI; no external moderation/AI/cloud activation.
- **S12-R12 — Evidence:** Maintain bidirectional requirements/tests/deliverables/PR/evidence traceability and distinguish deterministic CI evidence from named physical/production/provider exceptions.

## Acceptance tests

- **S12-T01:** Closed contract/schema tests reject unknown/sensitive report and moderation fields.
- **S12-T02:** Authorization composition proves moderation never broadens upstream eligibility.
- **S12-T03:** Report lifecycle/idempotency/retention/deletion tests fail closed.
- **S12-T04:** Server mute/block regressions cover channel, convoy, PTT/media and revocation transitions.
- **S12-T05:** Spam/rate/replay/concurrency controls are bounded and deterministic.
- **S12-T06:** Privacy/enumeration tests prove no prohibited location/audio/credential/provider data or unrelated-user leakage.
- **S12-T07:** Browser accessibility, confirmation, over-posting and degraded-state tests.
- **S12-T08:** Mobile offline/revoked/degraded/accessibility regressions.
- **S12-T09:** Race/stale/revocation/anti-enumeration hardening tests.
- **S12-T10:** Full backend/mobile/security/migration/schema-drift/Compose/IaC compatibility gates.
- **S12-T11:** Automated dependency/provider/cost gates prove zero external activation and zero new Terraform resources.
- **S12-T12:** Final traceability/evidence review covers S12-R01–R12 and named exceptions.

## Delivery order

D01 planning/readiness (#305), then strictly #296 → #297 → #298 → #299 → #300 → #301 → #302 → #303 → #304.

## Explicit exclusions

Sprint 12 does not authorize AWS or LiveKit Cloud, external moderation/AI providers, production/public beta, payment methods, background location/audio, audio recording/content retention, raw/durable movement history, tracking analytics, marketing profiles, or Sprint 13 implementation.
