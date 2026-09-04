# Sprint 9 D10 — Final evidence and review

Date: 2026-09-03

## Acceptance scope

This record closes S09-D10 / S09-R12 / S09-T12 for the local/GitHub-CI Sprint 9 Notifications milestone. Product-owner merge of the D10 PR accepts Sprint 9 only. It does not authorize Sprint 10 implementation.

## Bidirectional traceability

| Requirement | Acceptance test | Deliverable | PR | Primary evidence |
| --- | --- | --- | --- | --- |
| S09-R01 typed notification contract | S09-T01 | D02 | #231 | closed taxonomy, TTL, over-posting and sensitive-field contract tests |
| S09-R02 persistent account ownership | S09-T02 | D03 | #232 | registered-account ownership, persistence/API tests and private-credential exclusions |
| S09-R03 preferences and state | S09-T03 | D03 | #232 | bounded inbox/preferences, read/dismiss, expiry/deletion tests |
| S09-R04 authorization composition | S09-T04 | D04 | #234 | server-side eligible-receive composition and fail-closed authorization tests |
| S09-R05 lifecycle and idempotency | S09-T05 | D04 | #234 | replay receipt, expiry, stale/revoked/deleted lifecycle tests |
| S09-R06 urgent-alert safety contract | S09-T06 | D02 + D06 + D08 | #231, #237, #242 | locked safety copy, explicit initiation, TTL, targeting denial and abuse regression tests |
| S09-R07 provider boundary | S09-T07 | D05 | #236 | disabled/fake provider tests plus privacy/provider hard-disable gates |
| S09-R08 browser experience | S09-T08 | D06 | #237 | authenticated browser inbox/preferences/urgent-alert and accessibility regressions |
| S09-R09 mobile experience | S09-T09 | D07 | #239 | `docs/evidence/sprint-9-d07-mobile-notifications.md` and mobile notification/privacy tests |
| S09-R10 reliability and abuse resistance | S09-T10 | D08 | #242 | `docs/evidence/sprint-9-d08-urgent-alert-hardening.md`, limiter and lifecycle tests |
| S09-R11 hardening, compatibility, performance and cost | S09-T11 | D09 | #243 | `docs/evidence/sprint-9-d09-notification-hardening-scale.md`, hardening gate and named scale run |
| S09-R12 evidence and review | S09-T12 | D10 | D10 PR | this final review plus required Sprint 7/8/9 and normal CI gates |

Reverse mapping is therefore complete: D01/#230 locked R01–R12 and T01–T12; D02–D09 each implement the rows above; D10 reviews all rows and records the remaining exceptions. No D01–D10 deliverable is outside the approved requirement/test set.

## Urgent-alert safety and abuse review

The Sprint 9 urgent-alert contract remains intentionally constrained:

- RoadTalk is not an emergency service and does not dispatch or contact 911, police, fire, EMS, roadside assistance, or another guaranteed recipient.
- Delivery, receipt, reading, understanding and response are not guaranteed and must not be inferred from notification state.
- Users are directed to local emergency services directly when emergency assistance is needed.
- Alerts are explicitly user initiated, user-generated and unverified.
- Senders cannot select people, recipient IDs, exact coordinates, arbitrary radii, routes, corridors or destinations. Existing current authorization determines eligibility first; notification logic may only narrow that set.
- Urgent alerts have bounded TTL, idempotency and retry behavior. Stale, replayed, revoked and deleted state fails closed.
- Process-local account/device/peer/event rate limits and non-enumerating 429 failures reduce abuse without exposing recipient/location/eligibility information.
- Sprint 12 remains the planned location for broader moderation/reporting/mute/spam product scope; Sprint 9 does not silently expand into it.

## Privacy and security review

Notification payloads and logs remain prohibited from carrying exact other-user coordinates, exact distance/bearing, motion, route/corridor/destination/history, private usernames, passwords/recovery material, provider credentials/tokens or arbitrary audience overrides. Replay/rate-limit state is bounded and purpose-limited; the D09 limiter hashes the raw urgent event key before retaining the event dimension. No notification-derived movement history, marketing profile, cross-user engagement graph, contact sync or third-party notification analytics was introduced.

The D09 hardening gate rejects provider SDK/network/credential activation, sensitive implementation fields/logging, background location/audio capabilities, marketing analytics and spend-enabling notification dependencies. Test fixtures that merely assert forbidden runtime APIs are absent are excluded from runtime-capability scanning; production source remains covered.

## Provider, credential and cost review

Sprint 9 uses deterministic disabled/fake provider behavior only. APNs, FCM, Expo Push, SNS, Pinpoint, SES/SMS, Web Push and hosted notification brokers remain unactivated. No real provider URL, account, credential, token, payment method or recurring service is authorized or required for acceptance.

Current and incremental recurring implementation cost remains **$0**. No AWS resource, LiveKit Cloud service, paid/free-tier notification provider requiring activation/payment information, production/public-beta deployment, background location/audio service, or emergency/public-safety integration is authorized by this review.

## Accessibility and experience review

Browser and mobile experiences expose notification source, age/expiry context, preferences, read/dismiss state, urgent-alert safety language and degraded/expired behavior. Browser status uses accessible live-status behavior and native keyboard-operable controls. Mobile content includes equivalent textual status and safety semantics. Automated evidence supports these implemented in-app experiences; it does not prove every physical OS/browser notification presentation path.

## Reliability and performance review

D08 covers bounded retry behavior, idempotency collisions, rate-limit dimensions, provider failure, revocation/deletion races and non-enumerating failures within the approved single-worker/local design. Multi-worker/shared distributed rate limiting and durable external delivery queues remain outside Sprint 9 acceptance.

D09 locked a complete server-side compose p95 target of 1,500 ms before the named run. The named migrated synthetic matrix used 100 registered accounts, 25 potential recipients, 10 urgent-alert publishers and 5 opted-out recipients; 20 recipients per alert remained after preference narrowing. Recorded compose p95 was **523.2 ms**, 976.8 ms below the locked target. External push remained disabled and incremental recurring cost remained $0.

## Compatibility and evidence boundaries

Automated Sprint 9 evidence covers deterministic local/GitHub-CI behavior, migrated database behavior, in-app browser/mobile contracts, fake/disabled provider behavior, authorization/lifecycle/abuse regressions and synthetic scale. It does **not** convert the following unperformed cases into PASS:

- real APNs, FCM, Expo Push, SNS, Pinpoint, Web Push or another external provider;
- provider credentials, quotas, provider latency, provider privacy/terms or provider cost behavior;
- physical iOS/Android OS push delivery and broad physical browser notification presentation;
- suspended, killed, offline, roaming or network-transition device delivery;
- guaranteed delivery/read/acknowledgement/response or emergency-grade behavior;
- emergency-services/public-safety integration;
- multi-worker/shared rate limiting or durable external queue behavior;
- AWS/LiveKit Cloud deployment, production/public beta, regional failover or production capacity;
- background location/audio behavior;
- medical, safety, emergency or roadside-assistance effectiveness claims.

These are explicit exceptions, not deferred evidence that may be assumed successful.

## Risks and limitations

The largest remaining product limitation is that Sprint 9 notifications are primarily in-app awareness; without an approved external provider, RoadTalk cannot claim reliable awareness while an app/device is suspended or offline. The process-local limiter is appropriate to the approved local/single-worker scope but is not a distributed abuse-control system. Urgent user-generated content can still be false or misleading; the safety copy, narrow server-selected audience, expiry and rate limits reduce risk but do not verify content.

## Retrospective

Sprint 9 preserved the key architectural invariant that notification delivery never becomes an authorization engine. Separating contract, persistence, authorization composition, provider boundary, browser/mobile UX, abuse controls and hardening into ordered deliverables kept privacy and provider activation decisions reviewable. The D09 hardening work also exposed an important gate-design lesson: deny-list assertions in tests must not be confused with runtime capability activation. Future hardening gates should continue distinguishing implementation surfaces from negative test/guard surfaces.

## Product-owner acceptance boundary

Merge of the D10 PR means the product owner accepts the documented **Sprint 9 local/GitHub-CI milestone**, including the explicit limitations and unperformed evidence above. It does not authorize Sprint 10 planning or implementation, AWS or LiveKit Cloud activation, external notification provider activation/credentials, payment or recurring spend, production/public beta, background tracking/audio, emergency-services integration, or guaranteed/safety-critical delivery claims.
