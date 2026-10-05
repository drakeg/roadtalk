import type {
  AiCapability,
  AiLanguage,
  AiProviderMode,
  AuthorizedAiSource,
  MobileAiAction,
  MobileAiActionHandler,
  MobileAiSnapshot,
} from "./types";

const supportedLanguages = new Set<AiLanguage>(["en", "es", "fr", "de"]);

export class MobileAiController {
  private listeners = new Set<() => void>();
  private source: AuthorizedAiSource | null = null;
  private online = false;
  private appActive = true;
  private providerMode: AiProviderMode = "disabled";
  private snapshot: MobileAiSnapshot = {
    status: "unavailable",
    message: "AI controls are unavailable until an authorized source is present.",
    source: null,
    result: null,
  };

  constructor(private readonly onAction: MobileAiActionHandler) {}

  subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  getSnapshot = () => this.snapshot;

  setAuthorizedSource(source: AuthorizedAiSource | null) {
    this.source = source;
    this.refreshAvailability();
  }

  setOnline(online: boolean) {
    this.online = online;
    this.refreshAvailability();
  }

  setAppActive(active: boolean) {
    this.appActive = active;
    this.refreshAvailability();
  }

  setProviderMode(mode: AiProviderMode) {
    this.providerMode = mode === "test" ? "test" : "disabled";
    this.refreshAvailability();
  }

  clearResult() {
    if (this.source === null) {
      this.refreshAvailability();
      return;
    }
    this.setSnapshot({
      status: "ready",
      message: "AI result cleared.",
      source: this.source,
      result: null,
    });
  }

  async run(capability: AiCapability, targetLanguage?: AiLanguage) {
    if (!this.isReady() || this.source === null) {
      this.refreshAvailability();
      return;
    }

    let action: MobileAiAction;
    try {
      action = this.buildAction(capability, targetLanguage);
    } catch {
      this.setSnapshot({
        status: "error",
        message: "AI request is unavailable.",
        source: this.source,
        result: null,
      });
      return;
    }

    this.setSnapshot({
      status: "processing",
      message: "Processing explicit AI request…",
      source: this.source,
      result: null,
    });

    try {
      const response = await this.onAction(action);
      if (typeof response.text !== "string" || response.text.length === 0) {
        throw new Error("invalid result");
      }
      this.setSnapshot({
        status: "result",
        message: "AI result ready.",
        source: this.source,
        result:
          action.targetLanguage === undefined
            ? {
                text: response.text,
                capability,
              }
            : {
                text: response.text,
                capability,
                targetLanguage: action.targetLanguage,
              },
      });
    } catch {
      this.setSnapshot({
        status: "error",
        message: "AI request is unavailable. No prior result is shown.",
        source: this.source,
        result: null,
      });
    }
  }

  private buildAction(
    capability: AiCapability,
    targetLanguage?: AiLanguage,
  ): MobileAiAction {
    if (this.source === null) {
      throw new Error("authorized source required");
    }

    const base = {
      capability,
      sourceId: this.source.sourceId,
      sourceKind: this.source.sourceKind,
      sourceLanguage: this.source.sourceLanguage,
      authorizationSource: "existing_roadtalk_authorization" as const,
    };

    if (capability === "summary") {
      return { ...base, maxOutputChars: 1200 };
    }

    if (capability === "translation") {
      if (
        targetLanguage === undefined ||
        !supportedLanguages.has(targetLanguage) ||
        targetLanguage === this.source.sourceLanguage
      ) {
        throw new Error("translation target invalid");
      }
      return {
        ...base,
        targetLanguage,
        maxOutputChars: 4000,
        audiencePreserved: true,
      };
    }

    return {
      ...base,
      consent: {
        userInitiated: true,
        foregroundOnly: true,
        backgroundCapture: false,
        durableAudioRetention: false,
      },
    };
  }

  private isReady() {
    return (
      this.source !== null &&
      this.online &&
      this.appActive &&
      this.providerMode === "test"
    );
  }

  private refreshAvailability() {
    if (this.source === null) {
      this.setSnapshot({
        status: "unavailable",
        message: "AI controls are unavailable until an authorized source is present.",
        source: null,
        result: null,
      });
      return;
    }
    if (!this.appActive) {
      this.setSnapshot({
        status: "unavailable",
        message: "AI controls are paused while RoadTalk is not in the foreground.",
        source: null,
        result: null,
      });
      return;
    }
    if (!this.online) {
      this.setSnapshot({
        status: "unavailable",
        message: "AI controls are offline. Existing AI results were cleared.",
        source: null,
        result: null,
      });
      return;
    }
    if (this.providerMode !== "test") {
      this.setSnapshot({
        status: "unavailable",
        message: "AI provider is disabled. Existing AI results were cleared.",
        source: null,
        result: null,
      });
      return;
    }
    this.setSnapshot({
      status: "ready",
      message: "AI controls are ready for explicit action.",
      source: this.source,
      result: null,
    });
  }

  private setSnapshot(snapshot: MobileAiSnapshot) {
    this.snapshot = snapshot;
    this.listeners.forEach((listener) => listener());
  }
}
