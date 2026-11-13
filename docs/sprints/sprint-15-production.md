# Sprint 15 specification: Production readiness

- Planning issue: #444
- Implementation tracker: #455
- Delivery issues: #445–#454
- Baseline: Sprints 0–14 accepted.

## Objective

Make RoadTalk production-ready through explicit environment, security, observability, backup/restore, deployment/rollback, resilience, privacy/security, cost/support and evidence gates without claiming live-production behavior that has not actually been exercised.

## Requirements

- **S15-R01 — Environment contract:** Define production topology, domains/TLS, immutable artifacts, environment separation, configuration boundaries and deployment provenance.
- **S15-R02 — Secrets/IAM:** Production credentials use least privilege, managed secret boundaries, explicit rotation expectations and no shared static CI credentials.
- **S15-R03 — Operational health:** Define health/readiness, structured logging, metrics, alerting and SLO/error-budget signals with privacy-safe telemetry.
- **S15-R04 — Backup/restore:** Define encrypted backup scope, retention, restore validation, recovery objectives and evidence boundaries.
- **S15-R05 — Deployment/rollback:** Releases are versioned, approval-gated and rollback-capable with migration-safety rules and explicit stop/disable controls.
- **S15-R06 — Resilience:** Bound rate limits, dependency failures, database/network degradation, retries/timeouts and resource use without widening authorization.
- **S15-R07 — Security release gate:** Production release checks cover dependencies, containers, IaC, secrets, unsafe configuration and known high-risk findings.
- **S15-R08 — Privacy release gate:** Production logging/metrics/alerts exclude raw secrets, raw payment instruments, unnecessary precise location history and unrelated-user data.
- **S15-R09 — Cost/support/legal:** Recurring infrastructure/provider costs, support ownership, operational obligations and legal/privacy responsibilities are documented before release approval.
- **S15-R10 — Provider boundaries:** Premium/payment/store and other external providers remain disabled unless separately approved with credentials, fees, rollback and legal responsibilities documented.
- **S15-R11 — Evidence honesty:** Deterministic/local/CI evidence is clearly separated from live load, failover, disaster recovery, billing, public-beta and production traffic evidence.
- **S15-R12 — Final acceptance:** Maintain bidirectional requirements/tests/deliverables/PR/evidence traceability; D10 accepts only proven Sprint 15 readiness scope.

## Acceptance tests

- **S15-T01:** Production configuration/topology tests reject ambiguous environment or insecure deployment settings.
- **S15-T02:** IAM/secrets checks prove no committed/shared production credentials and enforce least-privilege configuration boundaries.
- **S15-T03:** Health/metrics/logging tests prove bounded operational signals and privacy-safe failure behavior.
- **S15-T04:** Backup/restore evidence proves deterministic backup integrity and restore validation where authorized, with named live-DR exceptions.
- **S15-T05:** Deployment/rollback tests prove immutable version selection, approval gates, migration checks and rollback/disable behavior.
- **S15-T06:** Failure-mode tests cover timeouts, dependency unavailability, bounded retries/rate limits and graceful degradation.
- **S15-T07:** CI security gates fail closed on prohibited secrets, critical/high findings without approved disposition, unsafe containers/IaC and unsupported runtimes.
- **S15-T08:** Privacy gates prove logs/metrics/alerts exclude sensitive fields and do not create new tracking profiles.
- **S15-T09:** Cost/support/legal evidence records recurring spend assumptions, owners, support/incident paths and explicit unresolved obligations.
- **S15-T10:** External-provider configuration remains disabled unless a separately approved provider plan is present.
- **S15-T11:** Evidence documents which production/load/failover/DR/billing checks were not performed and never presents simulations as live evidence.
- **S15-T12:** Final traceability review covers S15-R01–R12, S15-T01–T12, D01–D10, PRs and named exceptions.

## Delivery order and completed PRs

- D01 / #444 → PR #456
- D02 / #445 → PR #459
- D03 / #446 → PR #460
- D04 / #447 → PR #461
- D05 / #449 → PR #462
- D06 / #450 → PR #463
- D07 / #451 → PR #464
- D08 / #452 → PR #465
- D09 / #453 → PR #466
- D10 / #454 → final readiness review PR

## Explicit exclusions until separately approved

Sprint 15 acceptance does not itself authorize a production/public-beta launch, DNS cutover, real-user traffic, real-money/provider/store activation, new recurring spend, destructive infrastructure changes, production data migration, irreversible database changes, public marketing launch, or claims of live load/failover/disaster-recovery/billing evidence not actually collected.

The D10 final review is recorded in `docs/evidence/sprint-15-d10-final-production-readiness.md`.
