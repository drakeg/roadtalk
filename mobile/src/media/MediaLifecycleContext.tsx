import type { ReactNode } from "react";
import { createContext, useContext, useEffect, useMemo } from "react";
import { AppState } from "react-native";

import { useSession, useSessionClient } from "../session/SessionContext";
import { createDefaultMediaLifecycle } from "./defaultLifecycle";
import type { MediaLifecycleControl } from "./types";

const Context = createContext<MediaLifecycleControl | null>(null);

export function MediaLifecycleProvider({ children }: { children: ReactNode }) {
  const session = useSessionClient();
  const { snapshot } = useSession();
  const lifecycle = useMemo(() => createDefaultMediaLifecycle(session), [session]);
  useEffect(() => {
    void lifecycle.setAuthenticated(snapshot.status === "authenticated");
  }, [lifecycle, snapshot.status]);
  useEffect(() => {
    void lifecycle.setAppActive(AppState.currentState === "active");
    const subscription = AppState.addEventListener("change", (state) => {
      void lifecycle.setAppActive(state === "active");
    });
    return () => subscription.remove();
  }, [lifecycle]);
  useEffect(() => () => void lifecycle.dispose(), [lifecycle]);
  return <Context.Provider value={lifecycle}>{children}</Context.Provider>;
}

export function useMediaLifecycle(): MediaLifecycleControl | null {
  return useContext(Context);
}
