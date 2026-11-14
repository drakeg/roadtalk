# Public-beta launch authorization contract

Sprint 16 owner: S16-D02 / #477.

## Default state

The machine-readable launch authorization file is deliberately committed in a disabled state.
Every live-action authorization is `false`, allowed traffic is zero, and no approver, live
artifact, live Terraform plan, hostname, DNS change, or expiry is recorded.

This means repository merge alone cannot be interpreted as launch approval.

## Enabling authorization

A future authorized launch record must include:

- a unique approval ID;
- a named human approver;
- approval and expiry timestamps;
- an expiry no more than 24 hours after approval;
- an explicit scope listing every enabled authorization;
- an approval reason;
- the exact immutable release digest;
- the exact Terraform plan SHA-256;
- a distinct exact rollback digest;
- an explicit bounded traffic percentage;
- hostname and DNS change ID whenever DNS cutover is authorized.

The validator fails closed if an enabled action is not represented in the approval scope.

## Separately scoped actions

Public beta, production traffic, DNS cutover, recurring spend, real-money flows, provider
activation, and destructive changes are independent authorization flags. Approval for one does
not implicitly approve another.

## Rollback safety

Any future authorization continues to require a named exact rollback target, health-gated
cutover, rollback on failed health, emergency disable, and provider kill switch.

## Evidence boundary

S16-D02 validates the authorization mechanism only. It does not authorize or claim a live public
beta, traffic shift, DNS cutover, provider activation, recurring spend, or destructive operation.

Source: `infrastructure/environments/production/launch-authorization.json`  
Validator: `scripts/ci/check-public-beta-authorization.py`
