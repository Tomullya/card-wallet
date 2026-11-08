import pytest


@pytest.mark.req("NFR-06")
def test_health_returns_ok(api):
    r = api.get("/health")
    assert r.status_code == 200
    assert r.json()["database"] == "ok"
