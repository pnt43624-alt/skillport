---
name: docs-writer
description: Turn messy notes or repos into crisp README and docs with problem statement, quickstart, examples, and pitfalls. Use when writing or rewriting documentation.
license: MIT
metadata:
  tags:
    - docs
    - writing
---

## Goal

Ship documentation that converts a cold visitor in under 30 seconds: clear problem, proof it works, copy-paste quickstart, real examples.

## README skeleton

1. **One-liner** — what it does + for whom
2. **Hero proof** — screenshot, GIF, or 5-line demo
3. **Install** — single obvious command
4. **Quickstart** — under 5 minutes to first success
5. **Why this exists** — pain it removes (not feature laundry list)
6. **Examples** — 3 concrete use cases
7. **Configuration** — table of important flags/env
8. **FAQ / pitfalls**
9. **Contributing + License**

## Style rules

- Lead with the user's pain, not the architecture.
- Prefer commands the reader can paste.
- Cut adjectives; keep verbs.
- Mark optional vs required clearly.
- Keep the first screen scannable on mobile.

## Process

1. Skim code/entrypoints for the true UX (CLI flags, imports).
2. Draft the one-liner and quickstart first.
3. Add examples from real workflows.
4. Delete anything that doesn't help someone succeed or decide.
