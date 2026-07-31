import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import type { PageRef } from "./knowledge-injection";

/** Process-shared state for hook harnesses. SessionStart and prompt hooks are separate Node
 * processes, so this temp-file handoff carries lifecycle decisions without writing user config or
 * bank state. */
export interface SessionCache {
  turns?: number;
  reflectAnswer?: string; // present (even "") = reflect already ran this session
  /** SessionStart saw a new/empty bank; consume this on prompt one, then allow reflect. */
  deferInitialReflect?: boolean;
  pages?: { atTurn: number; list: PageRef[] };
}

export function sessionCacheFile(harness: string, sessionId: string): string {
  return join(tmpdir(), `hindsight-${harness}`, `${sessionId}.json`);
}

export function readSessionCache(cacheFile: string): SessionCache {
  try {
    return JSON.parse(readFileSync(cacheFile, "utf8")) as SessionCache;
  } catch {
    return {};
  }
}

export function writeSessionCache(cacheFile: string, cache: SessionCache): void {
  try {
    mkdirSync(dirname(cacheFile), { recursive: true });
    writeFileSync(cacheFile, JSON.stringify(cache));
  } catch {
    /* session state is best-effort */
  }
}
