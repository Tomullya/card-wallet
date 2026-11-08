import pytest


@pytest.mark.req("NFR-06", "NFR-07")
def test_health_returns_ok(api):
    r = api.get("/health")
    assert r.status_code == 200
    assert r.json()["database"] == "ok"


@pytest.mark.req("NFR-06", "BR-FRD-03")
def test_health_reports_fraud_service_ok(api):
    body = api.get("/health").json()
    assert body["fraud_service"] == "ok"
    assert body["status"] == "ok"
