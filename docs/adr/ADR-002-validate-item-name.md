# ADR-002: Harden Item Name Validation

- Status: Accepted
- Date: 2025-10-23

## Context

- Threat TM-3 describes attempts to inject oversized or malicious strings into item names.
- NFR-SC-2 mandates strict validation and canonicalisation of user-supplied text.
- Current validation allows arbitrary query parameters and only checks string length, leaving room for whitespace abuse and special characters.

## Decision

- Switch `POST /items` to a Pydantic request model with explicit min/max length and an allow-list regex for safe characters.
- Canonicalise the name by trimming leading/trailing whitespace before persistence.
- Rely on FastAPI validation errors but normalise them into the unified error envelope.

## Consequences

- Requests with disallowed characters or empty values now fail fast with `422 validation_error`.
- Boundary cases (e.g. exactly 100 characters) remain permitted.
- Tests need to cover the new validation rules to prevent regressions.

## Links

- [P03 / NFR-SC-2](../nfr/P03-nfr.md#nfr-sc-2)
- [P04 / F3](../threat-model/P04-threat-model.md#f3)
- [P04 / R2](../threat-model/P04-threat-model.md#r2)
- Verification: [tests/test_items_validation.py](../../tests/test_items_validation.py#L1)
