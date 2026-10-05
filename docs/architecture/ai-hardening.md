# Sprint 13 AI hardening

D09 turns the Sprint 13 planning boundaries into runtime and CI-enforced constraints.

## Replay and concurrency

The central AI provider boundary tracks a bounded set of active and recently completed request IDs. A request fails generically when its ID is already active, appears in the bounded replay window, or the configured in-flight limit has been reached.

Defaults are four concurrent operations and 256 recently completed request IDs. Configuration itself is bounded to prevent accidentally disabling the protection. Failed provider attempts are also entered into the replay window so retry storms cannot reuse an identical request identifier.

The replay state is process-local and intentionally contains UUIDs only; it does not retain source text, transcript text, audio, location or provider output.

## Generic failure behavior

Timeouts, provider exceptions, integrity mismatches, concurrency pressure and replay all resolve through the same non-disclosing `AI provider unavailable` boundary. Higher-level summary, translation and transcription services continue mapping that into capability-specific generic errors.

## Injection-like input

Authorized bounded text may contain instruction-like strings. Sprint 13 treats those strings strictly as content. They do not alter authorization, provider mode, audience or system configuration.

## Dependency and infrastructure gate

`scripts/ci/check-sprint-13-ai-hardening.py` fails CI if the approved implementation gains external AI/provider SDKs, direct network-client calls in AI implementation paths, AI cloud resources in Terraform, or provider/API-key activation in Compose.

The gate also verifies named reliability/privacy tests remain present and D09 evidence continues to state the $0 and evidence-exception boundaries.

## Compatibility

The provider API remains compatible with D03-D08 callers: disabled/test modes, request/result contracts and capability interfaces are unchanged. Hardening occurs inside the provider boundary.

## Cost

The hardening uses in-process Python data structures and deterministic CI only. It creates no cloud resource, external provider account, paid model/API, persistent data store or recurring service.
