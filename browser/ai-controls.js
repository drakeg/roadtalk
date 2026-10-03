"use strict";

(function () {
  const SUPPORTED_LANGUAGES = new Set(["en", "es", "fr", "de"]);
  const SOURCE_KINDS = new Set(["transcript", "message_window"]);
  const CAPABILITIES = new Set(["summary", "translation", "transcription"]);

  function requireAuthorizedSource(source) {
    if (
      !source ||
      typeof source.sourceId !== "string" ||
      !SOURCE_KINDS.has(source.sourceKind) ||
      !SUPPORTED_LANGUAGES.has(source.sourceLanguage) ||
      source.authorizedOnly !== true ||
      source.authorizationSource !== "existing_roadtalk_authorization"
    ) {
      throw new Error("authorized RoadTalk source required");
    }
    return Object.freeze({
      sourceId: source.sourceId,
      sourceKind: source.sourceKind,
      sourceLanguage: source.sourceLanguage,
      authorizedOnly: true,
      authorizationSource: "existing_roadtalk_authorization",
    });
  }

  function buildAction(capability, source, targetLanguage) {
    if (!CAPABILITIES.has(capability)) {
      throw new Error("unsupported AI capability");
    }

    const authorized = requireAuthorizedSource(source);
    const base = {
      capability,
      sourceId: authorized.sourceId,
      sourceKind: authorized.sourceKind,
      sourceLanguage: authorized.sourceLanguage,
      authorizationSource: authorized.authorizationSource,
    };

    if (capability === "translation") {
      if (
        !SUPPORTED_LANGUAGES.has(targetLanguage) ||
        targetLanguage === authorized.sourceLanguage
      ) {
        throw new Error("translation target must be supported and distinct");
      }
      return Object.freeze({
        ...base,
        targetLanguage,
        maxOutputChars: 4000,
        audiencePreserved: true,
      });
    }

    if (capability === "summary") {
      return Object.freeze({
        ...base,
        maxOutputChars: 1200,
      });
    }

    return Object.freeze({
      ...base,
      consent: Object.freeze({
        userInitiated: true,
        foregroundOnly: true,
        backgroundCapture: false,
        durableAudioRetention: false,
      }),
    });
  }

  function mountBrowserAiControls(root, options) {
    if (!(root instanceof HTMLElement)) {
      throw new Error("browser AI root element is required");
    }

    const status = root.querySelector("#ai-status");
    const result = root.querySelector("#ai-result");
    const resultText = root.querySelector("#ai-result-text");
    const resultProvenance = root.querySelector("#ai-result-provenance");
    const summaryButton = root.querySelector("#ai-summary");
    const translateButton = root.querySelector("#ai-translate");
    const transcribeButton = root.querySelector("#ai-transcribe");
    const targetSelect = root.querySelector("#ai-target-language");
    const controls = [summaryButton, translateButton, transcribeButton, targetSelect];

    if (controls.some((control) => !control) || !status || !result || !resultText || !resultProvenance) {
      throw new Error("browser AI controls are incomplete");
    }

    let currentSource = null;
    let online = options && options.online === true;
    let providerMode = options && options.providerMode ? options.providerMode : "disabled";
    const onAction =
      options && typeof options.onAction === "function"
        ? options.onAction
        : async function () {
            throw new Error("AI action handler unavailable");
          };

    function clearResult(message) {
      result.hidden = true;
      resultText.textContent = "";
      resultProvenance.textContent = "";
      status.textContent = message;
    }

    function refreshAvailability() {
      const enabled = Boolean(currentSource) && online && providerMode === "test";
      controls.forEach((control) => {
        control.disabled = !enabled;
      });

      if (!currentSource) {
        clearResult("AI controls are unavailable until an authorized source is present.");
      } else if (!online) {
        clearResult("AI controls are offline. Existing AI results were cleared.");
      } else if (providerMode !== "test") {
        clearResult("AI provider is disabled. Existing AI results were cleared.");
      } else {
        status.textContent = "AI controls are ready for explicit action.";
      }
    }

    async function run(capability) {
      if (!currentSource || !online || providerMode !== "test") {
        refreshAvailability();
        return;
      }

      clearResult("Processing explicit AI request…");

      let targetLanguage;
      if (capability === "translation") {
        targetLanguage = targetSelect.value;
      }

      try {
        const action = buildAction(capability, currentSource, targetLanguage);
        const response = await onAction(action);
        if (!response || typeof response.text !== "string" || response.text.length === 0) {
          throw new Error("invalid AI result");
        }

        resultText.textContent = response.text;
        resultProvenance.textContent =
          "Source: " + action.sourceKind + " · " + action.sourceLanguage +
          (action.targetLanguage ? " → " + action.targetLanguage : "");
        result.hidden = false;
        status.textContent = "AI result ready.";
      } catch (_error) {
        clearResult("AI request is unavailable. No prior result is shown.");
      }
    }

    summaryButton.addEventListener("click", function () {
      void run("summary");
    });
    translateButton.addEventListener("click", function () {
      void run("translation");
    });
    transcribeButton.addEventListener("click", function () {
      void run("transcription");
    });

    return Object.freeze({
      setAuthorizedSource(source) {
        currentSource = requireAuthorizedSource(source);
        refreshAvailability();
      },
      clearAuthorizedSource() {
        currentSource = null;
        refreshAvailability();
      },
      setOnline(value) {
        online = value === true;
        refreshAvailability();
      },
      setProviderMode(value) {
        providerMode = value === "test" ? "test" : "disabled";
        refreshAvailability();
      },
      clearResult() {
        clearResult("AI result cleared.");
      },
    });
  }

  window.RoadTalkBrowserAi = Object.freeze({
    buildAction,
    mountBrowserAiControls,
  });
})();
