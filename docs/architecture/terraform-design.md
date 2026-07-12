# RoadTalk Terraform Design

- Status: Approved for Sprint 1 implementation
- Issue: #9
- Requirements: S00-R07
- Acceptance: S00-T05
- Date: 2026-07-12

## Repository layout

```text
infrastructure/
  bootstrap/
    backend/
      main.tf
      variables.tf
      outputs.tf
      versions.tf
  environments/
    field-test/
      backend.tf
      main.tf
      variables.tf
      outputs.tf
      versions.tf
      terraform.tfvars.example
    production/
      backend.tf
      main.tf
      variables.tf
      outputs.tf
      versions.tf
      terraform.tfvars.example
  modules/
    network/
      main.tf
      variables.tf
      outputs.tf
    compute-field-test/
      main.tf
      variables.tf
      outputs.tf
    compute-ecs/
      main.tf
      variables.tf
      outputs.tf
    database/
      main.tf
      variables.tf
      outputs.tf
    observability/
      main.tf
      variables.tf
      outputs.tf
    storage/
      main.tf
      variables.tf
      outputs.tf
```

Every module must keep input declarations in `variables.tf` and outputs in `outputs.tf`; do not embed them in `main.tf`.

## State

- bootstrap the state bucket separately
- S3 backend with encryption, versioning, blocked public access, and least privilege
- enable S3 lockfile state locking with `use_lockfile = true`
- DynamoDB locking is not used for new configuration because HashiCorp marks it deprecated
- one distinct state key per environment
- never commit local state, plans containing secrets, or backend credentials
- state access is administrative and audited
- recovery includes version restoration and a documented force-unlock procedure

## Versions

- declare a tested Terraform minimum and bounded maximum
- pin provider source and compatible version range in `versions.tf`
- commit `.terraform.lock.hcl` for each root configuration
- module callers pin repository module versions once modules are externally versioned
- upgrades occur through reviewed changes with plan output and validation

## Environment policy

- no Terraform workspaces for field-test/production separation
- each environment has its own root, variables, state key, and approval boundary
- field-test topology is not promoted by renaming it production
- common modules are reused only where their semantics genuinely match
- production applies require review once infrastructure implementation begins

## Module contract rules

- small, cohesive modules with explicit inputs/outputs
- no circular dependencies
- pass identifiers rather than entire provider resources when practical
- provider configuration belongs in roots, not child modules
- names and tags are deterministic
- secrets are references, not plaintext inputs
- validation blocks constrain CIDRs, environments, retention, instance sizes, and destructive flags
- outputs do not expose secret values
- optional resources use clear booleans or typed objects, not ambiguous null behavior

## CI validation

For every infrastructure change:

1. `terraform fmt -check -recursive`
2. `terraform init -backend=false` for static validation roots
3. `terraform validate`
4. TFLint with pinned rules
5. tfsec or Checkov with documented suppressions
6. generated plan for the target environment
7. cost/security review for material resource changes
8. apply only after approval

## Deployment and drift

- CI uses short-lived OIDC credentials, not stored AWS access keys
- plan and apply roles are separate
- production apply is serialized and protected
- scheduled plan detects drift without automatically correcting it
- manual changes are exceptional, documented, and imported/reconciled
- destructive replacement requires backup/rollback review
- all resources carry standard ownership and cost tags

## Secrets

Terraform creates secret containers/policies but does not receive secret values in normal plans. Runtime values are written through an approved secret-management workflow. Sensitive outputs are still avoided because Terraform state retains them.

## Validation result

The layout has a single direction: environment roots call reusable modules; modules do not call environment roots or each other cyclically. Network and storage/observability foundations feed compute/database identifiers through explicit outputs.

## Primary references

- [Terraform S3 backend and lockfiles](https://developer.hashicorp.com/terraform/language/backend/s3)
- [Terraform state locking](https://developer.hashicorp.com/terraform/language/state/locking)
- [Terraform dependency lock file](https://developer.hashicorp.com/terraform/language/files/dependency-lock)
- [Terraform provider configuration](https://developer.hashicorp.com/terraform/tutorials/configuration-language/configure-providers)
