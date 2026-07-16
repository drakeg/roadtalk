import * as Location from "expo-location";

import type {
  ForegroundPermission,
  LocationFix,
  LocationGateway,
  LocationPrecision,
} from "./types";

function precision(
  permission: Location.LocationPermissionResponse,
): LocationPrecision | null {
  if (!permission.granted) {
    return null;
  }
  if (
    permission.ios?.accuracy === "reduced" ||
    permission.android?.accuracy === "coarse"
  ) {
    return "approximate";
  }
  return "precise";
}

export function normalizePermission(
  permission: Location.LocationPermissionResponse,
): ForegroundPermission {
  return {
    status: permission.status,
    canAskAgain: permission.canAskAgain,
    precision: precision(permission),
  };
}

function normalizeFix(location: Location.LocationObject): LocationFix {
  return {
    latitude: location.coords.latitude,
    longitude: location.coords.longitude,
    horizontalAccuracyM: location.coords.accuracy,
    headingDeg: location.coords.heading,
    speedMps: location.coords.speed,
    observedAtMs: location.timestamp,
  };
}

export const expoLocationGateway: LocationGateway = {
  hasServicesEnabled: () => Location.hasServicesEnabledAsync(),
  async getForegroundPermission() {
    return normalizePermission(await Location.getForegroundPermissionsAsync());
  },
  async requestForegroundPermission() {
    return normalizePermission(await Location.requestForegroundPermissionsAsync());
  },
  async watch(onLocation, onError) {
    return Location.watchPositionAsync(
      {
        accuracy: Location.Accuracy.Balanced,
        distanceInterval: 25,
        timeInterval: 10_000,
        mayShowUserSettingsDialog: false,
      },
      (location) => onLocation(normalizeFix(location)),
      () => onError(),
    );
  },
};
