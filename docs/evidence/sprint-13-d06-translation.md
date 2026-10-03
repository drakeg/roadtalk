# Sprint 13 D06 evidence — bounded translation

## Deterministic evidence

- Translation is restricted to authorized bounded transcript/message-window text snapshots.
- Source and target languages are explicit and must differ.
- Expired sources fail before provider processing.
- Sensitive over-posting fields and audience overrides are rejected.
- Provider failures are normalized and non-disclosing.
- Oversized source or output text is rejected.
- Returned receipts preserve source provenance, language metadata and audience/authorization invariants.
- No durable translation/message/transcript persistence or background processing is introduced.

## Requirements covered

- S13-R03 authorization remains authoritative.
- S13-R06 bounded translation with explicit source/target languages and audience preservation.
- S13-R07 disabled/test provider boundary remains unchanged.
- S13-R09 stale/provider/oversize behavior fails safely.
- S13-R10 location/audio/credential/provider/audience leakage remains excluded.
- S13-R11 incremental recurring implementation cost remains $0.

## Evidence exceptions — NOT PERFORMED

No live-provider translation quality, production latency, billing/quota behavior, physical-device UX, or external provider privacy/retention behavior is claimed.
