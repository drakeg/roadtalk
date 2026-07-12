# Sprint 0 Traceability Matrix

- Status: Complete
- Issue: #15
- Date: 2026-07-12

| Requirement | Deliverable(s) | Acceptance test(s) | Evidence/issues |
|---|---|---|---|
| S00-R01 System architecture | D01 | T01, T02 | System architecture; #6 |
| S00-R02 Technology decisions | D01, D02 | T01 | ADR-0001 through ADR-0005; #4, #6 |
| S00-R03 API architecture | D03 | T02 | API architecture; #5 |
| S00-R04 Data architecture | D04 | T03 | Logical data model; #7 |
| S00-R05 AWS architecture | D05 | T04 | AWS architecture, ADR-0005; #8 |
| S00-R06 Cost baseline | D06 | T04 | AWS cost model; #10 |
| S00-R07 Terraform design | D07 | T05 | Terraform design; #9 |
| S00-R08 UI wireframes | D08 | T06 | Wireframe specification and SVG; #11 |
| S00-R09 Security | D09 | T07 | Threat model; #12 |
| S00-R10 Privacy | D10 | T08 | Privacy model; #14 |
| S00-R11 Non-functional requirements | D11 | T09 | NFR targets; #13 |
| S00-R12 Traceability | D12 | T10 | This matrix; #15 |
| S00-R13 Sprint 1 readiness | D13 | T11 | Sprint 1 readiness; #16 |
| All | D14 | T12 | Sprint 0 review record; #17 |

## Forward dependency mapping

| Sprint | Depends on Sprint 0 |
|---|---|
| Sprint 1 — Project Foundation | Accepted mobile/API/AWS/Terraform ADRs, repository layout, CI gates, secrets, observability, authentication boundary. |
| Sprint 2 — Identity | Account/device/session/profile schema, API versioning, callsign constraints, secure storage, consent model. |
| Sprint 3 — Location | PostGIS model, permission flows, freshness/accuracy policy, privacy retention, battery/data targets. |
| Sprint 4 — Push-To-Talk | LiveKit ADR, grant contract, media trust boundary, PTT wireframes, latency/reconnect targets, threat controls. |
| Sprint 5 — Proximity Engine | ST_DWithin design, authorization order, block/mute/channel joins, boundary test matrix, capacity target. |

## ADR disposition

| ADR | Decision | Status |
|---|---|---|
| ADR-0001 | React Native + Expo development builds + TypeScript | Accepted |
| ADR-0002 | Python/FastAPI modular monolith control plane | Accepted |
| ADR-0003 | PostgreSQL/PostGIS durable geospatial store | Accepted |
| ADR-0004 | LiveKit/WebRTC media plane; LiveKit Cloud initially | Accepted |
| ADR-0005 | Local, controlled field-test, and managed production AWS stages | Accepted |

## Bidirectional audit

- Every S00-R requirement maps to deliverables and tests.
- Every S00-T test maps to one or more requirements and evidence.
- Every S00-D deliverable has a repository artifact and issue.
- Every accepted ADR maps to a Sprint 0 requirement.
- Every Sprint 1–5 dependency has an originating Sprint 0 decision or document.
- No Sprint 1 implementation was introduced.
