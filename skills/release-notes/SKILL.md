---
name: release-notes
description: Draft clear user-facing release notes from commits, PR titles, and issue labels. Use before tagging a release or writing a changelog blurb.
license: MIT
metadata:
  tags:
    - release
    - docs
    - git
---

## Goal

Tell users what changed and why they should care — not a git dump.

## Structure

```markdown
## Highlights
- ...

## New
- ...

## Improvements
- ...

## Fixes
- ...

## Breaking changes
- ...

## Upgrade notes
- ...
```

## Rules

- User voice, not engineer slang
- Group by impact
- Call out breaking changes first if severe
- Link issues/PRs when available
- Omit chore-only internal noise unless it affects users
