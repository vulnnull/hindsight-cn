import { readFileSync } from "node:fs";
import type { TransportTurn } from "./chat";
import { stripInjectedMemory } from "./transcript-util";

/** Normalize Copilot CLI's session-state `events.jsonl` user/assistant message records. */
export function readCopilotTranscript(path: string): TransportTurn[] {
  let raw: string;
  try {
    raw = readFileSync(path, "utf8");
  } catch {
    return [];
  }

  const turns: TransportTurn[] = [];
  for (const rawLine of raw.split("\n")) {
    try {
      const event = JSON.parse(rawLine) as {
        type?: string;
        timestamp?: string;
        data?: { content?: string };
      };
      const role =
        event.type === "user.message"
          ? "user"
          : event.type === "assistant.message"
            ? "assistant"
            : undefined;
      const content =
        typeof event.data?.content === "string"
          ? stripInjectedMemory(event.data.content).trim()
          : "";
      if (!role || !content) continue;
      turns.push({ role, content, ...(event.timestamp ? { timestamp: event.timestamp } : {}) });
    } catch {
      /* malformed events are ignored so agentStop remains fail-open */
    }
  }
  return turns;
}
