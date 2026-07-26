from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from .models import Skill

# Target tool -> relative install path pattern under a project root
# {name} is replaced with the skill name.
TOOL_LAYOUTS: Dict[str, Dict[str, str]] = {
    "claude": {
        "label": "Claude Code",
        "path": ".claude/skills/{name}/SKILL.md",
        "kind": "skill_md",
    },
    "cursor": {
        "label": "Cursor",
        "path": ".cursor/rules/{name}.mdc",
        "kind": "cursor_mdc",
    },
    "codex": {
        "label": "OpenAI Codex",
        "path": ".codex/skills/{name}/SKILL.md",
        "kind": "skill_md",
    },
    "copilot": {
        "label": "GitHub Copilot",
        "path": ".github/copilot-instructions/{name}.md",
        "kind": "agents_md",
    },
    "windsurf": {
        "label": "Windsurf",
        "path": ".windsurf/rules/{name}.md",
        "kind": "agents_md",
    },
    "agents": {
        "label": "AGENTS.md (universal)",
        "path": "AGENTS.md",
        "kind": "agents_append",
    },
    "continue": {
        "label": "Continue.dev",
        "path": ".continue/rules/{name}.md",
        "kind": "agents_md",
    },
    "aider": {
        "label": "Aider",
        "path": ".aider/skills/{name}.md",
        "kind": "agents_md",
    },
    "cline": {
        "label": "Cline",
        "path": ".clinerules/{name}.md",
        "kind": "agents_md",
    },
    "generic": {
        "label": "Generic SKILL.md",
        "path": "skills/{name}/SKILL.md",
        "kind": "skill_md",
    },
}


def list_tools() -> List[Tuple[str, str]]:
    return [(k, v["label"]) for k, v in TOOL_LAYOUTS.items()]


def render_for_tool(skill: Skill, tool: str) -> str:
    tool = tool.lower().strip()
    if tool not in TOOL_LAYOUTS:
        known = ", ".join(sorted(TOOL_LAYOUTS))
        raise ValueError(f"unknown tool '{tool}'. Choose one of: {known}")

    kind = TOOL_LAYOUTS[tool]["kind"]
    if kind == "skill_md":
        return skill.to_skill_md()
    if kind == "cursor_mdc":
        return _to_cursor_mdc(skill)
    if kind == "agents_md":
        return _to_agents_md(skill)
    if kind == "agents_append":
        return _to_agents_section(skill)
    raise ValueError(f"unsupported kind: {kind}")


def _to_cursor_mdc(skill: Skill) -> str:
    """Convert Agent Skill -> Cursor .mdc rule."""
    globs = ""
    meta = skill.metadata or {}
    if isinstance(meta.get("globs"), list):
        globs = ", ".join(str(g) for g in meta["globs"])
    elif isinstance(meta.get("globs"), str):
        globs = meta["globs"]
    always = meta.get("alwaysApply", False)
    always_s = "true" if always else "false"

    lines = [
        "---",
        f"description: {skill.description}",
    ]
    if globs:
        lines.append(f"globs: {globs}")
    lines.append(f"alwaysApply: {always_s}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {skill.name}")
    lines.append("")
    lines.append(skill.body.strip())
    lines.append("")
    return "\n".join(lines)


def _to_agents_md(skill: Skill) -> str:
    """Plain markdown instructions for tools that read freeform rules."""
    parts = [
        f"# {skill.name}",
        "",
        f"> {skill.description}",
        "",
        skill.body.strip(),
        "",
    ]
    return "\n".join(parts)


def _to_agents_section(skill: Skill) -> str:
    """Section suitable for appending into a root AGENTS.md."""
    return (
        f"\n## Skill: {skill.name}\n\n"
        f"{skill.description}\n\n"
        f"{skill.body.strip()}\n"
    )


def install_path(project_root: Path, tool: str, skill_name: str) -> Path:
    tool = tool.lower().strip()
    if tool not in TOOL_LAYOUTS:
        raise ValueError(f"unknown tool: {tool}")
    rel = TOOL_LAYOUTS[tool]["path"].format(name=skill_name)
    return project_root / rel


def write_skill(project_root: Path, tool: str, skill: Skill, force: bool = False) -> Path:
    dest = install_path(project_root, tool, skill.name)
    content = render_for_tool(skill, tool)

    if tool == "agents":
        # Append/update section in AGENTS.md
        dest.parent.mkdir(parents=True, exist_ok=True)
        marker_start = f"<!-- skillport:{skill.name}:start -->"
        marker_end = f"<!-- skillport:{skill.name}:end -->"
        section = f"{marker_start}\n{_to_agents_section(skill).strip()}\n{marker_end}\n"
        if dest.exists():
            existing = dest.read_text(encoding="utf-8")
            if marker_start in existing and marker_end in existing:
                pre = existing.split(marker_start)[0]
                post = existing.split(marker_end, 1)[1]
                new_text = pre + section + post.lstrip("\n")
            else:
                new_text = existing.rstrip() + "\n\n" + section
        else:
            new_text = f"# AGENTS.md\n\nProject agent instructions managed partly by SkillPort.\n\n{section}"
        dest.write_text(new_text, encoding="utf-8")
        return dest

    if dest.exists() and not force:
        raise FileExistsError(f"already exists: {dest} (use --force to overwrite)")

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    return dest