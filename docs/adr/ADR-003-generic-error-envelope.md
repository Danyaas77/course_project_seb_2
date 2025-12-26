# ADR-003: Hide Internal Exception Details

- Status: Accepted
- Date: 2025-10-23

## Context

- Threat TM-2 identifies that stack traces or raw exception messages can leak implementation insights.
- NFR-R-1 requires the service to avoid exposing internal error details.
- Currently, unhandled exceptions propagate through FastAPI defaults, returning verbose responses during failures.

## Decision

- Add a catch-all exception handler that logs internally (future enhancement) but always returns a generic `500` error envelope to callers.
- Ensure existing `ApiError` and `HTTPException` handlers continue to operate for expected scenarios.

## Consequences

- Attackers receive minimal information even when triggering unexpected failures.
- Operators rely on server-side logs for diagnostics; need to ensure logging captures stack traces (next step).
- Tests must assert that misconfigurations or runtime errors produce the sanitized response.

## Links

- [P03 / NFR-R-1](../nfr/P03-nfr.md#nfr-r-1)
- [P04 / F2](../threat-model/P04-threat-model.md#f2)
- [P04 / R3](../threat-model/P04-threat-model.md#r3)
- Verification: [tests/test_items_security.py](../../tests/test_items_security.py#L35)
