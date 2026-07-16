import { PermissionStatus } from "expo-location";
import type { LocationPermissionResponse } from "expo-location";

import { normalizePermission } from "../location/gateway";

function permission(
  overrides: Partial<LocationPermissionResponse>,
): LocationPermissionResponse {
  return {
    status: PermissionStatus.GRANTED,
    granted: true,
    canAskAgain: true,
    expires: "never",
    ...overrides,
  };
}

describe("foreground permission normalization", () => {
  it("preserves precise, approximate, denied, and blocked choices", () => {
    expect(
      normalizePermission(permission({ ios: { scope: "whenInUse", accuracy: "full" } })),
    ).toEqual({ status: "granted", canAskAgain: true, precision: "precise" });
    expect(
      normalizePermission(
        permission({ android: { accuracy: "coarse" } }),
      ),
    ).toEqual({ status: "granted", canAskAgain: true, precision: "approximate" });
    expect(
      normalizePermission(
        permission({
          status: PermissionStatus.DENIED,
          granted: false,
          canAskAgain: true,
        }),
      ),
    ).toEqual({ status: "denied", canAskAgain: true, precision: null });
    expect(
      normalizePermission(
        permission({
          status: PermissionStatus.DENIED,
          granted: false,
          canAskAgain: false,
        }),
      ),
    ).toEqual({ status: "denied", canAskAgain: false, precision: null });
  });
});
