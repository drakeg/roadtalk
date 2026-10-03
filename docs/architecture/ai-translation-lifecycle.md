# Bounded translation experience

Sprint 13 D06 adds translation over already-authorized bounded text while preserving its original audience and authorization.

## Source contract

A translation accepts only a server-internal `AuthorizedTranslationSource` with opaque source ID, source kind, bounded text, explicit source language, existing RoadTalk authorization, explicit audience preservation, and bounded observation/expiry timestamps.

Supported languages remain the D02 set: `en`, `es`, `fr`, and `de`.

## Language and degraded-state behavior

The target language must differ from the source language. Unsupported languages are rejected by the closed contract. Expired source snapshots fail before provider processing, disabled/provider failures return a generic unavailable state, and oversized provider output is rejected.

## Audience and authorization preservation

Translation transforms content only. It cannot add recipients, widen a channel/convoy/PTT audience, create proximity/media eligibility, enumerate unrelated users, or change moderation/authorization decisions.

The receipt explicitly carries `audience_preserved=true` and `authorization_source=existing_roadtalk_authorization`.

## Retention boundary

D06 does not add a translation table, cache, background job, object-store reference, durable transcript/message store, or content-history aggregation. Source text and translated output remain request-scoped apart from the bounded returned receipt.

## Cost/provider boundary

D06 uses only the D03 disabled/test provider boundary. No external provider, live model, paid API, AWS AI service, background collection, durable sensitive-content expansion, or recurring spend is introduced.
