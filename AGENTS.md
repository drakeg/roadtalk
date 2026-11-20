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

- During the initial documentation-only phase, focused documentation commits may be made directly to `main`.
- Once application code or infrastructure implementation begins, use feature branches and pull requests.
- Prefer small, reviewable commits.
- Update documentation with the behavior or decision it describes.
- Record material architecture choices as ADRs under `docs/adr/`.
- Do not mark work complete until its acceptance tests pass.


## Mad Mallard development standards

- Follow `Build → Deploy → Test → Fix → Redeploy → Continue` within authorized environments; do not stop merely because a PR, sprint, build, or deployment finishes.
- Continue automatically to the next ready Sprint 16/backlog item unless an action requires explicit authorization, destructive production changes, new cost, or another consequential decision.
- Follow `drakeg/madmallard-repository-standards` as the centralized baseline while preserving stricter RoadTalk-specific security, privacy, provider, evidence, and spend rules.
- Keep `SPRINTS.md`, `BACKLOG.md`, `RELEASES.md`, `SECURITY.md`, README, sprint evidence, runbooks, and implementation synchronized.
- Preserve RoadTalk as an independent repository; do not share services, data, auth, or implementation with unrelated projects unless explicitly requested.
- Treat the Docker Compose stack and LAN override as maintained test environments. CI or local failures are P0 break/fix work.
- Commercial work must prioritize measurable SMB value and a credible paid pilot; never invent demand, willingness to pay, revenue, or customer feedback.

## README badge maintenance

The badge block directly below the README H1 must reflect only verified repository facts. Inspect manifests, Compose/Docker files, Terraform/workflows, releases, and licensing before changing badges. Use live GitHub Actions/statistic badges where applicable; never hardcode passing CI/security status. Technology versions may be shown only when verified in repository configuration. Do not add a release badge without a published GitHub release or a license badge without a repository license file. Run `python scripts/ci/check-repository-standards.py` when badge-supporting technologies, workflows, release state, or licensing change.
