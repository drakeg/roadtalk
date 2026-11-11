# Production backup, restore, and data-protection contract

Sprint 15 owner: S15-D05 / #449.

## Backup scope

Production recovery must cover the primary database, required application configuration, and Terraform state. Object storage is included when RoadTalk stores durable application data there. Cache contents are not treated as authoritative durable data unless a later design explicitly changes that boundary.

Generic backups must not become a second secret store. Runtime secret values remain in the approved managed secret system and are recovered through that system's own protected recovery controls.

## Protection model

Production backups require encryption in transit and at rest, recovery points outside the primary failure domain, versioned or otherwise immutable recovery points, and deletion protection. The normal production runtime identity must not be able to erase all recovery copies.

The existing field-test backup module is not accepted as the production design by itself; production implementation must satisfy this stronger contract.

## Retention

The readiness baseline requires at least:

- seven daily recovery points;
- four weekly recovery points;
- three monthly recovery points;
- a normal retention window of at least 30 days and no more than 365 days unless separately approved.

## Recovery objectives

Initial production targets are:

- RPO: no more than 60 minutes;
- RTO: no more than 240 minutes.

These are design objectives only. They cannot be presented as achieved until a live, authorized restore/failover exercise measures them.

## Restore validation

Backups are not considered ready merely because a backup job reports success. A production-ready process must periodically restore to an isolated target, verify integrity and schema, run application smoke validation, record evidence, and clean up temporary restored data.

Restore testing must never overwrite production and must occur at least every 90 days once production is live.

## Data protection during restore

Restore targets are isolated and access-limited. Validation logs must not dump sensitive restored records. Temporary restored datasets require cleanup. Precise-location exports and raw payment instruments are explicitly excluded from backup/restore test artifacts.

## Disaster recovery

A DR runbook must name an owner, declaration criteria, communications path, and explicit failover approval. D05 defines those requirements but does not authorize a failover or claim a DR exercise occurred.

## Evidence boundary

CI validates the contract and negative cases only. No live production backup, restore, DR exercise, or measured RPO/RTO is claimed by D05.

The machine-readable source is `infrastructure/environments/production/backup-contract.json`, validated by `scripts/ci/check-production-backup.py`.
