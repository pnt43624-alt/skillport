# Launch playbook — get SkillPort to GitHub Trending

SkillPort is positioned for the **2026 agent-skills wave** (Claude Skills, Cursor rules, Codex, AGENTS.md). Stars come from distribution + a sharp README, not luck.

## Day 0 (today)

- [x] Public repo with working CLI + tests
- [ ] Star your own repo
- [ ] Pin the repo on your GitHub profile
- [ ] Add topics on GitHub UI: `ai`, `agents`, `claude-code`, `cursor`, `skills`, `cli`, `developer-tools`, `agentskills`, `llm`, `copilot`
- [ ] Enable Discussions
- [ ] Move `docs/ci.github-actions.yml` → `.github/workflows/ci.yml` (needs `workflow` scope on the GitHub token / app)
- [ ] Delete `HELLO.md` leftover probe file
- [ ] Publish to TestPyPI / PyPI when ready: `python -m build && twine upload dist/*`

## Day 1 — Show HN + Reddit (Tue–Thu, morning US time)

**Show HN title ideas:**
- Show HN: SkillPort – install AI agent skills once, run on Claude/Cursor/Codex/Copilot
- Show HN: One CLI to sync SKILL.md across every AI coding agent

**Post body skeleton:**
1. Pain (skills fragmented across tools)
2. One command demo
3. Link + what you want feedback on

**Subreddits (read rules first):** r/LocalLLaMA, r/ChatGPTCoding, r/cursor, r/ClaudeAI, r/commandline, r/Python, r/selfhosted (if self-host angle)

## Day 1–3 — Awesome lists (passive stars)

Open PRs to:
- awesome-claude-code / awesome-claude-skills style lists
- awesome-cursor
- awesome-ai-agents
- sindresorhus/awesome (only if it fits a child list first)

## Evergreen

- Reply to every issue < 24h
- Ship a skill pack weekly
- Write 1 Dev.to / blog: "I was tired of rewriting the same Cursor rule for Claude Code"
- Short demo video (30–45s) for X/LinkedIn

## Honest note

Nobody can guarantee stars. Repos that compound usually: solve a real multi-tool pain, install in <60s, and show up where developers already complain about the pain.
