# Sprint 14 readiness: Premium

Status: **PROPOSED — implementation blocked until this planning baseline is merged.**

## Ready conditions

- Sprints 0–13 are accepted on `main`.
- S14-R01–R12 and S14-T01–T12 are defined before implementation.
- Delivery order is locked to #346 → #347 → #348 → #349 → #350 → #351 → #352 → #353 → #354.
- Premium entitlement remains server-authoritative and cannot create or broaden RoadTalk communication eligibility.
- Payment/store/provider access is closed behind a disabled/test-capable abstraction.
- No client may self-assert Premium entitlement.
- Raw payment instruments, provider credentials, tax identifiers and unrelated-user data are excluded from Premium contracts.
- Refund/cancellation/tax/store-policy responsibilities are evidence boundaries until a live provider is separately approved.
- Local deterministic code/tests and GitHub CI are sufficient for the initially authorized implementation.
- Incremental recurring implementation cost is $0; no real-money/provider/store activation is authorized by D01.

## Provider approval boundary

A future change that activates Stripe, Apple, Google or another live payment/store provider must be separately approved and document:

- provider/store and merchant-of-record relationship;
- checkout/purchase data path and fields;
- provider/store credentials and secret handling;
- webhook/event authenticity and replay controls;
- product IDs, pricing, currencies and environments;
- refunds, cancellations, renewals, grace periods and chargebacks;
- taxes, VAT/sales-tax collection/remittance and legal responsibility;
- app-store policy implications;
- sandbox/test versus production account separation;
- rate limits/outages/degraded behavior;
- cost/fees and recurring spend;
- rollback/disable controls;
- privacy, retention, terms and support obligations.

D01 merge alone does not authorize that activation.

## Named evidence exceptions

Physical-device store purchase behavior; App Store/Google Play sandbox and production billing; live Stripe/other provider checkout; real payment instruments; provider webhooks; taxes/refunds/chargebacks; roaming/network behavior; production/public-beta operation; provider fees/billing; production capacity/failover; AWS billing/destroy.

## Approval effect

Merge of the D01 planning PR authorizes only D02→D10 in the locked order and the deterministic/local boundaries above. It does not authorize a live payment/store provider, real-money transactions, tax collection/remittance, Sprint 15 Production, production/public beta or recurring spend.
