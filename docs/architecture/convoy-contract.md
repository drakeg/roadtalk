# Convoy domain and privacy contract

Sprint 11 D02 locks the convoy domain and privacy/authorization contract before persistence, communication composition, current awareness, or browser/mobile UX.

## Domain

A convoy has an opaque UUID, bounded display name, and lifecycle state `active` or `disbanded`. Membership has an opaque membership ID, role `leader` or `member`, and state `active`, `left`, `revoked`, or `expired`.

Join requests use only an opaque invite secret. Callers cannot select a target account, recipient set, location, provider, or authorization source.

Member-visible identity is deliberately bounded to the already-public RoadTalk call sign plus account identifier, membership role, and active state. Non-active memberships are lifecycle results, not member-presence records.

## Authorization invariant

`ConvoyMembershipContext` is fixed to `context_only = true` and `authorization_source = existing_roadtalk_authorization`.

Convoy membership never creates account/session validity, location consent, current-location validity, proximity/Same-road eligibility, channel membership, recipient eligibility, or media grants. Every later Sprint 11 layer must first satisfy the existing authoritative RoadTalk rules; convoy state may only narrow or label that already-authorized result.

Invalid, unknown, left, revoked, expired, or disbanded membership fails closed and must not reveal another convoy's membership or unrelated users.

## Privacy boundary

Convoy contracts contain no raw coordinates, current/raw location payload, location or route history, heading/speed, background location/audio, private username/contact fields, password/hash, recovery material, access/refresh tokens, provider credentials, arbitrary recipient override, nearby-user enumeration, or non-member lists.

An optional membership expiry timestamp is lifecycle metadata only. It is not evidence of location, travel, arrival/departure, or route history.

## D02 exclusions

D02 adds no database tables/migrations, APIs, invite generation/storage, convoy discovery, location processing, channel/PTT behavior, browser/mobile UI, provider/network calls, cloud resources, analytics, or background execution. Those remain gated by D03 onward.

Incremental recurring cost remains $0.
