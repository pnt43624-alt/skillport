from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import httpx

from .models import Skill, SkillError, find_skill_dirs

# Built-in starter catalog — keep in sync with skills/ folders
BUILTIN_CATALOG = [
    {"name": "pr-review", "description": "Structured pull-request review: correctness, security, tests, and clarity.", "tags": ["git", "review", "quality"], "path": "skills/pr-review"},
    {"name": "commit", "description": "Write conventional, high-signal commit messages from a diff.", "tags": ["git", "commit"], "path": "skills/commit"},
    {"name": "security-audit", "description": "Threat-model and audit code for common security issues before merge.", "tags": ["security", "audit"], "path": "skills/security-audit"},
    {"name": "docs-writer", "description": "Turn messy notes into crisp README/docs with examples and warnings.", "tags": ["docs", "writing"], "path": "skills/docs-writer"},
    {"name": "test-writer", "description": "Design and write high-value unit/integration tests from code or requirements.", "tags": ["testing", "quality"], "path": "skills/test-writer"},
    {"name": "refactor", "description": "Safe, incremental refactors that improve design without changing behavior.", "tags": ["refactor", "quality"], "path": "skills/refactor"},
    {"name": "debug", "description": "Systematic debugging: reproduce, isolate, hypothesize, fix, verify.", "tags": ["debug", "quality"], "path": "skills/debug"},
    {"name": "api-design", "description": "Design clean REST/GraphQL APIs with consistent errors and versioning.", "tags": ["api", "design"], "path": "skills/api-design"},
    {"name": "release-notes", "description": "Draft user-facing release notes from commits and PR titles.", "tags": ["release", "docs", "git"], "path": "skills/release-notes"},
    {"name": "changelog", "description": "Maintain Keep-a-Changelog style CHANGELOG entries from git history.", "tags": ["release", "docs", "git"], "path": "skills/changelog"},
    {"name": "code-explain", "description": "Explain complex code paths in plain language with diagrams when useful.", "tags": ["docs", "learning"], "path": "skills/code-explain"},
    {"name": "performance", "description": "Profile and optimize hot paths with measurements, not guesses.", "tags": ["performance", "quality"], "path": "skills/performance"},
    {"name": "dependency-audit", "description": "Review dependencies for risk, bloat, license, and upgrade strategy.", "tags": ["security", "deps"], "path": "skills/dependency-audit"},
    {"name": "incident-response", "description": "Run an engineering incident: triage, mitigate, communicate, postmortem.", "tags": ["ops", "incident"], "path": "skills/incident-response"},
    {"name": "sql-review", "description": "Review SQL for correctness, indexes, injection, and plan hazards.", "tags": ["sql", "data", "review"], "path": "skills/sql-review"},
    {"name": "prompt-engineer", "description": "Craft robust system/user prompts and evals for LLM features.", "tags": ["ai", "prompts"], "path": "skills/prompt-engineer"},
]

BUILTIN_PACKS: Dict[str, Dict] = {
    "essentials": {
        "description": "Daily driver skills for most engineering repos",
        "skills": ["pr-review", "commit", "test-writer", "debug", "docs-writer"],
    },
    "security": {
        "description": "Security-focused review pack",
        "skills": ["security-audit", "dependency-audit", "sql-review"],
    },
    "shipping": {
        "description": "Ship features cleanly",
        "skills": ["pr-review", "test-writer", "release-notes", "changelog", "docs-writer"],
    },
    "quality": {
        "description": "Deep quality and design",
        "skills": ["refactor", "performance", "api-design", "code-explain", "test-writer"],
    },
    "ops": {
        "description": "Incidents and production readiness",
        "skills": ["incident-response", "performance", "security-audit"],
    },
    "all": {
        "description": "Every built-in skill",
        "skills": [e["name"] for e in BUILTIN_CATALOG],
    },
}


@dataclass
class CatalogEntry:
    name: str
    description: str
    tags: List[str]
    source: str
    kind: str  # builtin | local | remote | pack
    version: Optional[str] = None
    homepage: Optional[str] = None
    extra: Dict = field(default_factory=dict)


def package_skills_root() -> Path:
    here = Path(__file__).resolve().parent
    repo_skills = here.parent / "skills"
    if repo_skills.exists():
        return repo_skills
    return here / "skills"


def package_registry_path() -> Path:
    here = Path(__file__).resolve().parent
    repo_reg = here.parent / "registry" / "index.json"
    if repo_reg.exists():
        return repo_reg
    return here / "registry" / "index.json"


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


def pack_entries() -> List[CatalogEntry]:
    out: List[CatalogEntry] = []
    for name, meta in BUILTIN_PACKS.items():
        out.append(
            CatalogEntry(
                name=f"pack:{name}",
                description=str(meta.get("description") or name),
                tags=["pack"] + list(meta.get("skills") or [])[:5],
                source=name,
                kind="pack",
                extra={"skills": list(meta.get("skills") or [])},
            )
        )
    return out


def load_local_registry() -> List[CatalogEntry]:
    path = package_registry_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
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
                version=item.get("version"),
                homepage=item.get("homepage"),
            )
        )
    return out


def search_catalog(
    query: str = "",
    tags: Optional[Iterable[str]] = None,
    include_packs: bool = True,
    include_registry: bool = True,
) -> List[CatalogEntry]:
    q = (query or "").strip().lower()
    tag_set = {t.lower() for t in (tags or []) if t}
    pool = builtin_entries()
    if include_packs:
        pool = pool + pack_entries()
    if include_registry:
        pool = pool + load_local_registry()

    results: List[CatalogEntry] = []
    for entry in pool:
        hay = f"{entry.name} {entry.description} {' '.join(entry.tags)}".lower()
        if q and q not in hay:
            # allow multi-word AND
            words = q.split()
            if not all(w in hay for w in words):
                continue
        if tag_set and not tag_set.intersection({t.lower() for t in entry.tags}):
            continue
        results.append(entry)
    return results


def resolve_pack(name: str) -> List[str]:
    key = name.strip().lower()
    if key.startswith("pack:"):
        key = key.split(":", 1)[1]
    if key not in BUILTIN_PACKS:
        known = ", ".join(sorted(BUILTIN_PACKS))
        raise SkillError(f"unknown pack '{name}'. Available packs: {known}")
    return list(BUILTIN_PACKS[key]["skills"])


def resolve_source(source: str) -> Path:
    source = source.strip()
    if source.startswith("pack:"):
        raise SkillError("packs must be expanded before resolve_source")

    p = Path(source).expanduser()
    if p.exists():
        if p.is_file() and p.name.lower() in {"skill.md"} | {x for x in [p.name] if x.endswith((".md", ".mdc"))}:
            if p.name == "SKILL.md" or p.name.lower() == "skill.md":
                return p.parent
            return p  # file path for importers
        if p.is_dir():
            return p
        raise SkillError(f"path exists but is not a skill directory: {p}")

    for entry in builtin_entries():
        if entry.name == source:
            return Path(entry.source)

    # registry name
    for entry in load_local_registry():
        if entry.name == source and entry.source:
            return resolve_source(entry.source)

    if re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(/[\w./-]+)?$", source) and not source.startswith("."):
        parts = source.split("/")
        owner, repo = parts[0], parts[1]
        sub = "/".join(parts[2:]) if len(parts) > 2 else ""
        return _clone_github(owner, repo, subpath=sub)

    if source.startswith("http://") or source.startswith("https://") or source.startswith("git@"):
        return _clone_url(source)

    raise SkillError(
        f"cannot resolve skill source '{source}'. "
        "Use a local path, builtin name, pack:name, owner/repo, or git URL."
    )


def _clone_github(owner: str, repo: str, subpath: str = "", branch: str = "") -> Path:
    if repo.endswith(".git"):
        repo = repo[:-4]
    url = f"https://github.com/{owner}/{repo}.git"
    return _clone_url(url, subpath=subpath, branch=branch)


def _clone_url(url: str, subpath: str = "", branch: str = "") -> Path:
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
    from .adapters import import_skill  # local import to avoid cycle

    source = source.strip()
    if source.startswith("pack:") or source in BUILTIN_PACKS:
        names = resolve_pack(source)
        skills: List[Skill] = []
        for n in names:
            skills.extend(load_skills_from_source(n))
        return skills

    root = resolve_source(source)
    if root.is_file():
        return [import_skill(root)]

    dirs = find_skill_dirs(root)
    if not dirs:
        if (root / "SKILL.md").exists():
            dirs = [root]
        else:
            # maybe a folder of .mdc rules
            mdcs = list(root.rglob("*.mdc")) + list(root.glob("*.md"))
            if mdcs:
                return [import_skill(p) for p in mdcs if p.is_file()]
            raise SkillError(f"no SKILL.md found under {root}")
    return [Skill.load(d) for d in dirs]


def fetch_remote_catalog(url: str, timeout: float = 15.0) -> List[CatalogEntry]:
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
                version=item.get("version"),
                homepage=item.get("homepage"),
            )
        )
    return out


def export_lockfile(installed: List[dict], path: Path) -> None:
    path.write_text(
        json.dumps({"version": 1, "skills": installed}, indent=2) + "\n",
        encoding="utf-8",
    )


def read_lockfile(path: Path) -> List[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("skills") or [])


def build_registry_index(skills_root: Optional[Path] = None) -> dict:
    root = skills_root or package_skills_root()
    skills = []
    for d in find_skill_dirs(root):
        try:
            sk = Skill.load(d)
        except SkillError:
            continue
        skills.append(
            {
                "name": sk.name,
                "description": sk.description,
                "tags": list((sk.metadata or {}).get("tags") or []),
                "source": f"builtin:{sk.name}",
                "path": str(d.relative_to(root.parent)) if root.parent in d.parents else str(d),
                "version": "0.2.0",
            }
        )
    return {
        "name": "skillport-builtin",
        "version": 1,
        "skills": skills,
        "packs": {
            k: {"description": v["description"], "skills": v["skills"]}
            for k, v in BUILTIN_PACKS.items()
            if k != "all"
        },
    }
