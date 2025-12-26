# P03 — Non-Functional Security Requirements

<a id="nfr-sc-1"></a>
### NFR-SC-1 — Authenticated mutations
- Requirement: Mutating API endpoints **must** require authenticated callers (API key or stronger control).
- Rationale: Protect integrity of inventory data from unauthorized updates.

<a id="nfr-sc-2"></a>
### NFR-SC-2 — Canonicalised item names
- Requirement: User-supplied item names **must** be validated for length and character set before persistence.
- Rationale: Reduce risk of injection and resource exhaustion.

<a id="nfr-r-1"></a>
### NFR-R-1 — Opaque internal errors
- Requirement: The service **must not** leak internal exception details to clients.
- Rationale: Avoid giving attackers implementation hints (maps to P04/F2).

<a id="nfr-sc-3"></a>
### NFR-SC-3 — Secrets isolation
- Requirement: API ключи и другие секреты развёртывания **должны** храниться вне репозитория (ENV/secret store) и загружаться в рантайме; при компрометации ключ должен поддерживать замену без полной перезаливки.
- Rationale: Минимизирует риск утечки аутентификаторов при ревью/форке и упрощает ротацию.

<a id="nfr-val-1"></a>
### NFR-VAL-1 — Доменные проверки задач
- Requirement: Сущности `Chore` и `Assignment` **обязаны** проходить строгую валидацию (ограниченные enum cadence/status, ISO datetime c таймзоной, trimming строковых полей).
- Rationale: Исключает недопустимые состояния и уменьшает поверхность атак (DoS через неправильные даты, XSS через описания).

<a id="nfr-com-1"></a>
### NFR-COM-1 — Контроль исходящих уведомлений
- Requirement: Внешние интеграции (stub-уведомления/вебхуки) **должны** использовать allowlist хостов, короткие таймауты и логирование ошибок без чувствительных данных.
- Rationale: Снижает риск SSRF/эксфильтрации через компрометированные конечные точки.

<a id="nfr-au-1"></a>
### NFR-AU-1 — Аудит ключевых действий
- Requirement: Запросы на создание/удаление задач и статусов уведомлений **должны** логироваться с `correlation_id`, временем и идентификатором клиента, без хранения секретов.
- Rationale: Обеспечивает расследование инцидентов и непротиворечивость репортов доставки.

<a id="nfr-dos-1"></a>
### NFR-DOS-1 — Ограничение частоты запросов
- Requirement: Внешние клиенты **не должны** вызывать API чаще заданного порога (напр., 60 req/мин/ключ) — превышения блокируются и логируются.
- Rationale: Снижает вероятность DoS и обходов квот.

<a id="nfr-sdlc-1"></a>
### NFR-SDLC-1 — Интегритет CI/CD
- Requirement: CI/CD pipeline **должен** использовать подписанные контейнеры, principle of least privilege для секретов и требовать успешного прохождения безопасности перед деплоем.
- Rationale: Предотвращает supply-chain атаки при выкладке сервиса.

<a id="nfr-log-1"></a>
### NFR-LOG-1 — Санитария логов
- Requirement: Журналы аудита/доставки **не должны** содержать PII или секреты; данные минимизированы до идентификаторов и статусов.
- Rationale: Исключает вторичную утечку через системы наблюдаемости.

Last updated: 2025-02-17.
