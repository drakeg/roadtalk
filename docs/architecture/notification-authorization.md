# Notification authorization and lifecycle composition

Sprint 9 notification delivery composes **after** RoadTalk's existing authorization. It is
not a new discovery or targeting system.

## Audience source

Channel-activity and urgent-alert audience composition starts only from
`find_eligible_receive_grants()`. That existing PTT authorization path already requires
current account/session/device state, the selected enabled channel, private membership
where required, foreground location consent, a current usable location, the configured
proximity policy, a current receive grant, and Same-road filtering when either side has
selected Same-road mode.

The notification layer receives that already-authorized set and may only narrow it:

- duplicate receive grants are collapsed to one account-owned inbox item;
- only active registered accounts can receive Sprint 9 account-owned inbox content;
- `channel_activity_enabled=false` removes channel-activity delivery;
- `urgent_alert_enabled=false` removes urgent-alert delivery.

No notification code can add an account absent from the upstream eligible set. Clients do
not submit account/device IDs, coordinates, radius, route/corridor, audience membership,
or provider references.

## Current-state failure behavior

Audience composition fails closed when the sender account/session/device is no longer
current, the selected channel is unavailable, the channel context does not match the
notification event, the sender location/consent is unavailable to the upstream proximity
policy, or the upstream authorized audience is empty. Existing recipient account/session,
channel, location, consent, receive-grant and Same-road denials therefore remain denials.

No notification-derived location, route, audience-membership, or delivery-history table is
created.

## Idempotency and bounded replay receipts

Current delivery uses a caller-generated idempotency key. The key itself is never stored.
For each eligible account RoadTalk stores only:

- the owning account ID;
- SHA-256 of the idempotency key;
- SHA-256 of the semantic notification payload;
- an optional reference to the current inbox row; and
- a bounded guard-expiry timestamp.

The receipt does not contain sender identity, device identity, eligible-set membership,
message copy, channel authorization evidence, coordinates, distance, route/corridor,
destination, provider data, or engagement/read state.

A same-key/same-payload retry returns the original current inbox row. A same-key/different-
payload retry fails with an idempotency conflict. If the original inbox row has been
deleted while its replay guard remains, retry fails closed instead of recreating it. An
already-expired payload is rejected as not current. Replay guards are removed after their
bounded lifetime, while the payload's own issued/expiry timestamps prevent an old event
from becoming fresh again.

Account deletion cascades both inbox content and replay receipts. Inbox reads retain the
D03 behavior of deleting expired notification rows and do not depend on a worker.

## Privacy and cost boundary

Recipient membership remains transient during composition and is never returned by the
notification API. No external push provider, queue, worker, cache, AWS resource, LiveKit
Cloud resource, background location/audio, or recurring spend is introduced by D04.
