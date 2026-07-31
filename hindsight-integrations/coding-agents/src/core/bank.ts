/**
 * Dynamic bank resolution — which memory bank does THIS directory belong to?
 *
 * Coding memory is per-REPOSITORY: by default the bank id is derived from the git repo the
 * working directory lives in, worktree-aware — every linked worktree of a repo resolves to the
 * main worktree's basename and therefore shares one bank.
 *
 * Resolution order:
 *   1. `mapPathToBank` — absolute path -> bank; LONGEST matching prefix wins, so mapping a
 *      repo root covers every subdirectory (and worktree paths can be pinned individually).
 *      Overrides everything, including an explicit bankId.
 *   2. static — when `dynamicBankId` is false, or left unset WITH an explicit `bankId`
 *      (the benchmark harness and single-bank setups).
 *   3. dynamic — `bankIdTemplate` (default "coding-agent::{gitProject}") with placeholders:
 *        {gitProject}  worktree-aware repo name (all worktrees share it; non-git: dir basename)
 *        {project}     working-directory basename (no git involved)
 *        {harness}     the entry point asking ("opencode", "claude-code", "codex", "antigravity-cli", ...)
 *        {channel}     $HINDSIGHT_CHANNEL_ID or "default"
 *        {user}        $HINDSIGHT_USER_ID or "anonymous"
 *      e.g. "hindsight-{gitProject}" or "{harness}-{gitProject}" to split per agent. The default
 *      is harness-neutral "coding-agent::{gitProject}" so every coding agent shares ONE memory per repo.
 */
import { execFileSync } from "node:child_process";
import { homedir } from "node:os";
import { basename, dirname, join, normalize, sep } from "node:path";

export interface BankConfig {
  bankId?: string;
  dynamicBankId?: boolean;
  bankIdTemplate?: string;
  mapPathToBank?: Record<string, string>;
  resolveWorktrees?: boolean; // default true: worktrees share the main repo's bank
}

const DEFAULT_BANK_NAME = "coding";
// Harness-NEUTRAL default so every coding agent (Claude, Codex, Cursor, opencode) shares ONE bank
// per repo — switch agents, keep your memory. Namespaced with `coding-agent::` to identify these
// banks and avoid collisions with other Hindsight banks. Deliberately NOT `{harness}::…` (that would
// split memory per agent, defeating cross-agent sharing).
const DEFAULT_TEMPLATE = "coding-agent::{gitProject}";
const PLACEHOLDER = /\{([a-zA-Z]+)\}/g;

/** Main-worktree root for a directory inside a git repo (worktree- and bare-repo-aware), else null. */
export function getProjectRootFromGit(directory: string): string | null {
  if (!directory) return null;
  try {
    const commonDir = execFileSync(
      "git",
      ["rev-parse", "--path-format=absolute", "--git-common-dir"],
      { cwd: directory, encoding: "utf-8", stdio: ["ignore", "pipe", "ignore"], timeout: 1000 }
    ).trim();
    if (!commonDir) return null;
    // clones + `git worktree add`: common-dir is `<main root>/.git`; bare repos: the dir itself.
    return basename(commonDir) === ".git" ? dirname(commonDir) : commonDir;
  } catch {
    return null;
  }
}

/** Worktree-aware repo name for DOCUMENT IDS (gitlog:<name>, commit context): all worktrees of a
 *  repo must produce the SAME name, or each worktree writes its own gitlog document into the
 *  shared bank (seen in the wild: gitlog:hindsight-wt7 next to gitlog:memory-poc). */
export function projectNameOf(directory: string): string {
  return gitProjectName(directory, true);
}

function gitProjectName(directory: string, resolveWorktrees: boolean): string {
  if (resolveWorktrees) {
    const root = getProjectRootFromGit(directory);
    if (root) return basename(root);
  }
  return directory ? basename(directory) : "unknown";
}

/** Longest-prefix match of `directory` against the map's absolute paths (exact or ancestor). */
function mapLookup(map: Record<string, string>, directory: string): string | undefined {
  const cwd = normalize(directory);
  let best: { len: number; bank: string } | undefined;
  for (const [dir, bank] of Object.entries(map)) {
    const expanded = dir === "~" || dir.startsWith("~/") ? join(homedir(), dir.slice(1)) : dir;
    const p = normalize(expanded).replace(new RegExp(`\\${sep}+$`), "");
    if (cwd === p || cwd.startsWith(p + sep)) {
      if (!best || p.length > best.len) best = { len: p.length, bank };
    }
  }
  return best?.bank;
}

/** Derive the bank id for a working directory (see module doc for the resolution order). */
export function deriveBankId(config: BankConfig, directory: string, harness = "coding"): string {
  const mapped =
    directory && config.mapPathToBank ? mapLookup(config.mapPathToBank, directory) : undefined;
  if (mapped) return mapped;

  // dynamic by default — but an explicit bankId (without dynamicBankId: true) means "static".
  const dynamic = config.dynamicBankId ?? !config.bankId;
  if (!dynamic) return config.bankId || DEFAULT_BANK_NAME;

  const resolvers: Record<string, () => string> = {
    harness: () => harness,
    project: () => (directory ? basename(directory) : "unknown"),
    gitProject: () => gitProjectName(directory, config.resolveWorktrees ?? true),
    channel: () => process.env.HINDSIGHT_CHANNEL_ID || "default",
    user: () => process.env.HINDSIGHT_USER_ID || "anonymous",
  };
  return (config.bankIdTemplate || DEFAULT_TEMPLATE).replace(PLACEHOLDER, (_, name: string) => {
    const r = resolvers[name];
    if (!r) {
      console.error(
        `hindsight: unknown bankIdTemplate placeholder "{${name}}" — valid: ` +
          Object.keys(resolvers)
            .sort()
            .map((k) => `{${k}}`)
            .join(", ")
      );
      return "unknown";
    }
    return r();
  });
}
