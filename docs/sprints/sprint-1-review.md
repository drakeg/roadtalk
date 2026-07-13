# Sprint 1 review record

- Sprint: 1 — Project Foundation
- Status: Review complete — approval withheld pending manual acceptance
- Review date: 2026-07-13
- Deliverable: S01-D14
- Issue: #30
- Acceptance: S01-T14

## Review outcome

All S01-D01 through S01-D13 deliverables are merged. S01-D14 is this record. The
implemented repository foundation, automated test suite, CI/security gates,
disabled-by-default field-test infrastructure, deployment controls, monitoring, and
runbooks were reviewed.

The automated demonstration passed. The physical-device and enabled AWS portions
were not executed, so the Sprint 1 product demonstration is incomplete and final
approval is withheld. Merging this record does not waive an acceptance test or
authorize Sprint 2 implementation.

## Demonstration record

Demonstrated through CI and repository review:

- FastAPI health, readiness, version, problem response, and correlation behavior
- PostgreSQL/PostGIS empty migration, schema drift, tests, downgrade, and forward fix
- anonymous registration, refresh rotation, replay-family revocation, logout, and
  device revocation
- Expo Doctor, strict TypeScript, navigation/error/session unit tests
- dependency, secret, container, Dockerfile, Terraform, cost, and network gates
- immutable ARM backend image build and scan
- credential-free Terraform plans that create zero resources by default
- privacy-filtered logging and minimal monitoring/budget Terraform contracts
- deployment, rollback, restore, rotation, cost response, and shutdown runbooks
- absence of later-sprint feature routes, screens, permissions, and tables

Latest complete D13 pipeline: [CI run 29220131271](https://github.com/drakeg/roadtalk/actions/runs/29220131271),
with all three required jobs passing. The D14 pull request must pass the same jobs.

Not yet demonstrated:

- clean-machine end-to-end setup and mobile-to-local-API reachability
- installed iOS and Android development builds on target devices
- native Keychain/Keystore, backup, log, URL, and ordinary-storage credential audit
- the complete controlled CI defect-injection matrix
- an enabled field-test Terraform plan reviewed in the intended AWS account
- two-image field-test deployment and application rollback
- alarm, SNS, budget, and privacy-safe log-query rehearsal
- disposable database restore and credential-rotation review

## Acceptance results

| Test | Result | Review evidence/action |
|---|---|---|
| S01-T01 clean setup | PENDING | Automated dependency/database path passes; clean-machine record required |
| S01-T02 mobile targets | PENDING | Automated mobile suite passes; iOS and Android install/smoke required |
| S01-T03 API foundation | PASS | Backend endpoint, problem, readiness, logging, and correlation tests |
| S01-T04 database lifecycle | PASS | CI PostGIS migration, drift, constraint, downgrade/forward cycle |
| S01-T05 auth lifecycle | PASS | Migrated-database integration plus route/service/security tests |
| S01-T06 replay defense | PASS | Rotated-token replay and family revocation tests |
| S01-T07 credential storage | PENDING | Client persistence boundaries tested; native device audit required |
| S01-T08 CI gates | PENDING | Compliant pipelines pass; full controlled-failure matrix required |
| S01-T09 Terraform | PENDING | Static/zero-resource gates pass; enabled reviewed plan required |
| S01-T10 deploy/rollback | PENDING | Image and scripts pass gates; live A/B/rollback rehearsal required |
| S01-T11 monitoring | PENDING | Log tests/contracts pass; notification and budget rehearsal required |
| S01-T12 runbooks | PENDING | Runbook review passes; restore/rotation execution record required |
| S01-T13 scope protection | PASS | Repository inspection finds no Sprint 2–15 behavior or data collection |
| S01-T14 full demonstration | PENDING | Remains pending until every required manual record passes or is explicitly waived |

The detailed mapping and evidence locations are in
[Sprint 1 traceability and evidence](sprint-1-traceability.md).

## Definition of Done

- [x] S01-D01 through S01-D13 implemented and merged
- [x] automated CI, migration, test, security, container, and IaC gates pass
- [x] traceability and privacy-safe evidence template recorded
- [x] documentation and runbooks updated
- [x] no later-sprint feature behavior introduced
- [x] AWS defaults create zero resources
- [ ] required clean-machine and physical-device evidence accepted
- [ ] required enabled field-test, recovery, and alarm evidence accepted
- [ ] S01-T14 demonstration approved by the product owner
- [ ] Sprint 1 tracker closed as completed

## Cost decision

No AWS infrastructure was enabled for this review. This avoided compute, public IPv4,
EBS, ECR, S3, CloudWatch, SNS, and budget-notification charges. When AWS rehearsal is
approved, use one bounded field-test window, the existing smallest design, synthetic
data, and immediate shutdown. Do not add RDS, managed Redis, NAT Gateway, ALB,
Fargate, Multi-AZ, detailed monitoring, paid dashboards, or tracing.

## Known limitations and accepted design risks

- The single field-test host is intentionally not highly available.
- PostgreSQL/PostGIS runs on that host; logical backup/restore has not been rehearsed.
- Secret rotation currently causes a bounded session interruption because overlapping
  signing keys are not implemented.
- Physical-device secure storage and backup behavior still require platform evidence.
- No account recovery, profile, location, proximity, channel, media, notification, or
  later-sprint product behavior exists.
- Production topology, scaling, legal/store work, and availability claims remain out
  of scope.

## Retrospective

What worked:

- small requirement-linked deliverables and reviewed pull requests
- early CI gates that repeatedly validated the complete repository
- explicit privacy and later-sprint scope boundaries
- immutable images, migration-before-replacement, and non-destructive rollback
- disabled-by-default Terraform and repeated cost guardrails
- honest separation of automated, inspected, and unperformed evidence

Improvements:

- execute clean-machine and device smoke tests earlier in the sprint
- schedule one consolidated AWS rehearsal after static gates stabilize
- automate redacted evidence capture without introducing cloud credentials into CI
- reduce connector-created one-file commits when authenticated batch publication is
  available
- keep deployment proof separate from an implementation being merely deployable

## Approval decision and next action

**Decision: approval withheld.** The code and documentation baseline is suitable for
manual acceptance, but Sprint 1 is not complete while required evidence remains
pending. Use the records under `docs/evidence/sprint-1/` to execute the outstanding
tests. The product owner may then either:

1. approve Sprint 1 after all required tests pass; or
2. explicitly accept a named exception with rationale, risk, owner, and target date.

After that decision, update this record, the traceability matrix, issue #30, and the
Sprint 1 tracker. Sprint 2 planning may proceed only after Sprint 1 approval and an
approved Sprint 2 specification; Sprint 2 implementation may not begin from this
record alone.
