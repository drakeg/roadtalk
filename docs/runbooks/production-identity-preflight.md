# Production identity, secrets, and break-glass preflight

Sprint 16 owner: S16-D04 / #479.

## OIDC preflight

Before any public-beta or production action, verify that deployment automation uses GitHub Actions
OIDC scoped to `drakeg/roadtalk`, branch `main`, STS audience, and short-lived sessions no
longer than 60 minutes. Pull-request jobs must not assume production deployment roles.

Shared static AWS credentials and long-lived access keys remain prohibited.

## Role preflight

Production plan and apply roles remain separate, the apply role requires manual approval, and
wildcard actions/resources plus AdministratorAccess are prohibited. Runtime identities must not
modify IAM or read secrets outside the production namespace.

## Secret preflight

Production secret material must come from a managed store under `/roadtalk/production/`, be
fetched at runtime, and remain absent from repository content, CI logs, and Terraform state.
Rotation is required within 90 days and must have a named owner.

Provider credentials remain separately gated.

## Human-access preflight

Human access requires individual identities and MFA, with no shared users or direct long-lived
keys. Access-review cadence must not exceed 90 days.

## Break-glass preflight

Break-glass access is exceptional and requires MFA, a reason, a ticket/incident ID, a session
bounded to at most 60 minutes, audit logging, and post-use review. Shared emergency accounts and
standing admin sessions are prohibited.

## Evidence boundary

D04 validates deterministic preflight requirements only. It does not claim a live OIDC
assume-role exercise, secret rotation, break-glass exercise, or access review has occurred.

Source: `infrastructure/environments/production/identity-preflight-contract.json`  
Validator: `scripts/ci/check-identity-preflight.py`
