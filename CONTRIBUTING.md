# Contributing to RoadTalk

## Initial documentation phase

During the initial documentation-only phase, focused documentation changes may be committed directly to `main`. Each commit must remain within the active sprint and preserve requirements, decisions, tests, and history.

This exception ends when application code or infrastructure implementation begins.

## Branches

For application code, infrastructure implementation, and post-initialization work, create focused branches from `main`:

- `sprint/<number>-<description>` for planned sprint work
- `fix/<description>` for approved corrective work
- `docs/<description>` for later documentation-only work that requires review

## Pull requests

A pull request must include:

1. sprint or issue reference
2. summary of the exact change
3. requirements addressed
4. tests performed and results
5. deliverables produced
6. known limitations or follow-up work

Draft pull requests are encouraged while work is incomplete.

## Definition of Ready

A work item is ready only when it has a clear outcome, requirements, acceptance criteria, dependencies, priority, and sprint assignment.

## Definition of Done

A work item is done only when implementation and documentation are complete, automated and manual acceptance tests pass, security and privacy impacts are reviewed, and the pull request is approved and merged.
