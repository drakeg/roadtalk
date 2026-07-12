import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { AppNavigator } from "./src/AppNavigator";
import { ErrorBoundary } from "./src/ErrorBoundary";
import { SessionProvider } from "./src/session/SessionContext";

export default function App() {
  return (
    <ErrorBoundary>
      <SessionProvider>
        <SafeAreaProvider>
          <StatusBar style="auto" />
          <AppNavigator />
        </SafeAreaProvider>
      </SessionProvider>
    </ErrorBoundary>
  );
}
