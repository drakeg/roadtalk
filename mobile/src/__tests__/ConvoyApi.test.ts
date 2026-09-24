import { ConvoyApi } from "../convoys/api";

describe("mobile convoy API", () => {
  it("uses only authenticated server convoy endpoints", async () => {
    const authenticatedFetch = jest.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(null), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(null), { status: 200 }));
    const api = new ConvoyApi({ authenticatedFetch } as never);
    await api.status();
    await api.awareness();
    expect(authenticatedFetch.mock.calls.map((call) => call[0])).toEqual([
      expect.stringMatching(/\/convoys\/me$/),
      expect.stringMatching(/\/convoys\/awareness$/),
    ]);
  });

  it("sends only bounded lifecycle fields", async () => {
    const response = { convoy_id: "c", membership_id: "m", display_name: "Crew", role: "leader", state: "active" };
    const authenticatedFetch = jest.fn().mockImplementation(() =>\n      Promise.resolve(new Response(JSON.stringify(response), { status: 200 })),\n    );
    const api = new ConvoyApi({ authenticatedFetch } as never);
    await api.create("Crew");
    await api.join("00000000-0000-0000-0000-000000000001");
    expect(JSON.parse(authenticatedFetch.mock.calls[0][1].body)).toEqual({ display_name: "Crew" });
    expect(JSON.parse(authenticatedFetch.mock.calls[1][1].body)).toEqual({ convoy_id: "00000000-0000-0000-0000-000000000001" });
    const encoded = JSON.stringify(authenticatedFetch.mock.calls).toLowerCase();
    for (const forbidden of ["latitude", "longitude", "route_history", "background_location", "microphone"]) {
      expect(encoded).not.toContain(forbidden);
    }
  });
});
