# Sprint 15 D06 evidence — Production deployment and rollback automation

Issue: #450  
Requirements: S15-R05, S15-R10, S15-R11  
Acceptance tests: S15-T05, S15-T10, S15-T11

## Implemented

- Added machine-readable deployment/rollback automation requirements.
- Requires immutable application and rollback digests, provenance, and SBOM.
- Requires exact approved plan binding, short plan lifetime, matching deploy identity, and pre-apply drift checking.
- Requires migration preflight and backward compatibility.
- Defaults destructive/irreversible database changes to denied and blocks automatic rollback after irreversible changes.
- Requires pre/post health gates, bounded observation, and halt/rollback on failed health.
- Prohibits one-shot full-fleet replacement and automatic real-user rollout.
- Requires exact rollback target, database compatibility check, manual approval, and emergency disable.
- Added a manual dry-run workflow that validates exact immutable inputs but deliberately has no production credentials or deployment step.
- Added CI negative mutation tests.

## Not performed or claimed

No production Terraform apply, application deployment, database migration, rollback, DNS change, or real-user traffic shift was performed. The workflow is input/contract validation only.

## Acceptance boundary

Merge accepts deterministic release-automation safety invariants. Live production deployment and rollback execution evidence remain separately gated.
