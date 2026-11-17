# Production backup, restore, and disaster-recovery preflight

Sprint 16 owner: S16-D06 / #481.

## Isolated restore test

Restore validation must target an isolated environment and must never overwrite production.
The operator records the exact recovery point, validates provider/checksum integrity, validates
schema compatibility, runs bounded application smoke checks, limits access to restored data, and
cleans up temporary restored data afterward.

Validation output must not dump restored sensitive records.

## RPO/RTO measurement

Sprint 15 established target RPO <=60 minutes and RTO <=240 minutes. Sprint 16 requires measured
values before public-beta launch.

Evidence records capture:
- recovery-point timestamp;
- restore start timestamp;
- restore completion timestamp;
- measured RPO = restore start minus recovery-point timestamp;
- measured RTO = restore completion minus restore start.

Targets must not be described as measured achievements until an authorized restore exercise
actually collects those timestamps.

## Disaster recovery

A DR exercise requires a named owner, declaration criteria, communication path, rollback target,
and explicit failover approval. Destructive failover is prohibited by default and D06 keeps
production failover authorization false.

## Evidence tooling

`scripts/ci/restore-evidence.py` validates the evidence record format and calculates RPO/RTO
from timestamps. It is metadata-only and does not connect to AWS, production databases, backup
providers, or live systems.

A synthetic record lives at `docs/evidence/examples/sprint-16-isolated-restore.json` to prove the
format deterministically.

## Evidence boundary

D06 does not perform or claim a live production restore, DR exercise, or measured production
RPO/RTO.
