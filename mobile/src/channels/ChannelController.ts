import { ChannelApiError } from "./api";
import type {
  ChannelControl,
  ChannelSnapshot,
  ChannelTransition,
  ChannelTransport,
} from "./types";

type Listener = () => void;

export class ChannelController implements ChannelControl {
  private snapshot: ChannelSnapshot = { status: "loading" };
  private readonly listeners = new Set<Listener>();
  private operation = 0;

  constructor(
    private readonly transport: ChannelTransport,
    private readonly transition: ChannelTransition,
  ) {}

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  getSnapshot(): ChannelSnapshot {
    return this.snapshot;
  }

  async load(): Promise<void> {
    const operation = ++this.operation;
    this.publish({ status: "loading" });
    try {
      const [catalog, current] = await Promise.all([
        this.transport.list(),
        this.transport.current(),
      ]);
      if (operation !== this.operation) return;
      const selected = catalog.items.find((item) => item.id === current.id);
      if (selected === undefined || !selected.enabled) {
        throw new ChannelApiError(0, "CHANNEL_RESPONSE_INVALID");
      }
      this.publish({
        status: "ready",
        items: catalog.items.map((item) => ({
          ...item,
          selected: item.id === current.id,
        })),
        selectedId: current.id,
      });
    } catch {
      if (operation === this.operation) {
        this.publish({
          status: "error",
          items: [],
          selectedId: null,
          message: "Channels are temporarily unavailable. Try again.",
        });
      }
    }
  }

  async select(channelId: string): Promise<void> {
    const ready = this.readySnapshot();
    if (ready === null || ready.selectedId === channelId) return;
    await this.transitionOperation(async () => {
      const selected = await this.transport.select(channelId);
      return {
        items: ready.items.map((item) => ({
          ...item,
          selected: item.id === selected.id,
        })),
        selectedId: selected.id,
        notice: "selected" as const,
      };
    });
  }

  async join(invite: string): Promise<void> {
    const normalized = invite.trim();
    const ready = this.readySnapshot();
    if (ready === null || normalized.length < 40 || normalized.length > 128) {
      this.publishError("Enter a valid private channel invite.");
      return;
    }
    try {
      await this.transport.join(normalized);
      const catalog = await this.transport.list();
      this.publish({ ...ready, items: catalog.items, notice: "joined" });
    } catch {
      this.publishError("That private channel invite is unavailable.");
    }
  }

  async leave(channelId: string): Promise<void> {
    const ready = this.readySnapshot();
    const channel = ready?.items.find((item) => item.id === channelId);
    if (ready === null || channel?.type !== "private") return;
    await this.transitionOperation(async () => {
      await this.transport.leave(channelId);
      const [catalog, current] = await Promise.all([
        this.transport.list(),
        this.transport.current(),
      ]);
      return {
        items: catalog.items,
        selectedId: current.id,
        notice: "left" as const,
      };
    });
  }

  private async transitionOperation(
    mutate: () => Promise<{
      items: Extract<ChannelSnapshot, { status: "ready" }>["items"];
      selectedId: string;
      notice: "selected" | "left";
    }>,
  ): Promise<void> {
    const ready = this.readySnapshot();
    if (ready === null) return;
    const operation = ++this.operation;
    this.publish({
      status: "switching",
      items: ready.items,
      selectedId: ready.selectedId,
    });
    try {
      await this.transition.prepareChannelTransition();
      const result = await mutate();
      await this.transition.completeChannelTransition();
      if (operation === this.operation) {
        this.publish({ status: "ready", ...result });
      }
    } catch (error) {
      try {
        await this.transition.completeChannelTransition();
      } catch {
        // Media remains fail closed when reconnect cleanup also fails.
      }
      if (operation === this.operation) {
        this.publish({
          status: "error",
          items: ready.items,
          selectedId: ready.selectedId,
          message: this.transitionMessage(error),
        });
      }
    }
  }

  private readySnapshot(): Extract<ChannelSnapshot, { status: "ready" }> | null {
    return this.snapshot.status === "ready" ? this.snapshot : null;
  }

  private publishError(message: string): void {
    const ready = this.readySnapshot();
    this.publish({
      status: "error",
      items: ready?.items ?? [],
      selectedId: ready?.selectedId ?? null,
      message,
    });
  }

  private transitionMessage(error: unknown): string {
    if (error instanceof ChannelApiError && error.code === "CHANNEL_MEDIA_ACTIVE") {
      return "Finish the active transmission, then try changing channels again.";
    }
    return "The channel could not be changed. Your prior channel remains selected.";
  }

  private publish(snapshot: ChannelSnapshot): void {
    this.snapshot = snapshot;
    this.listeners.forEach((listener) => listener());
  }
}
