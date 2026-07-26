---
name: sql-review
description: Review SQL for correctness, injection safety, indexes, and execution-plan hazards. Use when writing or reviewing queries and migrations.
license: MIT
metadata:
  tags:
    - sql
    - data
    - review
---

## Goal

Correct, safe, and operable SQL.

## Checklist

- Parameterized queries only (no string-concat user input)
- Correct joins and grain (no fan-out duplicates)
- NULL semantics understood
- Indexes match filter/join/order patterns
- Migrations reversible or explicitly gated
- Locks / long transactions considered
- EXPLAIN (ANALYZE) on realistic data when performance-sensitive
- Least-privilege DB roles

## Output

- Findings by severity
- Rewritten SQL when helpful
- Index suggestions
- Test cases (including empty/NULL edge cases)
