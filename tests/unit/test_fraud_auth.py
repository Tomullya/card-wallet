"""Role table of the Fraud Service API keys (BR-FRD-04)."""

import pytest
from fraud_service.auth import ROLE_METHODS, role_for_key


@pytest.mark.req("BR-FRD-04")
def test_wallet_key_has_all_methods():
    assert role_for_key("dev-wallet-key") == "wallet"
    assert ROLE_METHODS["wallet"] is None


@pytest.mark.req("BR-FRD-04")
def test_monitor_key_limited():
    assert role_for_key("dev-monitor-key") == "monitor"
    assert ROLE_METHODS["monitor"] == {"WatchRiskEvents", "GetDecision"}


@pytest.mark.req("BR-FRD-04")
def test_unknown_and_missing_key():
    assert role_for_key("nope") is None
    assert role_for_key(None) is None
    assert role_for_key("") is None
