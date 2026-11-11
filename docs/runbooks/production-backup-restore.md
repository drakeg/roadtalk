# Production backup and restore readiness runbook

Status: contract-only; no production execution authorized by S15-D05.

## Backup success review

A future production operator must confirm that the expected recovery point exists, is encrypted, belongs to the correct production scope, is protected from routine runtime deletion, and has a copy outside the primary failure domain. A successful scheduler status alone is insufficient.

## Restore validation sequence

1. Record the selected immutable recovery point and expected source timestamp.
2. Create an isolated, non-production restore target.
3. Restrict restored-data access to the named restore operator(s).
4. Verify backup integrity and database/schema compatibility.
5. Run bounded application smoke checks against the isolated target.
6. Record start/end timestamps and calculate observed restore duration.
7. Verify validation output contains no raw secrets, precise location records, payment instruments, or unnecessary user payloads.
8. Delete temporary restored data after evidence is retained.
9. Record pass/fail findings and corrective actions.

The procedure must abort rather than target the live production database.

## Disaster declaration

A real disaster declaration requires the named operational owner, explicit incident criteria, a communications path, and approval before failover. Restoration and failover are separate decisions: a successful isolated restore does not automatically authorize production cutover.

## Evidence honesty

Until this runbook is executed against authorized production recovery points, RoadTalk must describe RPO/RTO values as targets rather than measured achievements.
