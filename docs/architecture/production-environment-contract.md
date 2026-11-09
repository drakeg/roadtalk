# Production environment and deployment contract

Sprint 15 owner: S15-D02 / #445.

## Scope

This contract defines the production target and release invariants without creating, enabling, or applying production infrastructure. The machine-readable source is `infrastructure/environments/production/production-contract.json`; CI validates it with `scripts/ci/check-production-contract.py`.

## Environment separation

Production is a distinct environment, state key, runtime-secret namespace, network boundary, and deployment approval path. It must not reuse the field-test Terraform workspace, state, VPC, host, database, cache, or secret prefix. A production implementation may reuse reviewed Terraform modules only when their contracts satisfy the production requirements; it may not copy the single-host field-test root.

## Target topology

The production target is a multi-AZ managed-services topology with a managed load-balancer ingress, private compute, a private managed PostgreSQL service, and a private managed Redis-compatible cache. At least two availability zones are required. Public database/cache exposure and a single-host production deployment are prohibited.

This is a topology contract, not authorization to provision it. Resource sizing, exact AWS services, capacity, cost, and availability implementation remain gated by later Sprint 15 work.

## Domains and TLS

Production domain names are explicit approved deployment inputs rather than repository defaults. A release must prove domain ownership and certificate validation before DNS cutover. TLS is mandatory, the minimum accepted contract is TLS 1.2, and plaintext HTTP must redirect to HTTPS.

D02 does not select or cut over a real production hostname.

## Immutable artifacts and provenance

A production backend release must select a container by SHA-256 digest. Mutable tags such as `latest` cannot identify the deployed version. Release provenance must tie the digest to the source revision and CI evidence, and the release must retain an explicitly identified rollback artifact. SBOM generation is required before production release approval.

## Configuration boundary

The runtime environment is explicitly `production`. Plaintext production secrets are prohibited in Terraform variables/state and CI configuration. Runtime secrets must come from a managed secret source under the dedicated `/roadtalk/production/` namespace.

Premium, payment, and store providers remain disabled by default. Their activation is not authorized by D02.

## Release and rollback semantics

Production release is approval-gated and must identify the exact infrastructure plan and exact immutable application artifact. Before deployment, the release path must verify database migration safety and record a rollback target and emergency-disable path.

Automatic real-user rollout is prohibited. An irreversible database migration blocks automatic rollback and requires an explicitly reviewed forward-recovery plan instead of pretending rollback is safe.

D06 owns the deployment/rollback automation; D02 defines the invariants that automation must enforce.

## Evidence boundary

CI can prove the contract is deterministic and rejects insecure/ambiguous settings. It cannot prove production traffic, capacity, load, failover, disaster recovery, DNS cutover, production billing, or a real production rollback. Those remain named exceptions until actually exercised and recorded.

## D02 acceptance

D02 satisfies the environment-contract portion of S15-R01 and the deterministic configuration portion of S15-T01 when:

- the machine-readable contract is present;
- CI validates the accepted contract;
- negative tests prove ambiguous/insecure mutations are rejected;
- production remains disabled and unprovisioned;
- the evidence record names all live-production exceptions.
