# Sprint 13 specification: AI

- Planning issue: #326
- Implementation tracker: #327
- Delivery issues: #317–#325
- Baseline: Sprints 0–12 accepted.

## Objective

Deliver privacy-safe, explicitly initiated summaries, transcription and translation without broadening RoadTalk authorization or activating an unapproved AI/model/provider.

## Requirements

- **S13-R01 — Domain:** Define bounded summary, transcript and translation state with explicit provenance and deterministic lifecycle semantics.
- **S13-R02 — Consent:** Any transcription-related capture/processing requires explicit foreground user action and must never activate background audio/location collection.
- **S13-R03 — Authorization:** AI-derived state may describe or transform already-authorized content only; it cannot create new account/session/location/proximity/Same-road/channel/convoy/media/moderation eligibility.
- **S13-R04 — Audio/privacy:** No durable audio recording/content retention is authorized. Transcription must use bounded ephemeral input and bounded retained metadata/text only when explicitly permitted by the contract.
- **S13-R05 — Summaries:** Summaries operate only on authorized bounded text/transcript state and expose provenance, source scope and stale/degraded status.
- **S13-R06 — Translation:** Translation uses explicit bounded source/target languages and does not broaden audience, retention or sensitive-content scope.
- **S13-R07 — Provider boundary:** Provider/model access is behind a closed abstraction with deterministic disabled/test behavior. Planning does not authorize an external/live provider.
- **S13-R08 — Browser/mobile:** Browser and mobile experiences require explicit actions, accessible state, provenance and safe provider-disabled/offline behavior.
- **S13-R09 — Reliability/abuse:** Concurrency, replay, stale output, provider failure, oversized input and injection-like content fail safely without leaking provider/internal data.
- **S13-R10 — Privacy/security:** No credentials, recovery material, provider secrets, unrelated-user data, raw location/route history, analytics profile or background collection enters AI payloads.
- **S13-R11 — Cost/provider:** Incremental recurring implementation cost remains $0 for authorized deterministic local/CI work. Any live model/provider activation requires separate explicit approval.
- **S13-R12 — Evidence:** Maintain bidirectional requirements/tests/deliverables/PR/evidence traceability and distinguish deterministic CI evidence from physical/live-provider/production exceptions.

## Acceptance tests

- **S13-T01:** Closed schemas reject unknown/sensitive AI fields and unsupported languages/capabilities.
- **S13-T02:** Explicit consent/action tests prove no automatic/background transcription activation.
- **S13-T03:** Authorization tests prove AI output never creates communication eligibility or audience expansion.
- **S13-T04:** Ephemeral transcription lifecycle tests prove no durable audio content/recording persistence.
- **S13-T05:** Summary tests prove bounded source scope, provenance and stale-state handling.
- **S13-T06:** Translation tests prove bounded languages, source scope and audience preservation.
- **S13-T07:** Provider abstraction tests cover disabled/test mode, timeouts/failure and secret non-disclosure.
- **S13-T08:** Browser/mobile tests cover accessibility, explicit action, offline/provider-disabled state and stale clearing.
- **S13-T09:** Abuse/reliability tests cover replay, concurrency, oversized input and generic failure behavior.
- **S13-T10:** Privacy tests prove no location/audio-history/credential/provider-secret/unrelated-user leakage.
- **S13-T11:** CI dependency/IaC/provider gates prove no external/live provider activation or recurring-spend resource.
- **S13-T12:** Final traceability/evidence review covers S13-R01–R12 and named exceptions.

## Delivery order

D01 planning/readiness (#326), then strictly #317 → #318 → #319 → #320 → #321 → #322 → #323 → #324 → #325.

## Explicit exclusions

Sprint 13 planning does not authorize external/live AI or speech providers, paid APIs/models, AWS AI services, durable audio recording/content retention, background audio/location collection, production/public beta, tracking analytics, marketing profiles, Sprint 14 Premium implementation or claims of live-provider/physical-device/production evidence not actually collected.
