"""The skills are the integration: in Grok Bot a plugin's hooks never run, only its skills.

These tests pin every Hindsight tool and parameter the skills tell a Bot to use
against the real MCP tool registry in hindsight-api-slim, so renaming a tool or a
parameter fails here instead of silently breaking every installed Bot.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

PLUGIN_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = PLUGIN_DIR / "skills"
MCP_TOOLS = PLUGIN_DIR.parent.parent / "hindsight-api-slim" / "hindsight_api" / "mcp_tools.py"

# Tool -> the parameters the skills tell the Bot to pass.
EXPECTED_CALLS: dict[str, set[str]] = {
    "list_banks": set(),
    "create_bank": {"bank_id", "name"},
    "recall": {"query", "bank_id"},
    "retain": {"content", "tags", "bank_id"},
    "reflect": {"query", "bank_id"},
    "list_mental_models": {"bank_id"},
    "get_mental_model": {"mental_model_id", "bank_id"},
    "create_mental_model": {"name", "source_query", "bank_id"},
}

# The root /mcp URL exposes these, so the skills must forbid them rather than use them.
FORBIDDEN = {"delete_bank", "clear_memories", "invalidate_memory", "delete_document", "delete_mental_model"}


class SkillFrontmatter(BaseModel):
    name: str
    description: str


@dataclass
class Skill:
    folder: str
    name: str
    description: str
    body: str


def _skills() -> list[Skill]:
    skills = []
    for path in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        text = path.read_text()
        match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
        assert match, f"{path} has no frontmatter"
        # Frontmatter here is flat `key: value` lines; parse it into a model so a missing field fails loudly.
        pairs = (line.split(": ", 1) for line in match.group(1).splitlines() if ": " in line)
        meta = SkillFrontmatter.model_validate(dict(pairs))
        skills.append(Skill(path.parent.name, meta.name, meta.description, match.group(2)))
    return skills


def _registry() -> dict[str, set[str]]:
    """Tool name -> parameters of its multi-bank variant (the one the root /mcp URL serves)."""
    tree = ast.parse(MCP_TOOLS.read_text())
    tools: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            params = {a.arg for a in node.args.args + node.args.kwonlyargs}
            # Each tool is defined once per bank mode; keep the variant that takes bank_id.
            if "bank_id" in params or node.name not in tools:
                tools[node.name] = params
    return tools


def test_every_skill_has_frontmatter_matching_its_folder() -> None:
    skills = _skills()
    assert len(skills) == 6
    for skill in skills:
        assert skill.name == skill.folder
        assert skill.description.strip()


def test_descriptions_say_when_to_fire() -> None:
    # Grok Bot picks a skill from its description alone, so each one must state its trigger.
    for skill in _skills():
        assert "Use " in skill.description and (" when " in skill.description or " at " in skill.description), (
            skill.folder
        )


def test_skills_only_reference_known_tools() -> None:
    known = set(EXPECTED_CALLS) | FORBIDDEN | _registry().keys()
    referenced: set[str] = set()
    for skill in _skills():
        referenced |= set(re.findall(r"`([a-z_]+)`", skill.body)) & known
    assert referenced - FORBIDDEN <= set(EXPECTED_CALLS), referenced - FORBIDDEN - set(EXPECTED_CALLS)


def test_expected_tools_and_parameters_exist_in_hindsight() -> None:
    registry = _registry()
    for tool, params in EXPECTED_CALLS.items():
        assert tool in registry, f"Hindsight has no MCP tool named {tool}"
        assert params <= registry[tool], f"{tool} lacks {params - registry[tool]}"
    for tool in FORBIDDEN:
        assert tool in registry, f"forbidden list names a tool that does not exist: {tool}"


def test_destructive_tools_appear_only_as_prohibitions() -> None:
    for skill in _skills():
        for line in skill.body.splitlines():
            if any(f"`{tool}`" in line for tool in FORBIDDEN):
                assert line.lstrip("- ").startswith("Never call"), f"{skill.folder}: {line}"


def test_skills_agree_on_bank_names() -> None:
    # The shared bank, the per-Bot or per-project placeholder, or a worked example of a slug
    # (lowercase, hyphens). Anything else means two skills disagree on where memory lives.
    # Cursor agents get per-project banks because the same plugin installs into Cursor
    # whenever a user adds it in Grok Bot, and a Cursor agent has no Bot name to use.
    allowed = re.compile(r"^(grok-bot::(shared|<bot-name>|[a-z0-9]+(-[a-z0-9]+)*)|cursor::<project-name>)$")
    for skill in _skills():
        for bank in re.findall(r"`((?:grok-bot|cursor)::[^`]+)`", skill.body):
            assert allowed.match(bank), f"{skill.folder}: {bank}"
