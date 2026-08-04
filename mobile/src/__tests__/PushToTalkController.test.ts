import { MediaLifecycleController } from "../media/MediaLifecycleController";
import { MediaGrantError } from "../media/api";
import type {
  MicrophonePermission,
  MicrophonePermissionGateway,
  ReceiveGrant,
  ReceiveGrantTransport,
  ReceiveRoomAdapter,
  RoomConnectionHandlers,
  TransmitGrant,
} from "../media/types";

class FakePermission implements MicrophonePermissionGateway {
  available = true;
  current: MicrophonePermission = {
    status: "granted",
    canAskAgain: true,
  };
  readonly getPermission = jest.fn(async () => this.current);
  readonly requestPermission = jest.fn(async () => this.current);
  isAvailable(): boolean {
    return this.available;
  }
}

class FakeTransport implements ReceiveGrantTransport {
  readonly receive: ReceiveGrant = {
    grantId: "receive-1",
    serverUrl: "wss://synthetic.invalid",
    participantToken: "synthetic-test-token",
  };
  readonly transmit: TransmitGrant = {
    grantId: "transmit-1",
    receiveGrantId: "receive-1",
    expiresAt: "2026-07-26T12:00:30Z",
  };
  readonly createReceiveGrant = jest.fn(async () => this.receive);
  readonly createTransmitGrant = jest.fn(
    async (_receiveGrantId: string) => this.transmit,
  );
  readonly releaseGrant = jest.fn(async (_grantId: string) => undefined);
}

class FakeRoom implements ReceiveRoomAdapter {
  handlers: RoomConnectionHandlers | null = null;
  readonly connectReceiveOnly = jest.fn(
    async (_grant: ReceiveGrant, handlers: RoomConnectionHandlers) => {
      this.handlers = handlers;
    },
  );
  readonly setMicrophoneEnabled = jest.fn(
    async (_enabled: boolean) => undefined,
  );
  readonly disconnect = jest.fn(async () => undefined);
}

function deferred<T>(): {
  promise: Promise<T>;
  resolve(value: T): void;
  reject(error: unknown): void;
} {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((accept, decline) => {
    resolve = accept;
    reject = decline;
  });
  return { promise, resolve, reject };
}

async function ready(
  options: {
    permission?: FakePermission;
    transport?: FakeTransport;
    room?: FakeRoom;
    scheduler?: {
      setTimeout(
        callback: () => void,
        delayMs: number,
      ): ReturnType<typeof setTimeout>;
      clearTimeout(handle: ReturnType<typeof setTimeout>): void;
    };
  } = {},
): Promise<{
  controller: MediaLifecycleController;
  permission: FakePermission;
  transport: FakeTransport;
  room: FakeRoom;
}> {
  const permission = options.permission ?? new FakePermission();
  const transport = options.transport ?? new FakeTransport();
  const room = options.room ?? new FakeRoom();
  const controller = new MediaLifecycleController(
    permission,
    transport,
    room,
    options.scheduler,
    30_000,
  );
  await controller.setAuthenticated(true);
  await controller.setAppActive(true);
  await controller.setScreenActive(true);
  await controller.enable();
  expect(controller.getSnapshot()).toEqual({ status: "ready" });
  return { controller, permission, transport, room };
}

async function flush(): Promise<void> {
  await new Promise((resolve) => setImmediate(resolve));
}

describe("server-authorized hold-to-talk", () => {
  it("keeps capture off until the transmit grant is returned", async () => {
    const pending = deferred<TransmitGrant>();
    const transport = new FakeTransport();
    transport.createTransmitGrant.mockImplementationOnce(() => pending.promise);
    const { controller, room } = await ready({ transport });

    const press = controller.pressToTalk();

    expect(controller.getSnapshot()).toEqual({ status: "authorizing" });
    expect(transport.createTransmitGrant).toHaveBeenCalledWith("receive-1");
    expect(room.setMicrophoneEnabled).not.toHaveBeenCalledWith(true);

    pending.resolve(transport.transmit);
    await press;

    expect(room.setMicrophoneEnabled).toHaveBeenCalledWith(true);
    expect(controller.getSnapshot()).toEqual({ status: "transmitting" });
    await controller.releaseToTalk();
  });

  it("disables capture before revoking the transmit grant on release", async () => {
    const { controller, transport, room } = await ready();
    await controller.pressToTalk();
    room.setMicrophoneEnabled.mockClear();
    transport.releaseGrant.mockClear();

    await controller.releaseToTalk();

    expect(controller.getSnapshot()).toEqual({ status: "ready" });
    expect(room.setMicrophoneEnabled).toHaveBeenCalledWith(false);
    expect(transport.releaseGrant).toHaveBeenCalledWith("transmit-1");
    expect(
      room.setMicrophoneEnabled.mock.invocationCallOrder[0]!,
    ).toBeLessThan(transport.releaseGrant.mock.invocationCallOrder[0]!);
  });

  it("cancels a rapid press and release before authorization without capture", async () => {
    const pending = deferred<TransmitGrant>();
    const transport = new FakeTransport();
    transport.createTransmitGrant.mockImplementationOnce(() => pending.promise);
    const { controller, room } = await ready({ transport });

    const press = controller.pressToTalk();
    await controller.releaseToTalk();
    pending.resolve(transport.transmit);
    await press;

    expect(room.setMicrophoneEnabled).not.toHaveBeenCalledWith(true);
    expect(transport.releaseGrant).toHaveBeenCalledWith("transmit-1");
    expect(controller.getSnapshot()).toEqual({ status: "ready" });
  });

  it("serializes release behind an in-flight native enable before cleanup", async () => {
    const nativeEnable = deferred<void>();
    const room = new FakeRoom();
    room.setMicrophoneEnabled.mockImplementationOnce(
      async (enabled: boolean) => {
        expect(enabled).toBe(true);
        await nativeEnable.promise;
      },
    );
    const { controller, transport } = await ready({ room });

    const press = controller.pressToTalk();
    await flush();
    const release = controller.releaseToTalk();

    expect(room.setMicrophoneEnabled).toHaveBeenCalledTimes(1);
    expect(transport.releaseGrant).not.toHaveBeenCalledWith("transmit-1");

    nativeEnable.resolve();
    await Promise.all([press, release]);

    expect(room.setMicrophoneEnabled.mock.calls).toEqual([
      [true],
      [false],
      [false],
    ]);
    expect(transport.releaseGrant).toHaveBeenCalledWith("transmit-1");
    expect(
      room.setMicrophoneEnabled.mock.invocationCallOrder[1]!,
    ).toBeLessThan(transport.releaseGrant.mock.invocationCallOrder[0]!);
    expect(controller.getSnapshot()).toEqual({ status: "ready" });
  });

  it("stops at the deterministic 30-second maximum", async () => {
    let maximumCallback: (() => void) | null = null;
    const scheduler = {
      setTimeout: jest.fn((callback: () => void, _delayMs: number) => {
        maximumCallback = callback;
        return 1 as unknown as ReturnType<typeof setTimeout>;
      }),
      clearTimeout: jest.fn((_handle: ReturnType<typeof setTimeout>) => undefined),
    };
    const { controller, transport, room } = await ready({ scheduler });
    await controller.pressToTalk();
    room.setMicrophoneEnabled.mockClear();
    transport.releaseGrant.mockClear();

    (maximumCallback as (() => void) | null)?.();
    await flush();

    expect(scheduler.setTimeout).toHaveBeenCalledWith(
      expect.any(Function),
      30_000,
    );
    expect(room.setMicrophoneEnabled).toHaveBeenCalledWith(false);
    expect(transport.releaseGrant).toHaveBeenCalledWith("transmit-1");
    expect(controller.getSnapshot()).toEqual({
      status: "ready",
      reason: "maximum",
    });
  });

  it.each([
    ["PTT_TRANSMIT_BUSY", "busy"],
    ["PTT_PROVIDER_UNAVAILABLE", "degraded"],
    ["PTT_RATE_LIMITED", "degraded"],
  ])("maps %s without enabling capture", async (code, expected) => {
    const transport = new FakeTransport();
    transport.createTransmitGrant.mockRejectedValueOnce(
      new MediaGrantError(code),
    );
    const { controller, room } = await ready({ transport });

    await controller.pressToTalk();

    expect(controller.getSnapshot().status).toBe(expected);
    expect(room.setMicrophoneEnabled).not.toHaveBeenCalledWith(true);
  });

  it("disconnects and exposes revoked permission after native enable fails", async () => {
    const permission = new FakePermission();
    const room = new FakeRoom();
    room.setMicrophoneEnabled.mockImplementationOnce(async (enabled) => {
      if (enabled) {
        permission.current = { status: "denied", canAskAgain: false };
        throw new Error("permission revoked");
      }
    });
    const { controller, transport } = await ready({ permission, room });

    await controller.pressToTalk();

    expect(controller.getSnapshot()).toEqual({ status: "blocked" });
    expect(room.setMicrophoneEnabled).toHaveBeenCalledWith(false);
    expect(room.disconnect).toHaveBeenCalled();
    expect(transport.releaseGrant).toHaveBeenCalledWith("transmit-1");
    expect(transport.releaseGrant).toHaveBeenCalledWith("receive-1");
  });

  it("shows incoming audio without implying local capture", async () => {
    const { controller, room } = await ready();

    room.handlers?.receivingChanged(true);
    expect(controller.getSnapshot()).toEqual({ status: "receiving" });
    expect(room.setMicrophoneEnabled).not.toHaveBeenCalledWith(true);

    room.handlers?.receivingChanged(false);
    expect(controller.getSnapshot()).toEqual({ status: "ready" });
  });

  it("stops transmission before reconnecting", async () => {
    const { controller, transport, room } = await ready();
    await controller.pressToTalk();
    room.setMicrophoneEnabled.mockClear();
    transport.releaseGrant.mockClear();

    room.handlers?.reconnecting();
    await flush();

    expect(room.setMicrophoneEnabled).toHaveBeenCalledWith(false);
    expect(transport.releaseGrant).toHaveBeenCalledWith("transmit-1");
    expect(controller.getSnapshot()).toEqual({ status: "reconnecting" });
  });

  it.each([
    [
      "background",
      (controller: MediaLifecycleController) => controller.setAppActive(false),
    ],
    [
      "screen exit",
      (controller: MediaLifecycleController) =>
        controller.setScreenActive(false),
    ],
    [
      "logout",
      (controller: MediaLifecycleController) =>
        controller.setAuthenticated(false),
    ],
  ])("turns capture off before cleanup on %s", async (_name, stop) => {
    const { controller, transport, room } = await ready();
    await controller.pressToTalk();
    room.setMicrophoneEnabled.mockClear();
    transport.releaseGrant.mockClear();

    await stop(controller);

    expect(room.setMicrophoneEnabled).toHaveBeenCalledWith(false);
    expect(transport.releaseGrant).toHaveBeenCalledWith("transmit-1");
    expect(transport.releaseGrant).toHaveBeenCalledWith("receive-1");
    expect(
      room.setMicrophoneEnabled.mock.invocationCallOrder[0]!,
    ).toBeLessThan(transport.releaseGrant.mock.invocationCallOrder[0]!);
  });

  it("ignores repeated presses while authorization is pending", async () => {
    const pending = deferred<TransmitGrant>();
    const transport = new FakeTransport();
    transport.createTransmitGrant.mockImplementationOnce(() => pending.promise);
    const { controller } = await ready({ transport });

    const first = controller.pressToTalk();
    await controller.pressToTalk();
    pending.resolve(transport.transmit);
    await first;

    expect(transport.createTransmitGrant).toHaveBeenCalledTimes(1);
    await controller.releaseToTalk();
  });

  it("stays fail-closed when authorization rejects after release", async () => {
    const pending = deferred<TransmitGrant>();
    const transport = new FakeTransport();
    transport.createTransmitGrant.mockImplementationOnce(() => pending.promise);
    const { controller, room } = await ready({ transport });

    const press = controller.pressToTalk();
    await controller.releaseToTalk();
    pending.reject(new MediaGrantError("PTT_TRANSMIT_BUSY"));
    await press;

    expect(room.setMicrophoneEnabled).not.toHaveBeenCalledWith(true);
    expect(controller.getSnapshot()).toEqual({ status: "ready" });
  });
});
