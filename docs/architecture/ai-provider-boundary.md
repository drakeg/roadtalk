# AI provider boundary

Sprint 13 D03 defines the provider boundary without activating any external model or speech service.

## Modes

Only two modes are authorized:

- `disabled` — default; all AI operations fail closed with the generic error `AI provider unavailable`.
- `test` — deterministic local/CI adapter with no network, provider account, API key, hosted model or recurring cost.

There is intentionally no `live`, `openai`, `aws`, `azure`, `google`, or other external provider mode.

## Capability and health contract

Provider health exposes only mode, availability and the bounded capabilities `transcription`, `summary`, and `translation`. It exposes no provider URL, model identifier, credentials, quota or billing metadata.

## Boundary behavior

The server boundary applies a bounded timeout, validates request/result identity and capability, accepts only deterministic `test-v1` results, and normalizes provider exceptions to the stable non-disclosing error `AI provider unavailable`.

Fake/test adapters are permitted only in `local` and `test` environments. Field-test and production environments may use only the disabled provider under D03.

## Text transformation requests

Summary and translation provider requests are bounded text-only inputs. Translation requires explicit distinct source/target languages. Arbitrary provider/model/prompt/credential fields are not part of the request contract.

## Ephemeral transcription request

D03 defines a server-internal bounded `ephemeral_audio` request solely so D04 can compose a transcription lifecycle through this provider boundary. It is not an API or persistence schema. It has a strict byte bound and no URL, recording identifier, storage reference, provider selector or credential fields.

D03 does not persist audio, implement capture, or authorize background processing. D04 must preserve the D02 foreground-consent and no-durable-audio invariants.

## Cost and activation boundary

Incremental recurring implementation cost remains $0. No external AI/model provider, paid API, AWS AI service, network activation or provider credential is introduced by D03. A future live provider requires separate explicit approval under the Sprint 13 readiness gate.
