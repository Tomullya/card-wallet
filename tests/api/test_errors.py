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


@pytest.mark.req("NFR-03")
@pytest.mark.parametrize(
    "body",
    [b"K\x80", b"\x80", b"{not json", b""],
    ids=["bad-utf8", "bad-byte", "bad-json", "empty"],
)
def test_malformed_body_is_validation_error(api, body):
    """Found by contract tests: undecodable bodies returned an undocumented 400."""
    r = api.post("/auth/login", content=body, headers={"Content-Type": "application/json"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
