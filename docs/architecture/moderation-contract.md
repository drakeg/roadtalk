# Moderation domain and privacy contract

Sprint 12 moderation is a restrictive safety layer. It does not create communication eligibility.

## Bounded report contract

Reports identify the authenticated reporter implicitly in later persistence/API work and contain only a subject account, bounded reason category, transport-safe idempotency key, lifecycle state and timestamps. Arbitrary narrative, attachments, audio/transcripts, location evidence and provider-controlled fields are excluded from the approved contract.

## Restriction contract

Mute/block state is pairwise restrictive context. It may deny or narrow behavior that RoadTalk's existing account/session, foreground-location/current-state, proximity/Same-road, channel, convoy and media rules would otherwise authorize. It cannot restore or independently grant eligibility.

## Privacy boundary

Moderation contracts prohibit raw/durable location or route history, audio content/recordings/transcripts, background collection, credentials/recovery material, provider secrets, arbitrary audience selectors, unrelated-user enumeration, moderator free text and authorization/enforcement overrides.

## Lifecycle vocabulary

Reports: `submitted`, `closed`, `withdrawn`.

Restrictions: `mute` or `block`; state `active`, `revoked`, or `expired`.

Persistence, retention/deletion and enforcement implementation remain D03/D04 work; this D02 contract does not activate a provider or external service.
