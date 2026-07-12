# Repository Guidance

## Source of truth

Treat this repository as the authoritative RoadTalk project record. Do not rely on an uncommitted chat summary when repository documentation exists.

## Scope discipline

- Work only within the active, approved sprint.
- Do not silently expand requirements.
- Preserve approved sprint wording.
- Propose scope changes through a documented change request.
- Keep unrelated changes out of a sprint branch or pull request.

## Delivery discipline

Every implementation change must identify:

- the sprint and requirement it satisfies
- the acceptance tests used
- the validation result
- any known limitation or deferred work

## Repository workflow

- Use feature branches and pull requests.
- Prefer small, reviewable commits.
- Update documentation in the same pull request when behavior or decisions change.
- Record material architecture choices as ADRs under `docs/adr/`.
- Do not mark work complete until its acceptance tests pass.
