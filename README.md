# Roommate Chores Tracker

![CI](https://github.com/hse-secdev-2025-fall/course-project-Danyaas77/actions/workflows/ci.yml/badge.svg)

Трекер домашних дел между участниками квартиры. Доменная модель:

- `User`
- `Chore (title, cadence)`
- `Assignment (user_id, due_at, status)`

API покрывает CRUD для `/chores` и `/assignments`, а также `GET /stats`. Аутентификация построена на API-ключе (`X-API-Key`), владелец может управлять ресурсами, остальные операции проходят в соответствии с проверками доступа.

## Требования

- Python 3.11+
- SQLite (по умолчанию) или подключение к Postgres через переменные окружения

## Подготовка окружения

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt || true
pip install ruff black isort pytest pre-commit
pre-commit install
```

### Конфигурация

- `APP_API_KEY` — обязательный API-ключ для всех защищённых запросов.
- `ATTACHMENTS_DIR` — каталог для безопасного хранения вложений (по умолчанию `./attachments`, создаётся автоматически).
- `NOTIFY_WEBHOOK_URL` — HTTPS-эндпойнт, куда отправляются уведомления о назначениях.
- `NOTIFY_ALLOWED_HOSTS` — список доменов через запятую; запросы к другим хостам блокируются.
- `NOTIFY_TOKEN` — опциональный Bearer-токен для аутентификации при вызове вебхука.

## Запуск приложения

1. Выставите API-ключ, который понадобится каждому запросу:

   ```bash
   export APP_API_KEY=super-secret-key
   ```

2. Поднимите FastAPI-приложение:

   ```bash
   uvicorn app.main:app --reload
   ```

3. Проверьте, что приложение откликается:

   ```bash
   curl -H "X-API-Key: $APP_API_KEY" http://127.0.0.1:8000/health
   ```

Контейнерный запуск доступен через `docker compose up --build` (используется `Dockerfile` и `compose.yaml`).

## Тесты

```bash
pytest -q
```

## Эндпойнты

- `GET /health` — проверка статуса сервиса.
- `POST /users`, `GET /users` — управление участниками квартиры.
- `POST /chores`, `GET /chores`, `GET /chores/{id}`, `PUT /chores/{id}`, `DELETE /chores/{id}` — CRUD по задачам с валидацией `cadence`.
- `POST /assignments`, `GET /assignments?status=pending|completed|skipped`, `PATCH /assignments/{id}` — назначение задач соседям и обновление статусов.
- `POST /chores/{id}/attachments` — безопасная загрузка изображений (PNG/JPEG, описание работы подтверждено тестами).
- `POST /assignments/{id}/notify` — отправка уведомлений во внешний вебхук с allowlist хостов и таймаутами.
- `GET /stats` — агрегированная статистика по пользователям, задачам и назначениям.

Пример создания назначения:

```bash
curl -X POST http://127.0.0.1:8000/assignments \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $APP_API_KEY" \
  -d '{
        "user_id": 1,
        "chore_id": 3,
        "due_at": "2025-01-10T09:00:00Z",
        "status": "pending"
      }'
```

## Локальные проверки перед PR

```bash
ruff check --fix .
black .
isort .
pytest -q
pre-commit run --all-files
```

## CI

- `.github/workflows/ci.yml` запускает линтеры, `pre-commit`, покрытие, сборку wheel и dry-run стейдж-деплой. Кэшируются `pip` и `poetry`, все секреты подставляются из GitHub Secrets/Vars и сразу маскируются через `::add-mask::`.
- Результаты (`reports/junit.xml`, `reports/coverage.xml`, собранные wheel-файлы и build/deploy-логи) сохраняются в артефактах джоба.
- Для корректного выполнения заведите Secrets `APP_API_KEY`, `NOTIFY_TOKEN`, `STAGING_DEPLOY_TOKEN` и репозиторные Variables `NOTIFY_WEBHOOK_URL`, `NOTIFY_ALLOWED_HOSTS`, `STAGING_APP_URL`, `STAGING_API_URL`.
- После загрузки репозитория в GitHub добавьте required-check **CI / Build & test** в защите ветки `main` (Settings → Branches).

## SBOM & SCA (P09)

- Workflow `.github/workflows/ci-sbom-sca.yml` (triggers: `push` по Python/requirements/pyproject/waivers, `workflow_dispatch`) генерирует SBOM (Syft, CycloneDX) и SCA-отчёт (Grype), сохраняет файлы в `EVIDENCE/P09/{sbom.json, sca_report.json, sca_summary.md}` и загружает артефакт `P09_EVIDENCE-${GITHUB_SHA}`.
- Структура артефактов описана в `EVIDENCE/P09/README.md`; файлы в каталоге — плейсхолдеры под результаты джоба.
- Локальное воспроизведение (аналог CI):

  ```bash
  mkdir -p EVIDENCE/P09
  docker run --rm -v "$PWD":/work -w /work anchore/syft:latest \
    packages dir:. -o cyclonedx-json > EVIDENCE/P09/sbom.json
  docker run --rm -v "$PWD":/work -w /work anchore/grype:latest \
    sbom:/work/EVIDENCE/P09/sbom.json -o json > EVIDENCE/P09/sca_report.json
  echo "# SCA summary" > EVIDENCE/P09/sca_summary.md
  jq '[.matches[].vulnerability.severity] | group_by(.) | map({(.[0]): length}) | add' \
    EVIDENCE/P09/sca_report.json >> EVIDENCE/P09/sca_summary.md || true
  ```

- Файл `policy/waivers.yml` хранит исключения на уязвимости; перед использованием заполните реальные `id`, `package`, ссылку на Issue/PR и срок пересмотра.

## Дополнительно

- Безопасность: см. `SECURITY.md`.
- Хуки: см. `.pre-commit-config.yaml`.
- Формат ошибок соответствует [RFC 7807](https://datatracker.ietf.org/doc/html/rfc7807)-подобному JSON и описан в `app/main.py`.
