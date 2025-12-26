P10 SAST & secrets summary (2025-12-23)

- Tools: Semgrep 1.146.0 (`p/ci` + `security/semgrep/rules.yml`) and Gitleaks 8.18.4 (`security/.gitleaks.toml`); artifacts saved to `EVIDENCE/P10/semgrep.sarif` and `EVIDENCE/P10/gitleaks.json`.
- Semgrep: 0 findings (High 0 / Medium 0 / Low 0). Custom FastAPI auth/TLS rules passed: every endpoint except `/health` enforces `Depends(require_api_key)` and no HTTP clients disable TLS verification.
- Gitleaks: 0 leaks. Allowlist keeps known fixture values `test-secret` and `notif-secret` in `tests/**` from blocking scans; nothing detected outside the allowlist.
- CI: `.github/workflows/ci-sast-secrets.yml` runs on push/PR/workflow_dispatch with concurrency; uploads `P10_EVIDENCE-*` artifacts for traceability.
- Follow-up: keep API/notify tokens rotated in CI secrets, expand SARIF upload to GitHub Code Scanning if needed.
