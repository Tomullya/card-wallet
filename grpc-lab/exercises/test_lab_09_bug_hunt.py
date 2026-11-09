"""Урок 9. Охота на баги.

На порту 50052 работает копия антифрода с тремя спрятанными багами.
1. Найди их руками в Postman (подсказки в docs/grpc-lab/08-how-to-test.md).
2. Напиши тесты: зелёные на нормальном сервисе, красные на сломанном.
   .venv/bin/python scripts/grpc_lab_check.py 9           — должны пройти
   .venv/bin/python scripts/grpc_lab_check.py 9 --buggy   — должны упасть все три
"""

import grpc  # noqa: F401
import pytest
from lab import WALLET, payment  # noqa: F401


def test_unknown_key_is_unauthenticated(stub):
    # Баг 1 — про коды ошибок авторизации.
    pytest.fail("TODO")


def test_bidi_stream_ends_when_i_finish(stub):
    # Баг 2 — про ScorePayments. Подсказка: без дедлайна такой тест повиснет навсегда.
    # Если вызов бросил grpc.RpcError — тест должен упасть через assert (не через ошибку).
    pytest.fail("TODO")


def test_request_id_returned_on_success(stub):
    # Баг 3 — про trailers.
    pytest.fail("TODO")
