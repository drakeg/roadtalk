# Releases and Versioning

RoadTalk uses Semantic Versioning for published releases.

- **MAJOR** — incompatible public API, deployment, data-contract, mobile compatibility, or operator workflow changes.
- **MINOR** — backward-compatible user-visible capability, meaningful new integration, or substantial operational feature.
- **PATCH** — backward-compatible defect, security, dependency, documentation, or operational fix that merits a release.

## Current state

No GitHub release is currently published. A merged PR or completed sprint does not automatically create a release.

## Release criteria

A release requires:
- intended scope merged and traceable to sprint/backlog items;
- required CI, tests, dependency audits, security scans, migrations, and container validation green;
- documentation and README badges current;
- known security/privacy/cost/provider implications reviewed;
- rollback/migration notes where applicable;
- changelog/release notes updated;
- version/tag chosen from verified compatibility impact.

The first public-beta software release must also satisfy Sprint 16 D10 and any separately required authorization. A release tag must never be treated as permission to activate production traffic, paid providers, DNS, or recurring spend.

## Release checklist

1. Confirm all required checks on the exact release commit.
2. Verify `CHANGELOG.md`, `SPRINTS.md`, `BACKLOG.md`, and this file are current.
3. Verify README badge claims against manifests/workflows/infrastructure.
4. Confirm no secrets or production data are present.
5. Document compatibility, migration, rollback, security, privacy, and cost impact.
6. Publish a GitHub release only when the user-visible or operator-visible change justifies it.
