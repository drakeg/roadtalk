# Mobile AI experience

Sprint 13 D08 adds an explicit React Native AI control surface using RoadTalk's existing foreground lifecycle and accessibility patterns.

## Explicit actions

Summary, translation and transcription are invoked only from user-activated Pressable controls. The controller does not run an AI action when a source is attached or when connectivity/provider state changes.

The transcription action carries the D02 consent invariants: user initiated, foreground only, no background capture and no durable audio retention. D08 does not add microphone capture or recording APIs; the D04 server lifecycle remains authoritative.

## Foreground/offline/provider-disabled behavior

The screen watches React Native AppState. Leaving the foreground immediately moves the AI controller to unavailable state and clears any displayed result. Offline state and disabled provider state do the same.

Controls are available only when all four conditions hold: an authorized source exists, the app is active, connectivity is available, and provider mode is deterministic test.

## Authorization and audience

The source is a closed application-owned descriptor carrying only source ID/kind/language and existing RoadTalk authorization. Translation explicitly preserves audience. Mobile AI does not create channel membership, proximity/media eligibility, recipients, moderation authority or unrelated-user discovery.

## Accessibility

The screen uses native headers, labelled buttons, selected-state language controls, polite live regions, selectable result text and 48px minimum action heights.

## Integration boundary

The controller accepts an injected action handler. The default navigable screen remains disabled until an authorized source, connectivity state and deterministic test handler/provider mode are supplied. D08 does not activate a live provider, add provider credentials or introduce a new networking library.

## Cost/provider boundary

No external AI service, paid model/API, AWS AI resource, background job or recurring spend is introduced.
