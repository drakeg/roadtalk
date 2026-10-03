from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "browser" / "ai-controls.html").read_text(encoding="utf-8")
JS = (ROOT / "browser" / "ai-controls.js").read_text(encoding="utf-8")


def test_browser_ai_controls_are_explicit_and_accessible() -> None:
    for token in (
        'aria-labelledby="roadtalk-ai-heading"',
        'role="status"',
        'aria-live="polite"',
        '<label for="ai-target-language">',
        'type="button"',
        "Request foreground transcription",
    ):
        assert token in HTML

    assert 'addEventListener("click"' in JS
    assert "getUserMedia" not in JS
    assert "MediaRecorder" not in JS
    assert "setInterval" not in JS
    assert "setTimeout" not in JS


def test_browser_ai_payload_is_closed_and_preserves_authorization() -> None:
    for required in (
        'authorizationSource: "existing_roadtalk_authorization"',
        "authorizedOnly: true",
        "audiencePreserved: true",
        "userInitiated: true",
        "foregroundOnly: true",
        "backgroundCapture: false",
        "durableAudioRetention: false",
        "maxOutputChars: 1200",
        "maxOutputChars: 4000",
    ):
        assert required in JS

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
        assert forbidden not in JS


def test_browser_ai_has_no_automatic_network_or_provider_activation() -> None:
    assert "fetch(" not in JS
    assert "XMLHttpRequest" not in JS
    assert "WebSocket" not in JS
    assert "EventSource" not in JS
    assert "openai" not in JS.lower()
    assert "bedrock" not in JS.lower()
    assert "providerMode === \"test\"" in JS
    assert 'providerMode = value === "test" ? "test" : "disabled"' in JS


def test_browser_ai_clears_stale_results_for_offline_or_disabled_state() -> None:
    assert "AI controls are offline. Existing AI results were cleared." in JS
    assert "AI provider is disabled. Existing AI results were cleared." in JS
    assert 'resultText.textContent = "";' in JS
    assert "result.hidden = true;" in JS
