# Premium compatibility, tax/refund and cost/provider boundaries

Sprint 14 D09 turns the remaining live-provider/legal/cost assumptions into explicit deterministic contracts.

## Compatibility baseline

RoadTalk Premium is validated only against the currently supported application baseline:

- Python 3.14
- Node.js 26
- React Native 0.86
- Expo SDK 57
- Premium provider modes: disabled or deterministic test only

Repository dependency policy prevents independent upgrades that would break this baseline. A future React Native / Expo platform migration must move the coordinated package family together and collect fresh compatibility evidence.

## Refund, cancellation, chargeback and tax responsibilities

The deterministic Premium lifecycle may model cancellation and entitlement expiry, but it does not claim to execute a provider refund, chargeback reversal, tax calculation, tax collection/remittance, app-store policy action or merchant-of-record responsibility.

Each of the following remains a separate live-activation responsibility:

- cancellation execution at a payment/store provider;
- refunds and partial refunds;
- chargebacks/disputes;
- sales tax, VAT or other tax determination/collection/remittance;
- Apple/Google/other store policy compliance;
- merchant-of-record designation and obligations.

Those responsibilities require separate approval before implementation against a live provider.

## Cost/provider boundary

The authorized Sprint 14 implementation has incremental recurring implementation cost of **$0**. Premium has no Stripe, Apple IAP, Google Play Billing, PayPal or other live payment/store SDK or credential path.

The only supported Premium provider states remain disabled and deterministic local/test. Field-test and production configuration reject any non-disabled Premium provider.

Any live-provider/store activation must separately approve and document pricing, fees, billing ownership, recurring spend, secrets, sandbox/production separation, webhook handling, refunds, taxes, legal responsibility and rollback controls.

## Evidence interpretation

CI evidence proves deterministic compatibility and boundary behavior only. It does not constitute live payment, store, tax, merchant-of-record, provider billing, production or physical-device purchase evidence.
