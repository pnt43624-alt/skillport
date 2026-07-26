<p align="center">
  <img src="assets/banner.svg" alt="SkillPort" width="100%" />
</p>

<h1 align="center">SkillPort</h1>

<p align="center">
  <strong>The package manager for AI agent skills.</strong><br/>
  Install once → run on Claude Code, Cursor, Codex, Copilot, Windsurf, Zed, JetBrains, Cline, Continue, Aider, OpenCode & AGENTS.md
</p>

<p align="center">
  <img alt="version" src="https://img.shields.io/badge/version-0.2.0-0ea5e9?style=flat-square" />
  <a href="LICENSE"><img alt="MIT" src="https://img.shields.io/badge/license-MIT-green?style=flat-square" /></a>
  <a href="https://agentskills.io"><img alt="agentskills" src="https://img.shields.io/badge/spec-agentskills.io-8b5cf6?style=flat-square" /></a>
  <img alt="python" src="https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square" />
  <img alt="skills" src="https://img.shields.io/badge/builtin_skills-16-f59e0b?style=flat-square" />
  <img alt="tools" src="https://img.shields.io/badge/targets-13-10b981?style=flat-square" />
  <img alt="tests" src="https://img.shields.io/badge/tests-18_passed-22c55e?style=flat-square" />
</p>

<p align="center">
  <a href="#quickstart">Quickstart</a> ·
  <a href="#why-skillport">Why</a> ·
  <a href="#commands">Commands</a> ·
  <a href="#skill-packs">Packs</a> ·
  <a href="#built-in-skills">Skills</a> ·
  <a href="#bidirectional-convert">Convert</a> ·
  <a href="#launch">Launch</a>
</p>

---

## The problem

Every AI coding tool stores “skills” differently:

| Tool | Path | Format |
|------|------|--------|
| Claude Code | `.claude/skills/<name>/SKILL.md` | Agent Skills |
| Cursor | `.cursor/rules/<name>.mdc` | MDC |
| Codex | `.codex/skills/...` | SKILL.md |
| Copilot / Windsurf / Cline / … | each different | freeform MD |

Teams rewrite the same prompt 6 times. It drifts. Reviews get worse.

## The fix

```bash
pip install skillport   # or: pip install -e . from source
skillport install pack:essentials --to claude,cursor,codex,copilot
```

**One canonical `SKILL.md` → every tool you actually use.**

---

## Quickstart

```bash
# from source
git clone https://github.com/pnt43624-alt/skillport.git
cd skillport
pip install -e ".[dev]"

skillport tools
skillport packs
skillport search review
skillport install pack:essentials --to claude,cursor
skillport doctor
```

Scaffold a repo:

```bash
cd your-project
skillport init --tools claude,cursor --pack essentials
```

---

## Why SkillPort?

| Capability | v0.2 |
|------------|------|
| Targets | **13** (Claude, Cursor, Codex, Copilot, Windsurf, Continue, Aider, Cline, Zed, JetBrains, OpenCode, AGENTS.md, generic) |
| Built-in skills | **16** production-ready |
| Packs | essentials, security, shipping, quality, ops, all |
| Convert | **bidirectional** (SKILL.md ↔ Cursor `.mdc` ↔ markdown rules) |
| Validate | agentskills.io + warnings (`--strict`) |
| Lockfile | `skillport.lock.json` + `sync` / `uninstall` |
| Registry | `registry/index.json` + `skillport registry` |
| DX | `doctor --fix`, `diff`, `show`, `info`, JSON output |

---

## Commands

| Command | Purpose |
|---------|---------|
| `skillport tools` | List targets + install paths |
| `skillport packs` | List skill packs |
| `skillport search [q]` | Search catalog / packs / registry |
| `skillport info <name>` | Metadata + preview |
| `skillport init` | Config + starter pack |
| `skillport install <src>` | Builtin, `pack:`, path, `owner/repo`, git URL |
| `skillport uninstall <name>` | Remove projections + lock entry |
| `skillport convert <src> --to <tool>` | Bidirectional convert |
| `skillport import <file> -o <dir>` | Cursor/md → SKILL.md |
| `skillport validate [path]` | Spec validation (CI) |
| `skillport list` | Installed skills |
| `skillport sync` | Re-apply lockfile |
| `skillport doctor [--fix]` | Health + drift |
| `skillport new <name>` | Scaffold skill |
| `skillport show <src>` | Print canonical SKILL.md |
| `skillport diff <a> <b>` | Unified diff two skills |
| `skillport registry` | Build/fetch registry index |

Alias: `sp`.

---

## Skill packs

```bash
skillport install pack:essentials --to claude,cursor
skillport install pack:security --to all
skillport install pack:shipping --to claude,copilot
```

| Pack | Skills |
|------|--------|
| **essentials** | pr-review, commit, test-writer, debug, docs-writer |
| **security** | security-audit, dependency-audit, sql-review |
| **shipping** | pr-review, test-writer, release-notes, changelog, docs-writer |
| **quality** | refactor, performance, api-design, code-explain, test-writer |
| **ops** | incident-response, performance, security-audit |
| **all** | every built-in skill |

---

## Built-in skills (16)

`pr-review` · `commit` · `security-audit` · `docs-writer` · `test-writer` · `refactor` · `debug` · `api-design` · `release-notes` · `changelog` · `code-explain` · `performance` · `dependency-audit` · `incident-response` · `sql-review` · `prompt-engineer`

```bash
skillport search
skillport show debug
skillport install prompt-engineer --to claude,cursor
```

---

## Bidirectional convert

```bash
# Agent Skill → Cursor rule
skillport convert ./skills/pr-review --to cursor -o .cursor/rules/pr-review.mdc

# Cursor rule → Agent Skill
skillport import .cursor/rules/pr-review.mdc -o ./skills/pr-review

# Skill → Copilot / Zed / JetBrains / AGENTS.md
skillport convert pr-review --to copilot -o out/
skillport convert pr-review --to zed -o out/
skillport install pr-review --to agents
```

Canonical format: **[agentskills.io SKILL.md](https://agentskills.io/specification)**.

---

## Supported tools (13)

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
| `zed` | Zed | `.rules/<name>.md` |
| `jetbrains` | JetBrains AI | `.aiassistant/rules/<name>.md` |
| `opencode` | OpenCode | `.opencode/skills/<name>/SKILL.md` |
| `agents` | AGENTS.md | marked sections |
| `generic` | Portable | `skills/<name>/SKILL.md` |

---

## CI

```yaml
- run: pip install skillport
- run: skillport validate ./skills --strict
```

Template (if Actions workflow scope is limited): [`docs/ci.github-actions.yml`](docs/ci.github-actions.yml)

---

## Project files after install

```text
your-repo/
├── .skillport.json
├── skillport.lock.json
├── .claude/skills/pr-review/SKILL.md
├── .cursor/rules/pr-review.mdc
└── .github/copilot-instructions/pr-review.md
```

---

## Create a skill

```bash
skillport new invoice-parser --description "Extract invoice fields from PDFs" --tag finance
skillport validate ./invoice-parser
skillport install ./invoice-parser --to claude,cursor
```

---

## Design principles

1. **SKILL.md is source of truth** — everything else is a projection  
2. **Zero daemon** — pure CLI, offline for local skills  
3. **Safe default** — no overwrite without `--force`  
4. **CI-friendly** — non-zero exit on invalid skills  
5. **Boring stack** — Python 3.9+, Click, Rich, PyYAML  

---

## Roadmap

- [x] Bidirectional Cursor import  
- [x] Skill packs  
- [x] Registry index  
- [x] Uninstall + doctor drift  
- [x] Zed / JetBrains / OpenCode targets  
- [ ] Hosted community registry  
- [ ] `skillport publish`  
- [ ] Skill versioning & signing  
- [ ] VS Code companion  

See [Issues](https://github.com/pnt43624-alt/skillport/issues) and [docs/LAUNCH.md](docs/LAUNCH.md).

---

## Launch

Star the repo if this saves you time. Distribution playbook: **[docs/LAUNCH.md](docs/LAUNCH.md)**.

```text
Show HN: SkillPort – npm for AI agent skills (Claude/Cursor/Codex/Copilot)
```

---

## License

[MIT](LICENSE) © SkillPort Contributors

<p align="center"><sub>Built for people who use more than one AI coding agent.</sub></p>
