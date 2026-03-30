"""Content processing utilities for Codex.

Adapts Openclaw/Claude Code content processing for Codex's transcript format.

Codex transcript format (JSONL):
  {"session_id": "...", "ts": 1234567890, "msg": {"type": "user_message", "message": "..."}}

EventMsg types (from codex-rs/protocol/src/protocol.rs, serde snake_case):
  - user_message   → role: user
  - agent_message  → role: assistant
  - task_started, task_complete, exec, etc. → skipped
"""

import json
import os
import re
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Memory tag stripping (anti-feedback-loop)
# ---------------------------------------------------------------------------


def strip_memory_tags(content: str) -> str:
    """Remove <hindsight_memories> and <relevant_memories> blocks.

    Prevents retain feedback loop — these were injected during recall and
    should not be re-stored.
    """
    content = re.sub(r"<hindsight_memories>[\s\S]*?</hindsight_memories>", "", content)
    content = re.sub(r"<relevant_memories>[\s\S]*?</relevant_memories>", "", content)
    return content


# ---------------------------------------------------------------------------
# Transcript reading
# ---------------------------------------------------------------------------


def read_transcript(transcript_path: str) -> list:
    """Read a Codex JSONL transcript and return list of {role, content} dicts.

    Codex disk format (rollout-*.jsonl):
      User:      {"type":"response_item","payload":{"type":"message","role":"user",
                   "content":[{"type":"input_text","text":"..."}]}}
      Assistant: {"type":"response_item","payload":{"type":"message","role":"assistant",
                   "content":[{"type":"output_text","text":"..."}],"phase":"final_answer"}}

    Flat format for testing:
      {"role": "user", "content": "..."}
    """
    if not transcript_path or not os.path.isfile(transcript_path):
        return []
    messages = []
    try:
        with open(transcript_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    # Codex response_item format
                    if entry.get("type") == "response_item":
                        payload = entry.get("payload", {})
                        if payload.get("type") == "message":
                            role = payload.get("role", "")
                            if role not in ("user", "assistant"):
                                continue
                            # Only include final_answer for assistant (not reasoning/intermediary)
                            if role == "assistant" and payload.get("phase") != "final_answer":
                                continue
                            content_blocks = payload.get("content", [])
                            text_parts = []
                            for block in content_blocks:
                                if isinstance(block, dict) and block.get("type") in ("input_text", "output_text"):
                                    t = block.get("text", "").strip()
                                    if t:
                                        text_parts.append(t)
                            text = "\n".join(text_parts).strip()
                            if text:
                                messages.append({"role": role, "content": text})
                    # Flat format (testing / future compatibility)
                    elif "role" in entry and "content" in entry:
                        messages.append({"role": entry["role"], "content": entry["content"]})
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return messages


# ---------------------------------------------------------------------------
# Recall: query composition and truncation
# ---------------------------------------------------------------------------


def compose_recall_query(
    latest_query: str,
    messages: list,
    recall_context_turns: int,
    recall_roles: list = None,
) -> str:
    """Compose a multi-turn recall query from conversation history.

    When recallContextTurns > 1, includes prior context above the latest
    user query. Format:

        Prior context:

        user: ...
        assistant: ...

        <latest query>
    """
    latest = latest_query.strip()
    if recall_context_turns <= 1 or not isinstance(messages, list) or not messages:
        return latest

    allowed_roles = set(recall_roles or ["user", "assistant"])
    contextual_messages = slice_last_turns_by_user_boundary(messages, recall_context_turns)

    context_lines = []
    for msg in contextual_messages:
        role = msg.get("role")
        if role not in allowed_roles:
            continue

        content = msg.get("content", "")
        if not isinstance(content, str):
            content = str(content)
        content = strip_memory_tags(content).strip()
        if not content:
            continue

        if role == "user" and content == latest:
            continue

        context_lines.append(f"{role}: {content}")

    if not context_lines:
        return latest

    return "\n\n".join(
        [
            "Prior context:",
            "\n".join(context_lines),
            latest,
        ]
    )


def truncate_recall_query(query: str, latest_query: str, max_chars: int) -> str:
    """Truncate a composed recall query to max_chars.

    Preserves the latest user message. Drops oldest context lines first.
    """
    if max_chars <= 0:
        return query

    latest = latest_query.strip()
    if len(query) <= max_chars:
        return query

    latest_only = latest[:max_chars] if len(latest) > max_chars else latest

    if "Prior context:" not in query:
        return latest_only

    context_marker = "Prior context:\n\n"
    marker_index = query.find(context_marker)
    if marker_index == -1:
        return latest_only

    suffix_marker = "\n\n" + latest
    suffix_index = query.rfind(suffix_marker)
    if suffix_index == -1:
        return latest_only

    suffix = query[suffix_index:]
    if len(suffix) >= max_chars:
        return latest_only

    context_body = query[marker_index + len(context_marker) : suffix_index]
    context_lines = [line for line in context_body.split("\n") if line]

    kept = []
    for i in range(len(context_lines) - 1, -1, -1):
        kept.insert(0, context_lines[i])
        candidate = f"{context_marker}{chr(10).join(kept)}{suffix}"
        if len(candidate) > max_chars:
            kept.pop(0)
            break

    if kept:
        return f"{context_marker}{chr(10).join(kept)}{suffix}"
    return latest_only


# ---------------------------------------------------------------------------
# Turn slicing
# ---------------------------------------------------------------------------


def slice_last_turns_by_user_boundary(messages: list, turns: int) -> list:
    """Slice messages to the last N turns, where a turn starts at a user message."""
    if not isinstance(messages, list) or not messages or turns <= 0:
        return []

    user_turns_seen = 0
    start_index = -1

    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "user":
            user_turns_seen += 1
            if user_turns_seen >= turns:
                start_index = i
                break

    if start_index == -1:
        return list(messages)

    return messages[start_index:]


# ---------------------------------------------------------------------------
# Memory formatting (recall results → context string)
# ---------------------------------------------------------------------------


def format_memories(results: list) -> str:
    """Format recall results into human-readable text."""
    if not results:
        return ""
    lines = []
    for r in results:
        text = r.get("text", "")
        mem_type = r.get("type", "")
        mentioned_at = r.get("mentioned_at", "")
        type_str = f" [{mem_type}]" if mem_type else ""
        date_str = f" ({mentioned_at})" if mentioned_at else ""
        lines.append(f"- {text}{type_str}{date_str}")
    return "\n\n".join(lines)


def format_current_time() -> str:
    """Format current UTC time for recall context."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%d %H:%M")


# ---------------------------------------------------------------------------
# Retention transcript formatting
# ---------------------------------------------------------------------------


def prepare_retention_transcript(
    messages: list,
    retain_roles: list = None,
    retain_full_window: bool = False,
) -> tuple:
    """Format messages into a retention transcript.

    Outputs plain text with [role: ...]...[role:end] markers.
    Codex doesn't have tool calls to retain (it's a coding agent with
    shell/patch commands, not MCP tools), so we use the text format only.

    Args:
        messages: List of {role, content} dicts.
        retain_roles: Roles to include (default: ['user', 'assistant']).
        retain_full_window: If True, retain all messages. If False, retain
            only the last turn (last user msg + responses).

    Returns:
        (transcript_text, message_count) or (None, 0) if nothing to retain.
    """
    if not messages:
        return None, 0

    if retain_full_window:
        target_messages = messages
    else:
        last_user_idx = -1
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "user":
                last_user_idx = i
                break
        if last_user_idx == -1:
            return None, 0
        target_messages = messages[last_user_idx:]

    allowed_roles = set(retain_roles or ["user", "assistant"])
    parts = []

    for msg in target_messages:
        role = msg.get("role", "unknown")
        if role not in allowed_roles:
            continue

        content = msg.get("content", "")
        if not isinstance(content, str):
            content = str(content)
        content = strip_memory_tags(content).strip()

        if not content:
            continue

        parts.append(f"[role: {role}]\n{content}\n[{role}:end]")

    if not parts:
        return None, 0

    transcript = "\n\n".join(parts)
    if len(transcript.strip()) < 10:
        return None, 0

    return transcript, len(parts)
