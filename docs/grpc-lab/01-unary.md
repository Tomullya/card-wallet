# Урок 1. Обычный вызов (unary) и reflection

## Зачем

Unary — самый частый вызов: один запрос, один ответ. Кошелёк на каждую оплату делает ровно
такой вызов: `CheckPayment`. Ответ — решение: `APPROVE` или `DECLINE`, причина и риск 0–100.

Правила антифрода (BR-FRD-01):

| Условие | Решение | Причина | Риск |
|---|---|---|---|
| Сумма больше `5000.00` | `DECLINE` | `HIGH_AMOUNT` | 90 |
| Категория `GAMBLING` | `DECLINE` | `BLOCKED_CATEGORY` | 80 |
| Иначе | `APPROVE` | — | 10 |

Сумма передаётся **строкой** (`"10.00"`), а не числом: дробные числа в компьютере неточные,
а в деньгах копейка важна.

## Попробуй в Postman

1. **New → gRPC**, адрес `localhost:50051`, метод через reflection: `CheckPayment`.
2. Вкладка **Metadata**: ключ `x-api-key`, значение `dev-wallet-key` (подробно — в уроке 2).
3. Вкладка **Message**: нажми **Use Example Message** или вставь:
   ```json
   {
     "transaction_id": "t-1",
     "user_id": "u-1",
     "card_last4": "4242",
     "amount": "10.00",
     "currency": "EUR",
     "merchant_name": "Shop",
     "merchant_category": "GROCERIES"
   }
   ```
4. **Invoke**. Ответ: `"decision": "APPROVE"`, `"risk_score": 10`, `"transaction_id": "t-1"`.
5. Поменяй сумму на `"5000.00"`, потом на `"5000.01"`. Где граница? (BR-FRD-01: ровно 5000.00 —
   одобряется.)
6. Сделай платёж через Swagger кошелька (localhost:8000/docs, `POST /payments`) — кошелёк
   отправит такой же вызов. Скопируй `transaction_id` из ответа и найди решение методом
   `GetDecision` (сообщение `{"transaction_id": "..."}`).

## Посмотри в коде

```python
answer = stub.CheckPayment(payment(), metadata=WALLET, timeout=2)
assert answer.decision == fraud_pb2.APPROVE
```

- `stub` — сгенерированный «пульт» для вызова методов сервиса.
- `payment()` из `grpc-lab/lab.py` собирает правильный платёж; меняй поля так:
  `payment(amount="6000.00")`.
- `timeout=2` — дедлайн в секундах (урок 4). **Всегда** ставь его в тестах.
- Сервер: `fraud-service/fraud_service/server.py`, метод `CheckPayment` → `decide`.

## Задание

`grpc-lab/exercises/test_lab_01_unary.py` — 4 теста. Проверка:

```bash
.venv/bin/python scripts/grpc_lab_check.py 1
```

## Вопросы с собеседования

1. Что такое stub?
2. Что такое server reflection и зачем он тестировщику?
3. Почему сумма в proto — строка?
4. Какие граничные значения ты проверишь для правила «сумма > 5000»?

### Ответы

1. Сгенерированный из proto клиентский объект: вызываешь метод как обычную функцию,
   а он сам упаковывает запрос в protobuf и шлёт по сети.
2. Сервис по запросу отдаёт описание своих методов и сообщений. Postman и grpcurl могут
   вызывать методы без proto-файла — удобно для ручного тестирования.
3. Чтобы не терять точность: `0.1 + 0.2` в числах с плавающей точкой не равно `0.3`.
4. `5000.00` (APPROVE), `5000.01` (DECLINE), плюс `4999.99`.
