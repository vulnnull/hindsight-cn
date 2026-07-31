import { execFileSync } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";
import type { TransportTurn } from "./chat";
import { stripInjectedMemory } from "./transcript-util";

const sessionDb = join(homedir(), ".local", "share", "devin", "cli", "sessions.db");

interface DevinMessageNode {
  node_id: number;
  chat_message: string;
}

/** Devin writes progressive assistant updates with a shared message id; retain their final value. */
export function parseDevinMessages(nodes: DevinMessageNode[]): TransportTurn[] {
  const messages = new Map<
    string,
    { index: number; role: "user" | "assistant"; content: string }
  >();
  for (const node of nodes) {
    try {
      const message = JSON.parse(node.chat_message) as {
        message_id?: string;
        role?: string;
        content?: string;
      };
      if ((message.role !== "user" && message.role !== "assistant") || !message.content?.trim())
        continue;
      const content = stripInjectedMemory(message.content).trim();
      if (!content) continue;
      const id = message.message_id || `node:${node.node_id}`;
      messages.set(id, {
        index: messages.get(id)?.index ?? node.node_id,
        role: message.role,
        content,
      });
    } catch {
      /* tool frames and incomplete rows are not conversational turns */
    }
  }
  return [...messages.values()]
    .sort((a, b) => a.index - b.index)
    .map(({ role, content }) => ({ role, content }));
}

/** Devin hooks provide no transcript path, but the local CLI persists its full conversation in
 * sessions.db. Use sqlite3 as a read-only bridge to avoid a native Node dependency in hook bundles. */
export function readDevinTranscript(sessionId: string | undefined): TransportTurn[] {
  if (!sessionId) return [];
  try {
    const quotedId = sessionId.replace(/'/g, "''");
    const raw = execFileSync(
      "sqlite3",
      [
        "-json",
        sessionDb,
        `SELECT node_id, chat_message FROM message_nodes WHERE session_id = '${quotedId}' ORDER BY node_id`,
      ],
      { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"], timeout: 2000 }
    );
    return parseDevinMessages(JSON.parse(raw) as DevinMessageNode[]);
  } catch {
    return [];
  }
}
