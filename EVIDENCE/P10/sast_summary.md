P10 SAST & secrets summary (2025-12-08)

- Tools: Semgrep (`p/ci` + `security/semgrep/rules.yml`) and Gitleaks (`security/.gitleaks.toml`) run locally via Docker; artifacts saved to `EVIDENCE/P10/semgrep.sarif` and `EVIDENCE/P10/gitleaks.json`.
- Semgrep: 0 findings (High 0 / Medium 0 / Low 0). Custom rule confirmed all FastAPI endpoints except `/health` enforce `Depends(require_api_key)`, and no HTTP calls disable TLS verification.
- Gitleaks: 0 leaks. Allowlist documents fixture values `test-secret` and `notif-secret` to avoid false positives from tests; no real secrets detected.
- Critical secrets policy: APP_API_KEY, NOTIFY_TOKEN, webhook URLs, storage/db creds are treated as high priority; rotate and revoke on detection, add allowlists only for documented test data with justification.
- CI: `.github/workflows/ci-sast-secrets.yml` publishes the reports on push/PR/workflow_dispatch; results feed into DS/PR notes and can be uploaded to GitHub code scanning SARIF if enabled later.
