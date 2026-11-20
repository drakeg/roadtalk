# RoadTalk Sprint Plan

RoadTalk uses sequential, acceptance-driven sprints. Detailed specifications and evidence remain under `docs/sprints/` and `docs/evidence/`; this file is the root roadmap required by the Mad Mallard Repository Standards.

## Completed delivery

- Sprints 0–14: product foundation through premium/readiness work; see `docs/sprints/` for authoritative scope and acceptance.
- Sprint 15 — Production readiness: completed deterministic production contracts and final readiness review without authorizing a live production launch.
- Sprint 16 D01–D06: merged public-beta planning, launch authorization, DNS/TLS/ingress, identity/secrets, observability/incident, and backup/restore/DR preflight work.

## Sprint 16 — Public-beta readiness

**Goal:** turn Sprint 15 controls into executable, fail-closed public-beta preflight gates without silently authorizing public traffic, destructive operations, provider activation, or recurring spend.

| Deliverable | Issue | Status |
| --- | ---: | --- |
| D01 Planning/readiness baseline | #476 | Complete |
| D02 Launch authorization | #477 | Complete |
| D03 DNS/TLS/public ingress | #478 | Complete |
| D04 Identity/secrets/break-glass | #479 | Complete |
| D05 Observability/incident readiness | #480 | Complete |
| D06 Backup/restore/DR readiness | #481 | Complete |
| D07 Load/failover/degraded mode | #482 | In progress — PR #501 |
| D08 Support/privacy/security/legal | #483 | Planned next |
| D09 Provider/billing/store/cost | #484 | Planned |
| D10 Final public-beta go/no-go | #485 | Planned |

Sprint 16 does not itself authorize public-beta traffic, DNS cutover, production failure injection, real-money/provider/store activation, destructive production changes, or recurring spend.

## Next product milestone

After Sprint 16 acceptance, prioritize a narrowly scoped SMB pilot that can demonstrate customer value without broad consumer launch. The leading customer hypotheses are campgrounds/RV parks, small guided-tour/outdoor operators, and small convoy/event operations that need simple location-aware push-to-talk coordination. These are hypotheses, not validated demand; customer interviews and a paid pilot must validate them before broader commercialization.
