P12 evidence for IaC and container scanning.

- Workflow: `.github/workflows/ci-p12-iac-container.yml`
- Tools: Hadolint (Dockerfile), Checkov (IaC), Trivy (built image `app:local`).
- Reports written by the workflow:
  - `hadolint_report.json`
  - `checkov_report.json`
  - `trivy_report.json`

Re-run the workflow to refresh the reports before merging.
