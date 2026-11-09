# Урок 2. Metadata: ключи доступа и ID запроса

## Зачем

Metadata — это «заголовки» gRPC, как headers в REST. В них передают то, что не относится к
самому платежу: **кто звонит** (ключ доступа) и **номер разговора** (ID запроса), чтобы потом
найти его в логах.

У нашего антифрода два ключа (BR-FRD-04):

| `x-api-key` | Роль | Можно |
|---|---|---|
| `dev-wallet-key` | кошелёк | всё |
| `dev-monitor-key` | мониторинг | только смотреть: `WatchRiskEvents`, `GetDecision` |

И две разные ошибки — частый вопрос на собеседовании:

| Ситуация | Код | Смысл |
|---|---|---|
| Ключа нет или он неизвестен | `UNAUTHENTICATED` (16) | «Я не знаю, кто ты» |
| Ключ верный, но роль не позволяет | `PERMISSION_DENIED` (7) | «Знаю, кто ты, но тебе нельзя» |

В REST это 401 и 403.

**ID запроса** (BR-FRD-05): клиент может прислать `x-request-id`. Сервис запишет его в лог и вернёт
обратно в **trailers** — это metadata, которая приходит **в конце** вызова, после ответа. Если
клиент ID не прислал, сервис придумает свой (UUID). Кошелёк шлёт новый ID на каждую оплату —
посмотри: `docker compose logs fraud --tail 5`.

Важно: ключи metadata **всегда строчными буквами** (`x-api-key`, не `X-Api-Key`). Библиотека
grpcio даже не даст отправить ключ с большой буквы.

## Попробуй в Postman

1. `CheckPayment` **без** metadata → `UNAUTHENTICATED`.
2. `x-api-key: wrong` → тоже `UNAUTHENTICATED`.
3. `x-api-key: dev-monitor-key` → `PERMISSION_DENIED`.
4. `x-api-key: dev-wallet-key` и `x-request-id: lab-123` → `OK`. В ответе открой вкладку
   **Trailers** (или **Metadata** ответа) и найди `x-request-id: lab-123`.
5. `GetDecision` с ключом мониторинга → работает: смотреть можно.

## Посмотри в коде

```python
metadata = WALLET + (("x-request-id", "my-test-1"),)
answer, call = stub.CheckPayment.with_call(payment(), metadata=metadata, timeout=2)
dict(call.trailing_metadata())["x-request-id"]   # "my-test-1"
```

- Metadata — кортеж пар `(ключ, значение)`.
- `.with_call(...)` возвращает ответ **и** объект вызова, у которого есть trailers.
- Сервер: `fraud-service/fraud_service/auth.py` — **interceptor**: код, который выполняется перед
  каждым методом (как middleware в веб-фреймворках). Он проверяет ключ и ставит trailers.

## Задание

`grpc-lab/exercises/test_lab_02_metadata.py` — 3 теста.

```bash
.venv/bin/python scripts/grpc_lab_check.py 2
```

## Вопросы с собеседования

1. Что такое metadata в gRPC и чем trailers отличаются от обычной metadata?
2. `UNAUTHENTICATED` или `PERMISSION_DENIED`: что вернуть на неверный ключ?
3. Зачем нужен request id?
4. Что такое interceptor?

### Ответы

1. Пары ключ–значение рядом с сообщением, как HTTP-заголовки. Начальная metadata идёт до ответа,
   trailers — после, вместе со статусом.
2. `UNAUTHENTICATED`: личность не подтверждена. `PERMISSION_DENIED` — когда личность известна,
   а прав нет. (В копии с багами на :50052 это перепутано — урок 8.)
3. Связать запрос клиента с записями в логах всех сервисов — трассировка при разборе инцидентов.
4. Перехватчик вызовов на клиенте или сервере: авторизация, логи, метрики в одном месте для
   всех методов.
