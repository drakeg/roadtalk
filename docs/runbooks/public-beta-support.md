# Public-beta support runbook

Status: **draft preflight — public beta not authorized**

This runbook defines the minimum support and incident-communication shape RoadTalk must have before a public beta. It does not claim that staffing, contact channels, or coverage have been approved.

## Required owners before launch

- A named operational owner must be accountable for service health and routine support.
- A named incident-communications owner must be accountable for user-facing incident updates.
- Each owner needs a primary and backup escalation route that is not dependent on the affected RoadTalk service.

These owner assignments are currently unresolved and therefore block public-beta readiness.

## Support contact and coverage

Before launch, publish one user-facing support path in the application/site and one private operator escalation path. The user-facing path must state expected coverage and response behavior accurately. Do not imply 24×7 support unless staffing actually provides it.

Current state: **support contact and coverage model not yet approved; launch blocked.**

## Severity and escalation

- **SEV-1:** active security/privacy incident, widespread inability to use critical functionality, or risk of material user harm. Disable affected capability when needed, page the operational owner, and begin incident communications.
- **SEV-2:** major degraded capability affecting many users without immediate security/privacy harm. Engage the operational owner and publish status when user impact is material.
- **SEV-3:** localized defect or support request with a workaround. Track through the normal support queue.

Any security/privacy signal takes precedence over availability restoration if restoring service would broaden exposure.

## Communications

Incident updates must avoid credentials, exact location, raw authorization material, private user content, or unsupported root-cause claims. State verified impact, affected capability, mitigation, and next decision point. A post-incident review must separate observed facts from hypotheses.

## Launch blockers

Public beta remains blocked until:
- named operational and incident-communications owners are assigned;
- support contact and backup escalation paths exist;
- support coverage/response expectations are approved and published;
- incident communications have at least a tabletop/deterministic rehearsal appropriate to launch scope.

No live support exercise has been performed by D08.
