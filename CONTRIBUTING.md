# Contributing to SkillPort

Thanks for helping build a neutral skill layer for AI coding agents.

## Dev setup

```bash
git clone https://github.com/pnt43624-alt/skillport.git
cd skillport
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## Project layout

```text
skillport/          # CLI + library
skills/             # built-in catalog skills
tests/              # pytest
```

## Guidelines

1. **SKILL.md remains canonical** — adapters project outward; don't invent a second source format.
2. Keep the CLI fast and dependency-light.
3. Add tests for every new adapter or validation rule.
4. Run `skillport validate ./skills` before opening a PR.
5. Use conventional commits (`feat:`, `fix:`, `docs:`).

## Adding a tool adapter

1. Register layout in `skillport/adapters.py` → `TOOL_LAYOUTS`.
2. Implement / reuse a renderer (`skill_md`, `cursor_mdc`, `agents_md`, ...).
3. Cover with a unit test in `tests/test_core.py`.
4. Document the tool in `README.md`.

## Adding a built-in skill

1. Create `skills/<name>/SKILL.md` following [agentskills.io](https://agentskills.io/specification).
2. Register it in `BUILTIN_CATALOG` inside `skillport/registry.py`.
3. Ensure `skillport validate ./skills` passes.

## PR checklist

- [ ] `pytest` green
- [ ] `skillport validate ./skills` green
- [ ] Docs updated if UX changed
- [ ] No secrets in fixtures

## Code of conduct

Be respectful. Assume good intent. No harassment.
