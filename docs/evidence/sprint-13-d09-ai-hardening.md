# Sprint 13 D09 evidence — AI hardening

## Deterministic evidence

- The provider boundary rejects completed request-ID replay.
- Concurrent reuse of the same request ID fails generically.
- A bounded maximum concurrent request count fails closed under pressure.
- The replay cache is bounded and retains UUIDs only.
- Provider exceptions, timeout/integrity errors, replay and concurrency pressure do not disclose provider internals.
- Injection-like authorized text remains inert bounded content and does not alter authorization or configuration.
- Existing stale-source, oversized input/output, disabled-provider, foreground-only and stale-result-clearing tests remain CI-required.
- CI scans AI implementation paths, backend/mobile dependencies, Compose and Terraform for unapproved external AI/provider/network activation.

## Privacy and retention

No replay/concurrency state contains audio, transcript text, message text, location/route history, credentials, unrelated-user data or provider output. No durable audio/content retention or background collection is introduced.

## Provider and cost boundary

No external AI or speech provider is activated. No live model/provider credential, SDK, API endpoint, paid service or AWS AI resource is configured. Incremental recurring implementation cost remains $0.

## Evidence exceptions — NOT PERFORMED

Physical-device abuse/load testing, live-provider quota/rate behavior, live-provider privacy/retention behavior, production capacity testing and public-beta behavior were not performed and are not claimed.
