"""Урок 2. Metadata: ключ доступа и ID запроса.

Проверка: .venv/bin/python scripts/grpc_lab_check.py 2
"""

import grpc  # noqa: F401
import pytest
from lab import MONITOR, WALLET, payment  # noqa: F401


def test_without_key_unauthenticated(stub):
    # Вызови CheckPayment БЕЗ metadata. Ошибку gRPC ловят так:
    #     with pytest.raises(grpc.RpcError) as error:
    #         ...вызов...
    # Потом проверь error.value.code() == grpc.StatusCode.UNAUTHENTICATED
    pytest.fail("TODO")


def test_monitor_key_may_not_pay(stub):
    # Ключ мониторинга (MONITOR) может только смотреть. Какой код вернёт CheckPayment?
    pytest.fail("TODO: ожидаем PERMISSION_DENIED")


def test_request_id_comes_back_in_trailers(stub):
    # metadata = WALLET + (("x-request-id", "my-test-1"),)
    # Чтобы увидеть trailers, вызывай через .with_call:
    #     answer, call = stub.CheckPayment.with_call(payment(), metadata=metadata, timeout=2)
    # dict(call.trailing_metadata())["x-request-id"] должен быть "my-test-1".
    pytest.fail("TODO")
