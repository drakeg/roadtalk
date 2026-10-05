export type AiLanguage = "en" | "es" | "fr" | "de";
export type AiSourceKind = "transcript" | "message_window";
export type AiCapability = "summary" | "translation" | "transcription";
export type AiProviderMode = "disabled" | "test";

export type AuthorizedAiSource = Readonly<{
  sourceId: string;
  sourceKind: AiSourceKind;
  sourceLanguage: AiLanguage;
  authorizedOnly: true;
  authorizationSource: "existing_roadtalk_authorization";
}>;

export type MobileAiAction = Readonly<{
  capability: AiCapability;
  sourceId: string;
  sourceKind: AiSourceKind;
  sourceLanguage: AiLanguage;
  authorizationSource: "existing_roadtalk_authorization";
  targetLanguage?: AiLanguage;
  maxOutputChars?: 1200 | 4000;
  audiencePreserved?: true;
  consent?: Readonly<{
    userInitiated: true;
    foregroundOnly: true;
    backgroundCapture: false;
    durableAudioRetention: false;
  }>;
}>;

export type MobileAiResult = Readonly<{ text: string }>;

export type MobileAiSnapshot =
  | Readonly<{ status: "unavailable"; message: string; source: null; result: null }>
  | Readonly<{ status: "ready"; message: string; source: AuthorizedAiSource; result: null }>
  | Readonly<{ status: "processing"; message: string; source: AuthorizedAiSource; result: null }>
  | Readonly<{
      status: "result";
      message: string;
      source: AuthorizedAiSource;
      result: Readonly<{
        text: string;
        capability: AiCapability;
        targetLanguage?: AiLanguage;
      }>;
    }>
  | Readonly<{
      status: "error";
      message: string;
      source: AuthorizedAiSource | null;
      result: null;
    }>;

export type MobileAiActionHandler = (action: MobileAiAction) => Promise<MobileAiResult>;
