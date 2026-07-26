from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .adapters import (
    TOOL_LAYOUTS,
    import_skill,
    install_path,
    list_tools,
    remove_skill,
    render_for_tool,
    write_skill,
)
from .models import Skill, SkillError, find_skill_dirs, slugify
from .registry import (
    BUILTIN_PACKS,
    build_registry_index,
    export_lockfile,
    fetch_remote_catalog,
    load_skills_from_source,
    read_lockfile,
    search_catalog,
)

console = Console()
ERR = Console(stderr=True)


def _project_root(path: Optional[str]) -> Path:
    return Path(path).expanduser().resolve() if path else Path.cwd().resolve()


def _parse_tools(tools: str) -> List[str]:
    if tools.strip().lower() in {"all", "*"}:
        return [t for t in TOOL_LAYOUTS.keys() if t != "generic"]
    parts = [p.strip().lower() for p in tools.split(",") if p.strip()]
    unknown = [p for p in parts if p not in TOOL_LAYOUTS]
    if unknown:
        raise click.ClickException(
            f"unknown tool(s): {', '.join(unknown)}. "
            f"Available: {', '.join(sorted(TOOL_LAYOUTS))}"
        )
    return parts


def _rel(root: Path, dest: Path) -> str:
    try:
        return str(dest.relative_to(root))
    except ValueError:
        return str(dest)


def _update_lock(root: Path, installed: List[dict]) -> None:
    export_lockfile(installed, root / "skillport.lock.json")
    cfg_path = root / ".skillport.json"
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            cfg["skills"] = installed
            cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        except json.JSONDecodeError:
            pass


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="skillport")
def main() -> None:
    """SkillPort — install AI agent skills once, run them everywhere.

    \b
    Examples:
      skillport init
      skillport search review
      skillport install pr-review --to claude,cursor
      skillport install pack:essentials --to all
      skillport convert ./rule.mdc --to claude
      skillport import .cursor/rules/foo.mdc -o ./skills/foo
      skillport validate ./skills --strict
      skillport doctor
    """


@main.command("tools")
def tools_cmd() -> None:
    """List supported AI coding tools."""
    table = Table(title="Supported tools", show_header=True, header_style="bold")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Install path")
    table.add_column("Kind", style="dim")
    for key, meta in TOOL_LAYOUTS.items():
        table.add_row(key, meta["label"], meta["path"], meta["kind"])
    console.print(table)


@main.command("packs")
def packs_cmd() -> None:
    """List built-in skill packs."""
    table = Table(title="Skill packs", show_header=True, header_style="bold")
    table.add_column("Pack", style="green")
    table.add_column("Description")
    table.add_column("Skills", style="dim")
    for name, meta in BUILTIN_PACKS.items():
        table.add_row(name, meta["description"], ", ".join(meta["skills"]))
    console.print(table)
    console.print("\nInstall: [bold]skillport install pack:essentials --to claude,cursor[/bold]")


@main.command("search")
@click.argument("query", required=False, default="")
@click.option("--tag", multiple=True, help="Filter by tag (repeatable)")
@click.option("--no-packs", is_flag=True, help="Hide packs from results")
@click.option("--json", "as_json", is_flag=True, help="Machine-readable output")
def search_cmd(query: str, tag: Tuple[str, ...], no_packs: bool, as_json: bool) -> None:
    """Search built-in catalog, packs, and local registry."""
    results = search_catalog(query, tags=tag, include_packs=not no_packs)
    if as_json:
        console.print_json(
            data=[
                {
                    "name": e.name,
                    "description": e.description,
                    "tags": e.tags,
                    "kind": e.kind,
                    "source": e.source,
                }
                for e in results
            ]
        )
        return
    if not results:
        console.print("[yellow]No skills matched.[/yellow]")
        return
    table = Table(title="Skill catalog", show_header=True, header_style="bold")
    table.add_column("Name", style="green")
    table.add_column("Kind", style="cyan")
    table.add_column("Description")
    table.add_column("Tags", style="dim")
    for e in results:
        table.add_row(e.name, e.kind, e.description, ", ".join(e.tags))
    console.print(table)
    console.print("\nInstall: [bold]skillport install <name> --to claude,cursor[/bold]")


@main.command("init")
@click.option("--path", "project", default=None, help="Project root (default: cwd)")
@click.option("--tools", default="claude,cursor", show_default=True, help="Comma-separated tools or 'all'")
@click.option("--pack", default="essentials", show_default=True, help="Starter pack (or 'none')")
@click.option("--with-examples/--no-examples", default=None, help="Deprecated: use --pack")
def init_cmd(
    project: Optional[str],
    tools: str,
    pack: str,
    with_examples: Optional[bool],
) -> None:
    """Scaffold skillport config and install a starter pack."""
    root = _project_root(project)
    cfg = root / ".skillport.json"
    tool_list = _parse_tools(tools)
    data = {"version": 1, "tools": tool_list, "skills": []}
    if cfg.exists():
        console.print(f"[yellow]Config already exists:[/yellow] {cfg}")
    else:
        cfg.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        console.print(f"[green]Created[/green] {cfg}")

    # backward compat
    if with_examples is False:
        pack = "none"
    elif with_examples is True and pack == "none":
        pack = "essentials"

    if pack and pack.lower() != "none":
        src = pack if pack.startswith("pack:") else f"pack:{pack}"
        try:
            skills = load_skills_from_source(src)
        except SkillError as exc:
            raise click.ClickException(str(exc)) from exc
        installed = read_lockfile(root / "skillport.lock.json")
        for skill in skills:
            errors = skill.validate()
            if errors:
                ERR.print(f"[red]skip {skill.name}:[/red] {'; '.join(errors)}")
                continue
            for t in tool_list:
                try:
                    dest = write_skill(root, t, skill, force=False)
                    console.print(f"[green]✓[/green] {t}: {_rel(root, dest)}")
                except FileExistsError:
                    console.print(f"[dim]-[/dim] exists: {_rel(root, install_path(root, t, skill.name))}")
            installed = [i for i in installed if i.get("name") != skill.name]
            installed.append(
                {
                    "name": skill.name,
                    "source": src,
                    "tools": tool_list,
                    "description": skill.description,
                }
            )
        _update_lock(root, installed)

    console.print(
        Panel.fit(
            "[bold]Next[/bold]\n"
            "• skillport search\n"
            "• skillport install security-audit --to claude,cursor\n"
            "• skillport packs\n"
            "• skillport doctor",
            title="SkillPort ready",
            border_style="cyan",
        )
    )


@main.command("install")
@click.argument("source")
@click.option("--to", "tools", default="claude,cursor", show_default=True, help="Target tools (comma list or all)")
@click.option("--path", "project", default=None, help="Project root (default: cwd)")
@click.option("--force", is_flag=True, help="Overwrite existing files")
@click.option("--name", default=None, help="Override skill name (single skill only)")
@click.option("--dry-run", is_flag=True, help="Show actions without writing")
def install_cmd(
    source: str,
    tools: str,
    project: Optional[str],
    force: bool,
    name: Optional[str],
    dry_run: bool,
) -> None:
    """Install a skill/pack from builtin name, path, owner/repo, or git URL."""
    root = _project_root(project)
    tool_list = _parse_tools(tools)
    try:
        skills = load_skills_from_source(source)
    except SkillError as exc:
        raise click.ClickException(str(exc)) from exc

    if name and len(skills) > 1:
        raise click.ClickException("--name can only be used when installing a single skill")

    installed = read_lockfile(root / "skillport.lock.json")
    for skill in skills:
        if name:
            skill.name = slugify(name)
        errors = skill.validate()
        if errors:
            raise click.ClickException(f"invalid skill '{skill.name}': " + "; ".join(errors))
        for t in tool_list:
            dest = install_path(root, t, skill.name)
            if dry_run:
                console.print(f"[cyan]dry-run[/cyan] {skill.name} → {t} ({_rel(root, dest)})")
                continue
            try:
                dest = write_skill(root, t, skill, force=force)
                console.print(f"[green]Installed[/green] {skill.name} → {t} ({_rel(root, dest)})")
            except FileExistsError as exc:
                raise click.ClickException(str(exc)) from exc
        if not dry_run:
            installed = [i for i in installed if i.get("name") != skill.name]
            installed.append(
                {
                    "name": skill.name,
                    "source": source,
                    "tools": tool_list,
                    "description": skill.description,
                }
            )
    if not dry_run:
        _update_lock(root, installed)


@main.command("uninstall")
@click.argument("name")
@click.option("--path", "project", default=None, help="Project root (default: cwd)")
@click.option("--from", "tools", default=None, help="Tools to remove from (default: lockfile/all known)")
@click.option("--keep-lock", is_flag=True, help="Do not remove from lockfile")
def uninstall_cmd(name: str, project: Optional[str], tools: Optional[str], keep_lock: bool) -> None:
    """Remove an installed skill from target tool folders."""
    root = _project_root(project)
    name = slugify(name)
    lock = read_lockfile(root / "skillport.lock.json")
    entry = next((i for i in lock if i.get("name") == name), None)
    if tools:
        tool_list = _parse_tools(tools)
    elif entry and entry.get("tools"):
        tool_list = list(entry["tools"])
    else:
        tool_list = [t for t in TOOL_LAYOUTS if t != "generic"]

    removed = 0
    for t in tool_list:
        path = remove_skill(root, t, name)
        if path:
            console.print(f"[green]Removed[/green] {name} from {t} ({_rel(root, path)})")
            removed += 1
        else:
            console.print(f"[dim]-[/dim] not found: {t}/{name}")
    if not keep_lock:
        new_lock = [i for i in lock if i.get("name") != name]
        _update_lock(root, new_lock)
    if removed == 0:
        raise click.ClickException(f"nothing removed for '{name}'")


@main.command("convert")
@click.argument("source")
@click.option("--to", "tool", required=True, help="Target tool id (cursor, claude, copilot, ...)")
@click.option("-o", "--output", type=click.Path(), default=None, help="Write to file/dir instead of stdout")
@click.option("--from-format", "from_fmt", default=None, help="Force source format: skill_md|cursor_mdc|agents_md")
def convert_cmd(source: str, tool: str, output: Optional[str], from_fmt: Optional[str]) -> None:
    """Convert a skill/rule into another tool's format (bidirectional)."""
    src_path = Path(source).expanduser()
    try:
        if src_path.exists() and (src_path.is_file() or (src_path.is_dir() and not (src_path / "SKILL.md").exists())):
            # import single file formats
            if src_path.is_file():
                skills = [import_skill(src_path)]
            else:
                skills = load_skills_from_source(source)
        else:
            skills = load_skills_from_source(source)
    except SkillError as exc:
        raise click.ClickException(str(exc)) from exc

    for skill in skills:
        errors = skill.validate()
        if errors:
            raise click.ClickException("; ".join(errors))
        try:
            text = render_for_tool(skill, tool)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        if output:
            out = Path(output)
            if out.is_dir() or str(output).endswith(("/", "\\")):
                out.mkdir(parents=True, exist_ok=True)
                if tool in {"claude", "codex", "generic", "opencode"}:
                    target = out / skill.name / "SKILL.md"
                    target.parent.mkdir(parents=True, exist_ok=True)
                elif tool == "cursor":
                    target = out / f"{skill.name}.mdc"
                else:
                    target = out / f"{skill.name}.md"
                target.write_text(text, encoding="utf-8")
                console.print(f"[green]Wrote[/green] {target}")
            else:
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(text, encoding="utf-8")
                console.print(f"[green]Wrote[/green] {out}")
        else:
            if len(skills) > 1:
                console.rule(skill.name)
            console.print(text, highlight=False)


@main.command("import")
@click.argument("source", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), required=True, help="Output skill directory")
@click.option("--name", default=None, help="Override skill name")
def import_cmd(source: str, output: str, name: Optional[str]) -> None:
    """Import Cursor .mdc / markdown rules into canonical SKILL.md."""
    src = Path(source)
    try:
        skill = import_skill(src, name_hint=name or src.stem)
    except SkillError as exc:
        raise click.ClickException(str(exc)) from exc
    if name:
        skill.name = slugify(name)
    errors = skill.validate()
    if errors:
        raise click.ClickException("; ".join(errors))
    out = Path(output).expanduser()
    # if output ends with skill name or is a dir
    if out.exists() and out.is_dir() and out.name != skill.name:
        dest_dir = out / skill.name
    else:
        dest_dir = out
    dest_dir.mkdir(parents=True, exist_ok=True)
    skill_md = dest_dir / "SKILL.md"
    skill_md.write_text(skill.to_skill_md(), encoding="utf-8")
    console.print(f"[green]Imported[/green] {skill.name} → {skill_md}")
    for w in skill.warnings():
        console.print(f"[yellow]warning:[/yellow] {w}")


@main.command("validate")
@click.argument("path", required=False, default=".")
@click.option("--strict", is_flag=True, help="Fail on warnings too")
@click.option("--json", "as_json", is_flag=True, help="JSON report")
def validate_cmd(path: str, strict: bool, as_json: bool) -> None:
    """Validate one or more skills (agentskills.io rules)."""
    root = Path(path).expanduser().resolve()
    dirs = find_skill_dirs(root)
    if not dirs and root.is_file():
        dirs = [root.parent if root.name == "SKILL.md" else root]
        if root.is_file() and root.suffix in {".md", ".mdc"} and root.name != "SKILL.md":
            # validate importable rule
            try:
                skill = import_skill(root)
                errs, warns = skill.validate_report()
            except SkillError as exc:
                raise click.ClickException(str(exc)) from exc
            if as_json:
                console.print_json(data=[{"name": skill.name, "errors": errs, "warnings": warns}])
            else:
                status = "FAIL" if errs or (strict and warns) else "OK"
                console.print(f"{skill.name}: {status}")
                for e in errs:
                    console.print(f"  [red]error[/red] {e}")
                for w in warns:
                    console.print(f"  [yellow]warn[/yellow] {w}")
            if errs or (strict and warns):
                sys.exit(1)
            return
    if not dirs:
        raise click.ClickException(f"no skills found under {root}")

    rows = []
    failed = 0
    table = Table(title="Validation", show_header=True, header_style="bold")
    table.add_column("Skill")
    table.add_column("Status")
    table.add_column("Details")

    for d in dirs:
        try:
            skill = Skill.load(d) if not (d.is_file()) else Skill.load(d)
            if d.is_file():
                skill = import_skill(d)
            errors, warnings = skill.validate_report()
        except SkillError as exc:
            failed += 1
            rows.append({"name": str(d), "errors": [str(exc)], "warnings": []})
            table.add_row(str(d), "[red]ERROR[/red]", str(exc))
            continue
        if errors or (strict and warnings):
            failed += 1
            detail = "; ".join(errors + (warnings if strict else []))
            table.add_row(skill.name or d.name, "[red]FAIL[/red]", detail[:80])
        else:
            extra = f" ({len(warnings)} warnings)" if warnings else ""
            table.add_row(skill.name, "[green]OK[/green]", (skill.description[:50] + extra))
        rows.append({"name": skill.name, "errors": errors, "warnings": warnings})

    if as_json:
        console.print_json(data=rows)
    else:
        console.print(table)
        console.print(f"\n{len(dirs) - failed}/{len(dirs)} valid")
    if failed:
        sys.exit(1)


@main.command("list")
@click.option("--path", "project", default=None, help="Project root (default: cwd)")
@click.option("--json", "as_json", is_flag=True)
def list_cmd(project: Optional[str], as_json: bool) -> None:
    """List skills installed in the current project."""
    root = _project_root(project)
    lock = read_lockfile(root / "skillport.lock.json")
    if as_json:
        console.print_json(data=lock)
        return
    table = Table(title=f"Installed skills in {root.name}", show_header=True, header_style="bold")
    table.add_column("Name", style="green")
    table.add_column("Tools")
    table.add_column("Source", style="dim")
    if lock:
        for item in lock:
            table.add_row(
                item.get("name", "?"),
                ", ".join(item.get("tools") or []),
                str(item.get("source") or ""),
            )
        console.print(table)
        return

    found = False
    for tool, meta in TOOL_LAYOUTS.items():
        base = meta["path"].split("{name}")[0]
        folder = root / base
        if folder.exists():
            for p in folder.rglob("*"):
                if p.is_file() and (p.suffix in {".md", ".mdc"} or p.name == "SKILL.md"):
                    table.add_row(
                        p.stem if p.name != "SKILL.md" else p.parent.name,
                        tool,
                        str(p.relative_to(root)),
                    )
                    found = True
    if not found:
        console.print("[yellow]No installed skills found. Try: skillport init[/yellow]")
        return
    console.print(table)


@main.command("doctor")
@click.option("--path", "project", default=None, help="Project root (default: cwd)")
@click.option("--fix", is_flag=True, help="Attempt to create missing config")
def doctor_cmd(project: Optional[str], fix: bool) -> None:
    """Check project setup and give fix suggestions."""
    root = _project_root(project)
    console.print(Panel.fit(f"[bold]SkillPort doctor[/bold] v{__version__}\nProject: {root}", border_style="cyan"))

    checks: List[Tuple[str, bool, str]] = []
    cfg = root / ".skillport.json"
    if fix and not cfg.exists():
        cfg.write_text(
            json.dumps({"version": 1, "tools": ["claude", "cursor"], "skills": []}, indent=2) + "\n",
            encoding="utf-8",
        )
    checks.append((".skillport.json", cfg.exists(), "run skillport init"))
    lock = root / "skillport.lock.json"
    checks.append(("skillport.lock.json", lock.exists(), "install at least one skill"))

    # drift: lock vs disk
    drift = 0
    if lock.exists():
        for item in read_lockfile(lock):
            name = item.get("name")
            for t in item.get("tools") or []:
                if t not in TOOL_LAYOUTS:
                    continue
                p = install_path(root, t, name)
                if t == "agents":
                    if not p.exists() or f"skillport:{name}:start" not in p.read_text(encoding="utf-8", errors="ignore"):
                        drift += 1
                elif not p.exists():
                    drift += 1
    checks.append(("lockfile matches disk", drift == 0, f"{drift} missing projections — run skillport sync --force"))

    for tool, meta in list_tools():
        if tool in {"generic", "agents"}:
            continue
        base = meta["path"].split("{name}")[0]
        exists = (root / base).exists()
        checks.append((f"{meta['label']} path ({base})", exists, f"skillport install pack:essentials --to {tool}"))

    table = Table(show_header=True, header_style="bold")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Hint", style="dim")
    ok_n = 0
    for name, ok, hint in checks:
        table.add_row(name, "[green]ok[/green]" if ok else "[yellow]missing[/yellow]", "" if ok else hint)
        if ok:
            ok_n += 1
    console.print(table)
    console.print(f"\n{ok_n}/{len(checks)} checks passed")


@main.command("new")
@click.argument("name")
@click.option("--path", "dest", default=".", help="Where to create the skill folder")
@click.option("--description", default=None, help="Skill description")
@click.option("--tag", multiple=True, help="Tags (repeatable)")
def new_cmd(name: str, dest: str, description: Optional[str], tag: Tuple[str, ...]) -> None:
    """Scaffold a new skill from the official template."""
    name = slugify(name)
    root = Path(dest).expanduser().resolve() / name
    if root.exists():
        raise click.ClickException(f"already exists: {root}")
    desc = description or f"TODO: describe what {name} does and when to use it (keywords help routing)."
    tags = list(tag) if tag else []
    skill = Skill(
        name=name,
        description=desc,
        body=(
            f"## When to use\n\n"
            f"Use this skill when the user asks about **{name.replace('-', ' ')}**.\n\n"
            f"## Instructions\n\n"
            f"1. Clarify the goal and constraints.\n"
            f"2. Do the work step by step.\n"
            f"3. Return a concise result with next actions.\n\n"
            f"## Examples\n\n"
            f"- Example request → expected behavior\n\n"
            f"## Pitfalls\n\n"
            f"- List common failure modes and how to avoid them.\n"
        ),
        license="MIT",
        metadata={"tags": tags},
    )
    errors = skill.validate()
    if errors:
        raise click.ClickException("; ".join(errors))
    root.mkdir(parents=True)
    (root / "SKILL.md").write_text(skill.to_skill_md(), encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "references").mkdir()
    console.print(f"[green]Created skill[/green] {root}")
    console.print("Edit SKILL.md, then: [bold]skillport validate " + str(root) + "[/bold]")


@main.command("sync")
@click.option("--path", "project", default=None, help="Project root (default: cwd)")
@click.option("--force", is_flag=True, help="Overwrite existing target files")
def sync_cmd(project: Optional[str], force: bool) -> None:
    """Re-install all skills from skillport.lock.json to configured tools."""
    root = _project_root(project)
    lock = read_lockfile(root / "skillport.lock.json")
    if not lock:
        raise click.ClickException("no skillport.lock.json — install skills first")
    for item in lock:
        source = item.get("source")
        tools = item.get("tools") or ["claude"]
        name = item.get("name")
        if not source:
            continue
        try:
            skills = load_skills_from_source(source)
        except SkillError as exc:
            # fallback: try by name if source was pack
            try:
                skills = load_skills_from_source(name)
            except SkillError:
                ERR.print(f"[red]{name}:[/red] {exc}")
                continue
        for skill in skills:
            if name and len(skills) == 1:
                skill.name = name
            if name and skill.name != name and len(skills) > 1:
                if skill.name != name:
                    continue
            for t in tools:
                try:
                    dest = write_skill(root, t, skill, force=force)
                    console.print(f"[green]Synced[/green] {skill.name} → {t} ({_rel(root, dest)})")
                except FileExistsError:
                    console.print(f"[yellow]skip exists[/yellow] {t}/{skill.name} (use --force)")


@main.command("diff")
@click.argument("source_a")
@click.argument("source_b")
def diff_cmd(source_a: str, source_b: str) -> None:
    """Show a textual diff between two skills (name/description/body)."""
    try:
        a = load_skills_from_source(source_a)[0]
        b = load_skills_from_source(source_b)[0]
    except (SkillError, IndexError) as exc:
        raise click.ClickException(str(exc)) from exc

    import difflib

    left = a.to_skill_md().splitlines(keepends=True)
    right = b.to_skill_md().splitlines(keepends=True)
    diff = difflib.unified_diff(left, right, fromfile=a.name, tofile=b.name)
    text = "".join(diff)
    if not text:
        console.print("[green]No differences[/green]")
    else:
        console.print(text, highlight=False)


@main.command("show")
@click.argument("source")
def show_cmd(source: str) -> None:
    """Print canonical SKILL.md for a skill source."""
    try:
        skills = load_skills_from_source(source)
    except SkillError as exc:
        raise click.ClickException(str(exc)) from exc
    for skill in skills:
        if len(skills) > 1:
            console.rule(skill.name)
        console.print(skill.to_skill_md(), highlight=False)


@main.command("registry")
@click.option("--write", "write_path", type=click.Path(), default=None, help="Write index JSON to path")
@click.option("--fetch", default=None, help="Fetch and display a remote registry URL")
def registry_cmd(write_path: Optional[str], fetch: Optional[str]) -> None:
    """Build or inspect the skill registry index."""
    if fetch:
        try:
            entries = fetch_remote_catalog(fetch)
        except Exception as exc:  # noqa: BLE001
            raise click.ClickException(f"fetch failed: {exc}") from exc
        table = Table(title=f"Remote registry ({len(entries)})")
        table.add_column("Name")
        table.add_column("Description")
        for e in entries:
            table.add_row(e.name, e.description[:60])
        console.print(table)
        return

    index = build_registry_index()
    if write_path:
        path = Path(write_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
        console.print(f"[green]Wrote[/green] {path} ({len(index.get('skills', []))} skills)")
    else:
        console.print_json(data=index)


@main.command("info")
@click.argument("name")
def info_cmd(name: str) -> None:
    """Show metadata for a catalog skill or pack."""
    hits = search_catalog(name, include_packs=True)
    exact = [h for h in hits if h.name == name or h.name == f"pack:{name}" or h.name.endswith(name)]
    entry = exact[0] if exact else (hits[0] if hits else None)
    if not entry:
        raise click.ClickException(f"not found: {name}")
    console.print(
        Panel.fit(
            f"[bold]{entry.name}[/bold]\n"
            f"{entry.description}\n\n"
            f"kind: {entry.kind}\n"
            f"tags: {', '.join(entry.tags)}\n"
            f"source: {entry.source}",
            border_style="cyan",
        )
    )
    if entry.kind != "pack":
        try:
            skill = load_skills_from_source(entry.name if entry.kind == "builtin" else entry.source)[0]
            console.print(f"\n[dim]preview[/dim]\n{skill.body.strip()[:400]}...")
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    main()
