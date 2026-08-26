# Route-awareness operations

Sprint 7 route awareness is deliberately local/GitHub-CI only. It has no scheduler,
worker, queue, Redis dependency, WebSocket, routing dataset, real routing provider, or
cloud monitoring service. Nearby remains the default behavior; Same-road is a
restrictive fail-closed filter.

## Safe operator signals

Use aggregate system metrics and semantic outcome codes only. Never log or expose a
corridor digest, provider corridor reference, direction, coordinate, heading, speed,
road name, route, participant reference, account/device identifier, or eligibility
reason.

Useful aggregate signals are:

- fresh current route-context count;
- expired current route-context count awaiting bounded cleanup;
- media grants in `delivery_reconciling` state;
- unexpired/non-revoked media-grant count;
- current location count.

A Same-road user with missing, expired, ambiguous, provider-failed, or mismatched
context is unavailable for Same-road delivery. Do not fall back to Nearby on that
user's behalf.

## Bounded recovery

There is no always-on cleanup process. Recovery is request/operator driven and bounded:

1. Recompute route context only from an already-accepted current foreground location.
2. Delete expired current route context with the bounded lifecycle cleanup path.
3. Reconcile active publications with the existing bounded proximity reconciliation
   path. It first marks delivery `delivery_reconciling`, commits the local denial, then
   performs provider unsubscribe/subscribe work.
4. If eligibility or provider work fails, keep the publication fail-closed and leave
   the semantic outcome `delivery_reconciling` for a later bounded retry.
5. Never retry in a tight loop. Each operator invocation must use the existing maximum
   batch limits (1..1000) and may be repeated only after inspecting aggregate state.

Pause, consent withdrawal, location deletion/expiry, logout, account/device/session
revocation, and route-mode changes already invalidate the authoritative location,
route-context, or media authority. Reconciliation must never recreate authority that
those boundaries removed.

## Failure triage

**Provider timeout/error:** Nearby traffic is unaffected. Same-road context is deleted
or unavailable; do not retain the failed provider payload or error detail.

**Database failure:** treat the operation as incomplete. Do not infer that provider
state grants local authority. Retry only through a bounded request/operator path after
database health is restored.

**Media partial failure:** local delivery denial wins. A failed unsubscribe/publish
cleanup remains `delivery_reconciling`; a later bounded reconciliation may retry the
provider cleanup.

**Expired route context:** it is ineligible immediately by query-time expiry checks even
before physical cleanup. Delete it through bounded cleanup; never extend its TTL.

**Mode change to Nearby:** current route context is removed and Nearby authorization
continues under the existing Sprint 5/6 rules.

**Pause/withdrawal/logout/revocation/deletion:** do not attempt route matching from stale
or revoked state. Existing cascade/revocation paths remove local authority; run bounded
media reconciliation only when provider cleanup remains outstanding.

## Privacy incident check

If logs, metrics, errors, or evidence contain a road/corridor value, direction, exact
location, participant/account/device identifier, provider payload, or eligibility
reason, treat that as a privacy regression. Preserve only the semantic event class and
aggregate count needed to diagnose the condition, remove the sensitive artifact, and
add a regression test before continuing Sprint 7.
