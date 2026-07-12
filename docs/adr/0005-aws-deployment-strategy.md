# ADR-0005: AWS deployment strategy

- Status: Accepted
- Date: 2026-07-12
- Deciders: Product owner and RoadTalk architecture review
- Sprint: 0
- Requirements: S00-R05, S00-R06, S00-R07

## Context

RoadTalk needs inexpensive development and field testing without locking production into a fragile single-server design. The realtime media plane has different networking and scaling needs from the API.

## Decision

Use three explicit stages:

1. **Local development:** Docker Compose for API, PostgreSQL/PostGIS, and optional Redis; LiveKit local development or Cloud project.
2. **Controlled field test:** one ARM EC2 instance for Caddy, API, PostgreSQL/PostGIS, and Redis with encrypted EBS and automated off-instance backups; LiveKit Cloud for media. This is non-production and accepts single-instance downtime.
3. **Production:** ECS Fargate for the API, ALB for HTTPS/WebSocket control traffic, private RDS PostgreSQL/PostGIS, managed Redis only when required, and LiveKit Cloud initially. Multi-AZ and additional tasks are enabled when public availability or measured demand requires them.

Use one AWS Region, initially `us-east-1`. Do not use a NAT Gateway in the bootstrap field-test design. Do not self-host LiveKit until measured cost, control, or compliance needs justify its operational burden.

## Consequences

The field-test environment is affordable and simple but not highly available. Production has higher fixed cost but separates failure domains and supports scaling. Terraform must make stage boundaries explicit and must not imply that the field-test topology is production-ready.

## Validation

Review costs, recovery, data protection, network paths, deployment promotion, and the documented triggers for moving between stages.
