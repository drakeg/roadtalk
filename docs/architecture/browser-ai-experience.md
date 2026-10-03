# Browser AI experience

Sprint 13 D07 adds a dependency-free browser control surface for the approved AI capabilities without adding a live provider or automatic capture path.

## Explicit action

Summary, translation and transcription are initiated only by button activation. The module contains no microphone API, MediaRecorder, timer, polling loop or automatic network request.

Transcription action payloads carry the fixed D02 foreground-consent invariants:

- user initiated = true;
- foreground only = true;
- background capture = false;
- durable audio retention = false.

The browser module does not itself capture audio. D04 remains authoritative for any eventual foreground audio lifecycle.

## Authorized source boundary

The host must supply an already-authorized source containing only source ID, source kind, source language and the existing RoadTalk authorization marker. The browser cannot mint authorization, audience expansion or provider configuration.

Summary/translation action builders include bounded output sizes and translation explicitly sets `audiencePreserved=true`.

## Accessibility

Controls use native buttons/selects, an explicit select label, a heading relationship, visible keyboard focus, minimum 44px control height, and a polite live status region.

## Disabled/offline/degraded state

Controls remain disabled until an authorized source is present, connectivity is explicitly available, and provider mode is the deterministic `test` mode. Offline or disabled-provider transitions clear any displayed result and announce the degraded state.

## Integration boundary

The module has no built-in `fetch`, WebSocket, EventSource or XMLHttpRequest call. A host may inject an `onAction` callback for deterministic/local integration. D07 does not authorize wiring that callback to an external/live provider.

## Cost/provider boundary

No new dependency, hosted service, paid API, live AI provider, AWS AI resource or recurring spend is introduced.
