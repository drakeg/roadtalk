# Sprint 15 readiness: Production

Status: **PROPOSED — implementation blocked until the D01 planning PR is merged.**

## Ready conditions

- Sprints 0–14 are accepted on `main`.
- S15-R01–R12 and S15-T01–T12 are defined before production implementation.
- Delivery order is locked to #445 → #446 → #447 → #449 → #450 → #451 → #452 → #453 → #454.
- Production environment and release artifacts are explicitly separated from local/test/field-test.
- Production secrets and CI/CD identity must not rely on shared static credentials.
- Health, logging, metrics and alerts must remain privacy-bounded.
- Backup/restore, rollback and disable controls are required before any launch approval.
- Security/privacy gates fail closed on unresolved high-risk findings.
- External payment/store/provider activation remains separately gated.
- Recurring spend and operational ownership must be documented before approval.
- CI/local evidence is not sufficient to claim live load, failover, disaster recovery, billing or real-user production behavior.

## Production approval boundary

A future change that actually enables production/public-beta traffic must separately demonstrate or explicitly waive, with recorded approval:

- production domain/TLS/DNS ownership and cutover plan;
- deployment identity, artifacts and rollback target;
- secrets/IAM rotation and break-glass handling;
- health/readiness/alerting ownership;
- backup completion and restore validation;
- database migration and rollback safety;
- capacity/load assumptions and limits;
- dependency outage/degraded-mode behavior;
- privacy/security release gates;
- incident/support ownership and escalation;
- recurring infrastructure/provider costs and budgets;
- terms/privacy/legal obligations;
- any live payment/store/provider approval;
- launch, rollback and emergency-disable criteria.

## Named evidence exceptions at D01

Not yet performed or claimed: live production traffic, public beta, DNS cutover, production database migration, live load test, live failover, disaster-recovery exercise, production backup restore, real provider billing, real payment/store flow, production incident exercise, production cost/billing reconciliation.

## Approval effect

Merge of the D01 planning PR authorizes only D02→D10 in the locked order and only within the bounded readiness work above. It does not authorize production/public-beta traffic, real-money/provider activation, destructive changes, new recurring spend or claims of unperformed live evidence.
