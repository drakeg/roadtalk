# Sprint 13 D07 evidence — browser AI experience

## Deterministic evidence

- Browser controls require explicit click actions.
- Accessible heading/label/status semantics are present.
- No microphone capture API or automatic/background timer exists.
- Closed action builders preserve existing RoadTalk authorization and bounded output settings.
- Translation explicitly preserves audience.
- Transcription action payload carries foreground-only/no-retention consent.
- Offline/provider-disabled transitions disable controls and clear stale results.
- No built-in network or provider activation path exists.
- Backend tests statically enforce the browser privacy/activation invariants.

## Requirements covered

- S13-R02 explicit foreground transcription action.
- S13-R03 authorization remains authoritative.
- S13-R06 translation audience preservation.
- S13-R08 browser accessibility, explicit actions and safe degraded behavior.
- S13-R10 sensitive payload fields remain excluded.
- S13-R11 incremental recurring implementation cost remains $0.

## Evidence exceptions — NOT PERFORMED

No cross-browser physical interaction matrix, assistive-technology lab session, real microphone capture, live provider/network behavior, production deployment, public beta or external-provider privacy/billing behavior is claimed.
