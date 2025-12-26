# ADR-001: Require API Key For Mutating Endpoints

- Status: Accepted
- Date: 2025-10-23

## Context

- Threat TM-1 from P04 highlights that anonymous callers can modify inventory data.
- NFR-SC-1 from P03 requires authentication for mutating API actions.
- The current `POST /items` endpoint allows unauthenticated writes, making exploitation trivial.

## Decision

- Introduce a lightweight API key check for state-changing endpoints.
- Expect callers to send `X-API-Key`; compare it with the configured secret using constant-time comparison.
- Treat missing configuration as a hard error to avoid accidentally exposing the endpoint.

## Consequences

- Additional deployment step: operators must configure `APP_API_KEY`.
- Legitimate clients need to update to include the header.
- Unauthorized or misconfigured requests receive a deterministic `401` error envelope instead of executing the handler.

## Links

- [P03 / NFR-SC-1](../nfr/P03-nfr.md#nfr-sc-1)
- [P04 / F1](../threat-model/P04-threat-model.md#f1)
- [P04 / R1](../threat-model/P04-threat-model.md#r1)
- Verification: [tests/test_items_security.py](../../tests/test_items_security.py#L16)
