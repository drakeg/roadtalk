# Sprint 16 specification: Public-beta readiness

- Planning issue: #476
- Implementation tracker: #486
- Delivery issues: #477–#485
- Baseline: Sprint 15 deterministic production-readiness controls accepted.

## Objective

Convert Sprint 15's deterministic readiness contracts and named live-evidence exceptions into
executable, fail-closed public-beta preflight gates without launching public beta, shifting real
user traffic, cutting over DNS, activating real-money/provider/store integrations, or authorizing
new recurring spend.

## Requirements

- **S16-R01 — Launch authorization:** Public-beta launch authorization is explicit, named, scoped,
  time-bounded, fail-closed, and defaults to disabled.
- **S16-R02 — DNS/TLS/ingress:** DNS ownership, certificate validation, public ingress, cutover,
  rollback, and health-check sequencing are defined and testable before live cutover.
- **S16-R03 — Identity/secrets:** Production OIDC, least privilege, secret scope/rotation, human
  access, and break-glass evidence are executable preflight requirements.
- **S16-R04 — Operational readiness:** Health, SLO, alert-delivery, incident ownership, severity,
  escalation, and privacy-safe telemetry have explicit preflight evidence.
- **S16-R05 — Backup/DR:** Backup integrity, isolated restore, RPO/RTO measurement format, DR
  approval, and destructive-safety boundaries are executable and evidence-producing.
- **S16-R06 — Resilience validation:** Load, failover, degraded-mode, dependency failure, and
  capacity tests have bounded profiles, stop conditions, cost guards, and explicit environments.
- **S16-R07 — Security/privacy launch gate:** High-risk findings, privacy regressions, unsafe
  configuration, and unsupported tracking behavior block launch unless an approved expiring
  exception exists.
- **S16-R08 — Support/legal obligations:** Support coverage, incident communications, retention,
  deletion, terms/privacy content, and unresolved legal obligations are recorded before launch.
- **S16-R09 — Provider/cost boundaries:** Premium/payment/store/provider activation remains
  disabled until credentials, fees, budget caps, billing ownership, legal/store obligations, and
  kill switches are separately approved.
- **S16-R10 — Evidence honesty:** Simulations, local tests, sandbox behavior, and deterministic CI
  are never presented as live public-beta or production evidence.
- **S16-R11 — No-spend/no-launch default:** Planning and preflight automation must not create
  recurring spend, public traffic, DNS cutover, destructive changes, or real-money flows.
- **S16-R12 — Final go/no-go:** D10 maintains bidirectional requirements/tests/deliverables/PR/
  evidence traceability and records only the scope actually proven.

## Acceptance tests

- **S16-T01:** Launch authorization validator rejects missing, expired, unnamed, over-broad, or
  default-enabled authorization.
- **S16-T02:** DNS/TLS/ingress preflight rejects ambiguous ownership, invalid certificate state,
  missing rollback, or unbounded cutover.
- **S16-T03:** Identity/secrets preflight rejects static/shared credentials, unscoped secret
  access, missing rotation, or unaudited break-glass configuration.
- **S16-T04:** Operational-readiness checks reject missing health/SLO/alert ownership or telemetry
  that exposes prohibited sensitive fields.
- **S16-T05:** Backup/restore checks require isolated restore evidence and distinguish target
  RPO/RTO from measured results.
- **S16-T06:** Resilience profiles enforce bounded load, retries, duration, cost, stop conditions,
  and explicit non-production/live authorization state.
- **S16-T07:** Security/privacy gate fails closed on unresolved HIGH/CRITICAL findings and
  prohibited data handling without a valid exception.
- **S16-T08:** Support/legal checklist records owners, escalation, retention/deletion, terms/privacy,
  and unresolved obligations without claiming legal approval that did not occur.
- **S16-T09:** Provider/billing/store configuration remains disabled unless a separately approved
  activation plan exists.
- **S16-T10:** CI/evidence clearly labels deterministic, sandbox, simulated, and live evidence.
- **S16-T11:** Planning and preflight changes prove no launch, DNS cutover, recurring spend,
  destructive operations, or real-money activation is authorized.
- **S16-T12:** Final review covers S16-R01–R12, S16-T01–T12, D01–D10, PRs, evidence, and named
  unresolved launch blockers.

## Locked delivery order

D01 #476, then strictly #477 → #478 → #479 → #480 → #481 → #482 → #483 → #484 → #485.

## Explicit exclusions until separately approved

Sprint 16 planning and preflight work does not itself authorize public-beta launch, production
traffic, DNS cutover, public marketing launch, production failure injection, destructive
infrastructure changes, production data migration, irreversible database changes, real-money
payment/store/provider activation, new recurring spend, or claims of live evidence not actually
collected.
