# NFR Traceability

Трассировка пользовательских историй к NFR и плану внедрения.

| Story ID | Описание истории | Связанные NFR | Приоритет | Релиз/веха | Backlog Issue | Тест/BDD |
| --- | --- | --- | --- | --- | --- | --- |
| US-ASSIGN-001 | Как владелец, я создаю поручение соседу с дедлайном, чтобы задачи выполнялись вовремя. | NFR-AUTH-1, NFR-DATA-1, NFR-TIME-1 | Must | Sprint 2 | Issue `NFR-101` (backlog) | BDD-1, BDD-2, unit/API tests |
| US-VIEW-002 | Как сосед, я быстро просматриваю свои назначения и дедлайны. | NFR-LAT-1, NFR-TIME-1, NFR-ERR-1 | Must | Sprint 2 | Issue `NFR-102` | BDD-3 |
| US-STATS-003 | Как владелец, я смотрю статистику (overdue/completed), чтобы распределять нагрузку. | NFR-LAT-1, NFR-LOG-1 | Should | Sprint 3 | Issue `NFR-103` | BDD-3 |
| US-ABUSE-004 | Как админ, я ограничиваю злоупотребления ключом, чтобы сервис оставался доступным. | NFR-RATE-1, NFR-AVAIL-1, NFR-ERR-1 | Must | Sprint 3 | Issue `NFR-104` | BDD-4 |
| US-SEC-005 | Как ответственный за безопасность, я вращаю API-ключи и не логирую секреты. | NFR-SEC-1, NFR-LOG-1, NFR-CI-1 | Must | Sprint 2 | Issue `NFR-105` | BDD-5 |

Примечание: номера Issue указаны как ориентиры для постановки задач в GitHub/Project Board; при создании реальных карточек используйте метку `nfr` и добавьте приоритет/срок.
