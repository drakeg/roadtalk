# Production deployment and rollback automation

Sprint 15 owner: S15-D06 / #450.

D06 establishes fail-closed automation inputs and release invariants without authorizing production deployment.

## Deployment inputs

A production release must bind to:
- an immutable application image digest;
- a distinct immutable known-good rollback digest;
- the exact approved Terraform plan hash;
- provenance and SBOM evidence.

Mutable tags such as `latest` are never accepted as release or rollback identities.

## Approval and identity

Production apply remains manually approved and unavailable to pull-request jobs. The exact plan, artifact, and deploying identity must match the approved release record. Plans expire within 60 minutes and require a drift check immediately before apply.

## Migration safety

Database migration preflight is mandatory. Changes must be backward-compatible across the deployment window. Destructive or irreversible changes default to denied and require separate approval. An irreversible migration blocks automatic rollback.

## Health-gated rollout

The future live deployment implementation must pass pre-release health, avoid one-shot full-fleet replacement, observe post-release health for at least 10 minutes, and halt or roll back on failure. D06 does not authorize real-user traffic shifting.

## Rollback

Rollback requires a named exact digest, database-state compatibility check, manual approval, and an emergency-disable path. Rollback to a mutable tag is prohibited.

## Dry-run workflow

`.github/workflows/production-deploy-dry-run.yml` validates immutable input formats and the D06 contract only. It intentionally requests no cloud credentials and contains no apply, deploy, DNS, or traffic-shift step.

Live production deployment/rollback evidence remains separately gated.
