# Sprint 15 D05 evidence — Production backup, restore, and data protection

Issue: #449  
Requirements: S15-R04, S15-R08, S15-R11  
Acceptance tests: S15-T04, S15-T08, S15-T11

## Implemented

- Added a machine-readable production backup/restore/data-protection contract.
- Requires database, configuration, and Terraform-state recovery scope.
- Requires encryption at rest/in transit, cross-failure-domain recovery copies, immutable/versioned recovery points, and delete protection.
- Prevents the normal runtime identity from deleting all backup copies.
- Defines daily/weekly/monthly retention minimums.
- Defines initial RPO <=60 minutes and RTO <=240 minutes as unproven targets requiring live validation.
- Requires isolated restore testing, integrity/schema checks, application smoke validation, evidence records, and cleanup.
- Prohibits restore tests from overwriting production.
- Requires quarterly-or-better restore validation after production launch.
- Adds privacy boundaries for restored data and validation logs.
- Adds a DR runbook contract with ownership, declaration, communication, and explicit failover approval.
- Adds CI validation and negative mutation tests.

## Deterministic validation

`python scripts/ci/check-production-backup.py --self-test`

The negative suite verifies fail-closed behavior for missing database backups, generic secret backup, missing cross-failure-domain copies, runtime-wide backup deletion, inadequate retention, weak RPO, production-overwriting restore tests, infrequent restore tests, non-isolated restore targets, precise-location exports, unapproved failover, and false live-restore claims.

## Not performed or claimed

No production backup was created, no production restore was performed, no DR exercise or failover occurred, and RPO/RTO were not measured against live production. No production resource or recurring cost is introduced by D05.

## Acceptance boundary

Merge accepts deterministic backup/restore/data-protection readiness requirements only. Live backup job evidence, isolated production-data restore evidence, measured RPO/RTO, and DR exercise evidence remain required before production launch claims.
