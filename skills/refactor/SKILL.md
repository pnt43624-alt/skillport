---
name: refactor
description: Plan and apply safe, incremental refactors that improve design without changing external behavior. Use when cleaning structure, reducing duplication, or preparing for a feature.
license: MIT
metadata:
  tags:
    - refactor
    - quality
---

## Goal

Improve internal structure while preserving behavior. Prove safety with tests.

## Rules

1. No behavior change unless explicitly requested.
2. Prefer small vertical slices over big-bang rewrites.
3. Keep the build green after each step.
4. Rename with tooling when possible.
5. Delete dead code only when sure (or behind a flag).

## Process

1. Characterize current behavior (tests or manual checklist).
2. Identify the design smell (coupling, duplication, layering).
3. Propose a step plan (3–8 steps max).
4. Execute step 1 with minimal diff.
5. Re-run tests; repeat.

## Output format

- Smell diagnosis
- Step plan
- First patch (complete)
- Risk notes / rollback
