/** Shared transcript-rendering helpers used by both the Claude (transcript.ts) and Codex
 *  (transcript-codex.ts) session readers. */

/** Cap on any single rendered tool input or tool result (mirrors v1's 2000-char cap): small
 *  edits/commands are captured verbatim while a giant Write/output is bounded. */
export const TOOL_TEXT_CAP = 2000;

/** Injected context — stripped from retained text so a write-back never re-ingests its own
 *  injected memory (a retain→reflect feedback loop). Covers every block the hooks inject, PLUS
 *  the host's own hook-transport wrappers (codex surfaces hook stdout/errors as `<hook_prompt>`
 *  user messages — transport noise, not the user's work). Tag-structural, not content-guessing. */
const MEMORY_TAG_RE =
  /<(hook_prompt|hindsight_memory|hindsight_memories|hindsight_bank|relevant_memories|user_feedback|hindsight_knowledge|hindsight_knowledge_refresh)\b[\s\S]*?<\/\1>/g;

export function stripInjectedMemory(s: string): string {
  return s.replace(MEMORY_TAG_RE, "");
}

export function truncate(s: string, max = TOOL_TEXT_CAP): string {
  return s.length > max ? `${s.slice(0, max)}… (truncated)` : s;
}

/** Keys tried, in order, to find a tool call's primary target for the compact action line. */
const TARGET_KEYS = [
  "file_path",
  "path",
  "notebook_path",
  "command",
  "pattern",
  "query",
  "url",
  "name",
  "id",
] as const;

const ACTION_TARGET_CAP = 100;

/**
 * Compact one tool call into an action line: the tool name plus its primary target — a file path,
 * command, pattern, … — with NO full arguments and NO output (e.g. `Edit boltons/strutils.py`).
 * Retaining raw args/outputs buries the session's decisions in mechanical noise; the extractor only
 * needs WHAT was touched.
 */
export function actionLine(tool: string, input: unknown): string {
  let target = "";
  if (input && typeof input === "object") {
    const rec = input as Record<string, unknown>;
    for (const k of TARGET_KEYS) {
      const v = rec[k];
      if (typeof v === "string" && v.trim()) {
        target = v.trim().split("\n")[0];
        break;
      }
    }
  } else if (typeof input === "string") {
    target = input.trim().split("\n")[0];
  }
  if (target.length > ACTION_TARGET_CAP) target = `${target.slice(0, ACTION_TARGET_CAP)}…`;
  return target ? `${tool} ${target}` : tool;
}
