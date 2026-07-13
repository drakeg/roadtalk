# Sprint 1 conditional acceptance exceptions

- Decision date: 2026-07-13
- Decision owner: Product owner
- Decision: Accept Sprint 1 conditionally and defer named manual evidence
- Cost at decision: $0 AWS resources enabled
- Hard deadline: Before the first field-test environment is enabled or distributed

These exceptions accept schedule risk, not a claim that the tests passed. They do
not authorize production use, remove a security control, or permit later-sprint
scope. Each exception closes only when a redacted record under
`docs/evidence/sprint-1/` is reviewed and linked here.

| Exception | Tests | Deferred evidence | Risk | Required controls and closure |
|---|---|---|---|---|
| S01-E01 Device and clean setup | T01, T02, T07, device portion of T13 | Clean-machine setup, mobile reachability, installed iOS/Android builds, Keychain/Keystore and leakage audit | Environment or platform behavior may differ from CI; credential persistence defect could remain undetected | Use synthetic accounts; run on both target platforms; inspect backups/logs/URLs/storage; fix any security failure before distribution; close before first field test |
| S01-E02 Controlled CI failures | T08 | Full synthetic format/type/test/migration/security defect matrix | A gate could appear configured but fail to reject a known-bad change | Use temporary branches and synthetic defects only; verify every required check; revert every defect; no cloud credentials; close before field-test release branch |
| S01-E03 AWS field-test rehearsal | T09, T10, T11, T12 | Enabled plan, deploy A/B/rollback, alarm/budget routing, restore, rotation | Deployment, recovery, notification, or cost controls may fail in the real account | One approved bounded window; smallest existing design; synthetic data; budget/SNS confirmed first; verified backup; capture redacted IDs; destroy/stop immediately; close before any user field test |

## Stop conditions

Do not begin or continue a field test if any exception remains open, the Terraform
plan contains an unapproved service, the budget contact is unconfirmed, a backup is
unverified, rollback/restore fails, credentials appear outside approved storage, or
the environment cannot be shut down cleanly.

## Cost ceiling

No rehearsal may introduce RDS, managed Redis, NAT Gateway, ALB, Fargate, Multi-AZ,
detailed monitoring, paid dashboards, or tracing. Estimate the bounded-window cost
before apply and obtain product-owner approval if it could exceed the configured $20
monthly budget. A budget alert is not permission to continue spending.

## Closure record

| Exception | Evidence link | Reviewer | Closed date | Result |
|---|---|---|---|---|
| S01-E01 | Pending | Pending | Pending | Open |
| S01-E02 | Pending | Pending | Pending | Open |
| S01-E03 | Pending | Pending | Pending | Open |
