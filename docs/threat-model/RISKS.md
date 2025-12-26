# Risk Register

| Risk ID | Description | Flow / NFR | L | I | Risk | Strategy | Owner | Due date | Status | Closure criteria |
|---------|-------------|------------|---|---|------|----------|-------|----------|--------|------------------|
| R1 | API key intercepted during provisioning → attacker controls API. | F1, NFR-SC-3 | 2 | 5 | 10 | Reduce | Kirill (DevOps) | 2025-02-20 | Mitigated | Password manager policy + rotation script run (evidence in ops runbook). |
| R2 | Tampered secrets injected during deploy (e.g., rogue APP_API_KEY). | F2, NFR-SC-3, NFR-SDLC-1 | 2 | 5 | 10 | Reduce | Kirill (DevOps) | 2025-02-25 | In progress | GitHub OIDC → cloud secrets + alert on drift. |
| R3 | Invalid payload bypass corrupts domain state. | F3/F5, NFR-VAL-1 | 2 | 4 | 8 | Reduce | Danya (Backend) | 2025-02-18 | Mitigated | `tests/test_chores_assignments.py` merged, validators in place. |
| R4 | Lack of rate limiting enables DoS/bruteforce. | F3, NFR-DOS-1 | 3 | 3 | 9 | Reduce (quick win) | Alex (Backend) | 2025-02-28 | Open | `fastapi-limiter` enabled + negative test demonstrating 429. |
| R5 | Unauthorized direct DB writes (bypass owner checks). | F4/F5, NFR-SC-1 | 2 | 4 | 8 | Reduce | Danya (Backend) | 2025-02-22 | Mitigated | PR #45 enforcing owner checks + cascade delete tests. |
| R6 | `/stats` or support dashboards leak sensitive occupancy info. | F6/F10, NFR-SC-1, NFR-AU-1 | 2 | 3 | 6 | Reduce | Dana (PM) | 2025-02-24 | Planned | Product spec limits stats granularity + dashboard SSO role review. |
| R7 | Notification webhook used for SSRF / hanging connections. | F7, NFR-COM-1 | 3 | 3 | 9 | Reduce | Kirill (DevOps) | 2025-03-01 | Open | Allowlist + 2s timeout + DLQ verified in staging. |
| R8 | Fake callback marks chores complete (silent failure). | F8, NFR-COM-1, NFR-AU-1 | 2 | 4 | 8 | Reduce | Sam (Backend) | 2025-03-05 | Planned | CIDR allowlist + HMAC signature + audit log test. |
| R9 | Supply-chain attack via CI/CD/registry. | F11/F12, NFR-SDLC-1 | 2 | 5 | 10 | Reduce | Kirill (DevOps) | 2025-03-10 | Planned | Cosign signing + verify step in pipeline. |
| R10 | Logs/metrics leak PII or secrets. | F9, NFR-LOG-1 | 2 | 4 | 8 | Reduce | Support team | 2025-02-27 | Open | Log scrubber unit tests + manual spot-check; logging SOP signed. |
| R11 | Manual fallback list (F7a/F9a) loses audit trail. | F7a/F9a, NFR-AU-1 | 2 | 3 | 6 | Reduce | Support team lead | 2025-02-25 | In review | SOP update + weekly audit evidence stored in Confluence. |
