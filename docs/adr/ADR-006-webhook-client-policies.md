# ADR-006: Webhook Client Allowlist and Timeouts

- Status: Accepted
- Date: 2025-12-26

## Context
- Assignment completions should notify external systems, but unbounded outbound calls risk SSRF and resource exhaustion (P04/F5).
- P03/NFR-COM-1 mandates host allowlists, short timeouts, and error masking for outbound notifications.
- Current code lacked any outbound client; assignment updates could hang indefinitely or call attacker-controlled hosts.

## Decision
- Introduce `SafeHttpClient` that enforces HTTP/HTTPS schemes, host allowlists, configurable timeouts (default 2s), and bounded retries; supports injected transport for offline tests.
- When an assignment transitions to `completed`, call the `ASSIGNMENT_WEBHOOK_URL` (if configured) using `SafeHttpClient`; include assignment identifiers in the JSON payload.
- Surface failures as RFC 7807 (`webhook_failed`, 502) and block disallowed hosts with 400 without mutating assignment state.
- Configure allowlist via `ASSIGNMENT_WEBHOOK_ALLOWLIST` (hostnames) with per-deployment timeout/retry overrides.

## Alternatives
- Fire-and-forget background tasks without allowlists — rejected due to SSRF and observability gaps.
- Queue-based delivery with workers — deferred; adds infrastructure overhead for the current scope.
- Ignore webhook failures and always persist status — rejected to avoid silent drops and false positives.

## Consequences
- Assignment completion can fail if the webhook host is unreachable or misconfigured; clients must handle 4xx/502 results.
- Additional configuration (URL, allowlist, retries) is required per environment; missing config simply skips notifications.

## Security impact
- Mitigates F5 by constraining egress hosts and runtime; residual risk includes malicious webhook responses and lack of request signing (future work).

## Rollout plan
- Set `ASSIGNMENT_WEBHOOK_URL` and matching allowlist per environment; keep retries low to avoid cascading failures.
- Monitor `webhook_failed` responses; consider alerting and adding signing/verification in a follow-up change.

## Links
- NFR: [P03 / NFR-COM-1](../nfr/P03-nfr.md#nfr-com-1)
- Threats: [P04 / F5](../threat-model/P04-threat-model.md#f5), [P04 / R5](../threat-model/P04-threat-model.md#r5)
- Verification: [tests/test_webhooks.py](../../tests/test_webhooks.py)
