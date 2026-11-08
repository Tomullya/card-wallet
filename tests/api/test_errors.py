import pytest


@pytest.mark.req("NFR-03")
def test_unknown_route_uses_error_format(api):
    r = api.get("/no-such-route")
    assert r.status_code == 404
    body = r.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "NOT_FOUND"
    assert isinstance(body["error"]["message"], str)


@pytest.mark.req("NFR-03")
def test_wrong_method_uses_error_format(api):
    r = api.delete("/health")
    assert r.status_code == 405
    assert r.json()["error"]["code"] == "METHOD_NOT_ALLOWED"
