# NFR Catalog — Roommate Chores Tracker

Консолидированный список измеримых нефункциональных требований для сервиса трекера квартирных дел. Метрики и цели подобраны под наш домен (создание/просмотр поручений между соседями).

| ID | Требование и цель | Метрика/порог | Проверка/источник |
| --- | --- | --- | --- |
| NFR-AVAIL-1 | Доступность API за месяц не ниже 99.5% | Uptime ≥ 99.5%/30 дней | Synthetic ping + алёрт; отчёт uptime-бота |
| NFR-LAT-1 | Время ответа для чтения задач/статистики остаётся быстрым | P95 latency `GET /assignments` и `GET /stats` ≤ 200 мс при 20 rps и ≤500 назначений | K6/Gatling прогон, дашборд latency |
| NFR-ERR-1 | Ошибки сервера контролируемы | 5xx rate ≤ 0.5% за скользящее 24 ч | Логи/metrics (error rate) |
| NFR-AUTH-1 | Все мутационные запросы требуют ключ | 100% `POST/PUT/PATCH/DELETE` без валидного `X-API-Key` → 401 | Автотесты (`tests/test_errors.py`, `tests/test_chores_assignments.py`), лог 401 |
| NFR-RATE-1 | Защита от перегрузки по ключу | ≤ 60 req/min на API-ключ; 95% превышений → 429 за ≤1 с | Rate-limit middleware + метрика throttle |
| NFR-DATA-1 | Доменные поля валидируются | 100% невалидных `cadence/status/due_at` → 422, без записи | Автотесты валидации, лог 422 |
| NFR-TIME-1 | Сроки заданий в единой таймзоне | Все `due_at` хранятся/отдаются в UTC, дрейф ≤0.5 c | Контракт-тест на нормализацию |
| NFR-LOG-1 | Логи безопасны и трассируемы | 0 секретов/API-ключей в логах; ≥99% ответов с `correlation_id` | Лог-сэмплы, stat check в Fluentd/ELK |
| NFR-SEC-1 | Ключи вращаются и не лежат в коде | `APP_API_KEY` хранится в ENV/secret store; ротация ≤ 90 дней | Секреты в CI/ops, журнал ротаций |
| NFR-CI-1 | Мёрджи защищены проверками | 100% PR в `main` проходят CI (`ruff`, `black`, `isort`, `pytest`, `pre-commit`) | Required check `CI / build` |

## Контроль и доказательства
- CI: `.github/workflows/ci.yml` гоняет линтеры, форматтеры, тесты и pre-commit; PR не мёрджатся без зелёного `CI / build`.
- Автотесты: `tests/test_errors.py` и `tests/test_chores_assignments.py` покрывают NFR-AUTH-1, NFR-DATA-1, NFR-TIME-1 (валидация, UTC, 401).
- Локальная проверка: `pytest -q` (см. лог последнего запуска в PR).
- Для rate limit/uptime/latency предусмотрены будущие прогоны (K6/monitoring) — добавить ссылки на дашборды после подключения.

Последний апдейт: 2025-02-17.
