---
name: prompt-engineer
description: Craft robust system and user prompts, tool instructions, and lightweight evals for LLM features. Use when building AI products or agent behaviors.
license: MIT
metadata:
  tags:
    - ai
    - prompts
---

## Goal

Prompts that are specific, testable, and resistant to jailbreaks/drift.

## Structure

1. Role & objective
2. Hard constraints / safety
3. Input contract
4. Output contract (schema/format)
5. Few-shot examples (edge cases)
6. Failure behavior when uncertain

## Practices

- Prefer procedures over vibes
- Put invariants in system/developer messages
- Separate untrusted user content clearly
- Define tool-use policies
- Add eval set: 10–30 cases with expected traits
- Version prompts like code

## Output

- Final prompt(s)
- Example I/O
- Eval cases
- Known failure modes
