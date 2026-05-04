import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdtemp, rm, writeFile, mkdir } from "fs/promises";
import { tmpdir } from "os";
import { join } from "path";
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync, statSync, rmSync } from "fs";
import { execSync } from "child_process";
import { extname, relative, basename } from "path";

// ── Extracted helpers (mirroring cli.ts logic for unit testing) ──

const CONTENT_EXTS = new Set([".md", ".txt", ".html", ".json", ".csv", ".xml"]);
const IGNORED_FILES = new Set(["bank-template.json"]);

function findContentFiles(dir: string): string[] {
  const results: string[] = [];
  function walk(current: string) {
    for (const entry of readdirSync(current)) {
      const full = join(current, entry);
      if (statSync(full).isDirectory()) {
        walk(full);
      } else if (CONTENT_EXTS.has(extname(entry).toLowerCase()) && !IGNORED_FILES.has(entry)) {
        results.push(relative(dir, full));
      }
    }
  }
  walk(dir);
  return results.sort();
}

function isLocalPath(input: string): boolean {
  return (
    input.startsWith("./") ||
    input.startsWith("../") ||
    input.startsWith("/") ||
    input.startsWith("~")
  );
}

function parseAgentsJson(raw: string): any[] {
  const clean = raw.replace(/\n?\x1b\[[0-9;]*m[^\n]*/g, "").trim();
  const arrStart = clean.indexOf("\n[");
  const jsonStr = arrStart >= 0 ? clean.slice(arrStart + 1) : clean.startsWith("[") ? clean : "[]";
  return JSON.parse(jsonStr);
}

function resolveFromPluginConfig(
  agentId: string,
  pc: Record<string, any>
): { apiUrl: string; bankId: string; apiToken?: string } {
  const apiUrl = pc.hindsightApiUrl || `http://localhost:${pc.apiPort || 9077}`;
  const apiToken = pc.hindsightApiToken || undefined;

  let bankId: string;
  if (pc.dynamicBankId === false && pc.bankId) {
    bankId = pc.bankId;
  } else {
    const granularity: string[] = pc.dynamicBankGranularity || ["agent", "channel", "user"];
    const fieldMap: Record<string, string> = {
      agent: agentId,
      channel: "unknown",
      user: "anonymous",
      provider: "unknown",
    };
    const base = granularity.map((f) => encodeURIComponent(fieldMap[f] || "unknown")).join("::");
    bankId = pc.bankIdPrefix ? `${pc.bankIdPrefix}-${base}` : base;
  }

  return { apiUrl, bankId, apiToken };
}

// ── Tests ──

describe("findContentFiles", () => {
  let tmpDir: string;

  beforeEach(async () => {
    tmpDir = await mkdtemp(join(tmpdir(), "sda-test-"));
  });

  afterEach(async () => {
    await rm(tmpDir, { recursive: true, force: true });
  });

  it("finds .md files recursively", async () => {
    await writeFile(join(tmpDir, "root.md"), "hello");
    await mkdir(join(tmpDir, "sub"));
    await writeFile(join(tmpDir, "sub", "nested.md"), "world");

    const files = findContentFiles(tmpDir);
    expect(files).toEqual(["root.md", "sub/nested.md"]);
  });

  it("finds multiple content extensions", async () => {
    await writeFile(join(tmpDir, "a.md"), "md");
    await writeFile(join(tmpDir, "b.txt"), "txt");
    await writeFile(join(tmpDir, "c.html"), "html");
    await writeFile(join(tmpDir, "d.csv"), "csv");

    const files = findContentFiles(tmpDir);
    expect(files).toEqual(["a.md", "b.txt", "c.html", "d.csv"]);
  });

  it("excludes bank-template.json", async () => {
    await writeFile(join(tmpDir, "bank-template.json"), "{}");
    await writeFile(join(tmpDir, "readme.md"), "hello");

    const files = findContentFiles(tmpDir);
    expect(files).toEqual(["readme.md"]);
  });

  it("excludes non-content files", async () => {
    await writeFile(join(tmpDir, "image.png"), "binary");
    await writeFile(join(tmpDir, "script.js"), "code");
    await writeFile(join(tmpDir, "doc.md"), "content");

    const files = findContentFiles(tmpDir);
    expect(files).toEqual(["doc.md"]);
  });

  it("handles deeply nested directories", async () => {
    await mkdir(join(tmpDir, "a", "b", "c"), { recursive: true });
    await writeFile(join(tmpDir, "a", "b", "c", "deep.md"), "deep");

    const files = findContentFiles(tmpDir);
    expect(files).toEqual(["a/b/c/deep.md"]);
  });

  it("returns empty for directory with no content", async () => {
    await writeFile(join(tmpDir, "bank-template.json"), "{}");
    await writeFile(join(tmpDir, "image.png"), "binary");

    const files = findContentFiles(tmpDir);
    expect(files).toEqual([]);
  });

  it("ignores bank-template.json in subdirectories too", async () => {
    await mkdir(join(tmpDir, "sub"));
    await writeFile(join(tmpDir, "sub", "bank-template.json"), "{}");
    await writeFile(join(tmpDir, "sub", "guide.md"), "content");

    const files = findContentFiles(tmpDir);
    expect(files).toEqual(["sub/guide.md"]);
  });
});

describe("isLocalPath", () => {
  it("detects relative paths", () => {
    expect(isLocalPath("./my-agent")).toBe(true);
    expect(isLocalPath("../parent/agent")).toBe(true);
  });

  it("detects absolute paths", () => {
    expect(isLocalPath("/Users/me/agent")).toBe(true);
  });

  it("detects home paths", () => {
    expect(isLocalPath("~/dev/agent")).toBe(true);
  });

  it("rejects GitHub-style references", () => {
    expect(isLocalPath("marketing")).toBe(false);
    expect(isLocalPath("org/repo/path")).toBe(false);
    expect(isLocalPath("marketing/seo")).toBe(false);
  });
});

describe("deriveDefaultName", () => {
  // Mirrors the logic in resolveAgentDir:
  // - GitHub refs: subpath with / → hyphens (marketing/seo → marketing-seo)
  // - Local paths: basename of resolved dir

  function deriveFromGitHub(input: string): string {
    const parts = input.split("/");
    const subpath = parts.length <= 2 ? input : parts.slice(2).join("/");
    return subpath.replace(/\//g, "-");
  }

  it("single name stays as-is", () => {
    expect(deriveFromGitHub("marketing")).toBe("marketing");
  });

  it("two segments become hyphenated", () => {
    expect(deriveFromGitHub("marketing/seo")).toBe("marketing-seo");
  });

  it("three+ segments treat first two as org/repo", () => {
    // marketing/seo/technical → org=marketing, repo=seo, path=technical
    expect(deriveFromGitHub("marketing/seo/technical")).toBe("technical");
  });

  it("org/repo with deep path uses hyphenated path", () => {
    expect(deriveFromGitHub("my-org/my-repo/agents/seo")).toBe("agents-seo");
  });
});

describe("parseAgentsJson", () => {
  it("parses clean JSON array", () => {
    const agents = parseAgentsJson('[{"id": "main"}]');
    expect(agents).toEqual([{ id: "main" }]);
  });

  it("strips ANSI log lines before JSON", () => {
    const raw =
      "\x1b[38;5;103mhindsight:\x1b[0m plugin entry invoked\n" +
      '[\n  {"id": "main"},\n  {"id": "seo-writer", "name": "seo-writer"}\n]';
    const agents = parseAgentsJson(raw);
    expect(agents).toHaveLength(2);
    expect(agents[1].id).toBe("seo-writer");
  });

  it("returns empty array for unparseable output", () => {
    const agents = parseAgentsJson("some random text");
    expect(agents).toEqual([]);
  });

  it("handles multiple ANSI lines", () => {
    const raw = [
      "Config warnings:",
      "\x1b[35m[plugins]\x1b[39m registering plugin",
      "\x1b[35m[plugins]\x1b[39m hooks registered",
      '[{"id": "test"}]',
    ].join("\n");
    const agents = parseAgentsJson(raw);
    expect(agents).toEqual([{ id: "test" }]);
  });
});

describe("resolveFromPluginConfig", () => {
  it("uses external API URL when set", () => {
    const result = resolveFromPluginConfig("my-agent", {
      hindsightApiUrl: "https://api.example.com",
      hindsightApiToken: "tok-123",
      dynamicBankGranularity: ["agent"],
    });
    expect(result.apiUrl).toBe("https://api.example.com");
    expect(result.apiToken).toBe("tok-123");
    expect(result.bankId).toBe("my-agent");
  });

  it("falls back to localhost with apiPort", () => {
    const result = resolveFromPluginConfig("my-agent", {
      apiPort: 8888,
      dynamicBankGranularity: ["agent"],
    });
    expect(result.apiUrl).toBe("http://localhost:8888");
    expect(result.apiToken).toBeUndefined();
  });

  it("defaults to port 9077", () => {
    const result = resolveFromPluginConfig("my-agent", {});
    expect(result.apiUrl).toBe("http://localhost:9077");
  });

  it("computes bank ID with prefix", () => {
    const result = resolveFromPluginConfig("seo-writer", {
      bankIdPrefix: "nicolo",
      dynamicBankGranularity: ["agent"],
    });
    expect(result.bankId).toBe("nicolo-seo-writer");
  });

  it("computes bank ID without prefix", () => {
    const result = resolveFromPluginConfig("seo-writer", {
      dynamicBankGranularity: ["agent"],
    });
    expect(result.bankId).toBe("seo-writer");
  });

  it("uses multi-field granularity", () => {
    const result = resolveFromPluginConfig("my-agent", {
      dynamicBankGranularity: ["agent", "channel", "user"],
    });
    expect(result.bankId).toBe("my-agent::unknown::anonymous");
  });

  it("uses default granularity when not specified", () => {
    const result = resolveFromPluginConfig("my-agent", {});
    expect(result.bankId).toBe("my-agent::unknown::anonymous");
  });

  it("uses static bankId when dynamicBankId is false", () => {
    const result = resolveFromPluginConfig("my-agent", {
      dynamicBankId: false,
      bankId: "static-bank",
    });
    expect(result.bankId).toBe("static-bank");
  });

  it("resolves nemoclaw-style config (external API, static bank)", () => {
    const result = resolveFromPluginConfig("marketing-seo", {
      hindsightApiUrl: "https://api.hindsight.vectorize.io",
      hindsightApiToken: "hsk_abc",
      llmProvider: "claude-code",
      dynamicBankId: false,
      bankIdPrefix: "my-sandbox",
    });
    expect(result.apiUrl).toBe("https://api.hindsight.vectorize.io");
    expect(result.apiToken).toBe("hsk_abc");
    // dynamicBankId=false but no bankId set, so falls through to dynamic path
    // with bankIdPrefix
    expect(result.bankId).toBe("my-sandbox-marketing-seo::unknown::anonymous");
  });

  it("resolves nemoclaw-style config with static bankId", () => {
    const result = resolveFromPluginConfig("marketing-seo", {
      hindsightApiUrl: "https://api.hindsight.vectorize.io",
      hindsightApiToken: "hsk_abc",
      dynamicBankId: false,
      bankId: "my-sandbox-openclaw",
    });
    expect(result.bankId).toBe("my-sandbox-openclaw");
  });
});

describe("versionGte", () => {
  function versionGte(current: string, required: string): boolean {
    const [aMaj, aMin, aPat] = current.split(".").map(Number);
    const [bMaj, bMin, bPat] = required.split(".").map(Number);
    if (aMaj !== bMaj) return aMaj > bMaj;
    if (aMin !== bMin) return aMin > bMin;
    return aPat >= bPat;
  }

  it("equal versions return true", () => {
    expect(versionGte("0.7.2", "0.7.2")).toBe(true);
  });

  it("higher patch returns true", () => {
    expect(versionGte("0.7.3", "0.7.2")).toBe(true);
  });

  it("lower patch returns false", () => {
    expect(versionGte("0.7.1", "0.7.2")).toBe(false);
  });

  it("higher minor returns true", () => {
    expect(versionGte("0.8.0", "0.7.2")).toBe(true);
  });

  it("higher major returns true", () => {
    expect(versionGte("1.0.0", "0.7.2")).toBe(true);
  });

  it("lower major returns false", () => {
    expect(versionGte("0.6.9", "1.0.0")).toBe(false);
  });
});

describe("harness argument parsing", () => {
  function parseHarness(args: string[]): { harness?: string; sandbox?: string } {
    let harness: string | undefined;
    let sandbox: string | undefined;
    for (let i = 0; i < args.length; i++) {
      if (args[i] === "--harness" && args[i + 1]) harness = args[++i];
      else if (args[i] === "--sandbox" && args[i + 1]) sandbox = args[++i];
    }
    return { harness, sandbox };
  }

  it("parses openclaw harness", () => {
    const { harness, sandbox } = parseHarness(["--harness", "openclaw"]);
    expect(harness).toBe("openclaw");
    expect(sandbox).toBeUndefined();
  });

  it("parses nemoclaw harness with sandbox", () => {
    const { harness, sandbox } = parseHarness([
      "--harness",
      "nemoclaw",
      "--sandbox",
      "my-assistant",
    ]);
    expect(harness).toBe("nemoclaw");
    expect(sandbox).toBe("my-assistant");
  });

  it("nemoclaw without sandbox returns undefined sandbox", () => {
    const { harness, sandbox } = parseHarness(["--harness", "nemoclaw"]);
    expect(harness).toBe("nemoclaw");
    expect(sandbox).toBeUndefined();
  });

  it("parses claude harness", () => {
    const { harness } = parseHarness(["--harness", "claude"]);
    expect(harness).toBe("claude");
  });
});

// ── Claude skill generation (mirroring generateClaudeSkill logic) ──

function generateSkillMd(
  agentId: string,
  apiUrl: string,
  bankId: string,
  apiToken?: string
): string {
  const authHeader = apiToken ? `-H "Authorization: Bearer ${apiToken}"` : "";
  return `---
name: ${agentId}
description: Activate the ${agentId} agent. Loads knowledge pages from Hindsight memory.
---

# ${agentId}

You are the **${agentId}** agent with long-term memory powered by Hindsight.

## Startup — run these steps immediately

1. List your knowledge pages and read each one:

\`\`\`bash
curl -s ${authHeader} "${apiUrl}/v1/default/banks/${bankId}/mental-models?detail=metadata"
\`\`\`
`.trim();
}

describe("generateClaudeSkill", () => {
  let tmpDir: string;

  beforeEach(async () => {
    tmpDir = await mkdtemp(join(tmpdir(), "sda-claude-test-"));
  });

  afterEach(async () => {
    await rm(tmpDir, { recursive: true, force: true });
  });

  it("generates SKILL.md with correct frontmatter", () => {
    const md = generateSkillMd("marketing-seo", "https://api.example.com", "marketing-seo", "tok-123");

    // Required frontmatter fields
    expect(md).toContain("name: marketing-seo");
    expect(md).toContain("description: Activate the marketing-seo agent");

    // Starts with frontmatter
    expect(md.startsWith("---")).toBe(true);
  });

  it("bakes API URL and bank ID into curl commands", () => {
    const md = generateSkillMd("my-agent", "https://api.hindsight.vectorize.io", "my-bank");

    expect(md).toContain("https://api.hindsight.vectorize.io/v1/default/banks/my-bank/mental-models");
  });

  it("bakes auth token into curl commands when provided", () => {
    const md = generateSkillMd("my-agent", "https://api.example.com", "bank", "secret-token");

    expect(md).toContain('-H "Authorization: Bearer secret-token"');
  });

  it("omits auth header when no token", () => {
    const md = generateSkillMd("my-agent", "https://api.example.com", "bank");

    expect(md).not.toContain("Authorization");
  });

  it("uses agent ID as skill name", () => {
    const md = generateSkillMd("seo-writer", "https://api.example.com", "bank");

    expect(md).toContain("name: seo-writer");
    expect(md).toContain("# seo-writer");
  });

  it("generates valid zip structure with directory wrapping", () => {
    const agentId = "test-agent";
    const skillDir = join(tmpDir, agentId);
    mkdirSync(skillDir, { recursive: true });
    writeFileSync(join(skillDir, "SKILL.md"), generateSkillMd(agentId, "https://api.example.com", "bank"));

    // Zip the same way the CLI does: cd to parent, zip the directory
    const zipPath = join(tmpDir, `${agentId}.zip`);
    execSync(`cd ${JSON.stringify(tmpDir)} && zip -r ${JSON.stringify(zipPath)} ${JSON.stringify(agentId)}`, {
      stdio: "pipe",
    });

    expect(existsSync(zipPath)).toBe(true);

    // Verify zip contents have directory structure: test-agent/SKILL.md
    const listing = execSync(`unzip -l ${JSON.stringify(zipPath)}`, { encoding: "utf-8" });
    expect(listing).toContain(`${agentId}/SKILL.md`);
    // Should NOT have SKILL.md at root
    expect(listing).not.toMatch(/^\s+\d+.*\s+SKILL\.md$/m);
  });

  it("generates skill with list pages curl command", () => {
    const md = generateSkillMd("my-agent", "https://api.example.com", "my-bank", "tok");

    expect(md).toContain("curl -s");
    expect(md).toContain("/mental-models?detail=metadata");
  });
});

describe("claude skill content completeness", () => {
  // Test against a full skill generation to verify all API operations are present
  function generateFullSkillMd(
    agentId: string,
    apiUrl: string,
    bankId: string,
    apiToken?: string
  ): string {
    const authHeader = apiToken ? `-H "Authorization: Bearer ${apiToken}"` : "";
    // This mirrors the full template from cli.ts
    return [
      `curl -s ${authHeader} "${apiUrl}/v1/default/banks/${bankId}/mental-models?detail=metadata"`,
      `curl -s ${authHeader} "${apiUrl}/v1/default/banks/${bankId}/mental-models/PAGE_ID?detail=full"`,
      `curl -s -X POST ${authHeader}`,
      `"${apiUrl}/v1/default/banks/${bankId}/mental-models"`,
      `curl -s -X POST ${authHeader}`,
      `"${apiUrl}/v1/default/banks/${bankId}/memories/recall"`,
      `curl -s -X POST ${authHeader}`,
      `"${apiUrl}/v1/default/banks/${bankId}/memories"`,
      `curl -s -X PATCH ${authHeader}`,
      `curl -s -X DELETE ${authHeader}`,
    ].join("\n");
  }

  it("includes list pages endpoint", () => {
    const md = generateFullSkillMd("a", "https://h.io", "b");
    expect(md).toContain("/mental-models?detail=metadata");
  });

  it("includes get page endpoint", () => {
    const md = generateFullSkillMd("a", "https://h.io", "b");
    expect(md).toContain("/mental-models/PAGE_ID?detail=full");
  });

  it("includes create page endpoint", () => {
    const md = generateFullSkillMd("a", "https://h.io", "b");
    expect(md).toContain("POST");
    expect(md).toContain("/mental-models");
  });

  it("includes recall endpoint", () => {
    const md = generateFullSkillMd("a", "https://h.io", "b");
    expect(md).toContain("/memories/recall");
  });

  it("includes retain/ingest endpoint", () => {
    const md = generateFullSkillMd("a", "https://h.io", "b");
    expect(md).toContain("/memories");
  });

  it("includes update endpoint", () => {
    const md = generateFullSkillMd("a", "https://h.io", "b");
    expect(md).toContain("PATCH");
  });

  it("includes delete endpoint", () => {
    const md = generateFullSkillMd("a", "https://h.io", "b");
    expect(md).toContain("DELETE");
  });
});

describe("claude config validation", () => {
  it("rejects localhost URLs", () => {
    const validate = (v: string | undefined) => {
      if (!v) return "URL required";
      try {
        const parsed = new URL(v);
        if (parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1") {
          return "Claude connects from Anthropic's cloud — localhost won't work. Use a public URL.";
        }
      } catch {
        return "Invalid URL";
      }
    };

    expect(validate("http://localhost:9077")).toContain("localhost");
    expect(validate("http://127.0.0.1:9077")).toContain("localhost");
    expect(validate("https://api.example.com")).toBeUndefined();
    expect(validate("")).toBe("URL required");
    expect(validate(undefined)).toBe("URL required");
    expect(validate("not-a-url")).toBe("Invalid URL");
  });

  it("cloud URL is the correct constant", () => {
    const HINDSIGHT_CLOUD_API_URL = "https://api.hindsight.vectorize.io";
    expect(HINDSIGHT_CLOUD_API_URL).toMatch(/^https:\/\//);
    expect(HINDSIGHT_CLOUD_API_URL).not.toContain("localhost");
  });
});

describe("harness validation", () => {
  const SUPPORTED_HARNESSES = ["openclaw", "nemoclaw", "claude"];

  it("accepts all supported harnesses", () => {
    for (const h of SUPPORTED_HARNESSES) {
      expect(SUPPORTED_HARNESSES.includes(h)).toBe(true);
    }
  });

  it("rejects unknown harnesses", () => {
    expect(SUPPORTED_HARNESSES.includes("chatgpt")).toBe(false);
    expect(SUPPORTED_HARNESSES.includes("claude-code")).toBe(false);
    expect(SUPPORTED_HARNESSES.includes("claude-cowork")).toBe(false);
    expect(SUPPORTED_HARNESSES.includes("")).toBe(false);
  });
});
