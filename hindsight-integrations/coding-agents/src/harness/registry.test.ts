import { describe, expect, it } from "vitest";
import { getHarness, HARNESS_NAMES } from "./registry";

describe("HARNESS_NAMES", () => {
  it("lists all registered harnesses", () => {
    expect(HARNESS_NAMES).toEqual(
      expect.arrayContaining([
        "opencode",
        "kilo",
        "cline-cli",
        "claude-code",
        "cursor-cli",
        "codex",
        "antigravity-cli",
        "devin-cli",
      ])
    );
    expect(HARNESS_NAMES).toHaveLength(8);
  });
});

describe("getHarness", () => {
  it("resolves hook harnesses without touching the opencode adapter", async () => {
    for (const name of ["claude-code", "cursor-cli", "codex", "antigravity-cli", "devin-cli"]) {
      const adapter = await getHarness(name);
      expect(adapter.name).toBe(name);
      // Lightweight hook adapters have no persistent runtime — createRuntime always throws before
      // touching its argument, so a stand-in value is fine here.
      expect(() => adapter.createRuntime({} as never)).toThrow();
    }
  });

  it("resolves the opencode adapter by name", async () => {
    const adapter = await getHarness("opencode");
    expect(adapter.name).toBe("opencode");
    // Deliberate invariant: opencode via the registry is a no-runtime adapter (same shape as the
    // hook harnesses) — the real opencode runtime is built by src/index.ts importing opencodeAdapter
    // directly, bypassing this registry. Lock it so a future change can't silently make this look
    // functional.
    expect(() => adapter.createRuntime({} as never)).toThrow();
  });

  it("resolves Cline as a native-plugin harness rather than a hook binary", async () => {
    const adapter = await getHarness("cline-cli");
    expect(adapter.name).toBe("cline-cli");
    expect(() => adapter.createRuntime({} as never)).toThrow(/src\/cline\.ts/);
  });

  it("rejects unknown harness names", async () => {
    await expect(getHarness("nope")).rejects.toThrow(/unknown harness/);
  });
});
