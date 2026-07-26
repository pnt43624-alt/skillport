---
name: performance
description: Profile and optimize hot paths with measurements first. Use for latency, CPU, memory, or database slowdowns.
license: MIT
metadata:
  tags:
    - performance
    - quality
---

## Goal

Make it faster with evidence. No cargo-cult optimization.

## Process

1. Define the metric (p95 latency, allocs, query time) and budget.
2. Measure baseline with a realistic workload.
3. Find the dominant cost (profile, EXPLAIN, tracing).
4. Change the bottleneck only.
5. Re-measure; keep the win; discard noise.

## Common wins

- N+1 queries → batch/join
- Hot-path allocations → reuse buffers
- Sync I/O on request path → async/batch
- Unbounded caches → TTL/size limits
- Missing indexes / wrong cardinality

## Output

- Baseline numbers
- Top offenders
- Patch
- After numbers
- Tradeoffs
