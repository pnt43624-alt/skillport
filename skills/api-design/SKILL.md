---
name: api-design
description: Design clean REST or GraphQL APIs with consistent resource modeling, errors, pagination, and versioning. Use when adding or revising HTTP APIs.
license: MIT
metadata:
  tags:
    - api
    - design
---

## Goal

APIs that are boringly consistent, hard to misuse, and easy to evolve.

## Checklist

- Resources & nouns over RPC soup (unless truly actions)
- Consistent naming, pluralization, and path structure
- Error shape: machine `code`, human `message`, optional `details`
- Pagination: cursor preferred for large sets
- Idempotency for unsafe retries where needed
- Authn/z at the edge; never trust client-supplied ownership IDs alone
- Versioning strategy (path or header) stated explicitly
- OpenAPI/GraphQL schema as source of truth

## Output

1. Resource model
2. Endpoints / types
3. Error catalog
4. Example requests
5. Compatibility notes
