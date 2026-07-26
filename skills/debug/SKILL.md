---
name: debug
description: Systematic debugging to reproduce, isolate, hypothesize, fix, and verify failures. Use for bugs, flaky tests, crashes, and unexpected behavior.
license: MIT
metadata:
  tags:
    - debug
    - quality
---

## Goal

Find root cause quickly with a scientific loop — not random changes.

## Loop

1. **Reproduce** — minimal reliable steps; note environment.
2. **Observe** — exact error, logs, stack, inputs/outputs.
3. **Isolate** — binary search, bisect, disable subsystems.
4. **Hypothesize** — one theory at a time; predict what you'd see.
5. **Experiment** — smallest change or probe to confirm/deny.
6. **Fix** — address root cause, not only symptoms.
7. **Verify** — regression test + original repro fails closed.

## Anti-patterns

- Shotgun refactors while debugging
- "Works on my machine" without capturing env
- Fixing without a failing test when feasible

## Output

- Repro steps
- Root cause (with evidence)
- Fix
- Regression test
- Residual risk
