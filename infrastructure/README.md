# Infrastructure

Sprint 1 owner: S01-D09.

This directory will contain Terraform bootstrap configuration, environment roots, and reusable AWS modules.

## Required rules

- separate field-test and production roots
- S3 backend with lockfile state locking
- no Terraform workspaces for environment separation
- every module keeps variables in `variables.tf` and outputs in `outputs.tf`
- provider configuration belongs in root modules
- no plaintext secrets or Terraform state in Git
- no NAT Gateway or public database/cache ports in the field-test design
- infrastructure changes require reviewed plans and pull requests

No Terraform resources exist yet. S01-D09 creates them.
