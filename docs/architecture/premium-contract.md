# Premium domain and privacy contract

Sprint 14 D02 defines provider-neutral Premium state without activating billing.

## Domain

Premium state is account-owned and server-authoritative. The closed domain includes:

- account tier: `free` or `premium`;
- subscription states: inactive, active, grace, canceled, expired and revoked;
- entitlement states: inactive, active, expired and revoked;
- provider mode: disabled or deterministic test only.

No price, currency, SKU, checkout URL, store identifier or provider-specific transaction model is introduced in D02.

## Authorization invariant

Premium may later gate approved premium-only features, but Premium state cannot create or broaden RoadTalk account/session/location/proximity/Same-road/channel/convoy/media/moderation authorization.

The entitlement contract fixes `communication_authorization_unchanged=true` and retains `authorization_source=existing_roadtalk_authorization`.

## Privacy boundary

Closed schemas reject raw payment instruments, payment tokens, billing addresses, tax identifiers, provider/webhook secrets, receipts/transaction IDs, raw location/route history, unrelated-user selectors, credentials, analytics profiles and marketing profiles.

## Provider and cost boundary

Only `disabled` and `test` provider modes are representable. No live payment/store provider, real-money transaction, recurring service or cloud resource is introduced.
