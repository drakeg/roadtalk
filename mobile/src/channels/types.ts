export type ChannelSummary = {
  id: string;
  slug: "general" | "rv" | null;
  displayLabel: string;
  type: "public" | "private";
  selected: boolean;
  enabled: boolean;
  version: number;
};

export type ChannelCatalog = {
  items: ChannelSummary[];
};

export type ChannelSelection = ChannelSummary & {
  selected: true;
  selectedAt: string;
  selectionVersion: number;
};

export type ChannelLifecycle = {
  channelId: string;
  state: "joined" | "left" | "closed";
  changedAt: string;
  replayed: boolean;
};

export type PrivateChannelReceipt = ChannelSummary & {
  createdAt: string;
  invite: string | null;
  replayed: boolean;
};

export type ChannelTransport = {
  list(): Promise<ChannelCatalog>;
  current(): Promise<ChannelSelection>;
  select(channelId: string): Promise<ChannelSelection>;
  join(invite: string): Promise<ChannelLifecycle>;
  leave(channelId: string): Promise<ChannelLifecycle>;
  create(displayLabel: string): Promise<PrivateChannelReceipt>;
  rotate(channelId: string): Promise<PrivateChannelReceipt>;
  close(channelId: string): Promise<ChannelLifecycle>;
};

export type ChannelTransition = {
  prepareChannelTransition(): Promise<void>;
  completeChannelTransition(): Promise<void>;
};

export type ChannelSnapshot =
  | { status: "loading" }
  | {
      status: "ready";
      items: ChannelSummary[];
      selectedId: string;
      notice?:
        | "joined"
        | "left"
        | "selected"
        | "created"
        | "rotated"
        | "closed";
      oneTimeInvite?: { channelId: string; value: string } | undefined;
    }
  | {
      status: "switching";
      items: ChannelSummary[];
      selectedId: string;
    }
  | {
      status: "error";
      items: ChannelSummary[];
      selectedId: string | null;
      message: string;
    };

export type ChannelControl = {
  subscribe(listener: () => void): () => void;
  getSnapshot(): ChannelSnapshot;
  load(): Promise<void>;
  select(channelId: string): Promise<void>;
  join(invite: string): Promise<void>;
  leave(channelId: string): Promise<void>;
  create(displayLabel: string): Promise<void>;
  rotate(channelId: string): Promise<void>;
  close(channelId: string): Promise<void>;
  dismissInvite(): void;
};
