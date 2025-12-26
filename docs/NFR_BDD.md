# NFR BDD Scenarios

Формат Given/When/Then для ключевых NFR.

### BDD-1 — Auth required for mutations (NFR-AUTH-1)
```
Given сервис запущен без установленных API-ключей в заголовках
When клиент отправляет POST /chores с валидным телом
Then ответ имеет статус 401
And тело ошибки содержит code "unauthorized"
```

### BDD-2 — Domain validation of chores (NFR-DATA-1)
```
Given установлен валидный X-API-Key
When клиент отправляет POST /chores с cadence "yearly"
Then ответ имеет статус 422
And поле code равно "validation_error"
And задача не появляется в списке /chores
```

### BDD-3 — UTC normalization for due dates (NFR-TIME-1)
```
Given у меня есть пользователь и поручение с due_at "2025-02-20T10:00:00+03:00"
When я создаю assignment через POST /assignments
Then ответ содержит due_at в формате UTC (оканчивается на "Z")
And разница между переданным временем и сохранённым не превышает 0.5 секунды
```

### BDD-4 — Rate limiting per API key (NFR-RATE-1)
```
Given установлен валидный X-API-Key
And зафиксировано 60 запросов к API за последние 60 секунд
When приходит 61-й запрос с тем же ключом
Then ответ имеет статус 429
And в логах появляется запись о превышении лимита без утечки ключа
```

### BDD-5 — CI gate on main branch (NFR-CI-1)
```
Given открыт PR в ветку main
When workflow .github/workflows/ci.yml отрабатывает успешно
Then PR получает зелёный required-check "CI / build"
And без успешного чек-рана merge невозможен
```
