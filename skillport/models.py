from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.DOTALL)


class SkillError(ValueError):
    """Raised when a skill is invalid or cannot be loaded."""


@dataclass
class Skill:
    """Canonical representation of an Agent Skill (agentskills.io)."""

    name: str
    description: str
    body: str
    path: Optional[Path] = None
    license: Optional[str] = None
    compatibility: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    allowed_tools: Optional[str] = None
    extra_frontmatter: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.name:
            errors.append("name is required")
        elif len(self.name) > 64:
            errors.append("name must be <= 64 characters")
        elif not NAME_RE.match(self.name):
            errors.append(
                "name must be lowercase letters, numbers, hyphens only "
                "(no leading/trailing hyphen)"
            )
        if not self.description or not str(self.description).strip():
            errors.append("description is required")
        elif len(self.description) > 1024:
            errors.append("description must be <= 1024 characters")
        if self.compatibility and len(self.compatibility) > 500:
            errors.append("compatibility must be <= 500 characters")
        if not self.body or not self.body.strip():
            errors.append("SKILL.md body (instructions) must not be empty")
        return errors

    def to_frontmatter(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "name": self.name,
            "description": self.description,
        }
        if self.license:
            data["license"] = self.license
        if self.compatibility:
            data["compatibility"] = self.compatibility
        if self.metadata:
            data["metadata"] = self.metadata
        if self.allowed_tools:
            data["allowed-tools"] = self.allowed_tools
        data.update(self.extra_frontmatter)
        return data

    def to_skill_md(self) -> str:
        fm = yaml.safe_dump(
            self.to_frontmatter(),
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        ).strip()
        body = self.body.lstrip("\n").rstrip() + "\n"
        return f"---\n{fm}\n---\n\n{body}"

    @classmethod
    def from_skill_md(cls, text: str, path: Optional[Path] = None) -> "Skill":
        match = FRONTMATTER_RE.match(text.strip() + ("\n" if not text.endswith("\n") else ""))
        if not match:
            # allow missing trailing newline variants
            match = FRONTMATTER_RE.match(text)
        if not match:
            raise SkillError("SKILL.md must start with YAML frontmatter (--- ... ---)")

        raw_fm, body = match.group(1), match.group(2)
        try:
            fm = yaml.safe_load(raw_fm) or {}
        except yaml.YAMLError as exc:
            raise SkillError(f"invalid YAML frontmatter: {exc}") from exc
        if not isinstance(fm, dict):
            raise SkillError("frontmatter must be a YAML mapping")

        known = {
            "name",
            "description",
            "license",
            "compatibility",
            "metadata",
            "allowed-tools",
            "allowed_tools",
        }
        extra = {k: v for k, v in fm.items() if k not in known}
        allowed = fm.get("allowed-tools") or fm.get("allowed_tools")
        metadata = fm.get("metadata") or {}
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, dict):
            raise SkillError("metadata must be a mapping")

        name = str(fm.get("name") or "").strip()
        description = str(fm.get("description") or "").strip()
        return cls(
            name=name,
            description=description,
            body=body or "",
            path=path,
            license=fm.get("license"),
            compatibility=fm.get("compatibility"),
            metadata=metadata,
            allowed_tools=str(allowed) if allowed else None,
            extra_frontmatter=extra,
        )

    @classmethod
    def load(cls, path: Path) -> "Skill":
        skill_md = path / "SKILL.md" if path.is_dir() else path
        if not skill_md.exists():
            raise SkillError(f"SKILL.md not found at {skill_md}")
        text = skill_md.read_text(encoding="utf-8")
        skill = cls.from_skill_md(text, path=skill_md)
        if path.is_dir() and not skill.name:
            skill.name = path.name
        return skill


def find_skill_dirs(root: Path) -> List[Path]:
    """Find skill directories (contain SKILL.md) under root."""
    root = root.resolve()
    if (root / "SKILL.md").exists():
        return [root]
    found: List[Path] = []
    for p in sorted(root.rglob("SKILL.md")):
        # skip nested node_modules / venv noise
        parts = set(p.parts)
        if parts & {".git", "node_modules", ".venv", "venv", "__pycache__"}:
            continue
        found.append(p.parent)
    return found