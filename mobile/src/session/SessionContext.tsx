import type { ReactNode } from "react";
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useSyncExternalStore,
} from "react";

import { environment } from "../config";
import { AuthApi } from "./api";
import { SessionClient } from "./SessionClient";
import { secureSessionStorage } from "./storage";
import type { SessionSnapshot } from "./types";

const defaultClient = new SessionClient(
  new AuthApi(environment.apiBaseUrl),
  secureSessionStorage,
);
const Context = createContext<SessionClient | null>(null);

export function SessionProvider({
  children,
  client = defaultClient,
}: {
  children: ReactNode;
  client?: SessionClient;
}) {
  useEffect(() => {
    void client.bootstrap();
  }, [client]);
  return <Context.Provider value={client}>{children}</Context.Provider>;
}

export function useSession(): {
  snapshot: SessionSnapshot;
  logout(): Promise<void>;
  reconnect(): Promise<void>;
  revokeCurrentDevice(): Promise<void>;
} {
  const client = useContext(Context);
  if (client === null) {
    throw new Error("useSession must be used inside SessionProvider.");
  }
  const snapshot = useSyncExternalStore(
    (listener) => client.subscribe(listener),
    () => client.getSnapshot(),
  );
  return useMemo(
    () => ({
      snapshot,
      logout: () => client.logout(),
      reconnect: () => client.register(),
      revokeCurrentDevice: () => client.revokeCurrentDevice(),
    }),
    [client, snapshot],
  );
}
