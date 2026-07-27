import { MediaLifecycleController } from "../media/MediaLifecycleController";
import type {
  MicrophonePermission,
  MicrophonePermissionGateway,
  ReceiveGrant,
  ReceiveGrantTransport,
  ReceiveRoomAdapter,
  RoomConnectionHandlers,
} from "../media/types";

class FakePermission implements MicrophonePermissionGateway {
  available = true;
  current: MicrophonePermission = {
    status: "undetermined",
    canAskAgain: true,
  };
  requested: MicrophonePermission = {
    status: "granted",
    canAskAgain: true,
  };
  readonly getPermission = jest.fn(async () => this.current);
  readonly requestPermission = jest.fn(async () => this.requested);
  isAvailable(): boolean {
    return this.available;
  }
}

class FakeTransport implements ReceiveGrantTransport {
  readonly grant: ReceiveGrant = {
    grantId: "grant-1",
    serverUrl: "wss://synthetic.invalid",
    participantToken: "synthetic-test-token",
  };
  readonly createReceiveGrant = jest.fn(async () => this.grant);
  readonly releaseGrant = jest.fn(async (_grantId: string) => undefined);
}

class FakeRoom implements ReceiveRoomAdapter {
  handlers: RoomConnectionHandlers | null = null;
  readonly connectReceiveOnly = jest.fn(
    async (_grant: ReceiveGrant, handlers: RoomConnectionHandlers) => {
      this.handlers = handlers;
    },
  );
  readonly disconnect = jest.fn(async () => undefined);
}

async function active(controller: MediaLifecycleController): Promise<void> {
  await controller.setAuthenticated(true);
  await controller.setAppActive(true);
  await controller.setScreenActive(true);
}

describe("microphone and receive-room lifecycle", () => {
  it("shows purpose before requesting permission, then joins receive-ready", async () => {
    const permission = new FakePermission();
    const transport = new FakeTransport();
    const room = new FakeRoom();
    const controller = new MediaLifecycleController(
      permission,
      transport,
      room,
    );
    await active(controller);

    expect(controller.getSnapshot()).toEqual({ status: "purpose" });
    expect(permission.getPermission).not.toHaveBeenCalled();
    expect(permission.requestPermission).not.toHaveBeenCalled();
    expect(transport.createReceiveGrant).not.toHaveBeenCalled();

    await controller.enable();

    expect(permission.requestPermission).toHaveBeenCalledTimes(1);
    expect(room.connectReceiveOnly).toHaveBeenCalledWith(
      transport.grant,
      expect.objectContaining({
        reconnecting: expect.any(Function),
        reconnected: expect.any(Function),
        disconnected: expect.any(Function),
      }),
    );
    expect(controller.getSnapshot()).toEqual({ status: "ready" });
  });

  it.each([
    {
      name: "unavailable",
      configure: (permission: FakePermission) => {
        permission.available = false;
      },
      expected: "unavailable",
      requests: 0,
    },
    {
      name: "denied",
      configure: (permission: FakePermission) => {
        permission.requested = { status: "denied", canAskAgain: true };
      },
      expected: "denied",
      requests: 1,
    },
    {
      name: "blocked",
      configure: (permission: FakePermission) => {
        permission.current = { status: "denied", canAskAgain: false };
      },
      expected: "blocked",
      requests: 0,
    },
  ])("handles $name without obtaining a media grant", async (testCase) => {
    const permission = new FakePermission();
    testCase.configure(permission);
    const transport = new FakeTransport();
    const room = new FakeRoom();
    const controller = new MediaLifecycleController(
      permission,
      transport,
      room,
    );
    await active(controller);

    await controller.enable();

    expect(controller.getSnapshot().status).toBe(testCase.expected);
    expect(permission.requestPermission).toHaveBeenCalledTimes(
      testCase.requests,
    );
    expect(transport.createReceiveGrant).not.toHaveBeenCalled();
    expect(room.connectReceiveOnly).not.toHaveBeenCalled();
  });

  it("exposes reconnect state without requesting permission again", async () => {
    const permission = new FakePermission();
    permission.current = { status: "granted", canAskAgain: true };
    const transport = new FakeTransport();
    const room = new FakeRoom();
    const controller = new MediaLifecycleController(
      permission,
      transport,
      room,
    );
    await active(controller);
    await controller.enable();

    room.handlers?.reconnecting();
    expect(controller.getSnapshot()).toEqual({ status: "reconnecting" });
    room.handlers?.reconnected();
    expect(controller.getSnapshot()).toEqual({ status: "ready" });
    expect(permission.requestPermission).not.toHaveBeenCalled();
  });

  it("rechecks a permission changed in settings before reconnecting", async () => {
    const permission = new FakePermission();
    permission.current = { status: "granted", canAskAgain: true };
    const transport = new FakeTransport();
    const room = new FakeRoom();
    const controller = new MediaLifecycleController(
      permission,
      transport,
      room,
    );
    await active(controller);
    await controller.enable();
    await controller.setAppActive(false);
    permission.current = { status: "denied", canAskAgain: false };

    await controller.setAppActive(true);

    expect(controller.getSnapshot()).toEqual({ status: "blocked" });
    expect(permission.requestPermission).not.toHaveBeenCalled();
    expect(room.connectReceiveOnly).toHaveBeenCalledTimes(1);
    expect(transport.createReceiveGrant).toHaveBeenCalledTimes(1);
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
      "logout or revocation",
      (controller: MediaLifecycleController) =>
        controller.setAuthenticated(false),
    ],
    [
      "explicit pause",
      (controller: MediaLifecycleController) => controller.pause(),
    ],
    ["unmount", (controller: MediaLifecycleController) => controller.dispose()],
  ])("disconnects and releases on %s", async (_name, stop) => {
    const permission = new FakePermission();
    permission.current = { status: "granted", canAskAgain: true };
    const transport = new FakeTransport();
    const room = new FakeRoom();
    const controller = new MediaLifecycleController(
      permission,
      transport,
      room,
    );
    await active(controller);
    await controller.enable();

    await stop(controller);

    expect(room.disconnect).toHaveBeenCalled();
    expect(transport.releaseGrant).toHaveBeenCalledWith("grant-1");
  });

  it("fails closed and releases after connection failure", async () => {
    const permission = new FakePermission();
    permission.current = { status: "granted", canAskAgain: true };
    const transport = new FakeTransport();
    const room = new FakeRoom();
    room.connectReceiveOnly.mockRejectedValueOnce(new Error("offline"));
    const controller = new MediaLifecycleController(
      permission,
      transport,
      room,
    );
    await active(controller);

    await controller.enable();

    expect(controller.getSnapshot()).toEqual({ status: "error" });
    expect(room.disconnect).toHaveBeenCalled();
    expect(transport.releaseGrant).toHaveBeenCalledWith("grant-1");
  });

  it("disconnects after an unrecoverable room event", async () => {
    const permission = new FakePermission();
    permission.current = { status: "granted", canAskAgain: true };
    const transport = new FakeTransport();
    const room = new FakeRoom();
    const controller = new MediaLifecycleController(
      permission,
      transport,
      room,
    );
    await active(controller);
    await controller.enable();

    room.handlers?.disconnected();
    await new Promise((resolve) => setImmediate(resolve));

    expect(controller.getSnapshot()).toEqual({ status: "error" });
    expect(transport.releaseGrant).toHaveBeenCalledWith("grant-1");
  });
});
