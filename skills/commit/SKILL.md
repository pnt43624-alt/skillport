---
name: commit
description: Write conventional, high-signal git commit messages from a staged diff. Use when the user asks to commit, draft a commit message, or summarize changes.
license: MIT
metadata:
  tags:
    - git
    - commit
---

## Goal

Create a commit message that future-you can skim in `git log` and understand *why* the change exists.

## Format

```
<type>(<optional-scope>): <imperative summary ≤72 chars>

<body: what changed and why, wrap ~72 cols>

<footer: BREAKING CHANGE / Fixes #123 if needed>
```

### Types

`feat` `fix` `docs` `style` `refactor` `perf` `test` `build` `ci` `chore` `revert`

## Process

1. Inspect the staged diff (prefer `git diff --cached`).
2. Infer the **primary intent** (one commit = one intent).
3. If the diff mixes unrelated concerns, recommend a split.
4. Draft summary in **imperative mood** ("add", not "added").
5. Body explains **why**, not a file laundry list.
6. Never invent ticket IDs or co-authors.

## Examples

```
fix(auth): reject expired refresh tokens

Tokens past `exp` were accepted when clock skew compensation
ran after signature checks. Validate expiry before use.
```

```
feat(api): add cursor pagination to /v1/items
```

## Output

Return **only** the final commit message in a fenced code block, unless the user asks for rationale.
