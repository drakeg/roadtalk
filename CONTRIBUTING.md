# Contributing to RoadTalk

## Initial documentation phase

During the initial documentation-only phase, focused documentation changes could be committed directly to `main`. That exception ended when application code and infrastructure implementation began. Current work uses focused branches and pull requests.

## Branches

For application code, infrastructure implementation, and post-initialization work, create focused branches from `main`:

- `sprint/<number>-<description>` for approved sprint work
- `fix/<description>` for approved corrective work
- `docs/<description>` for documentation-only reconciliation

## Pull requests

A pull request must include:

1. sprint, tracker, or issue reference
2. summary of the exact change
3. requirements or acceptance criteria addressed
4. automated and manual tests performed and results
5. documentation changed, or an explicit explanation of why no documentation changes are needed
6. security/privacy/provider/cost impact
7. known limitations or follow-up work

Code, tests, and documentation are one deliverable. Do not intentionally defer required tests or documentation to a later cleanup pull request.

Draft pull requests are encouraged while work is incomplete.

## Definition of Ready

A work item is ready only when it has a clear outcome, requirements, acceptance criteria, dependencies, priority, and an approved tracker/sprint or separately documented corrective-work decision.

## Definition of Done

A work item is done only when:

- implementation and user/operator/developer documentation describe the same behavior;
- new or changed behavior has appropriate automated acceptance and regression coverage;
- obsolete tests and stale documentation are updated or removed in the same pull request;
- required automated and manual checks pass;
- security, privacy, provider, compatibility, and cost impacts are reviewed;
- sprint/tracker/evidence records are updated when the change affects them; and
- the pull request is approved and merged.

A passing implementation suite does not make a change done when its documentation is stale, and documentation alone does not make changed behavior done when regression coverage is missing.


## Coding and validation standards

All implementation work follows these repository-wide standards:

- preserve established architecture, typing, formatting, naming, security and privacy conventions;
- keep changes focused to the active issue/sprint and avoid unrelated refactors;
- add or update automated regression coverage with every behavior change;
- update architecture, runbooks, sprint evidence and user/developer documentation in the same pull request when behavior changes;
- never weaken an authorization, privacy, security, migration, dependency or cost gate merely to make CI pass;
- inspect the final stored diff/source after automated or connector-based edits so escaped-newline, truncation and partial-write corruption cannot reach review;
- before opening a pull request, run the applicable local parity gates. Backend changes use `make pre-pr-check`; migration changes additionally use `make backend-migrate backend-migration-check`; mobile changes use `make mobile-doctor mobile-typecheck mobile-test`;
- a CI failure is repaired on the same branch/pull request whenever practical. Re-run the complete relevant gate set after the repair rather than fixing only the first reported symptom.

## Sprint documentation standard

Every sprint must have an approved specification/readiness record before implementation, a tracker with ordered deliverables, requirements and acceptance tests, synchronized evidence during implementation, and a final review/traceability record before acceptance. Sprint documentation must identify exclusions, provider/cost boundaries, known evidence exceptions and follow-up work. A later sprint does not silently authorize work excluded from an earlier sprint.
