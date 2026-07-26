# Changelog

## 0.2.0 — 2026-07-26

### Added
- **16 built-in skills** (was 4): test-writer, refactor, debug, api-design, release-notes, changelog, code-explain, performance, dependency-audit, incident-response, sql-review, prompt-engineer
- **Skill packs**: essentials, security, shipping, quality, ops, all (`skillport install pack:essentials`)
- **Bidirectional convert/import**: Cursor `.mdc` and markdown rules → SKILL.md
- **New targets**: Zed, JetBrains AI, OpenCode (13 total)
- Commands: `uninstall`, `import`, `packs`, `info`, `show`, `diff`, `registry`
- `validate --strict` warnings, `--json` on search/list/validate
- `doctor --fix` and lockfile drift detection
- `install --dry-run`
- `registry/index.json` generator
- Expanded test suite (18 tests)

### Improved
- Safer Cursor frontmatter rendering via YAML dump
- Import prefers H1 title as canonical skill name
- Init installs full essentials pack by default
- README rewritten as product landing page

## 0.1.0 — 2026-07-26

### Added
- Initial public release
- CLI: init, install, convert, validate, search, list, sync, doctor, new, tools
- Adapters for Claude, Cursor, Codex, Copilot, Windsurf, Continue, Aider, Cline, AGENTS.md
- Built-in skills: pr-review, commit, security-audit, docs-writer
