# P04 — Threat Model Highlights

## Findings

<a id="f1"></a>
### F1 — Unauthenticated mutation attempts
- Impact: Unauthorized data creation/modification via `POST /items`.
- Exploit path: Callers script requests without credentials.

<a id="f2"></a>
### F2 — Error detail leakage
- Impact: Information disclosure enables targeted exploits.
- Exploit path: Trigger unhandled exceptions to surface stack traces.

<a id="f3"></a>
### F3 — Malicious item names
- Impact: Stored XSS or resource exhaustion due to oversized payloads.
- Exploit path: Submit crafted names with HTML/JS or excessive length.

<a id="f4"></a>
### F4 — Unsafe file uploads
- Impact: Path traversal or oversized payloads can lead to arbitrary file writes or DoS.
- Exploit path: Upload crafted filenames like `../../etc/passwd` or large bodies without validation.

<a id="f5"></a>
### F5 — Outbound webhook abuse
- Impact: SSRF or hung connections when calling external endpoints without allowlist or timeouts.
- Exploit path: Point webhook URL to attacker-controlled host or slow endpoint, exhausting workers.

## Responses

<a id="r1"></a>
### R1 — Enforce API key on mutations
- Mitigates: F1
- References: ADR-001, tests/test_items_security.py

<a id="r2"></a>
### R2 — Normalize request validation
- Mitigates: F3
- References: ADR-002, tests/test_items_validation.py

<a id="r3"></a>
### R3 — Sanitize unhandled errors
- Mitigates: F2
- References: ADR-003, ADR-005, tests/test_items_security.py, tests/test_errors.py

<a id="r4"></a>
### R4 — Validate uploads at the edge
- Mitigates: F4
- References: ADR-004, tests/test_uploads.py

<a id="r5"></a>
### R5 — Enforce webhook client policies
- Mitigates: F5
- References: ADR-006, tests/test_webhooks.py

Last updated: 2025-10-23.
