from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from .models import FRONTMATTER_RE, Skill, SkillError, slugify

# Target tool -> relative install path pattern under a project root
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
    "zed": {
        "label": "Zed",
        "path": ".rules/{name}.md",
        "kind": "agents_md",
    },
    "jetbrains": {
        "label": "JetBrains AI",
        "path": ".aiassistant/rules/{name}.md",
        "kind": "agents_md",
    },
    "opencode": {
        "label": "OpenCode",
        "path": ".opencode/skills/{name}/SKILL.md",
        "kind": "skill_md",
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

    # Prefer YAML dump for safe escaping
    fm: Dict = {"description": skill.description, "alwaysApply": bool(always)}
    if globs:
        fm["globs"] = globs
    fm_txt = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=1000).strip()
    return (
        f"---\n{fm_txt}\n---\n\n"
        f"# {skill.name}\n\n"
        f"{skill.body.strip()}\n"
    )


def _to_agents_md(skill: Skill) -> str:
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
            new_text = (
                "# AGENTS.md\n\n"
                "Project agent instructions managed partly by SkillPort.\n\n"
                f"{section}"
            )
        dest.write_text(new_text, encoding="utf-8")
        return dest

    if dest.exists() and not force:
        raise FileExistsError(f"already exists: {dest} (use --force to overwrite)")

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    return dest


def remove_skill(project_root: Path, tool: str, skill_name: str) -> Optional[Path]:
    """Remove an installed skill projection. Returns path if something was removed."""
    tool = tool.lower().strip()
    if tool == "agents":
        dest = install_path(project_root, tool, skill_name)
        if not dest.exists():
            return None
        text = dest.read_text(encoding="utf-8")
        marker_start = f"<!-- skillport:{skill_name}:start -->"
        marker_end = f"<!-- skillport:{skill_name}:end -->"
        if marker_start not in text or marker_end not in text:
            return None
        pre = text.split(marker_start)[0]
        post = text.split(marker_end, 1)[1]
        new_text = (pre.rstrip() + "\n" + post.lstrip("\n")).strip() + "\n"
        dest.write_text(new_text, encoding="utf-8")
        return dest

    dest = install_path(project_root, tool, skill_name)
    if not dest.exists():
        # skill_md may live in a directory
        if dest.name == "SKILL.md" and dest.parent.exists():
            # remove SKILL.md and empty parent if only that file
            dest.unlink()
            try:
                next(dest.parent.iterdir())
            except StopIteration:
                dest.parent.rmdir()
            return dest
        return None
    if dest.is_file():
        dest.unlink()
        if dest.name == "SKILL.md":
            parent = dest.parent
            try:
                if parent.exists() and not any(parent.iterdir()):
                    parent.rmdir()
            except OSError:
                pass
        return dest
    return None


def detect_format(path: Path) -> str:
    """Best-effort detect source format of a file/dir."""
    p = path
    if p.is_dir():
        if (p / "SKILL.md").exists():
            return "skill_md"
        return "unknown"
    name = p.name.lower()
    if name == "skill.md":
        return "skill_md"
    if name.endswith(".mdc") or ".cursor" in str(p).replace("\\", "/"):
        return "cursor_mdc"
    if name == "agents.md":
        return "agents_md"
    if name.endswith(".md"):
        text = p.read_text(encoding="utf-8", errors="replace")
        if FRONTMATTER_RE.match(text if text.endswith("\n") else text + "\n"):
            # could be skill or cursor
            if "alwaysApply:" in text or "always_apply:" in text or "globs:" in text:
                return "cursor_mdc"
            if re.search(r"^name:\s*", text, re.M) and re.search(r"^description:\s*", text, re.M):
                return "skill_md"
        return "agents_md"
    return "unknown"


def import_skill(path: Path, name_hint: Optional[str] = None) -> Skill:
    """Import any supported format into a canonical Skill."""
    path = path.expanduser().resolve()
    fmt = detect_format(path)
    if path.is_dir():
        return Skill.load(path)
    text = path.read_text(encoding="utf-8")
    if fmt == "skill_md":
        skill = Skill.from_skill_md(text, path=path)
        if not skill.name:
            skill.name = slugify(name_hint or path.parent.name or path.stem)
        return skill
    if fmt == "cursor_mdc":
        return from_cursor_mdc(text, name_hint=name_hint or path.stem, path=path)
    if fmt in {"agents_md", "unknown"}:
        return from_agents_md(text, name_hint=name_hint or path.stem, path=path)
    raise SkillError(f"cannot import format from {path}")


def from_cursor_mdc(text: str, name_hint: str = "imported-rule", path: Optional[Path] = None) -> Skill:
    raw = text if text.endswith("\n") else text + "\n"
    match = FRONTMATTER_RE.match(raw)
    body = text
    fm: Dict = {}
    if match:
        try:
            fm = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError as exc:
            raise SkillError(f"invalid Cursor frontmatter: {exc}") from exc
        if not isinstance(fm, dict):
            fm = {}
        body = match.group(2) or ""

    description = str(fm.get("description") or "").strip()
    # Strip leading H1 if it duplicates name
    body_stripped = body.strip()
    title = ""
    m = re.match(r"^#\s+(.+?)\s*\n", body_stripped)
    if m:
        title = m.group(1).strip()
        body_stripped = body_stripped[m.end() :].lstrip()
    # Prefer explicit H1 title (canonical skill name) over file stem hints
    name = slugify(title or name_hint or "imported-rule")
    if not description:
        description = f"Imported Cursor rule '{title}'. Use when the matching globs/context apply."
    meta: Dict = {"tags": ["imported", "cursor"], "source_format": "cursor_mdc"}
    if "globs" in fm:
        meta["globs"] = fm["globs"]
    if "alwaysApply" in fm:
        meta["alwaysApply"] = bool(fm["alwaysApply"])
    elif "always_apply" in fm:
        meta["alwaysApply"] = bool(fm["always_apply"])
    return Skill(
        name=name,
        description=description[:1024],
        body=body_stripped or "Imported rule body was empty.",
        path=path,
        license="MIT",
        metadata=meta,
    )


def from_agents_md(text: str, name_hint: str = "imported-rule", path: Optional[Path] = None) -> Skill:
    body = text.strip()
    title = ""
    description = ""
    m = re.match(r"^#\s+(.+?)\s*\n", body)
    if m:
        title = m.group(1).strip()
        body = body[m.end() :].lstrip()
    # blockquote description
    m2 = re.match(r"^>\s*(.+?)(?:\n\n|\n(?!>))", body, re.S)
    if m2:
        description = re.sub(r"\s+", " ", m2.group(1).replace("\n", " ")).strip()
        body = body[m2.end() :].lstrip()
    name = slugify(title or name_hint or "imported-rule")
    if not description:
        description = f"Imported markdown agent rule '{title}'. Use when relevant to the task."
    return Skill(
        name=name,
        description=description[:1024],
        body=body or "Imported rule body was empty.",
        path=path,
        license="MIT",
        metadata={"tags": ["imported"], "source_format": "agents_md"},
    )


def roundtrip_ok(skill: Skill, tool: str = "cursor") -> bool:
    """True if skill survives render→import with same name/description/body core."""
    rendered = render_for_tool(skill, tool)
    if tool == "cursor":
        back = from_cursor_mdc(rendered, name_hint=skill.name)
    elif TOOL_LAYOUTS[tool]["kind"] == "skill_md":
        back = Skill.from_skill_md(rendered)
    else:
        back = from_agents_md(rendered, name_hint=skill.name)
    return (
        back.name == skill.name
        and back.description.strip() == skill.description.strip()
        and back.body.strip() == skill.body.strip()
    )
