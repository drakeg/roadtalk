# Sprint 1 Readiness

- Status: READY
- Decision date: 2026-07-12
- Issue: #16
- Acceptance: S00-T11

## Decision

RoadTalk is ready to plan and implement Sprint 1: Project Foundation after Sprint 0 closure is recorded. No unresolved foundational blocker prevents coding.

## Accepted technology baseline

- mobile: React Native, Expo development builds, TypeScript
- control API: Python, FastAPI, REST + WebSocket events
- data: PostgreSQL with PostGIS; Alembic migrations
- ephemeral coordination: Redis only when required
- media: LiveKit/WebRTC; LiveKit Cloud initially
- AWS: local Docker development; controlled EC2 field-test; ECS/RDS managed production path
- infrastructure: Terraform with S3 lockfile state, environment roots, explicit modules
- ingress: Caddy for field test; ALB for managed production control traffic
- observability: structured privacy-filtered logs, metrics, alarms, correlation IDs

## Sprint 1 repository layout

```text
mobile/
  app/
  src/
    api/
    components/
    features/
    navigation/
    state/
    test/
backend/
  app/
    api/
    domains/
      identity/
      location/
      proximity/
      channels/
      media/
    infrastructure/
    observability/
  migrations/
  tests/
infrastructure/
  bootstrap/
  environments/
  modules/
docs/
```

Exact scaffolding is a Sprint 1 deliverable and may refine names without changing accepted boundaries.

## First coding sequence

1. scaffold repository tooling and reproducible local setup
2. scaffold Expo development build and physical-device smoke path
3. scaffold FastAPI health/version endpoints and structured logging
4. add PostgreSQL/PostGIS and Alembic baseline
5. establish configuration and secret-reference pattern
6. establish unit/integration/API schema tests
7. establish CI formatting, linting, test, dependency, container, and Terraform checks
8. add field-test Terraform only when the Sprint 1 requirements authorize infrastructure implementation
9. add monitoring and deployment runbooks
10. implement only the Sprint 1 authentication/foundation requirements; later sprint features remain absent

## Required Sprint 1 engineering gates

- branch and pull request workflow resumes for code/infrastructure
- no credentials or local state committed
- every Terraform module uses separate `variables.tf` and `outputs.tf`
- OpenAPI and event schemas are versioned
- physical iOS and Android development-build smoke tests
- backend tests include auth/authorization boundaries
- database migrations tested empty and upgrade paths
- CI produces actionable failures
- logs pass sensitive-data scan
- deployment and rollback are reproducible
- README and runbooks allow a clean setup

## Accepted deferrals with owner/target

| Deferral | Owner | Target |
|---|---|---|
| Exact anonymous recovery/user profile behavior | Product/engineering | Sprint 2 |
| Location precision/frequency constants | Product/engineering, validated on devices | Sprint 3 |
| LiveKit physical-device PTT performance proof | Engineering | Sprint 1 technical integration, accepted feature in Sprint 4 |
| Redis deployment | Engineering | When WebSocket/presence scaling evidence requires it |
| Multi-AZ production topology | Operations/product | Before public availability commitment |
| Private channels | Product/engineering | Sprint 6 |
| Recording/transcription/AI | Product/privacy/security | Sprint 13 or separately approved change |
| Production legal text and store submissions | Product/legal | Before Sprint 15 launch |

## Risks carried forward

- mobile background behavior and battery require device evidence
- press-to-audible latency requires field measurement
- field-test single instance is intentionally not highly available
- LiveKit usage cost must be observed
- spoofed consumer-device location cannot be eliminated, only mitigated
- store policy and legal requirements can change and require revalidation

## Readiness checklist

- [x] architecture baseline
- [x] API architecture
- [x] logical data model
- [x] AWS topology and cost model
- [x] Terraform design
- [x] MVP wireframes
- [x] threat model
- [x] privacy model
- [x] measurable NFRs
- [x] accepted ADRs
- [x] traceability
- [x] no unresolved foundational blocker
