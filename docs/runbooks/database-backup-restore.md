# Database backup and restore

## Boundary

The field-test database is PostgreSQL/PostGIS on the single EC2 host, not RDS. Its
EBS volume is not a backup. Logical dumps belong in the Terraform-managed encrypted,
versioned S3 bucket and expire under its short field-test retention policy. Use only
synthetic data.

## Create and verify a backup

1. Confirm AWS account, region, instance ID, bucket, database name, and maintenance
   window. Obtain IDs from Terraform outputs; never guess them.
2. Connect through SSM, not SSH, and load the root-only runtime environment.
3. Stream a custom-format dump from the database container to a root-only temporary
   file. Do not pass the database password on a command line.
4. Run `pg_restore --list` against the file and calculate its SHA-256 checksum.
5. Upload it with `aws s3 cp` to
   `s3://BUCKET/database/YYYY/MM/DD/UTC_TIMESTAMP-COMMIT.dump`.
6. Confirm server-side AES-256 encryption, object version ID, size, and checksum;
   then securely delete the host temporary file.
7. Record identifiers and counts, never dump contents or secret values.

If any verification fails, retain the source database, mark the backup unusable, and
stop. A successful upload alone is not a verified backup.

## Restore rehearsal into a disposable database

1. Select a verified object version and recheck its checksum after download.
2. Start a disposable PostgreSQL/PostGIS 17/3.5 database isolated from the live API.
3. Create PostGIS, restore with `pg_restore --exit-on-error --no-owner
   --no-privileges`, and run `alembic upgrade head` only if the chosen application
   commit requires it.
4. Compare migration revision, table list, and per-table row counts with the source.
5. run `/health/ready` and a synthetic anonymous-authentication smoke test against
   the restored database.
6. Record checksums, object key/version, revision, comparisons, and result, then
   destroy the disposable database.

Never rehearse by overwriting the active database.

## Emergency in-place restore

This is destructive and requires explicit owner approval. Announce maintenance,
stop the API, take and verify a pre-restore dump, confirm the intended object version
twice, restore while failing on the first error, verify schema/counts/readiness, and
then restart traffic. If verification fails, keep traffic stopped and restore the
pre-change dump or escalate. Application rollback never performs this procedure and
Alembic downgrade is not a substitute for backup restore.

## Cost and retention

Keep only policy-required backups. Do not add RDS, cross-region replication, AWS
Backup, or long archive tiers without a measured need and reviewed cost decision.
The backup bucket's non-empty/versioned safety may block Terraform destroy; preserve
required evidence, expire objects through policy, and never bypass that protection
merely to make destroy succeed.
