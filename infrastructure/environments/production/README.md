# Production Terraform root

Sprint 15 production work is contract-gated. This directory remains non-deploying in S15-D02.

The production root is separate from field test and does not reuse Terraform workspaces,
state, VPCs, hosts, databases, caches, or runtime-secret prefixes. The accepted machine-
readable contract is `production-contract.json` and is validated in CI by
`scripts/ci/check-production-contract.py`.

The target contract requires a multi-AZ managed-services topology, private compute and
data services, managed load-balancer ingress, explicit approved domain/TLS inputs,
immutable digest-selected application artifacts, deployment provenance, and rollback
semantics.

D02 does **not** create Terraform resources or authorize an apply. Production/public-beta
traffic, DNS cutover, recurring spend, real provider/store/payment activation, destructive
changes, and live-production evidence remain separately gated by later Sprint 15 work.

Do not copy the single-host field-test topology into production.
