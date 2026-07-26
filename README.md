<p align="center">
  <img src="assets/banner.svg" alt="SkillPort" width="100%" />
</p>

<h1 align="center">SkillPort</h1>

<p align="center">
  <strong>One CLI to install AI agent skills once — and run them everywhere.</strong><br/>
  Claude Code · Cursor · Codex · Copilot · Windsurf · Continue · Aider · Cline · AGENTS.md
</p>

<p align="center">
  <a href="https://pypi.org/project/skillport/"><img alt="PyPI" src="https://img.shields.io/badge/pip_install-skillport-0ea5e9?style=flat-square" /></a>
  <a href="LICENSE"><img alt="MIT" src="https://img.shields.io/badge/license-MIT-green?style=flat-square" /></a>
  <a href="https://agentskills.io"><img alt="agentskills" src="https://img.shields.io/badge/spec-agentskills.io-8b5cf6?style=flat-square" /></a>
  <a href="#quickstart"><img alt="python" src="https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square" /></a>
  <img alt="tools" src="https://img.shields.io/badge/tools-10_targets-f59e0b?style=flat-square" />
</p>

<p align="center">
  <a href="#quickstart">Quickstart</a> ·
  <a href="#why-skillport">Why</a> ·
  <a href="#commands">Commands</a> ·
  <a href="#supported-tools">Tools</a> ·
  <a href="#built-in-skills">Skills</a> ·
  <a href="#convert-any-skill">Convert</a> ·
  <a href="#launch--star-growth">Launch</a>
</p>

---

## The problem

In 2026 every AI coding tool wants skills in a **different folder and format**:

| Tool | Where skills live | Format |
|------|-------------------|--------|
| Claude Code | `.claude/skills/<name>/SKILL.md` | Agent Skills spec |
| Cursor | `.cursor/rules/<name>.mdc` | MDC frontmatter |
| Codex | `.codex/skills/...` | SKILL.md |
| Copilot | `.github/copilot-instructions/` | freeform MD |
| Windsurf / Cline / Continue / Aider | each different | each different |

So teams copy-paste the same prompt 6 times, drift out of sync, and ship inconsistent agent behavior.

**SkillPort fixes that.**

```bash
skillport install pr-review --to claude,cursor,codex,copilot
```

One source skill → every tool you actually use.

---

## Demo

```bash
# Install SkillPort
pip install skillport

# See what you can target
skillport tools

# Search the built-in catalog
skillport search review

# Drop a PR-review skill into Claude + Cursor in one shot
skillport install pr-review --to claude,cursor

# Convert any SKILL.md into a Cursor rule
skillport convert ./skills/security-audit --to cursor -o .cursor/rules/security-audit.mdc

# Validate against the agentskills.io spec
skillport validate ./skills

# Health-check a repo
skillport doctor
```

<details>
<summary><strong>Example: Claude SKILL.md → Cursor .mdc (automatic)</strong></summary>

**Input** (`SKILL.md`):

```yaml
---
name: pr-review
description: Structured pull-request review...
metadata:
  globs: "**/*"
---
## Goal
Produce a high-signal PR review...
```

**Output** (`.cursor/rules/pr-review.mdc`):

```yaml
---
description: Structured pull-request review...
globs: **/*
alwaysApply: false
---
# pr-review

## Goal
Produce a high-signal PR review...
```

</details>

---

## Why SkillPort?

| Pain | SkillPort |
|------|-----------|
| Skills locked to one vendor | **10 targets** out of the box |
| Broken YAML / bad names | **`validate`** against agentskills.io |
| "Works on my Claude, not your Cursor" | **`sync`** + lockfile |
| Copy-paste rot | **One canonical SKILL.md** |
| Empty repo bootstrap | **`init`** + starter skills |
| Remote catalogs | install from `owner/repo` or git URL |

Built for the wave of [Agent Skills](https://agentskills.io), Claude Skills, Cursor rules, and AGENTS.md — not against it.

---

## Quickstart

### Install

```bash
pip install skillport
# or
pipx install skillport
```

From source:

```bash
git clone https://github.com/pnt43624-alt/skillport.git
cd skillport
pip install -e ".[dev]"
```

### Initialize a project

```bash
cd your-repo
skillport init --tools claude,cursor
```

Creates:

- `.skillport.json` — tool targets
- starter skills (`pr-review`, `commit`) installed for those tools
- `skillport.lock.json` — reproducible installs

### Install more skills

```bash
# Built-in
skillport install security-audit --to claude,cursor,copilot

# Local path
skillport install ./my-skills/foo --to all

# GitHub shorthand (clones shallow)
skillport install anthropics/skills --to claude

# Full git URL + subfolder tree URLs supported
skillport install https://github.com/org/repo.git --to cursor
```

---

## Commands

| Command | What it does |
|---------|----------------|
| `skillport tools` | List supported AI tools + install paths |
| `skillport search [q]` | Search built-in catalog |
| `skillport init` | Scaffold config + optional examples |
| `skillport install <src>` | Install skill(s) to target tools |
| `skillport convert <src> --to <tool>` | Convert format (stdout or `-o`) |
| `skillport validate [path]` | Spec validation (CI-friendly) |
| `skillport list` | Show installed skills |
| `skillport sync` | Re-apply lockfile |
| `skillport doctor` | Project health check |
| `skillport new <name>` | Scaffold a new skill template |

Global alias: `sp` (same CLI).

---

## Supported tools

| ID | Tool | Output |
|----|------|--------|
| `claude` | Claude Code | `.claude/skills/<name>/SKILL.md` |
| `cursor` | Cursor | `.cursor/rules/<name>.mdc` |
| `codex` | OpenAI Codex | `.codex/skills/<name>/SKILL.md` |
| `copilot` | GitHub Copilot | `.github/copilot-instructions/<name>.md` |
| `windsurf` | Windsurf | `.windsurf/rules/<name>.md` |
| `continue` | Continue.dev | `.continue/rules/<name>.md` |
| `aider` | Aider | `.aider/skills/<name>.md` |
| `cline` | Cline | `.clinerules/<name>.md` |
| `agents` | Universal AGENTS.md | append section with markers |
| `generic` | Portable SKILL.md | `skills/<name>/SKILL.md` |

```bash
skillport install commit --to all
```

---

## Built-in skills

| Name | Use when |
|------|----------|
| `pr-review` | Reviewing pull requests / diffs |
| `commit` | Writing conventional commit messages |
| `security-audit` | Pre-merge security pass |
| `docs-writer` | README / docs that convert readers |

```bash
skillport search
skillport install docs-writer --to claude,cursor
```

---

## Convert any skill

```bash
# Print Cursor rule to stdout
skillport convert ./skills/pr-review --to cursor

# Write file
skillport convert ./skills/pr-review --to copilot -o out/pr-review.md

# Validate first (great in CI)
skillport validate ./skills && echo OK
```

Canonical format is **[agentskills.io SKILL.md](https://agentskills.io/specification)** — YAML frontmatter + markdown body.

---

## Project layout after install

```text
your-repo/
├── .skillport.json
├── skillport.lock.json
├── .claude/skills/pr-review/SKILL.md
├── .cursor/rules/pr-review.mdc
└── .github/copilot-instructions/pr-review.md
```

Commit the generated tool files **or** commit only lockfile + sources and run `skillport sync` in CI/bootstrap — your choice.

---

## CI validation

```yaml
# .github/workflows/skills.yml
- name: Validate skills
  run: |
    pip install skillport
    skillport validate ./skills
```

---

## Create your own skill

```bash
skillport new invoice-parser --description "Extract invoice fields from PDFs"
skillport validate ./invoice-parser
skillport install ./invoice-parser --to claude,cursor
```

Minimal `SKILL.md`:

```markdown
---
name: invoice-parser
description: Extract invoice fields from PDFs and images for bookkeeping agents.
---

## Instructions

1. ...
```

---

## Design principles

1. **SKILL.md is the source of truth** — everything else is a projection.
2. **Zero daemon** — pure CLI, works offline for local skills.
3. **Safe by default** — won't overwrite without `--force`.
4. **CI-friendly** — `validate` exits non-zero on bad skills.
5. **Boring stack** — Python 3.9+, Click, Rich, PyYAML.

---

## Roadmap

- [ ] Official registry (`skillport publish` / search remote index)
- [ ] Bidirectional import (Cursor `.mdc` → SKILL.md)
- [ ] VS Code / JetBrains companion
- [ ] Skill versioning & signing
- [ ] Team policy packs (required skills per repo)

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Launch & star growth

If SkillPort saves you time, **star the repo** — it helps other devs discover a neutral skill layer instead of another walled garden.

Share your setup:

```bash
skillport doctor
```

Post your `skillport install ...` one-liners in Discussions.

---

## FAQ

**Is this affiliated with Anthropic / OpenAI / Cursor?**  
No. SkillPort is an independent open-source bridge implementing the public Agent Skills ideas and practical editor layouts.

**Will conversion be lossy?**  
Metadata that only exists in one ecosystem (e.g. Cursor `alwaysApply`) is preserved when present under `metadata` and best-effort mapped. Body instructions stay intact.

**Can I use it privately?**  
Yes. MIT licensed. Local paths never leave your machine. Remote install only runs when you pass a git URL.

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=pnt43624-alt/skillport&type=Date)](https://star-history.com/#pnt43624-alt/skillport&Date)

---

## License

[MIT](LICENSE) © SkillPort Contributors

---

<p align="center">
  <sub>Built for people who use more than one AI coding agent — which is everyone now.</sub>
</p>
