# ADR-005: RFC7807 Error Envelope and Correlation IDs

- Status: Accepted
- Date: 2025-12-26

## Context
- Default FastAPI errors mixed response shapes and sometimes echoed upstream exception details, conflicting with P03/NFR-R-1.
- Incident investigations lacked a consistent correlation identifier; clients could not easily align server logs with responses (P03/NFR-ERR-1).
- Threat model F2 calls for masking internals while still providing actionable, standardized error metadata.

## Decision
- Introduce middleware that propagates an incoming `X-Correlation-ID` or generates one, attaching it to responses and problem payloads.
- Normalize error construction to RFC 7807 fields with `timestamp` and `instance`, deriving `type` from error codes when none is provided.
- Mask `HTTPException` details with a generic message and always return `application/problem+json` for error handlers.
- Keep validation errors compact (`field`, `message`) while preserving the unified envelope for tracing.

## Alternatives
- Keep FastAPI defaults and rely on server logs — rejected because response shapes and leakage risks remain.
- Adopt a custom trace-id header separate from correlation IDs — deferred until distributed tracing is introduced.
- Push correlation entirely to clients — rejected; server-generated IDs are needed for unauthenticated or legacy callers.

## Consequences
- Clients must be ready for the stricter, uniform envelope and the `X-Correlation-ID` header.
- Reduced verbosity can slow ad-hoc debugging if server-side logging is missing; observability must capture correlation IDs.

## Security impact
- Reduces information disclosure for F2 while improving traceability across logs and client reports.

## Rollout plan
- Update client integrations and monitoring dashboards to surface `X-Correlation-ID`.
- Document the error contract for integrators; ensure server logs include the correlation ID for 4xx/5xx paths.

## Links
- NFR: [P03 / NFR-ERR-1](../nfr/P03-nfr.md#nfr-err-1), [P03 / NFR-R-1](../nfr/P03-nfr.md#nfr-r-1)
- Threats: [P04 / F2](../threat-model/P04-threat-model.md#f2), [P04 / R3](../threat-model/P04-threat-model.md#r3)
- Verification: [tests/test_errors.py](../../tests/test_errors.py), [tests/test_items_security.py](../../tests/test_items_security.py)
