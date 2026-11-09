"""Урок 5. Поток от сервера: WatchRiskEvents.

Проверка: .venv/bin/python scripts/grpc_lab_check.py 5
"""

import pytest
from lab import MONITOR, WALLET, Watch, payment  # noqa: F401


def test_watch_sees_my_payment(stub):
    # 1. watch = Watch(stub)                       — подписались
    # 2. отправь платёж GAMBLING через CheckPayment — сервер опубликует событие
    # 3. event = watch.find(request.transaction_id) — найди своё событие
    # 4. watch.stop(); проверь, что event не None и risk_score == 80
    pytest.fail("TODO")


def test_filter_hides_low_risk(stub):
    # Подпишись с min_risk_score=50. Отправь обычный платёж (риск 10) и 6000.00 (риск 90).
    # Событие на 6000.00 должно прийти, обычное — нет: watch.find(..., seconds=0.2) is None.
    pytest.fail("TODO")
