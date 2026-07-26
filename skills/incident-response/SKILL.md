---
name: incident-response
description: Run an engineering incident from triage through mitigation, communication, and postmortem. Use during outages or severe production defects.
license: MIT
metadata:
  tags:
    - ops
    - incident
---

## Goal

Restore service safely, communicate clearly, learn afterward.

## Roles

- Incident lead (decides)
- Comms (status updates)
- Ops/scribe (timeline)

## Phases

1. **Detect & declare** — severity, channels, lead
2. **Triage** — blast radius, user impact, recent changes
3. **Mitigate** — rollback, feature flag, scale, failover (prefer reversible)
4. **Stabilize** — confirm metrics/user reports
5. **Follow-up** — postmortem with action items and owners

## Comms template

- What happened (user impact)
- What we know / don't know
- What we're doing next
- Next update time

## Postmortem rules

Blameless. Facts, timeline, contributing factors, action items with due dates.
