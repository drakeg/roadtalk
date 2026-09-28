import { NavigationContainer, DefaultTheme } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";

import { CampgroundsScreen } from "./screens/CampgroundsScreen";
import { DiagnosticsScreen } from "./screens/DiagnosticsScreen";
import { ConvoysScreen } from "./screens/ConvoysScreen";
import { ChannelScreen } from "./screens/ChannelScreen";
import { HomeScreen } from "./screens/HomeScreen";
import { IdentityScreen } from "./screens/IdentityScreen";
import { LocationPermissionScreen } from "./screens/LocationPermissionScreen";
import { MapAwarenessScreen } from "./screens/MapAwarenessScreen";
import { MicrophonePermissionScreen } from "./screens/MicrophonePermissionScreen";
import { NotificationsScreen } from "./screens/NotificationsScreen";
import { RecoveryScreen } from "./screens/RecoveryScreen";
import { SafetyScreen } from "./screens/SafetyScreen";
import { RouteModeScreen } from "./screens/RouteModeScreen";
import { colors } from "./theme";

export type RootStackParamList = {
  Foundation: undefined;
  Campgrounds: undefined;
  Channels: undefined;
  Diagnostics: undefined;
  Convoys: undefined;
  Identity: undefined;
  LocationPermission: undefined;
  MapAwareness: undefined;
  MicrophonePermission: undefined;
  Notifications: undefined;
  Recovery: undefined;
  Safety: undefined;
  RouteMode: undefined;
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
        <Stack.Screen component={CampgroundsScreen} name="Campgrounds" options={{ title: "Campgrounds" }} />
        <Stack.Screen component={ChannelScreen} name="Channels" options={{ title: "Channels" }} />
        <Stack.Screen component={ConvoysScreen} name="Convoys" options={{ title: "Convoys" }} />
        <Stack.Screen component={RouteModeScreen} name="RouteMode" options={{ title: "Audience mode" }} />
        <Stack.Screen component={MapAwarenessScreen} name="MapAwareness" options={{ title: "Map awareness" }} />
        <Stack.Screen component={LocationPermissionScreen} name="LocationPermission" options={{ title: "Location privacy" }} />
        <Stack.Screen component={MicrophonePermissionScreen} name="MicrophonePermission" options={{ title: "Microphone and live audio" }} />
        <Stack.Screen component={NotificationsScreen} name="Notifications" options={{ title: "Notifications" }} />
        <Stack.Screen component={HomeScreen} name="Foundation" options={{ title: "RoadTalk" }} />
        <Stack.Screen component={IdentityScreen} name="Identity" options={{ title: "Identity" }} />
        <Stack.Screen component={RecoveryScreen} name="Recovery" options={{ title: "Account recovery" }} />
        <Stack.Screen component={SafetyScreen} name="Safety" options={{ title: "Safety controls" }} />
        <Stack.Screen component={DiagnosticsScreen} name="Diagnostics" options={{ title: "Diagnostics" }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
