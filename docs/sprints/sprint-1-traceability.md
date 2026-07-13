# Sprint 1 traceability and evidence

- Status: Complete — manual evidence conditionally accepted as named exceptions
- Deliverable: S01-D13
- Issue: #32
- Baseline: merge commit `c4404af96ebfc4cd4379fd226f6807346241a622`
- Evidence date: 2026-07-13

## Status vocabulary

- **Passed — automated:** reproducible CI or repository test evidence passed.
- **Passed — inspection:** implementation and guardrails were reviewed without a
  live device or AWS environment.
- **Pending — manual:** requires hardware, a Docker-capable clean machine, or an
  explicitly enabled field-test window. It is not represented as passed.
- **Deferred:** intentionally moved to a named future closure condition.
- **Accepted exception:** product owner accepted the stated risk and controls without
  representing the deferred procedure as passed.

## Requirement traceability

| Requirement | Deliverable(s) | Test(s) | Evidence | Status |
|---|---|---|---|---|
| S01-R01 Repository foundation | D01, D07 | T01 | PRs [#34](https://github.com/drakeg/roadtalk/pull/34), [#35](https://github.com/drakeg/roadtalk/pull/35); root Make targets and clean-setup runbook | Passed — inspection; S01-E01 accepted |
| S01-R02 Mobile foundation | D02 | T02 | PR [#39](https://github.com/drakeg/roadtalk/pull/39); Jest, TypeScript, Expo Doctor in CI | Automated portion passed; S01-E01 accepted |
| S01-R03 Backend foundation | D03 | T03 | PR [#36](https://github.com/drakeg/roadtalk/pull/36); `backend/tests/test_health.py`, `test_system.py`, `test_logging.py` | Passed — automated |
| S01-R04 Database foundation | D04 | T04 | PR [#37](https://github.com/drakeg/roadtalk/pull/37); CI empty migration, drift, tests, downgrade/forward cycle | Passed — automated |
| S01-R05 Anonymous authentication | D05 | T05 | PR [#38](https://github.com/drakeg/roadtalk/pull/38); auth route/service/integration tests | Passed — automated |
| S01-R06 Session lifecycle | D05 | T05, T06 | PR #38; refresh rotation, logout, revocation, replay-family tests | Passed — automated |
| S01-R07 Mobile credential security | D06 | T07 | PR [#40](https://github.com/drakeg/roadtalk/pull/40); SessionClient tests and dependency inspection | Automated portion passed; S01-E01 accepted |
| S01-R08 Local development | D07, D12 | T01 | PRs #35 and [#45](https://github.com/drakeg/roadtalk/pull/45); Compose health and clean-setup procedure | CI database use passed; S01-E01 accepted |
| S01-R09 CI/CD foundation | D08 | T08 | PR [#41](https://github.com/drakeg/roadtalk/pull/41); required three-job workflow and controlled-failure runbook | Compliant pipeline passed; S01-E02 accepted |
| S01-R10 Terraform field test | D09 | T09 | PR [#42](https://github.com/drakeg/roadtalk/pull/42); fmt/init/validate/TFLint/Trivy and credential-free zero-resource plans | Automated/inspection passed; S01-E03 accepted |
| S01-R11 Deployment foundation | D10 | T10 | PR [#43](https://github.com/drakeg/roadtalk/pull/43); ARM image build/scan and SSM deploy/rollback scripts | Build passed; S01-E03 accepted |
| S01-R12 Monitoring | D03, D11 | T03, T11 | PRs #36 and [#44](https://github.com/drakeg/roadtalk/pull/44); privacy-safe log tests and Terraform alarm/budget inspection | Automated portion passed; S01-E03 accepted |
| S01-R13 Documentation/runbooks | D12 | T12 | PR #45; bounded rollback, restore, rotation, and shutdown runbooks | Passed — inspection; S01-E03 accepted |
| S01-R14 Scope protection | D01–D13 | T13 | route/screen/schema/config/dependency audit; no later-sprint permissions or data models | Passed — inspection |

## Acceptance-test evidence

| Test | Automated evidence | Manual evidence | Result |
|---|---|---|---|
| S01-T01 clean setup | CI installs dependencies, starts PostGIS, migrates, and tests | Execute `docs/runbooks/clean-setup.md` from a clean machine and attach record | Accepted exception S01-E01 |
| S01-T02 mobile targets | Expo Doctor, strict TypeScript, and Jest smoke tests pass | Install and launch local development builds on iOS and Android | Accepted exception S01-E01 |
| S01-T03 API foundation | Backend CI tests live/ready/version/problems/correlation/privacy | None additional | Passed — automated |
| S01-T04 database lifecycle | CI upgrades empty PostGIS, checks drift, tests, downgrades, and upgrades | None additional | Passed — automated |
| S01-T05 auth lifecycle | Route, service, security, and migrated-PostGIS integration tests | Optional device-to-field-test smoke | Passed — automated |
| S01-T06 refresh replay | Service/integration tests verify family revocation | None additional | Passed — automated |
| S01-T07 credential storage | Tests prove access tokens are not persisted and refresh cleanup fails closed | Inspect iOS Keychain, Android Keystore, backups, logs, URLs, and ordinary storage | Accepted exception S01-E01 |
| S01-T08 CI gates | Current compliant workflow passes every required job | Run the documented controlled defect matrix with synthetic defects only | Accepted exception S01-E02 |
| S01-T09 Terraform | Disabled plans, formatting, validation, locks, lint, security, cost/network/module guards pass | Review an enabled field-test plan in the intended AWS account; do not apply for this test | Accepted exception S01-E03 |
| S01-T10 deploy/rollback | ARM container builds and passes vulnerability scanning; scripts pass static gates | Deploy A, deploy B, roll back to A, verify health and data | Accepted exception S01-E03 |
| S01-T11 monitoring | Structured-log tests and Terraform monitoring guards pass | Confirm SNS, alarms, budget routing, and privacy-safe bounded query | Accepted exception S01-E03 |
| S01-T12 runbooks | Runbooks reviewed against current parameter names, outputs, and runtime | Restore into disposable DB and complete rollback/rotation review record | Accepted exception S01-E03 |
| S01-T13 scope protection | Repository audit finds only foundation/auth routes, screens, tables, and permissions | Confirm device prompts expose no later-sprint permission | Passed — inspection; device confirmation pending |
| S01-T14 full demonstration | Full CI passed on D13/D14 commits | Product owner conditionally approved named exceptions | Passed — conditional |

## Automated baseline

The latest completed pre-D13 pipeline is [CI run 29219772809](https://github.com/drakeg/roadtalk/actions/runs/29219772809)
for PR #45 at `686823c1b9b8ac8067c9ebef4f5445a5846204df`.
All required jobs passed:

- Backend, database, and migrations
- Mobile quality
- Dependencies, secrets, containers, and IaC

The D13 pull request must pass the same three jobs before merge. CI uses no AWS
credentials and does not apply Terraform, so this evidence incurs no AWS cost.

## Deliverable audit

| Deliverable | Issue | Pull request | State |
|---|---:|---:|---|
| S01-D01 | #19 | #34 | Merged |
| S01-D02 | #20 | #39 | Merged |
| S01-D03 | #22 | #36 | Merged |
| S01-D04 | #21 | #37 | Merged |
| S01-D05 | #23 | #38 | Merged |
| S01-D06 | #24 | #40 | Merged |
| S01-D07 | #25 | #35 | Merged |
| S01-D08 | #27 | #41 | Merged |
| S01-D09 | #26 | #42 | Merged |
| S01-D10 | #28 | #43 | Merged |
| S01-D11 | #29 | #44 | Merged |
| S01-D12 | #31 | #45 | Merged |
| S01-D13 | #32 | #46 | Merged |
| S01-D14 | #30 | #47 | Merged |

## Scope and cost audit

Repository inspection confirms no profile/callsign, continuous location, PTT/media,
proximity, channel, map, notification, campground, convoy, moderation, AI, premium,
or production-launch behavior. The mobile configuration requests no location,
microphone, notification, or tracking permission. The database contains only
account, device, and session foundation tables.

Terraform remains disabled by default and CI plans zero resources. The optional
field-test design excludes NAT Gateway, RDS, managed Redis, ALB, Fargate, Elastic IP,
Multi-AZ, detailed monitoring, paid dashboards, tracing, and high-volume logs. No AWS
resource was created to produce this record.

## Exit decision

Sprint 1 is conditionally approved. S01-E01 through S01-E03 must close before the
first field test. Sprint 2 planning is authorized; implementation remains blocked
until the Sprint 2 specification is approved.
