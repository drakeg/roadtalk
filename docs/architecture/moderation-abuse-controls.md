# Sprint 12 abuse and rate-limit controls

D05 keeps abuse prevention deterministic and local for the approved single-worker evidence environment. It does not add Redis, an external moderation service, provider credentials, or recurring spend.

## Report attempts

`ModerationReportLimiter` applies independent sliding-window limits to authenticated account, device, network peer and account-scoped event/replay key dimensions. Event keys are SHA-256 hashed before they become bucket identifiers. The limiter returns one generic error and bounded retry-after value rather than exposing which dimension was exhausted.

Report persistence remains independently idempotent through the reporter-scoped hashed idempotency key introduced in D03. A rate limit therefore cannot turn a replay into a second stored report.

## Communication attempts

Existing `PttLimiter` independently bounds receive and transmit attempts across peer, account and device dimensions. Existing grant idempotency and active-grant lifecycle checks bound replay/concurrent communication attempts. D04's mute/block filter is evaluated only after upstream communication eligibility, so retries cannot bypass moderation restrictions.

Urgent alerts retain their existing account/device/peer/event limiter. Together these controls provide the Sprint 12 bounded account/device/peer/event dimensions without introducing a new network dependency.

## Limitations

These in-memory buckets intentionally match RoadTalk's locked local/single-worker evidence environment. They are not claimed as production-distributed rate limiting. Multi-worker/distributed enforcement remains outside the current $0 Sprint 12 scope and must be re-evaluated before production deployment.
