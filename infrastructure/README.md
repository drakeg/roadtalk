# Infrastructure

Sprint 1 owner: S01-D09.

Terraform implements the accepted controlled field-test foundation. Every deployable
root is disabled by default; the default plans create zero resources.

## Layout

- `bootstrap/` — opt-in encrypted/versioned S3 state bucket with native lockfile
  locking; no DynamoDB table.
- `environments/field-test/` — opt-in low-cost single-host field-test root.
- `environments/production/` — explicit non-implementation boundary.
- `modules/network/` — VPC, internet gateway, two public subnets, and routing.
- `modules/compute/` — one ARM EC2 host, encrypted gp3 volume, SSM administration,
  and least-privilege backup/parameter access.
- `modules/backup/` — encrypted, versioned, private S3 backup bucket with short
  lifecycle retention.
- `modules/registry/` — immutable encrypted ECR repository retaining only three
  rollback images.

Every module keeps inputs in `variables.tf` and outputs in `outputs.tf`.

## Cost boundary

The field-test root deliberately excludes:

- NAT Gateway;
- RDS/Aurora;
- ElastiCache or managed Redis;
- ALB;
- ECS/Fargate;
- Elastic IP;
- Route 53 hosted zone;
- KMS customer-managed keys;
- Multi-AZ or autoscaling resources.

When explicitly enabled, recurring charges are primarily one `t4g.small` instance,
40 GB encrypted gp3 storage, one public IPv4 address, low-volume S3 usage, and at most
three compressed ECR images. Increase the instance size only after measured load
requires it. Stop or destroy the field test when it is not actively needed, after
verifying off-instance backups.

## Prerequisites

- Terraform 1.15.x
- AWS CLI credentials for the dedicated field-test account
- reviewed globally unique state and backup bucket names
- two available AZs in `us-east-1`
- no secrets in `.tfvars`, command history, plans, or state

## Validate the zero-resource defaults

```sh
sh scripts/ci/validate-terraform.sh
```

CI runs formatting, initialization, validation, TFLint, disabled plans, module-contract
checks, cost/network guardrails, and Trivy IaC scanning. The disabled plans use dummy
credentials and do not contact AWS.

## Bootstrap state explicitly

Copy `bootstrap/terraform.tfvars.example` outside Git or create an ignored
`terraform.tfvars`. Keep `enable_bootstrap = false` while reviewing:

```sh
terraform -chdir=infrastructure/bootstrap init
terraform -chdir=infrastructure/bootstrap plan
```

Only after reviewing the plan and bucket name, set `enable_bootstrap = true`, rerun
the plan, and apply it manually. The state bucket has `prevent_destroy`; removing it
requires a separate reviewed recovery/retention decision.

## Initialize field-test remote state

```sh
terraform -chdir=infrastructure/environments/field-test init \
  -backend-config="bucket=<state-bucket>" \
  -backend-config="key=field-test/terraform.tfstate" \
  -backend-config="region=us-east-1" \
  -backend-config="use_lockfile=true"
terraform -chdir=infrastructure/environments/field-test plan
```

The first plan must report zero resources because `enable_field_test = false`.

For an approved field-test window, copy `terraform.tfvars.example` to an ignored
private file, set the real account/bucket values, and change
`enable_field_test = true`. Save the reviewed plan to a protected location and apply
that exact plan manually. CI never applies Terraform.

## Runtime secrets

Terraform grants the host read access to `/roadtalk/field-test/*` in SSM Parameter
Store but does not create parameter values. D10 provisions/rotates runtime values
out-of-band so plaintext secrets never enter Terraform state. PostgreSQL and Redis stay
in host-local containers with no public ports.

## Operational limitations

This topology is non-production: one host and one volume share a failure domain,
maintenance causes downtime, public IP replacement can require DNS changes, and
recovery depends on tested S3 backups. Production must use its separately approved
root and must not inherit this topology by copy.
