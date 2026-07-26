---
name: security-audit
description: Threat-model and audit code for OWASP-style issues, secrets, auth bugs, and unsafe defaults before merge or release.
license: MIT
metadata:
  tags:
    - security
    - audit
---

## Goal

Find exploitable or high-impact security issues quickly, with clear severity and remediation.

## Checklist (adapt to stack)

1. **Secrets & config** — hardcoded keys, tokens in logs, insecure defaults
2. **AuthN / AuthZ** — missing checks, IDOR, privilege escalation, JWT misuse
3. **Injection** — SQL/NoSQL/command/template/path traversal
4. **XSS / CSRF / SSRF** — especially on user-controlled URLs and HTML
5. **Deserialization / file upload** — untrusted data execution
6. **Crypto** — weak algorithms, homemade crypto, improper randomness
7. **Dependencies** — obviously dangerous packages / outdated critical libs
8. **Multi-tenant isolation** — data bleed across orgs/users
9. **Supply chain** — install scripts, CI secrets, artifact integrity

## Output format

| ID | Severity | Location | Issue | Exploit sketch | Fix |
|----|----------|----------|-------|----------------|-----|
| S1 | Critical/High/Med/Low | path | ... | ... | ... |

Then:

- **Threat model notes** (assets, attackers, trust boundaries)
- **Residual risk** if fixes are deferred
- **Test plan** to prove each fix

## Rules

- Prefer **demonstrable** issues over theoretical noise.
- Mark confidence: confirmed / likely / needs-repro.
- Do not claim a full formal audit unless scope was exhaustive.
- Never print live secrets; redact and point to location only.
