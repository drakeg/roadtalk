# Sprint 13 readiness: AI

Status: **PROPOSED — implementation blocked until this planning baseline is merged.**

## Ready conditions

- Sprints 0–12 are accepted on `main`.
- S13-R01–R12 and S13-T01–T12 are defined before implementation.
- Delivery order is locked to #317 → #318 → #319 → #320 → #321 → #322 → #323 → #324 → #325.
- AI features transform only already-authorized bounded content and cannot create communication eligibility.
- Transcription requires explicit foreground action; no automatic/background audio capture is authorized.
- No durable audio recording/content retention is authorized.
- Provider access is closed behind a disabled/test-capable abstraction.
- Local deterministic code/tests and GitHub CI are sufficient for the initially authorized implementation.
- Incremental recurring implementation cost is $0; no external/live AI/model/provider activation is authorized by D01.

## Provider approval boundary

A future change that activates a live model/provider must be separately approved and document:

- provider/model and data path;
- content retention/training policy;
- credentials/secrets handling;
- per-request and recurring cost controls;
- rate limits/quotas;
- latency/timeouts/degraded behavior;
- supported languages/capabilities;
- privacy/terms/legal implications;
- rollback/disable controls.

D01 merge alone does not authorize that activation.

## Named evidence exceptions

Physical-device behavior; microphone/OS audio behavior; suspended/killed/background execution; roaming/network behavior; live speech/AI provider latency, accuracy, quota, retention, privacy, terms and cost; production capacity/failover; AWS billing/destroy; real-world transcription/translation quality.

## Approval effect

Merge of the D01 planning PR authorizes only D02→D10 in the locked order and the deterministic/local boundaries above. It does not authorize a live AI/model provider, Sprint 14 Premium, production/public beta, durable recording, background collection or recurring spend.
