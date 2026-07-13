# Production Terraform root

Production infrastructure is intentionally not implemented in Sprint 1.

The production root remains separate from field test and will not reuse Terraform
workspaces. ECS/Fargate, ALB, RDS, managed Redis, NAT Gateway, and Multi-AZ resources
require their approved production-stage implementation, availability decision, and
cost review. Do not copy the single-host field-test topology into production.
