# ADR-004: Canonical Validation For Chores & Assignments

- Status: Accepted
- Date: 2025-02-17

## Context

- Threat flow **F3** (client payloads) highlights tampering attempts with oversized text, unknown cadence/status values, или некорректные даты, что приводит к риску **R3** (порча доменного состояния) из реестра рисков.
- NFR-VAL-1 / NFR-SC-2 требуют строгую доменную валидацию и канонизацию пользовательских данных.
- Без единых правил `Chore`/`Assignment` сущности могут содержать пустые названия, локальные даты без таймзоны и произвольные статусы, что затрудняет расчёт дедлайнов и статистики.

## Decision

- Описать все входные модели через Pydantic со следующими ограничениями:
  - `ChoreCreate`/`ChoreUpdate`: `title` триммится и проверяется на длину (1–120 символов), `cadence` ограничен enum (`daily`, `weekly`, `biweekly`, `monthly`, `adhoc`), `description` ограничена 500 символами.
  - `AssignmentCreate`/`AssignmentUpdate`: `status` ограничен enum (`pending`, `completed`, `skipped`), `due_at` конвертируется в UTC через кастомный валидатор (принимаем ISO8601 строки и `datetime` объекты).
  - Все идентификаторы (`user_id`, `chore_id`, `owner_id`) должны быть > 0.
- Нецензурные входы приводят к `422 validation_error`, используя существующий RFC 7807 обработчик.

## Consequences

- Клиенты получают немедленную обратную связь при неверных данных и должны отправлять ISO datetime с таймзоной.
- Единый формат предотвращает накопление «грязных» записей и упрощает расчёт дедлайнов/статистики.
- Требуется поддержка миграций/валидаций при добавлении новых значений cadence/status (потребуются новые тесты).

## Links

- NFR references: [NFR-VAL-1](../nfr/P03-nfr.md#nfr-val-1), [NFR-SC-2](../nfr/P03-nfr.md#nfr-sc-2)
- Threat model / risks: F3 в [STRIDE](../threat-model/STRIDE.md), R3 в [Risk Register](../threat-model/RISKS.md#risk-register)
- Verification tests: [`tests/test_chores_assignments.py::test_chore_cadence_validation`](../../tests/test_chores_assignments.py#L74), [`tests/test_chores_assignments.py::test_assignments_and_stats_flow`](../../tests/test_chores_assignments.py#L91)
