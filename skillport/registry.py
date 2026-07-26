from __future__ import annotations

import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.parse import urlparse

import httpx

from .models import Skill, SkillError, find_skill_dirs

# Built-in starter catalog (ships with the CLI). Users can also point at any git URL.
BUILTIN_CATALOG = [
    {
        "name": "pr-review",
        "description": "Structured pull-request review: correctness, security, tests, and clarity.",
        "tags": ["git", "review", "quality"],
        "path": "skills/pr-review",
    },
    {
        "name": "commit",
        "description": "Write conventional, high-signal commit messages from a diff.",
        "tags": ["git", "commit"],
        "path": "skills/commit",
    },
    {
        "name": "security-audit",
        "description": "Threat-model and audit code for common security issues before merge.",
        "tags": ["security", "audit"],
        "path": "skills/security-audit",
    },
    {
        "name": "docs-writer",
        "description": "Turn messy notes into crisp README/docs with examples and warnings.",
        "tags": ["docs", "writing"],
        "path": "skills/docs-writer",
    },
]


@dataclass
class CatalogEntry:
    name: str
    description: str
    tags: List[str]
    source: str  # builtin path, local path, or git URL
    kind: str  # builtin | local | remote


def package_skills_root() -> Path:
    """Return the skills/ directory next to the installed package or repo root."""
    here = Path(__file__).resolve().parent
    # dev: repo_root/skills
    repo_skills = here.parent / "skills"
    if repo_skills.exists():
        return repo_skills
    # installed wheel optional data
    return here / "skills"


def builtin_entries() -> List[CatalogEntry]:
    root = package_skills_root()
    entries: List[CatalogEntry] = []
    for item in BUILTIN_CATALOG:
        entries.append(
            CatalogEntry(
                name=item["name"],
                description=item["description"],
                tags=list(item.get("tags") or []),
                source=str(root / Path(item["path"]).name),
                kind="builtin",
            )
        )
    # Also discover any extra local skills shipped alongside
    if root.exists():
        known = {e.name for e in entries}
        for d in find_skill_dirs(root):
            if d.name in known:
                continue
            try:
                sk = Skill.load(d)
            except SkillError:
                continue
            entries.append(
                CatalogEntry(
                    name=sk.name or d.name,
                    description=sk.description,
                    tags=list((sk.metadata or {}).get("tags") or []),
                    source=str(d),
                    kind="builtin",
                )
            )
    return entries


def search_catalog(query: str = "", tags: Optional[Iterable[str]] = None) -> List[CatalogEntry]:
    q = (query or "").strip().lower()
    tag_set = {t.lower() for t in (tags or []) if t}
    results: List[CatalogEntry] = []
    for entry in builtin_entries():
        hay = f"{entry.name} {entry.description} {' '.join(entry.tags)}".lower()
        if q and q not in hay:
            continue
        if tag_set and not tag_set.intersection({t.lower() for t in entry.tags}):
            continue
        results.append(entry)
    return results


def resolve_source(source: str) -> Path:
    """
    Resolve a skill source to a local directory containing SKILL.md.
    Supports:
      - local path
      - builtin name
      - git URL (https://github.com/org/repo[.git][/tree/branch/path])
      - owner/repo or owner/repo/path shorthand for GitHub
    """
    source = source.strip()
    p = Path(source).expanduser()
    if p.exists():
        if p.is_file() and p.name == "SKILL.md":
            return p.parent
        if p.is_dir():
            return p
        raise SkillError(f"path exists but is not a skill directory: {p}")

    # builtin name
    for entry in builtin_entries():
        if entry.name == source:
            return Path(entry.source)

    # GitHub shorthand: owner/repo or owner/repo/sub/path
    if re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(/[\w./-]+)?$", source) and not source.startswith("."):
        parts = source.split("/")
        owner, repo = parts[0], parts[1]
        sub = "/".join(parts[2:]) if len(parts) > 2 else ""
        return _clone_github(owner, repo, subpath=sub)

    if source.startswith("http://") or source.startswith("https://") or source.startswith("git@"):
        return _clone_url(source)

    raise SkillError(
        f"cannot resolve skill source '{source}'. "
        "Use a local path, builtin name, owner/repo, or git URL."
    )


def _clone_github(owner: str, repo: str, subpath: str = "", branch: str = "") -> Path:
    if repo.endswith(".git"):
        repo = repo[:-4]
    url = f"https://github.com/{owner}/{repo}.git"
    return _clone_url(url, subpath=subpath, branch=branch)


def _clone_url(url: str, subpath: str = "", branch: str = "") -> Path:
    """Shallow clone into a temp dir and return skill path."""
    # Support GitHub tree URLs
    # https://github.com/org/repo/tree/main/skills/foo
    m = re.match(
        r"https?://github\.com/([^/]+)/([^/]+)/tree/([^/]+)(?:/(.*))?$",
        url.rstrip("/"),
    )
    if m:
        owner, repo, branch, sub = m.group(1), m.group(2), m.group(3), m.group(4) or ""
        url = f"https://github.com/{owner}/{repo}.git"
        subpath = sub or subpath

    tmp = Path(tempfile.mkdtemp(prefix="skillport-"))
    dest = tmp / "repo"
    import subprocess

    cmd = ["git", "clone", "--depth", "1"]
    if branch:
        cmd += ["--branch", branch]
    cmd += [url, str(dest)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        shutil.rmtree(tmp, ignore_errors=True)
        raise SkillError("git is required to install from remote URLs") from exc
    except subprocess.CalledProcessError as exc:
        shutil.rmtree(tmp, ignore_errors=True)
        raise SkillError(f"git clone failed: {exc.stderr or exc.stdout}") from exc

    root = dest / subpath if subpath else dest
    if not root.exists():
        shutil.rmtree(tmp, ignore_errors=True)
        raise SkillError(f"path '{subpath}' not found in cloned repo")
    return root


def load_skills_from_source(source: str) -> List[Skill]:
    root = resolve_source(source)
    dirs = find_skill_dirs(root)
    if not dirs:
        # maybe single skill file
        if (root / "SKILL.md").exists():
            dirs = [root]
        else:
            raise SkillError(f"no SKILL.md found under {root}")
    skills: List[Skill] = []
    for d in dirs:
        skills.append(Skill.load(d))
    return skills


def fetch_remote_catalog(url: str, timeout: float = 15.0) -> List[CatalogEntry]:
    """Optional: load a JSON catalog from a URL."""
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        data = resp.json()
    items = data if isinstance(data, list) else data.get("skills", [])
    out: List[CatalogEntry] = []
    for item in items:
        out.append(
            CatalogEntry(
                name=item["name"],
                description=item.get("description", ""),
                tags=list(item.get("tags") or []),
                source=item.get("source") or item.get("url") or "",
                kind="remote",
            )
        )
    return out


def export_lockfile(installed: List[dict], path: Path) -> None:
    path.write_text(json.dumps({"version": 1, "skills": installed}, indent=2) + "\n", encoding="utf-8")


def read_lockfile(path: Path) -> List[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("skills") or [])