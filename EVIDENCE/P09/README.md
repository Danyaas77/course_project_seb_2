# P09 evidence layout

- `sbom.json` — CycloneDX SBOM, генерируется Syft внутри workflow `.github/workflows/ci-sbom-sca.yml`.
- `sca_report.json` — отчёт Grype по SBOM.
- `sca_summary.md` — агрегированная сводка по severity, формируется через `jq`.

Файлы перезаписываются на каждом прогоне `Security - SBOM & SCA` и загружаются артефактом `P09_EVIDENCE-${GITHUB_SHA}`. Используйте эти артефакты для DS-раздела итогового отчёта и для триажа уязвимостей (обновление зависимостей или waivers).
