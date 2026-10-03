# Ephemeral transcription lifecycle

Sprint 13 D04 adds a bounded transcription lifecycle that composes with existing RoadTalk PTT authorization and the D03 deterministic AI provider boundary.

## Authorization source

Transcription requires an already-active, caller-owned `MediaGrant` with:

- matching account and device;
- the requested transmit-grant ID;
- `grant_kind=transmit`;
- `action_scope=microphone_publish`;
- no revocation;
- an expiry after the current server time.

This lifecycle does not create or refresh a PTT grant, channel membership, proximity decision, media permission, convoy authorization or moderation decision. If the existing transmit grant is absent, stale, revoked or belongs to another account/device, transcription fails closed.

## Consent and foreground boundary

The caller must provide the D02 `ForegroundConsent` contract. Its invariants remain fixed to explicit user initiation, foreground-only operation, no background capture and no durable audio retention.

D04 does not add an API route that starts capture automatically and does not add background jobs, microphone daemons or scheduled audio processing.

## Ephemeral audio boundary

Audio is accepted only as the D03 bounded in-memory `ephemeral_audio` request and passed directly through the AI provider boundary. It is never added to a database model, receipt, audit record, URL, object-storage reference or durable file.

The returned receipt contains only request/grant IDs, bounded transcript text, language, deterministic provider mode, completion time and explicit false retention/background flags.

## Failure behavior

Missing/stale/revoked authorization fails with `AI_TRANSCRIPTION_NOT_AUTHORIZED`. Disabled or failed provider behavior is normalized to `AI_TRANSCRIPTION_UNAVAILABLE`. Provider internals are not exposed.

## Cost/provider boundary

D04 uses only the already-approved disabled/test provider modes. No external speech/AI service, provider credential, paid API, network activation, AWS AI resource, background collection or recurring spend is introduced.
