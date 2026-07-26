---
name: changelog
description: Maintain Keep-a-Changelog and semver-oriented CHANGELOG entries from git history. Use when preparing versions or backfilling history.
license: MIT
metadata:
  tags:
    - release
    - docs
    - git
---

## Goal

A CHANGELOG humans trust: [Unreleased] + versioned sections following Keep a Changelog.

## Categories

Added, Changed, Deprecated, Removed, Fixed, Security

## Process

1. Read commits/PRs since last tag.
2. Classify each user-visible change.
3. Rewrite into concise bullets.
4. Bump section for the version being cut.
5. Leave [Unreleased] empty after release.

## Example bullet

- Fixed refresh tokens being accepted after expiry under clock-skew compensation.
