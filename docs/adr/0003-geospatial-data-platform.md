# ADR-0003: Geospatial data platform

- Status: Proposed
- Date: 2026-07-12
- Deciders: Product owner and RoadTalk architecture review
- Sprint: 0
- Requirements: S00-R02, S00-R04, S00-R05, S00-R10, S00-R11

## Context

RoadTalk must determine which active users are within an approved radius while preserving identity, channels, authorization, retention, and audit relationships. The data platform must support transactional application state and indexed geospatial queries without creating separate sources of truth prematurely.

## Decision

Use PostgreSQL with PostGIS as the durable system of record.

Represent proximity-query points using PostGIS `geography(Point, 4326)` where meter-based geodesic distance is required. Use GiST spatial indexes and `ST_DWithin` for radius eligibility queries.

Use Redis only as an expiring cache for active presence and coordination after its need is demonstrated; PostgreSQL remains authoritative for durable identity, policy, channel, and consent state.

Use Amazon RDS for PostgreSQL as the preferred managed production path. A lower-cost development or field-test topology may run PostgreSQL in a controlled non-production environment, but it must use the same migration and PostGIS behavior.

## Rationale

- PostgreSQL supplies transactions and relational integrity for core product state
- PostGIS adds native spatial types and indexed proximity operations
- `ST_DWithin` supports geography distances in meters and uses spatial indexes
- Amazon RDS documents support for PostGIS
- one durable database reduces synchronization and consistency risks during MVP development

## Constraints

- exact coordinates are sensitive data and must not appear in application logs or user-facing payloads
- location rows require freshness, accuracy, and consent metadata
- queries must apply authorization, channel, block/mute, and presence rules in addition to distance
- stale or implausible locations fail closed or enter an explicitly defined degraded state
- retention and deletion rules apply to derived data and backups as well as primary rows
- database access is private and least-privilege
- schema migrations are versioned, reviewed, and reversible when practical

## Alternatives considered

### DynamoDB with geohash indexing

Offers serverless scale but requires custom spatial bucketing and more application-level consistency logic. Reconsider if measured access patterns and scale outgrow PostgreSQL.

### Redis GEO as the sole location store

Fast for transient lookup but unsuitable as the durable authority for consent, identity, policy, and relational state. Redis may accelerate active-presence workloads later.

### Separate relational and geospatial databases

Rejected for the MVP because synchronization and operational costs exceed the demonstrated need.

## Consequences

### Positive

- relational and spatial rules share transactions
- familiar migration, backup, and recovery model
- accurate meter-based proximity operations
- managed RDS growth path

### Negative

- high-frequency location writes require careful update policy and indexing
- RDS creates a recurring baseline cost
- large-scale realtime presence may eventually require Redis or partitioning

## Validation

- define the logical entity model and ownership rules
- benchmark representative `ST_DWithin` queries using realistic active-user distributions
- verify spatial-index use with query plans
- test stale, inaccurate, blocked, muted, cross-channel, and boundary-distance cases
- verify deletion and retention behavior
- test backup restoration with PostGIS enabled

## Sources

- [PostGIS ST_DWithin](https://postgis.net/docs/ST_DWithin.html)
- [PostGIS guidance for radius queries](https://postgis.net/documentation/tips/st-dwithin/)
- [PostGIS spatial types](https://postgis.net/docs/using_postgis_dbmanagement.html)
- [Amazon RDS PostgreSQL PostGIS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Appendix.PostgreSQL.CommonDBATasks.PostGIS.html)
