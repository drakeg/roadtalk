from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = (ROOT / "mobile" / "src" / "ai" / "MobileAiController.ts").read_text(encoding="utf-8")
SCREEN = (ROOT / "mobile" / "src" / "screens" / "AiToolsScreen.tsx").read_text(encoding="utf-8")


def test_mobile_ai_requires_explicit_foreground_actions() -> None:
    assert 'ownedController.run("summary")' in SCREEN
    assert 'ownedController.run("translation", targetLanguage)' in SCREEN
    assert 'ownedController.run("transcription")' in SCREEN
    assert "AppState.addEventListener" in SCREEN
    assert 'setAppActive(state === "active")' in SCREEN

    for forbidden in (
        "startRecording",
        "startAudioRecording",
        "setInterval",
        "setTimeout",
        "BackgroundFetch",
        "TaskManager",
    ):
        assert forbidden not in SCREEN
        assert forbidden not in CONTROLLER


def test_mobile_ai_preserves_authorization_and_privacy_boundaries() -> None:
    for required in (
        'authorizationSource: "existing_roadtalk_authorization"',
        "audiencePreserved: true",
        "userInitiated: true",
        "foregroundOnly: true",
        "backgroundCapture: false",
        "durableAudioRetention: false",
        "maxOutputChars: 1200",
        "maxOutputChars: 4000",
    ):
        assert required in CONTROLLER

    for forbidden in (
        "latitude",
        "longitude",
        "routeHistory",
        "nearbyUsers",
        "recipientIds",
        "apiKey",
        "providerKey",
        "modelId",
        "systemPrompt",
        "microphoneStream",
    ):
        assert forbidden not in CONTROLLER


def test_mobile_ai_degraded_states_clear_stale_results() -> None:
    assert "AI controls are offline. Existing AI results were cleared." in CONTROLLER
    assert "AI provider is disabled. Existing AI results were cleared." in CONTROLLER
    assert "AI controls are paused while RoadTalk is not in the foreground." in CONTROLLER
    assert "result: null" in CONTROLLER
