# Project Governance

## Purpose

RoadTalk is developed incrementally through approved sprints. The repository preserves the complete decision and delivery history.

## Authority

Committed documentation on `main` is authoritative. A draft pull request is a proposal and does not change approved scope until merged.

## Scope control

Sprint requirements, acceptance tests, and deliverables are treated as a locked baseline once approved. A proposed change must document:

- requested change
- reason
- affected requirements and tests
- schedule or dependency impact
- approval decision

No implementation may silently reinterpret or omit an approved requirement.

## Traceability

Each work item and pull request must trace to a sprint requirement. Each requirement must trace to at least one acceptance test and an explicit deliverable.

## Decision records

Material technical choices are documented as Architecture Decision Records. Superseded decisions remain in history and point to their replacements.
