# ADR-005: Enforce Referential Integrity For Assignments

- Status: Accepted
- Date: 2025-02-17

## Context

- Threat flow **F4/F5** и риск **R5** описывают возможность подделки связей между пользователями, задачами и назначениями, если сервис не проверяет существование сущностей.
- NFR-SC-1 и NFR-VAL-1 требуют, чтобы только владелец мог создавать/обновлять задания и чтобы `Assignment` всегда ссылался на валидные `User`/`Chore`.
- Удаление `Chore` без очистки связанных `Assignment` оставляет «висячие» записи и искажает статистику.

## Decision

- Перед каждым созданием/обновлением `Chore`/`Assignment` выполнять явный поиск целевой сущности (`_get_user_or_404`, `_get_chore_or_404`, `_get_assignment_or_404`) и поднимать `ApiError(404, code=*_not_found)` при несоответствии.
- При `DELETE /chores/{id}` каскадно удалять связанные `assignments` из `_DB` для сохранения консистентности и предотвращения утечки данных о прошлых назначениях.
- Все проверки проходят под той же зависимостью `require_api_key`, чтобы соответствовать owner-only политике.

## Consequences

- Клиенты получают прозрачные 404-ответы, если пытаются сослаться на несуществующие сущности.
- Статистика (`GET /stats`) и листинги заданий не содержат «битых» ссылок даже после удаления задач.
- Требуется повторное чтение данных при каждом обновлении (незначительные накладные расходы), но это упрощает будущую миграцию на настоящую БД.

## Links

- NFR references: [NFR-SC-1](../nfr/P03-nfr.md#nfr-sc-1), [NFR-VAL-1](../nfr/P03-nfr.md#nfr-val-1)
- Threat model / risks: F4/F5 в [STRIDE](../threat-model/STRIDE.md), R5 в [Risk Register](../threat-model/RISKS.md#risk-register)
- Verification tests: [`tests/test_chores_assignments.py::test_chore_crud_flow`](../../tests/test_chores_assignments.py#L40), [`tests/test_chores_assignments.py::test_assignments_and_stats_flow`](../../tests/test_chores_assignments.py#L91)
