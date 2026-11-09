import pytest


@pytest.mark.req("NFR-08")
def test_buggy_mode_off_by_default(monkeypatch):
    """Planted defects must never be active unless BUGGY_MODE is set explicitly."""
    monkeypatch.delenv("BUGGY_MODE", raising=False)
    from app import buggy
    from app.config import Settings, get_settings

    get_settings.cache_clear()
    assert Settings(database_url="x", jwt_secret="y", card_hash_secret="z").buggy_mode is False
    assert buggy.enabled("BUG-01") is False


@pytest.mark.req("NFR-08")
def test_fraud_buggy_mode_off_by_default(monkeypatch):
    """The Fraud Service planted defects (BUG-17…19) follow the same rule."""
    monkeypatch.delenv("BUGGY_MODE", raising=False)
    from fraud_service import buggy

    assert buggy.enabled("BUG-17") is False
    monkeypatch.setenv("BUGGY_MODE", "true")
    assert buggy.enabled("BUG-17") is True
