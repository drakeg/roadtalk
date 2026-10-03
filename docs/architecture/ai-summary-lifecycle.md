# Bounded conversation summaries

Sprint 13 D05 adds deterministic summaries over already-authorized bounded text. It does not create a message/transcript store or a new authorization path.

## Source contract

A summary accepts only a server-internal `AuthorizedSummarySource` with:

- opaque source ID;
- source kind `transcript` or `message_window`;
- bounded text up to 8,000 characters;
- bounded language;
- `authorized_only=true`;
- `authorization_source=existing_roadtalk_authorization`;
- timezone-aware observation and expiry timestamps.

The source is a transient snapshot produced after existing RoadTalk authorization has already been applied. It is not a client-supplied authorization assertion.

## Stale/degraded behavior

Expired source snapshots fail closed before the AI provider boundary is called. Disabled/provider failures return a generic summary-unavailable error. A provider result that exceeds the requested output bound is rejected.

## Provenance

The returned receipt carries source ID, source kind, source language, source expiry, generation time and existing-authority marker. This makes summary provenance explicit without exposing unrelated users, movement history, provider internals or a larger conversation audience.

## Retention boundary

D05 does not add a database model, summary table, transcript table, message table, cache, object-store reference or background summarization job. Source text and provider input remain request-scoped. The receipt contains bounded summary text only.

## Authorization and audience

A summary can describe only the source already authorized to the caller. It cannot create channel membership, PTT/media permission, proximity eligibility, convoy membership, moderation authority, recipient expansion or unrelated-user enumeration.

## Cost/provider boundary

D05 uses only the D03 disabled/test provider modes. No live model/provider, network activation, paid API, AWS AI service, recurring spend, background collection or durable audio/content retention is introduced.
