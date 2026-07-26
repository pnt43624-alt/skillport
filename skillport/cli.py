from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import __version__
from .adapters import TOOL_LAYOUTS, install_path, list_tools, render_for_tool, write_skill
from .models import Skill, SkillError, find_skill_dirs
from .registry import (
    export_lockfile,
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


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="skillport")
def main() -> None:
    """SkillPort — install AI agent skills once, run them everywhere.

    \b
    Examples:
      skillport init
      skillport search review
      skillport install pr-review --to claude,cursor
      skillport convert ./my-skill --to cursor -o out.mdc
      skillport validate ./skills
      skillport doctor
    """


@main.command("tools")
def tools_cmd() -> None:
    """List supported AI coding tools."""
    table = Table(title="Supported tools", show_header=True, header_style="bold")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Install path")
    for key, meta in TOOL_LAYOUTS.items():
        table.add_row(key, meta["label"], meta["path"])
    console.print(table)


@main.command("search")
@click.argument("query", required=False, default="")
@click.option("--tag", multiple=True, help="Filter by tag (repeatable)")
def search_cmd(query: str, tag: Tuple[str, ...]) -> None:
    """Search the built-in skill catalog."""
    results = search_catalog(query, tags=tag)
    if not results:
        console.print("[yellow]No skills matched.[/yellow]")
        return
    table = Table(title="Skill catalog", show_header=True, header_style="bold")
    table.add_column("Name", style="green")
    table.add_column("Description")
    table.add_column("Tags", style="dim")
    for e in results:
        table.add_row(e.name, e.description, ", ".join(e.tags))
    console.print(table)
    console.print("\nInstall with: [bold]skillport install <name> --to claude,cursor[/bold]")


@main.command("init")
@click.option("--path", "project", default=None, help="Project root (default: cwd)")
@click.option("--tools", default="claude,cursor", show_default=True, help="Comma-separated tools or 'all'")
@click.option("--with-examples/--no-examples", default=True, show_default=True)
def init_cmd(project: Optional[str], tools: str, with_examples: bool) -> None:
    """Scaffold skillport config and optional starter skills in a project."""
    root = _project_root(project)
    cfg = root / ".skillport.json"
    tool_list = _parse_tools(tools)
    data = {
        "version": 1,
        "tools": tool_list,
        "skills": [],
    }
    if cfg.exists():
        console.print(f"[yellow]Config already exists:[/yellow] {cfg}")
    else:
        cfg.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        console.print(f"[green]Created[/green] {cfg}")

    if with_examples:
        for name in ("pr-review", "commit"):
            try:
                skills = load_skills_from_source(name)
            except SkillError as exc:
                ERR.print(f"[red]skip {name}:[/red] {exc}")
                continue
            for skill in skills:
                for t in tool_list:
                    try:
                        dest = write_skill(root, t, skill, force=False)
                        console.print(f"[green]✓[/green] {t}: {dest.relative_to(root)}")
                    except FileExistsError:
                        console.print(f"[dim]-[/dim] exists: {install_path(root, t, skill.name).relative_to(root)}")
                    except Exception as exc:  # noqa: BLE001
                        ERR.print(f"[red]failed {t}/{skill.name}:[/red] {exc}")

    console.print(
        Panel.fit(
            "[bold]Next[/bold]\n"
            "• skillport search\n"
            "• skillport install security-audit --to claude,cursor\n"
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
@click.option("--name", default=None, help="Override skill name")
def install_cmd(
    source: str,
    tools: str,
    project: Optional[str],
    force: bool,
    name: Optional[str],
) -> None:
    """Install a skill from builtin name, path, owner/repo, or git URL."""
    root = _project_root(project)
    tool_list = _parse_tools(tools)
    try:
        skills = load_skills_from_source(source)
    except SkillError as exc:
        raise click.ClickException(str(exc)) from exc

    installed = read_lockfile(root / "skillport.lock.json")
    for skill in skills:
        if name:
            skill.name = name
        errors = skill.validate()
        if errors:
            raise click.ClickException(f"invalid skill '{skill.name}': " + "; ".join(errors))
        for t in tool_list:
            try:
                dest = write_skill(root, t, skill, force=force)
                try:
                    rel = dest.relative_to(root)
                except ValueError:
                    rel = dest
                console.print(f"[green]Installed[/green] {skill.name} → {t} ({rel})")
            except FileExistsError as exc:
                raise click.ClickException(str(exc)) from exc
        installed = [i for i in installed if i.get("name") != skill.name]
        installed.append(
            {
                "name": skill.name,
                "source": source,
                "tools": tool_list,
                "description": skill.description,
            }
        )

    export_lockfile(installed, root / "skillport.lock.json")
    # merge into .skillport.json if present
    cfg_path = root / ".skillport.json"
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            cfg["skills"] = installed
            cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        except json.JSONDecodeError:
            pass


@main.command("convert")
@click.argument("source")
@click.option("--to", "tool", required=True, help="Target tool id (cursor, claude, copilot, ...)")
@click.option("-o", "--output", type=click.Path(), default=None, help="Write to file instead of stdout")
def convert_cmd(source: str, tool: str, output: Optional[str]) -> None:
    """Convert a skill into another tool's format."""
    try:
        skills = load_skills_from_source(source)
    except SkillError as exc:
        raise click.ClickException(str(exc)) from exc
    if len(skills) != 1 and not output:
        # if multiple, require directory output path ending with /
        pass
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
            if out.is_dir() or str(output).endswith("/"):
                out.mkdir(parents=True, exist_ok=True)
                # pick extension by tool
                ext = ".mdc" if tool == "cursor" else "SKILL.md" if tool in {"claude", "codex", "generic"} else f"{skill.name}.md"
                if tool in {"claude", "codex", "generic"}:
                    target = out / skill.name / "SKILL.md"
                    target.parent.mkdir(parents=True, exist_ok=True)
                else:
                    target = out / (f"{skill.name}.mdc" if tool == "cursor" else f"{skill.name}.md")
                target.write_text(text, encoding="utf-8")
                console.print(f"[green]Wrote[/green] {target}")
            else:
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(text, encoding="utf-8")
                console.print(f"[green]Wrote[/green] {out}")
        else:
            console.print(text, highlight=False)


@main.command("validate")
@click.argument("path", required=False, default=".")
@click.option("--strict", is_flag=True, help="Exit 1 on any warning-level issue")
def validate_cmd(path: str, strict: bool) -> None:
    """Validate one or more skills (agentskills.io rules)."""
    root = Path(path).expanduser().resolve()
    dirs = find_skill_dirs(root)
    if not dirs and root.is_file():
        dirs = [root.parent]
    if not dirs:
        raise click.ClickException(f"no skills found under {root}")

    failed = 0
    table = Table(title="Validation", show_header=True, header_style="bold")
    table.add_column("Skill")
    table.add_column("Status")
    table.add_column("Details")

    for d in dirs:
        try:
            skill = Skill.load(d)
            errors = skill.validate()
        except SkillError as exc:
            failed += 1
            table.add_row(str(d), "[red]ERROR[/red]", str(exc))
            continue
        if errors:
            failed += 1
            table.add_row(skill.name or d.name, "[red]FAIL[/red]", "; ".join(errors))
        else:
            table.add_row(skill.name, "[green]OK[/green]", skill.description[:60])

    console.print(table)
    console.print(f"\n{len(dirs) - failed}/{len(dirs)} valid")
    if failed:
        sys.exit(1)


@main.command("list")
@click.option("--path", "project", default=None, help="Project root (default: cwd)")
def list_cmd(project: Optional[str]) -> None:
    """List skills installed in the current project (from lockfile + scan)."""
    root = _project_root(project)
    lock = read_lockfile(root / "skillport.lock.json")
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
    else:
        # scan common locations
        found = False
        for tool, meta in TOOL_LAYOUTS.items():
            # heuristic scan
            base = meta["path"].split("{name}")[0]
            folder = root / base
            if folder.exists():
                for p in folder.rglob("*"):
                    if p.is_file() and p.suffix in {".md", ".mdc"} or p.name == "SKILL.md":
                        table.add_row(p.stem if p.name != "SKILL.md" else p.parent.name, tool, str(p.relative_to(root)))
                        found = True
        if not found:
            console.print("[yellow]No installed skills found. Try: skillport init[/yellow]")
            return
    console.print(table)


@main.command("doctor")
@click.option("--path", "project", default=None, help="Project root (default: cwd)")
def doctor_cmd(project: Optional[str]) -> None:
    """Check project setup and give fix suggestions."""
    root = _project_root(project)
    console.print(Panel.fit(f"[bold]SkillPort doctor[/bold]\nProject: {root}", border_style="cyan"))

    checks: List[Tuple[str, bool, str]] = []
    cfg = root / ".skillport.json"
    checks.append((".skillport.json", cfg.exists(), "run skillport init"))
    lock = root / "skillport.lock.json"
    checks.append(("skillport.lock.json", lock.exists(), "install at least one skill"))

    for tool, meta in list_tools():
        if tool in {"generic", "agents"}:
            continue
        # show whether tool config dir exists
        base = meta["path"].split("{name}")[0]
        exists = (root / base).exists()
        checks.append((f"{meta['label']} path ({base})", exists, f"skillport install pr-review --to {tool}"))

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
def new_cmd(name: str, dest: str, description: Optional[str]) -> None:
    """Scaffold a new skill from the official template."""
    name = name.strip().lower().replace(" ", "-")
    root = Path(dest).expanduser().resolve() / name
    if root.exists():
        raise click.ClickException(f"already exists: {root}")
    desc = description or f"TODO: describe what {name} does and when to use it."
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
            f"- Example request → expected behavior\n"
        ),
        license="MIT",
        metadata={"tags": []},
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
            ERR.print(f"[red]{name}:[/red] {exc}")
            continue
        for skill in skills:
            if name:
                skill.name = name
            for t in tools:
                try:
                    dest = write_skill(root, t, skill, force=force)
                    console.print(f"[green]Synced[/green] {skill.name} → {t} ({dest})")
                except FileExistsError:
                    console.print(f"[yellow]skip exists[/yellow] {t}/{skill.name} (use --force)")


if __name__ == "__main__":
    main()