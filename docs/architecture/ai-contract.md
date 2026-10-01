# AI domain, consent and privacy contract

Sprint 13 AI transforms already-authorized RoadTalk content. It does not create communication eligibility, widen an audience, activate a provider, or authorize background collection.

## Capability vocabulary

The approved capability vocabulary is bounded to:

- `transcription`
- `summary`
- `translation`

Lifecycle state is bounded to `requested`, `ready`, `unavailable`, and `expired`.

## Consent boundary

Transcription-related processing requires explicit user initiation in the foreground. The contract fixes:

- `user_initiated=true`
- `foreground_only=true`
- `background_capture=false`
- `durable_audio_retention=false`

D02 does not define or persist an audio payload. Ephemeral audio handling remains D04 work and may not weaken these invariants.

## Authorized-source boundary

Summaries and translations reference an already-authorized bounded RoadTalk text source. The source contract fixes `authorized_only=true` and `authorization_source=existing_roadtalk_authorization`. AI state cannot grant access to a message, transcript, channel, convoy, participant, media stream, or recipient that existing RoadTalk authorization denied.

## Language and output bounds

The initial deterministic contract supports `en`, `es`, `fr`, and `de`. Translation requires distinct source and target languages. Summary and translation outputs have explicit maximum character counts to avoid unbounded model/provider payloads in later work.

Expansion of the supported language set is a contract change that requires tests and review.

## Privacy boundary

AI commands and result metadata prohibit raw/durable location or route history, audio recordings/URLs/bytes, background audio/location fields, microphone streams, credentials/recovery material, provider secrets, model/provider selectors, arbitrary prompts/system prompts, arbitrary audience selectors, authorization/enforcement overrides, tracking identifiers, analytics profiles and marketing profiles.

## Provider boundary

The D02 contract permits only `disabled` and deterministic `test` provider modes in result metadata. No live external model/provider, API key, network activation, paid API, AWS AI service or recurring-spend dependency is authorized.

## Persistence boundary

D02 defines schemas only. It does not create database tables, retain audio/content, introduce transcript persistence, call a provider, or add browser/mobile AI behavior. Those later deliverables must preserve this contract.
