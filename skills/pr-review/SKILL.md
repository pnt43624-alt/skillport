---
name: pr-review
description: Structured pull-request review covering correctness, security, tests, API design, and clarity. Use when reviewing diffs, PRs, or pre-merge changes.
license: MIT
metadata:
  tags:
    - git
    - review
    - quality
  globs: "**/*"
---

## Goal

Produce a high-signal PR review a senior engineer would respect: specific, actionable, severity-ranked, and free of nitpick noise.

## Workflow

1. **Summarize the change in 2–4 bullets** (what / why / risk surface).
2. **Scan for blockers first**:
   - correctness bugs, race conditions, data loss
   - authz/authn gaps, injection, secret leakage
   - breaking API / migration hazards
   - missing tests for critical paths
3. **Then review design**: naming, boundaries, complexity, observability.
4. **Only then** style nits (group them; don't dominate the review).

## Output format

```markdown
## Summary
...

## Blocking
- [ ] file:line — issue — why it matters — suggested fix

## Should fix
- [ ] ...

## Nits
- ...

## Tests to add
- ...

## Verdict
Approve | Request changes | Comment-only
```

## Rules

- Cite `path` + approximate location for every finding.
- Prefer patches / concrete code suggestions over vague advice.
- If you lack context, say what you need instead of guessing.
- Separate **blocking** from **nice-to-have**.
- Call out what was done *well* (1–3 points) so authors keep good patterns.
