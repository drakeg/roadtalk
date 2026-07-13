# Field-test deployment and rollback

## Cost posture

Deployment uses the existing single `t4g.small` host. ECR retains only three
compressed images for rollback. No ALB, ECS/Fargate, NAT Gateway, RDS, managed Redis,
or extra deployment host is created. Build and deploy only during an approved
field-test window.

## Runtime parameters

Create SecureString parameters out-of-band under `/roadtalk/field-test/`. Required
basenames:

- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `ROADTALK_TOKEN_SIGNING_KEY`
- `ROADTALK_REFRESH_TOKEN_PEPPER`
- `ROADTALK_ENVIRONMENT`
- `ROADTALK_DOCS_ENABLED`
- `ROADTALK_HOSTNAME`

Use unique generated values. Never pass values through Terraform, Git, workflow
inputs, image layers, or shell history. The deployment host writes them to root-only
`runtime.env` and `deployment.env`.

## Build and publish

```sh
export AWS_REGION=us-east-1
repository_url="$(terraform -chdir=infrastructure/environments/field-test output -raw repository_url)"
image="$(sh scripts/deploy/build-and-push.sh "$repository_url")"
```

The image is built for ARM64 and tagged with the Git commit SHA. ECR rejects tag
replacement and expires images beyond the newest three.

## Deploy

```sh
instance_id="$(terraform -chdir=infrastructure/environments/field-test output -raw instance_id)"
sh scripts/deploy/ssm-deploy.sh "$instance_id" "$image"
```

Ordering is fixed:

1. pull the immutable image;
2. install the image-bundled deployment files;
3. fetch runtime parameters through the instance role;
4. start PostgreSQL/PostGIS;
5. run `alembic upgrade head` once;
6. replace the API and Caddy containers;
7. require readiness success before recording the image current.

Migrations must be backward-compatible with the immediately previous image. Never
automatically downgrade a database during application rollback.

## Roll back

```sh
sh scripts/deploy/ssm-rollback.sh "$instance_id"
```

Rollback selects the previously recorded immutable image, replaces API/Caddy, and
requires readiness. It does not reverse migrations or delete data.

## Acceptance rehearsal

In a disposable field-test window:

1. deploy image A and verify live/ready/version plus anonymous authentication;
2. deploy image B and verify the same checks;
3. invoke rollback and confirm image A becomes healthy;
4. confirm database records remain intact;
5. confirm ECR contains no more than three images after lifecycle processing;
6. stop/destroy the field-test resources when the rehearsal is complete.

## Failure handling

If migration fails, the API replacement does not occur. If health fails after
replacement, run rollback. Preserve SSM command IDs and image digests as Sprint 1
evidence. Restore from the encrypted S3 database backup only through the restore
runbook; deployment scripts never delete the database volume.
