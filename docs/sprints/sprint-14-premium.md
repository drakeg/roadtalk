# Sprint 14 specification: Premium

- Planning issue: #355
- Implementation tracker: #356
- Delivery issues: #346–#354
- Baseline: Sprints 0–13 accepted.

## Objective

Deliver privacy-safe, server-authoritative Premium subscription and entitlement behavior without weakening RoadTalk authorization or activating an unapproved real-money/payment/store provider.

## Requirements

- **S14-R01 — Domain:** Define closed Premium product, subscription, entitlement, provider-state and lifecycle contracts with deterministic provenance/state semantics.
- **S14-R02 — Authorization:** Premium state may gate approved premium-only features but cannot create account/session/location/proximity/Same-road/channel/convoy/media/moderation eligibility.
- **S14-R03 — Provider boundary:** Payment/store/provider access is behind a closed abstraction with deterministic disabled/test behavior. Planning does not authorize Stripe, Apple, Google or any other live provider.
- **S14-R04 — Subscription lifecycle:** Subscription and entitlement activation, renewal, cancellation, expiry, revocation and grace semantics are explicit, bounded and server-authoritative.
- **S14-R05 — Feature gating:** Premium feature checks are centralized, auditable and fail closed; non-Premium users retain all baseline functionality not explicitly designated Premium.
- **S14-R06 — Browser/mobile:** Browser and mobile Premium experiences require explicit actions, accessible state, provenance and safe offline/provider-disabled/stale behavior.
- **S14-R07 — Idempotency/replay:** Purchase/subscription commands, provider events and entitlement transitions have deterministic replay/idempotency/concurrency handling and generic failure behavior.
- **S14-R08 — Webhook/security boundary:** Any future webhook path requires authenticity verification, bounded payloads, replay resistance, secret non-disclosure and no trust in client-asserted entitlement.
- **S14-R09 — Privacy:** No card/bank data, provider credentials, tax identifiers, raw location/route history, unrelated-user data, recovery material, analytics profiles or marketing profiles enter Premium contracts unless separately approved.
- **S14-R10 — Refund/tax/legal boundary:** Refund, cancellation, chargeback, tax collection/remittance, app-store policy and merchant-of-record responsibilities are documented before live activation; deterministic implementation does not claim those live behaviors.
- **S14-R11 — Cost/provider:** Incremental recurring implementation cost remains $0 for authorized deterministic local/CI work. Any real-money/provider/store activation requires separate explicit approval.
- **S14-R12 — Evidence:** Maintain bidirectional requirements/tests/deliverables/PR/evidence traceability and distinguish deterministic CI evidence from live-payment/store/physical-device/production exceptions.

## Acceptance tests

- **S14-T01:** Closed schemas reject unknown/sensitive Premium/payment/provider fields and unsupported product/provider states.
- **S14-T02:** Authorization tests prove Premium entitlement never creates communication eligibility or bypasses existing server authorization.
- **S14-T03:** Provider abstraction tests cover disabled/test mode, generic failures and secret non-disclosure without network activation.
- **S14-T04:** Lifecycle tests cover activation, renewal, cancellation, expiry, revocation and stale entitlement behavior.
- **S14-T05:** Feature-gating tests prove server-authoritative allow/deny behavior and preserve approved non-Premium baseline features.
- **S14-T06:** Browser/mobile tests cover accessibility, explicit actions, offline/provider-disabled state and stale clearing.
- **S14-T07:** Replay/concurrency/idempotency tests cover duplicate commands/events and generic failure behavior.
- **S14-T08:** Webhook-boundary tests prove authenticity/replay requirements remain fail closed before any future provider integration.
- **S14-T09:** Privacy tests prove no payment secrets, raw payment instruments, location history, unrelated-user data or analytics/marketing profiles leak into Premium payloads.
- **S14-T10:** Refund/cancellation/tax/store-policy evidence explicitly distinguishes deterministic logic from live provider/legal behavior.
- **S14-T11:** CI dependency/IaC/provider gates prove no live payment/store provider activation, merchant service or recurring-spend resource.
- **S14-T12:** Final traceability/evidence review covers S14-R01–R12 and named exceptions.

## Delivery order

D01 planning/readiness (#355), then strictly #346 → #347 → #348 → #349 → #350 → #351 → #352 → #353 → #354.

## Explicit exclusions

Sprint 14 planning does not authorize Stripe, Apple In-App Purchase, Google Play Billing, PayPal or other live payment/store providers; real-money transactions; card/bank/payment-instrument collection; tax collection/remittance; merchant-of-record claims; production/public beta; Sprint 15 Production implementation; tracking analytics/marketing profiles; or claims of live-provider/store/physical-device/production evidence not actually collected.
