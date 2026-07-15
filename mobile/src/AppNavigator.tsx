import { NavigationContainer, DefaultTheme } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";

import { DiagnosticsScreen } from "./screens/DiagnosticsScreen";
import { HomeScreen } from "./screens/HomeScreen";
import { IdentityScreen } from "./screens/IdentityScreen";
import { RecoveryScreen } from "./screens/RecoveryScreen";
import { colors } from "./theme";

export type RootStackParamList = {
  Foundation: undefined;
  Diagnostics: undefined;
  Identity: undefined;
  Recovery: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();
const theme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    background: colors.background,
    card: colors.surface,
    primary: colors.primary,
    text: colors.text,
    border: colors.border,
  },
};

export function AppNavigator() {
  return (
    <NavigationContainer theme={theme}>
      <Stack.Navigator
        initialRouteName="Foundation"
        screenOptions={{
          headerBackButtonDisplayMode: "minimal",
          headerTitleStyle: { fontWeight: "600" },
        }}
      >
        <Stack.Screen
          component={HomeScreen}
          name="Foundation"
          options={{ title: "RoadTalk" }}
        />
        <Stack.Screen
          component={IdentityScreen}
          name="Identity"
          options={{ title: "Identity" }}
        />
        <Stack.Screen
          component={RecoveryScreen}
          name="Recovery"
          options={{ title: "Account recovery" }}
        />
        <Stack.Screen
          component={DiagnosticsScreen}
          name="Diagnostics"
          options={{ title: "Diagnostics" }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
