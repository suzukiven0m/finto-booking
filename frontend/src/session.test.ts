import { beforeEach, describe, expect, it, vi } from "vitest";

// WP3-mandated (P1/P2): session round-trip and wrong-shape guard, node env
// with a stubbed sessionStorage (no browser storage here).
function stubStorage() {
  const store = new Map<string, string>();
  vi.stubGlobal("sessionStorage", {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
    removeItem: (key: string) => {
      store.delete(key);
    },
  });
  return store;
}

async function freshSession() {
  vi.resetModules();
  return import("./session");
}

const session = { email: "manager@buby.travel", role: "manager", token: "jwt-di-prova" };

beforeEach(() => {
  vi.unstubAllGlobals();
});

describe("session storage", () => {
  it("saves, loads and clears the session round-trip", async () => {
    const store = stubStorage();
    const { saveSession, loadSession, clearSession } = await freshSession();

    expect(loadSession()).toBeNull();
    saveSession(session);
    expect(store.get("buby-session")).toBe(JSON.stringify(session));
    expect(loadSession()).toEqual(session);
    clearSession();
    expect(store.has("buby-session")).toBe(false);
    expect(loadSession()).toBeNull();
  });

  it.each([
    ["token not a string", { email: "manager@buby.travel", role: "manager", token: 123 }],
    ["email not a string", { email: null, role: "manager", token: "jwt-di-prova" }],
    ["missing fields", { role: "manager" }],
    ["a bare string", "jwt-di-prova"],
    ["an array", [session]],
    ["null", null],
  ])("loadSession returns null for valid-JSON-wrong-shape storage (%s)", async (_label, value) => {
    const store = stubStorage();
    store.set("buby-session", JSON.stringify(value));
    const { loadSession } = await freshSession();
    expect(loadSession()).toBeNull();
  });

  it("loadSession returns null for invalid JSON", async () => {
    const store = stubStorage();
    store.set("buby-session", "{non-json");
    const { loadSession } = await freshSession();
    expect(loadSession()).toBeNull();
  });
});