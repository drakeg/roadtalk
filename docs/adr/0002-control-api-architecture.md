# ADR-0002: Control API architecture

- Status: Proposed
- Date: 2026-07-12
- Deciders: Product owner and RoadTalk architecture review
- Sprint: 0
- Requirements: S00-R01, S00-R02, S00-R03, S00-R04, S00-R05

## Context

RoadTalk needs APIs for identity, profiles, location updates, proximity authorization, channel membership, media-token issuance, abuse controls, and operational telemetry. It also needs bidirectional transient events, but realtime audio must not pass through the application API.

The MVP should avoid distributed-system complexity while preserving clear internal boundaries.

## Decision

Use Python with FastAPI as a modular monolith for the control plane.

Use:

- HTTPS REST for durable commands, queries, and token issuance
- WebSockets for transient control events that require immediate bidirectional delivery
- background worker execution only for measured asynchronous workloads
- PostgreSQL/PostGIS as the durable source of truth
- Redis only for ephemeral presence, rate limits, cross-instance fanout, or LiveKit clustering when required

Organize code by domain boundaries rather than technical layers alone: identity, location, proximity, channels, media authorization, moderation hooks, and operations.

## Rationale

- FastAPI uses standard Python type hints and produces schema-driven APIs
- FastAPI supports WebSockets through Starlette
- WebSocket behavior can be covered with its test client
- Python aligns with geospatial, data-processing, and future AI needs
- a modular monolith is simpler to deploy, observe, test, and transact than initial microservices
- the media plane remains independently scalable through LiveKit/WebRTC

## Constraints

- WebSocket connection state cannot live only in process memory once multiple API instances exist
- long-running or CPU-heavy work must not block request workers
- media packets never traverse the FastAPI service
- domain modules must not bypass authorization or data-ownership boundaries
- OpenAPI and event schemas are versioned and treated as contracts
- idempotency is required for retry-prone mobile mutations where duplication would be harmful

## Alternatives considered

### Node.js with NestJS

Strong TypeScript alignment and realtime ecosystem. Not selected because Python provides a direct path for the expected geospatial/AI work and FastAPI supplies the required async API surface with less framework ceremony.

### Go

Excellent concurrency and operational footprint. Not selected for the MVP because development speed and future Python-based processing outweigh the likely control-plane efficiency gain at initial scale.

### Serverless functions per endpoint

Can reduce idle compute cost but creates additional local-development, connection-state, deployment, and tracing complexity for WebSockets and cohesive domain transactions. Re-evaluate after traffic shape is measured.

### Initial microservices

Rejected because independent deployment, networking, schemas, and failure modes would add complexity before boundaries and scaling needs are validated.

## Consequences

### Positive

- fast API iteration with explicit schemas
- one transactional boundary for early domain workflows
- simpler deployment and observability
- clean separation from the media plane
- later extraction remains possible around domain modules

### Negative

- horizontal WebSocket scaling eventually requires shared coordination
- careless module coupling could create a difficult monolith
- Python workers require measurement for CPU-bound workloads

## Validation

- document REST and WebSocket contract conventions
- trace registration, location, proximity, transmit authorization, and subscription flows
- prove unit and integration test strategies for REST and WebSockets
- confirm module dependency direction and prohibit circular domain dependencies
- load-test control events separately from the media plane
- define extraction triggers for any future service boundary

## Sources

- [FastAPI](https://fastapi.tiangolo.com/)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [Testing FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/testing-websockets/)
- [FastAPI deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/)
