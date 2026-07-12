# CI quality and security gates

## Workflow

`.github/workflows/ci.yml` runs for pull requests, pushes to `main`, and manual
dispatches. A newer run for the same ref cancels an older run to control runner
minutes. The workflow has read-only repository permissions and no cloud credentials.

Required job names:

- **Backend, database, and migrations**
- **Mobile quality**
- **Dependencies, secrets, containers, and IaC**

Repository administrators must configure these three jobs as required status checks
for `main` after their first successful run.

## Enforced checks

The backend job enforces Ruff formatting/linting, strict mypy, branch coverage,
PostGIS-backed integration tests, empty-database migration, metadata drift, downgrade,
and forward migration.

The mobile job enforces locked dependency installation, Expo Doctor, strict
TypeScript, and Jest/React Native Testing Library tests.

The security job enforces Python and production-mobile dependency audits plus Trivy
high/critical vulnerability, secret, Dockerfile, and Terraform misconfiguration scans.
Dockerfile and Terraform checks activate as soon as those approved artifacts exist.
Image build/scanning is added with S01-D10 because no container image exists yet.

## Controlled gate test

Use a temporary branch and revert every change after observing the expected failure:

| Defect | Expected job |
|---|---|
| misformat a Python file | Backend, database, and migrations |
| introduce a Ruff or mypy violation | Backend, database, and migrations |
| make a backend/mobile assertion fail | Corresponding quality job |
| change a model without a migration | Backend, database, and migrations |
| add a known high/critical vulnerable dependency | Security |
| add a credential-shaped test secret | Security |
| add an insecure Dockerfile or Terraform resource | Security |

Never use a real secret in a gate test. Record run links in the Sprint 1 evidence
deliverable.

## Local parity

```sh
make backend-format-check
make backend-lint
make backend-typecheck
make backend-test
make mobile-doctor
make mobile-typecheck
make mobile-test
npm --prefix mobile audit --omit=dev --audit-level=high
```

Migration integration requires a migrated disposable PostgreSQL/PostGIS database and
`ROADTALK_RUN_DATABASE_TESTS=1`.

## Cost controls

- no AWS credentials or resources;
- no macOS runner;
- no EAS cloud build;
- concurrency cancellation enabled;
- dependency caches enabled;
- 15-minute job timeouts;
- container and Terraform work remains conditional until the artifacts exist.
