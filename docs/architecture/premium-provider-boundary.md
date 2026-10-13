# Premium provider boundary

Sprint 14 D03 introduces a closed payment/subscription provider abstraction without activating billing.

## Modes

The provider boundary supports only `disabled` and deterministic `test` behavior.

- Disabled mode fails closed with a stable non-disclosing error.
- Fake mode is allowed only in local/test environments.
- Field-test and production environments reject fake activation.
- No live provider mode is representable.

## Request and result boundary

Provider requests contain only a request ID, RoadTalk account ID and the bounded operation `subscription_status`.

Provider results contain only request/account identity, bounded subscription state and deterministic test provenance. The boundary verifies request/account identity and provider provenance before returning a result.

No card/bank data, payment method/token, checkout URL, receipt, transaction ID, provider credential, webhook secret, tax data, location or unrelated-user data is accepted or returned.

## Failure behavior

Provider exceptions, timeouts and integrity mismatches are normalized to `Premium provider unavailable`; provider-internal details are not surfaced.

## Cost/provider boundary

No Stripe, Apple, Google, PayPal or other payment/store SDK, endpoint, credential, account or recurring service is added.
