# Notification contract

Sprint 9 D02 locks notification taxonomy, public payload minimization, expiry semantics, and the urgent-alert safety boundary before persistence, provider delivery, or UI implementation.

## Closed classes

RoadTalk has exactly three Sprint 9 notification classes:

- `account`: account/session/security state that the authenticated account is allowed to know;
- `channel_activity`: current channel/activity awareness that has already passed the existing server authorization rules;
- `urgent_alert`: an explicitly user-initiated, short-lived RoadTalk community alert.

Unknown classes and unexpected fields are rejected.

## Public fields

Account notices expose class, priority, source, title, message, issued time, and expiry time. Channel activity adds only the authorized display label for the channel. Urgent alerts expose class, urgent priority, user-generated source, bounded message, issued time, expiry time, and fixed safety semantics.

The notification contract contains no recipient/account/device identifier, private username, credential, recovery material, push/provider token, raw coordinate, arbitrary radius, exact distance/bearing, motion, route/corridor, destination, or history field.

Recipient selection is not part of this contract. Later Sprint 9 authorization work must derive recipients server-side from existing current account/session/location/channel/Same-road rules and may only narrow those existing audiences.

## Lifetime limits

- Account notices: at most 7 days.
- Channel activity: at most 2 hours.
- Urgent alerts: at most 10 minutes.

Issue and expiry timestamps must include an explicit timezone. Expiry must be after issue
time. A retry or replay must never turn an old urgent alert into a fresh event;
lifecycle/idempotency enforcement is implemented in later locked deliverables.

## Urgent-alert command

The user-initiated command accepts only:

- a message of 1–280 characters; and
- a 16–128 character transport-safe idempotency key using only letters, digits, `.\`,
  `_\`, `~\`, and `-\`.

There is deliberately no recipient, person, account, device, coordinate, radius, route, provider, or delivery control.

## Mandatory urgent-alert safety semantics

Every urgent-alert payload fixes these statements/flags and callers cannot override them:

- `RoadTalk is not an emergency service.`
- `Delivery is not guaranteed.`
- `Contact local emergency services directly when emergency assistance is needed.`
- `This alert is user-generated and unverified.`
- `verified = false`
- `emergency_service = false`
- `delivery_guaranteed = false`

A delivery/read result must never be described as proof that a person saw, understood, or acted on an alert.

## Explicit exclusions

D02 does not introduce persistence, recipient selection, push delivery, background work, external providers, emergency dispatch, automatic crash/medical/panic detection, public-safety integration, background location/audio, marketing, analytics, or notification-derived movement history.

The Sprint 9 $0/local-GitHub-CI and provider-disable boundaries remain unchanged.
