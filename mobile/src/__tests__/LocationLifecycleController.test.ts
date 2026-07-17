import { LocationLifecycleController } from "../location/LocationLifecycleController";
import type {
  ForegroundPermission,
  LocationFix,
  LocationGateway,
  LocationSubscription,
  LocationTransport,
  PublishedLocationSample,
} from "../location/types";

class FakeGateway implements LocationGateway {
  servicesEnabled = true;
  currentPermission: ForegroundPermission = {
    status: "undetermined",
    canAskAgain: true,
    precision: null,
  };
  requestedPermission: ForegroundPermission = {
    status: "granted",
    canAskAgain: true,
    precision: "precise",
  };
  readonly hasServicesEnabled = jest.fn(async () => this.servicesEnabled);
  readonly getForegroundPermission = jest.fn(async () => this.currentPermission);
  readonly requestForegroundPermission = jest.fn(
    async () => this.requestedPermission,
  );
  readonly removals: jest.Mock[] = [];
  watchCount = 0;
  private onLocation: ((fix: LocationFix) => void) | null = null;
  private onError: (() => void) | null = null;

  readonly watch = jest.fn(
    async (
      onLocation: (fix: LocationFix) => void,
      onError: () => void,
    ): Promise<LocationSubscription> => {
      this.watchCount += 1;
      this.onLocation = onLocation;
      this.onError = onError;
      const remove = jest.fn();
      this.removals.push(remove);
      return { remove };
    },
  );

  emit(fix: LocationFix): void {
    this.onLocation?.(fix);
  }

  fail(): void {
    this.onError?.();
  }
}

function transport(): LocationTransport & {
  grantConsent: jest.Mock;
  publish: jest.Mock;
  pause: jest.Mock;
  nearby: jest.Mock;
} {
  return {
    grantConsent: jest.fn(async () => undefined),
    publish: jest.fn(async (_sample: PublishedLocationSample) => undefined),
    pause: jest.fn(async () => undefined),
    nearby: jest.fn(async () => null),
  };
}

function fix(overrides: Partial<LocationFix> = {}): LocationFix {
  return {
    latitude: 40,
    longitude: -75,
    horizontalAccuracyM: 25,
    headingDeg: 90,
    speedMps: 4,
    observedAtMs: Date.parse("2026-07-16T12:00:00Z"),
    ...overrides,
  };
}

class FakeScheduler {
  private nextId = 1;
  private readonly timers = new Map<
    ReturnType<typeof setTimeout>,
    { at: number; callback: () => void }
  >();

  constructor(private readonly clock: { value: number }) {}

  setTimeout(
    callback: () => void,
    delayMs: number,
  ): ReturnType<typeof setTimeout> {
    const handle = this.nextId as unknown as ReturnType<typeof setTimeout>;
    this.nextId += 1;
    this.timers.set(handle, { at: this.clock.value + delayMs, callback });
    return handle;
  }

  clearTimeout(handle: ReturnType<typeof setTimeout>): void {
    this.timers.delete(handle);
  }

  advanceBy(delayMs: number): void {
    this.clock.value += delayMs;
    const due = [...this.timers.entries()]
      .filter(([, timer]) => timer.at <= this.clock.value)
      .sort((left, right) => left[1].at - right[1].at);
    due.forEach(([handle, timer]) => {
      this.timers.delete(handle);
      timer.callback();
    });
  }

  pending(): number {
    return this.timers.size;
  }
}

async function flush(): Promise<void> {
  for (let turn = 0; turn < 5; turn += 1) {
    await Promise.resolve();
  }
}

async function ready(controller: LocationLifecycleController): Promise<void> {
  await controller.setAuthenticated(true);
  await controller.setAppActive(true);
  await controller.setScreenActive(true);
}

describe("foreground location lifecycle", () => {
  it("never requests permission before the explicit enable action", async () => {
    const gateway = new FakeGateway();
    const remote = transport();
    const controller = new LocationLifecycleController(gateway, remote);
    await ready(controller);

    expect(controller.getSnapshot()).toEqual({ status: "purpose" });
    expect(gateway.getForegroundPermission).not.toHaveBeenCalled();
    expect(gateway.requestForegroundPermission).not.toHaveBeenCalled();

    await controller.enable();

    expect(gateway.requestForegroundPermission).toHaveBeenCalledTimes(1);
    expect(remote.grantConsent).toHaveBeenCalledTimes(1);
    expect(remote.pause).toHaveBeenCalledTimes(1);
    expect(gateway.watch).toHaveBeenCalledTimes(1);
    expect(controller.getSnapshot()).toEqual({
      status: "active",
      precision: "precise",
      upload: "waiting",
      local: { status: "waiting" },
      nearby: { status: "waiting" },
    });
  });

  it.each([
    {
      name: "unavailable services",
      configure: (gateway: FakeGateway) => {
        gateway.servicesEnabled = false;
      },
      expected: "unavailable",
      requested: 0,
    },
    {
      name: "denied permission",
      configure: (gateway: FakeGateway) => {
        gateway.requestedPermission = {
          status: "denied",
          canAskAgain: true,
          precision: null,
        };
      },
      expected: "denied",
      requested: 1,
    },
    {
      name: "blocked permission",
      configure: (gateway: FakeGateway) => {
        gateway.currentPermission = {
          status: "denied",
          canAskAgain: false,
          precision: null,
        };
      },
      expected: "blocked",
      requested: 0,
    },
  ])("handles $name without starting collection", async (testCase) => {
    const gateway = new FakeGateway();
    testCase.configure(gateway);
    const remote = transport();
    const controller = new LocationLifecycleController(gateway, remote);
    await ready(controller);

    await controller.enable();

    expect(controller.getSnapshot().status).toBe(testCase.expected);
    expect(gateway.requestForegroundPermission).toHaveBeenCalledTimes(
      testCase.requested,
    );
    expect(gateway.watch).not.toHaveBeenCalled();
    expect(remote.grantConsent).not.toHaveBeenCalled();
  });

  it("accepts approximate permission and sends bounded monotonic samples", async () => {
    const gateway = new FakeGateway();
    gateway.currentPermission = {
      status: "granted",
      canAskAgain: true,
      precision: "approximate",
    };
    const remote = transport();
    const clock = { value: 20_000, now: () => clock.value };
    const controller = new LocationLifecycleController(
      gateway,
      remote,
      clock,
      10_000,
    );
    await ready(controller);
    await controller.enable();

    gateway.emit(fix());
    await flush();
    clock.value += 5_000;
    gateway.emit(fix({ latitude: 40.0001 }));
    await flush();
    clock.value += 5_000;
    gateway.emit(fix());
    await flush();

    expect(remote.publish).toHaveBeenCalledTimes(2);
    expect(remote.publish.mock.calls[0]?.[0]).toEqual({
      observed_at: "2026-07-16T12:00:00.000Z",
      latitude: 40,
      longitude: -75,
      horizontal_accuracy_m: 25,
      heading_deg: 90,
      speed_mps: 4,
      client_sequence: 1,
      consent_policy_version: "location-v1",
    });
    expect(remote.publish.mock.calls[1]?.[0]).toEqual(
      expect.objectContaining({ client_sequence: 2 }),
    );
    expect(controller.getSnapshot()).toEqual({
      status: "active",
      precision: "approximate",
      upload: "current",
      local: {
        status: "current",
        horizontalAccuracyM: 25,
        headingDeg: 90,
        speedMps: 4,
        observedAtMs: Date.parse("2026-07-16T12:00:00Z"),
      },
      nearby: { status: "unavailable" },
    });
  });

  it("stops and removes the server sample on background, screen exit, logout, and dispose", async () => {
    const gateway = new FakeGateway();
    gateway.currentPermission = {
      status: "granted",
      canAskAgain: true,
      precision: "precise",
    };
    const remote = transport();
    const controller = new LocationLifecycleController(gateway, remote);
    await ready(controller);
    await controller.enable();

    await controller.setAppActive(false);
    expect(gateway.removals[0]).toHaveBeenCalledTimes(1);
    expect(remote.pause).toHaveBeenCalledTimes(2);

    await controller.setAppActive(true);
    expect(gateway.watch).toHaveBeenCalledTimes(2);
    await controller.setScreenActive(false);
    expect(gateway.removals[1]).toHaveBeenCalledTimes(1);
    expect(remote.pause).toHaveBeenCalledTimes(3);

    await controller.setScreenActive(true);
    await controller.setAuthenticated(false);
    expect(gateway.removals[2]).toHaveBeenCalledTimes(1);
    await controller.dispose();
    expect(gateway.watch).toHaveBeenCalledTimes(3);
  });

  it("drops malformed fixes and converts invalid optional motion values to null", async () => {
    const gateway = new FakeGateway();
    gateway.currentPermission = {
      status: "granted",
      canAskAgain: true,
      precision: "precise",
    };
    const remote = transport();
    const controller = new LocationLifecycleController(gateway, remote);
    await ready(controller);
    await controller.enable();

    gateway.emit(fix({ horizontalAccuracyM: null }));
    gateway.emit(fix({ latitude: Number.NaN }));
    gateway.emit(fix({ headingDeg: 360, speedMps: -1 }));
    await flush();

    expect(remote.publish).toHaveBeenCalledTimes(1);
    expect(remote.publish).toHaveBeenCalledWith(
      expect.objectContaining({ heading_deg: null, speed_mps: null }),
    );
  });

  it("keeps pause authoritative when an upload finishes late", async () => {
    const gateway = new FakeGateway();
    gateway.currentPermission = {
      status: "granted",
      canAskAgain: true,
      precision: "precise",
    };
    const remote = transport();
    let resolveUpload: (value?: void) => void = () => undefined;
    remote.publish.mockImplementation(
      () =>
        new Promise<void>((resolve) => {
          resolveUpload = resolve;
        }),
    );
    const controller = new LocationLifecycleController(gateway, remote);
    await ready(controller);
    await controller.enable();

    gateway.emit(fix());
    await flush();
    await controller.pause();
    resolveUpload();
    await flush();

    expect(controller.getSnapshot()).toEqual({ status: "paused" });
    expect(remote.pause.mock.calls.length).toBeGreaterThanOrEqual(3);
  });

  it("retries a failed upload only when the next device sample arrives", async () => {
    const gateway = new FakeGateway();
    gateway.currentPermission = {
      status: "granted",
      canAskAgain: true,
      precision: "precise",
    };
    const remote = transport();
    remote.publish
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce(undefined);
    const clock = { now: () => fix().observedAtMs };
    const controller = new LocationLifecycleController(gateway, remote, clock);
    await ready(controller);
    await controller.enable();

    gateway.emit(fix());
    await flush();
    expect(controller.getSnapshot()).toEqual({
      status: "active",
      precision: "precise",
      upload: "retrying",
      local: {
        status: "current",
        horizontalAccuracyM: 25,
        headingDeg: 90,
        speedMps: 4,
        observedAtMs: Date.parse("2026-07-16T12:00:00Z"),
      },
      nearby: { status: "waiting" },
    });
    expect(remote.publish).toHaveBeenCalledTimes(1);

    gateway.emit(fix({ observedAtMs: fix().observedAtMs + 1_000 }));
    await flush();
    expect(remote.publish).toHaveBeenCalledTimes(2);
    expect(remote.publish.mock.calls[1]?.[0]).toEqual(
      expect.objectContaining({ client_sequence: 1 }),
    );
    expect(controller.getSnapshot()).toEqual({
      status: "active",
      precision: "precise",
      upload: "current",
      local: {
        status: "current",
        horizontalAccuracyM: 25,
        headingDeg: 90,
        speedMps: 4,
        observedAtMs: Date.parse("2026-07-16T12:00:01Z"),
      },
      nearby: { status: "unavailable" },
    });
  });

  it("stops after a native watch failure using a stable error state", async () => {
    const gateway = new FakeGateway();
    gateway.currentPermission = {
      status: "granted",
      canAskAgain: true,
      precision: "precise",
    };
    const remote = transport();
    const controller = new LocationLifecycleController(gateway, remote);
    await ready(controller);
    await controller.enable();

    gateway.fail();
    await flush();

    expect(gateway.removals[0]).toHaveBeenCalledTimes(1);
    expect(controller.getSnapshot()).toEqual({ status: "error" });
  });

  it("shows owner-only quality and polls semantic nearby state on a bounded timer", async () => {
    const gateway = new FakeGateway();
    gateway.currentPermission = {
      status: "granted",
      canAskAgain: true,
      precision: "precise",
    };
    const remote = transport();
    const clock = { value: fix().observedAtMs, now: () => clock.value };
    const scheduler = new FakeScheduler(clock);
    remote.nearby.mockResolvedValue({
      availability: "available",
      bucket: "few",
      freshness: "fresh",
      expiresAtMs: clock.value + 120_000,
    });
    const controller = new LocationLifecycleController(
      gateway,
      remote,
      clock,
      10_000,
      30_000,
      30_000,
      scheduler,
    );
    await ready(controller);
    await controller.enable();

    gateway.emit(fix());
    await flush();

    expect(remote.nearby).toHaveBeenCalledTimes(1);
    expect(controller.getSnapshot()).toEqual({
      status: "active",
      precision: "precise",
      upload: "current",
      local: {
        status: "current",
        horizontalAccuracyM: 25,
        headingDeg: 90,
        speedMps: 4,
        observedAtMs: fix().observedAtMs,
      },
      nearby: {
        status: "current",
        bucket: "few",
        expiresAtMs: clock.value + 120_000,
      },
    });

    scheduler.advanceBy(30_000);
    await flush();
    expect(remote.nearby).toHaveBeenCalledTimes(2);
    expect(controller.getSnapshot()).toEqual(
      expect.objectContaining({
        local: expect.objectContaining({ status: "stale" }),
        nearby: expect.objectContaining({ status: "current", bucket: "few" }),
      }),
    );

    await controller.setAppActive(false);
    expect(scheduler.pending()).toBe(0);
    scheduler.advanceBy(120_000);
    await flush();
    expect(remote.nearby).toHaveBeenCalledTimes(2);
  });

  it("marks an expired nearby result stale when a refresh fails", async () => {
    const gateway = new FakeGateway();
    gateway.currentPermission = {
      status: "granted",
      canAskAgain: true,
      precision: "precise",
    };
    const remote = transport();
    const clock = { value: fix().observedAtMs, now: () => clock.value };
    const scheduler = new FakeScheduler(clock);
    remote.nearby
      .mockResolvedValueOnce({
        availability: "available",
        bucket: "many",
        freshness: "fresh",
        expiresAtMs: clock.value + 5_000,
      })
      .mockRejectedValueOnce(new Error("offline"));
    const controller = new LocationLifecycleController(
      gateway,
      remote,
      clock,
      10_000,
      30_000,
      30_000,
      scheduler,
    );
    await ready(controller);
    await controller.enable();

    gateway.emit(fix());
    await flush();
    expect(controller.getSnapshot()).toEqual(
      expect.objectContaining({
        nearby: expect.objectContaining({ status: "current", bucket: "many" }),
      }),
    );

    scheduler.advanceBy(5_000);
    await flush();
    expect(controller.getSnapshot()).toEqual(
      expect.objectContaining({
        nearby: { status: "stale", expiresAtMs: clock.value },
      }),
    );
    await controller.pause();
    expect(scheduler.pending()).toBe(0);
  });

  it("cancels nearby polling on screen exit, logout, and unmount", async () => {
    const gateway = new FakeGateway();
    gateway.currentPermission = {
      status: "granted",
      canAskAgain: true,
      precision: "precise",
    };
    const remote = transport();
    const clock = { value: fix().observedAtMs, now: () => clock.value };
    const scheduler = new FakeScheduler(clock);
    remote.nearby.mockImplementation(async () => ({
      availability: "available",
      bucket: "none",
      freshness: "fresh",
      expiresAtMs: clock.value + 120_000,
    }));
    const controller = new LocationLifecycleController(
      gateway,
      remote,
      clock,
      10_000,
      30_000,
      30_000,
      scheduler,
    );
    await ready(controller);
    await controller.enable();

    gateway.emit(fix({ observedAtMs: clock.value }));
    await flush();
    expect(remote.nearby).toHaveBeenCalledTimes(1);
    expect(scheduler.pending()).toBeGreaterThan(0);

    await controller.setScreenActive(false);
    expect(scheduler.pending()).toBe(0);
    scheduler.advanceBy(10_000);
    await controller.setScreenActive(true);
    gateway.emit(fix({ observedAtMs: clock.value }));
    await flush();
    expect(remote.nearby).toHaveBeenCalledTimes(2);

    await controller.setAuthenticated(false);
    expect(scheduler.pending()).toBe(0);
    scheduler.advanceBy(10_000);
    await controller.setAuthenticated(true);
    gateway.emit(fix({ observedAtMs: clock.value }));
    await flush();
    expect(remote.nearby).toHaveBeenCalledTimes(3);

    await controller.dispose();
    expect(scheduler.pending()).toBe(0);
    scheduler.advanceBy(120_000);
    await flush();
    expect(remote.nearby).toHaveBeenCalledTimes(3);
  });
});
