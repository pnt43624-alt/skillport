---
name: dependency-audit
description: Review dependencies for security risk, bloat, license issues, and upgrade strategy. Use when adding packages or doing periodic audits.
license: MIT
metadata:
  tags:
    - security
    - deps
---

## Goal

Know what you ship: risk, size, license, and maintainership.

## Checklist

- Why is this dependency needed? Can stdlib/existing code replace it?
- Maintainer health (recent commits, bus factor)
- Known CVEs / advisories
- Transitive tree size and duplicates
- License compatibility with the project
- Pinning / lockfile policy
- Supply-chain signals (install scripts, typosquat names)

## Output table

| Package | Why | Risk | License | Action |
|---------|-----|------|---------|--------|

Actions: keep / replace / remove / upgrade / vendor
