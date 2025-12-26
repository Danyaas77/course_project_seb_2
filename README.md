# Roommate Chores Tracker

Мини-приложение для распределения домашних дел между соседями. Доменная модель:

- `User` — участник квартиры.
- `Chore` — задача с периодичностью.
- `Assignment` — назначение задачи на пользователя с дедлайном и статусом.

Все запросы (кроме `/health`) требуют API-ключа через заголовок `X-API-Key`.

## Подготовка окружения
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
```

## Запуск
```bash
export APP_API_KEY=super-secret-key
uvicorn app.main:app --reload
# проверка
curl -H \"X-API-Key: $APP_API_KEY\" http://127.0.0.1:8000/health
```

## Эндпойнты
- `GET /health` — статус сервиса.
- `POST /users`, `GET /users` — создание и список участников.
- `POST /chores`, `GET /chores`, `GET /chores/{id}`, `PUT /chores/{id}`, `DELETE /chores/{id}` — CRUD задач с валидацией `cadence`.
- `POST /assignments`, `GET /assignments?status=...`, `PATCH /assignments/{id}` — назначение задач и обновление статусов.
- `GET /stats` — агрегированная статистика по пользователям/задачам/назначениям.

Пример создания назначения:
```bash
curl -X POST http://127.0.0.1:8000/assignments \\
  -H \"Content-Type: application/json\" \\
  -H \"X-API-Key: $APP_API_KEY\" \\
  -d '{\"user_id\": 1, \"chore_id\": 2, \"due_at\": \"2025-01-10T09:00:00Z\", \"status\": \"pending\"}'
```

## Локальные проверки
```bash
ruff --fix .
black .
isort .
pytest -q
pre-commit run --all-files
```

См. также: `SECURITY.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`.
