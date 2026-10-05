# Sprint 13 D08 evidence — mobile AI experience

## Deterministic evidence

- Summary/translation/transcription actions require explicit user presses.
- Transcription action carries foreground-only/no-retention consent.
- React Native AppState disables AI and clears stale results outside the foreground.
- Offline/provider-disabled states clear stale results and disable actions.
- Translation action preserves audience and explicit source/target language state.
- Closed mobile action objects carry existing RoadTalk authorization only.
- Jest tests cover explicit action, translation audience/language behavior, consent and degraded-state clearing.
- Backend static privacy tests reject background/capture and sensitive-field regressions.
- The AI screen is reachable from the existing RoadTalk navigator/home but defaults fail-closed.

## Requirements covered

- S13-R02 explicit foreground action/no background capture.
- S13-R03 existing authorization remains authoritative.
- S13-R06 translation audience preservation.
- S13-R08 mobile accessibility, explicit action and degraded behavior.
- S13-R10 sensitive location/audio-history/credential/provider/audience fields excluded.
- S13-R11 incremental recurring implementation cost remains $0.

## Evidence exceptions — NOT PERFORMED

No physical-device accessibility lab, OS suspend/kill matrix, real microphone capture, live provider/network behavior, production deployment, public beta or external-provider privacy/billing behavior is claimed.
