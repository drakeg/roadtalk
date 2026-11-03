# Sprint 14 D09 evidence — compatibility, tax/refund and cost/provider boundaries

## Deterministic evidence

- Executable compatibility contract records Python 3.14, Node 26, React Native 0.86 and Expo 57.
- Supported Premium provider modes are limited to disabled/test.
- Field-test and production configuration already reject non-disabled Premium providers.
- Refund, chargeback, tax, app-store-policy and merchant-of-record responsibilities are represented only as live-approval-required boundaries.
- Deterministic cancellation semantics do not claim provider-side cancellation or refund execution.
- Incremental recurring implementation cost is fixed at $0 by the boundary contract.
- No live payment/store provider, billing credential or merchant service is introduced.

## Requirements covered

- S14-R10 / T10 — refund, cancellation, chargeback, tax/store and merchant-of-record responsibilities are explicitly separated from deterministic lifecycle behavior.
- S14-R11 / T11 — compatibility/provider configuration remains local/test only and recurring implementation cost remains $0.
- S14-R12 — evidence names live-provider/store/production exceptions rather than treating CI as live evidence.

## Evidence exceptions — NOT PERFORMED

No Stripe, Apple IAP, Google Play Billing, PayPal or other provider integration; no real payment instrument; no refund, chargeback or tax transaction; no merchant-of-record determination; no provider/store fees; no sandbox or production billing account; no physical-device store purchase; and no production/public-beta operation is claimed.
