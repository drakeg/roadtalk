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
