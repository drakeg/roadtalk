import { MobileAiController } from "../ai/MobileAiController";
import type { AuthorizedAiSource, MobileAiAction } from "../ai/types";

const source: AuthorizedAiSource = {
  sourceId: "source-1",
  sourceKind: "transcript",
  sourceLanguage: "en",
  authorizedOnly: true,
  authorizationSource: "existing_roadtalk_authorization",
};

function readyController(actions: MobileAiAction[]) {
  const controller = new MobileAiController(async (action) => {
    actions.push(action);
    return { text: "deterministic mobile result" };
  });
  controller.setAuthorizedSource(source);
  controller.setOnline(true);
  controller.setAppActive(true);
  controller.setProviderMode("test");
  return controller;
}

describe("MobileAiController", () => {
  test("requires explicit summary action and preserves authorization", async () => {
    const actions: MobileAiAction[] = [];
    const controller = readyController(actions);

    expect(actions).toHaveLength(0);
    await controller.run("summary");

    expect(actions).toEqual([
      {
        capability: "summary",
        sourceId: "source-1",
        sourceKind: "transcript",
        sourceLanguage: "en",
        authorizationSource: "existing_roadtalk_authorization",
        maxOutputChars: 1200,
      },
    ]);
    expect(controller.getSnapshot().status).toBe("result");
  });

  test("translation preserves audience and uses explicit distinct language", async () => {
    const actions: MobileAiAction[] = [];
    const controller = readyController(actions);

    await controller.run("translation", "es");

    expect(actions[0]).toMatchObject({
      capability: "translation",
      sourceLanguage: "en",
      targetLanguage: "es",
      maxOutputChars: 4000,
      audiencePreserved: true,
    });
  });

  test("same-language translation fails without invoking the handler", async () => {
    const actions: MobileAiAction[] = [];
    const controller = readyController(actions);

    await controller.run("translation", "en");

    expect(actions).toHaveLength(0);
    expect(controller.getSnapshot()).toMatchObject({
      status: "error",
      result: null,
    });
  });

  test("transcription action carries foreground-only no-retention consent", async () => {
    const actions: MobileAiAction[] = [];
    const controller = readyController(actions);

    await controller.run("transcription");

    expect(actions[0]).toMatchObject({
      capability: "transcription",
      consent: {
        userInitiated: true,
        foregroundOnly: true,
        backgroundCapture: false,
        durableAudioRetention: false,
      },
    });
  });

  test("offline provider-disabled and background transitions clear result state", async () => {
    const actions: MobileAiAction[] = [];
    const controller = readyController(actions);

    await controller.run("summary");
    expect(controller.getSnapshot().status).toBe("result");

    controller.setOnline(false);
    expect(controller.getSnapshot()).toMatchObject({
      status: "unavailable",
      result: null,
    });

    controller.setOnline(true);
    controller.setProviderMode("disabled");
    expect(controller.getSnapshot()).toMatchObject({
      status: "unavailable",
      result: null,
    });

    controller.setProviderMode("test");
    controller.setAppActive(false);
    expect(controller.getSnapshot()).toMatchObject({
      status: "unavailable",
      result: null,
    });
  });
});
