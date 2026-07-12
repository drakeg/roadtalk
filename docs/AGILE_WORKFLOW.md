# Agile and Kanban Workflow

## Board columns

| Column | Meaning | Exit condition |
|---|---|---|
| Backlog | Candidate work not yet committed | Prioritized and selected for refinement |
| Ready | Meets Definition of Ready | Pulled into the active sprint |
| In Progress | Actively being implemented | Implementation and developer validation complete |
| Review | Pull request or product review is active | Review feedback addressed |
| Testing | Acceptance tests are executing | All required tests pass |
| Done | Accepted and merged | Deliverables recorded and sprint evidence complete |
| Blocked | Cannot progress | Blocker resolved and documented |

## Work-in-progress limits

- One primary active sprint at a time.
- A person should normally own no more than one In Progress item.
- Blocked work remains visible and does not justify silently starting unrelated scope.

## Work-item fields

Every card should include:

- title and outcome
- sprint and requirement identifier
- priority
- owner
- dependencies
- acceptance criteria
- test evidence
- pull request or artifact links
- blocker and resolution notes, when applicable

## Ceremonies

- Sprint planning: confirm scope, requirements, tests, deliverables, and dependencies.
- Daily review: update board state and blockers.
- Sprint review: demonstrate deliverables and record acceptance results.
- Retrospective: record process improvements without rewriting completed history.

## GitHub mapping

Use GitHub Issues for work items, milestones for sprints, pull requests for reviewable changes, and a GitHub Project as the Kanban board.
