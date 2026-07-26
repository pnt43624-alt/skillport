---
name: code-explain
description: Explain complex code paths in plain language with structure, invariants, and diagrams when useful. Use for onboarding, reviews, or understanding legacy code.
license: MIT
metadata:
  tags:
    - docs
    - learning
---

## Goal

Make non-obvious code understandable in minutes.

## Format

1. **One-liner** — what this module does
2. **Entry points** — how control gets here
3. **Core flow** — step sequence
4. **Invariants** — what must always be true
5. **Data shapes** — key types/fields
6. **Failure modes**
7. **Ascii/mermaid diagram** if control flow branches

## Rules

- Prefer precise names over metaphors
- Quote small code anchors (symbols), not huge dumps
- Call out footguns explicitly
