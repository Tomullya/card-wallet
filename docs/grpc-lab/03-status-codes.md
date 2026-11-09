# Урок 3. Статус-коды

## Зачем

В REST ошибку видно по HTTP-коду (404, 500). В gRPC у каждого вызова свой **статус-код**
(их 17) и текст `details`. Тестировщик должен знать главные — и проверять, что сервис отвечает
**правильным** кодом: от кода зависит, что сделает клиент (повторить запрос, показать ошибку,
обновить ключ).

## Карта кодов нашего антифрода

| Код (номер) | Чья вина | Как получить | Похоже в REST |
|---|---|---|---|
| `OK` (0) | — | любой верный вызов | 200 |
| `CANCELLED` (1) | клиент передумал | клиент отменил поток (урок 4) | — |
| `INVALID_ARGUMENT` (3) | клиент | `amount: "abc"`; `min_risk_score: 101`; пустой `CheckBatch` | 400 / 422 |
| `DEADLINE_EXCEEDED` (4) | время вышло | магазин `TEST_TIMEOUT` + дедлайн 1 с | 504 |
| `NOT_FOUND` (5) | клиент | `GetDecision` с несуществующим id | 404 |
| `PERMISSION_DENIED` (7) | права | ключ мониторинга на `CheckPayment` | 403 |
| `RESOURCE_EXHAUSTED` (8) | лимит | `CheckBatch` из 1001 платежа; 9-й подписчик потока; 17-й одновременный `CheckBatch` / `ScorePayments` | 429 |
| `INTERNAL` (13) | сервер | магазин `TEST_ERROR` | 500 |
| `UNAVAILABLE` (14) | сеть или сервис лежит | вызов на `localhost:59999` или выключенный сервис | 503 |
| `UNAUTHENTICATED` (16) | ключ | нет `x-api-key` | 401 |

Полный список тестов по кодам — в шапке файла `tests/grpc/test_status_codes.py`.

**Важно для QA:** `UNAVAILABLE` и `DEADLINE_EXCEEDED` клиент обычно может **повторить**,
а `INVALID_ARGUMENT` — нет: тот же запрос снова будет ошибочным. Поэтому неправильный код —
это настоящий баг, а не мелочь.

Как кошелёк реагирует на ошибки антифрода: на `DEADLINE_EXCEEDED`, `INTERNAL`, `UNAVAILABLE` —
отвечает клиенту `503` и ничего не списывает (BR-PAY-08).

## Попробуй в Postman

Получи каждый код из таблицы, кроме `CANCELLED` (его — в уроке 4). Для `UNAVAILABLE` смени адрес
на `localhost:59999`. Запиши в заметки: код, номер, текст `details`.

## Посмотри в коде

```python
with pytest.raises(grpc.RpcError) as error:
    stub.GetDecision(fraud_pb2.GetDecisionRequest(transaction_id="no-such-id"),
                     metadata=WALLET, timeout=2)
assert error.value.code() == grpc.StatusCode.NOT_FOUND
error.value.details()   # текст: "unknown transaction_id"
```

## Задание

`grpc-lab/exercises/test_lab_03_status_codes.py` — 3 теста.

```bash
.venv/bin/python scripts/grpc_lab_check.py 3
```

## Вопросы с собеседования

1. Какие коды gRPC можно безопасно повторять?
2. Чем `INVALID_ARGUMENT` отличается от `FAILED_PRECONDITION`?
3. Как проверить ошибку gRPC в автотесте?

### Ответы

1. Обычно `UNAVAILABLE`, иногда `DEADLINE_EXCEEDED` и `RESOURCE_EXHAUSTED` (с паузой) — если
   операция идемпотентная. Ошибки клиента (`INVALID_ARGUMENT`, `NOT_FOUND`) повторять бессмысленно.
2. `INVALID_ARGUMENT` — запрос плохой сам по себе (сумма «abc»). `FAILED_PRECONDITION` — запрос
   нормальный, но система не в том состоянии (например, карта заблокирована).
3. Поймать `grpc.RpcError` и проверить `.code()` и при необходимости `.details()`.
