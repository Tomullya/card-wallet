"""Урок 5. Поток от сервера: WatchRiskEvents."""

from lab import WALLET, Watch, payment


def test_watch_sees_my_payment(stub):
    watch = Watch(stub)
    request = payment(merchant_category="GAMBLING")
    stub.CheckPayment(request, metadata=WALLET, timeout=2)
    event = watch.find(request.transaction_id)
    watch.stop()
    assert event is not None
    assert event.risk_score == 80


def test_filter_hides_low_risk(stub):
    watch = Watch(stub, min_risk_score=50)
    low, high = payment(), payment(amount="6000.00")
    stub.CheckPayment(low, metadata=WALLET, timeout=2)
    stub.CheckPayment(high, metadata=WALLET, timeout=2)
    assert watch.find(high.transaction_id) is not None
    assert watch.find(low.transaction_id, seconds=0.2) is None
    watch.stop()
