from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

    def clone(self, **kwargs: Any) -> "Skill":
        return replace(self, **kwargs)

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
        if "<" in self.description or ">" in self.description:
            # soft: agentskills discourages angle brackets in description
            pass
        return errors

    def warnings(self) -> List[str]:
        warns: List[str] = []
        if self.description and len(self.description) < 40:
            warns.append("description is short; add when-to-use keywords for better routing")
        if self.body and len(self.body.strip()) < 120:
            warns.append("body is very short; add steps/examples for reliability")
        if not self.metadata.get("tags"):
            warns.append("metadata.tags missing — harder to search in catalogs")
        lower = (self.body or "").lower()
        if "todo" in lower or "tbd" in lower:
            warns.append("body still contains TODO/TBD placeholders")
        if self.name and self.name in {"skill", "test", "demo", "tmp", "temp"}:
            warns.append(f"name '{self.name}' looks generic")
        return warns

    def validate_report(self) -> Tuple[List[str], List[str]]:
        return self.validate(), self.warnings()

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
            width=1000,
        ).strip()
        body = self.body.lstrip("\n").rstrip() + "\n"
        return f"---\n{fm}\n---\n\n{body}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "license": self.license,
            "compatibility": self.compatibility,
            "metadata": self.metadata,
            "allowed_tools": self.allowed_tools,
            "body": self.body,
            "path": str(self.path) if self.path else None,
        }

    @classmethod
    def from_skill_md(cls, text: str, path: Optional[Path] = None) -> "Skill":
        raw = text if text.endswith("\n") else text + "\n"
        match = FRONTMATTER_RE.match(raw)
        if not match:
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


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    value = re.sub(r"-{2,}", "-", value)
    return value[:64] or "skill"


def find_skill_dirs(root: Path) -> List[Path]:
    """Find skill directories (contain SKILL.md) under root."""
    root = root.resolve()
    if root.is_file() and root.name == "SKILL.md":
        return [root.parent]
    if (root / "SKILL.md").exists():
        return [root]
    found: List[Path] = []
    for p in sorted(root.rglob("SKILL.md")):
        parts = set(p.parts)
        if parts & {".git", "node_modules", ".venv", "venv", "__pycache__", ".tox"}:
            continue
        found.append(p.parent)
    return found
