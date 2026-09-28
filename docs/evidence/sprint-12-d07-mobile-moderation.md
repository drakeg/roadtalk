# Sprint 12 D07 — mobile moderation evidence

The native Safety screen uses the authenticated RoadTalk moderation endpoints introduced in D06. It supports report (one bounded reason and opaque idempotency key), mute, block, review of the current account's active restrictions, and confirmed unmute/unblock.

The screen has no background location, microphone, audio, route, analytics, or external moderation provider integration. It does not make client-side eligibility decisions: the D04 server-side moderation filter and existing session/current-location/proximity/channel/convoy/media authorization remain authoritative.

Confirmation precedes report, mute, block, and revocation. Input must be a UUID. Status messages are in an accessibility live region and actions have accessible labels. Offline, revoked, unauthenticated, and failed refresh states clear displayed restriction data, disable unauthenticated actions, and never imply that server-side restrictions have been lifted. Errors do not disclose target existence or moderation state.

Automated tests cover closed request payloads, authenticated transport, generic unavailable errors, confirmation before mutation, stale-state clearing, and signed-out denial. Physical-device accessibility, background/suspended lifecycle, real network transitions, and real-world moderation staffing remain named evidence exceptions for later review.
