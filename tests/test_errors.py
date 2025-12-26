from uuid import UUID


def _assert_problem(payload, *, status: int, code: str | None = None):
    assert payload["status"] == status
    assert payload["title"]
    assert payload["detail"]
    UUID(payload["correlation_id"])
    if code:
        assert payload["code"] == code


def test_not_found_item(client):
    r = client.get("/items/999")
    assert r.status_code == 404
    body = r.json()
    _assert_problem(body, status=404, code="not_found")
    assert body["type"].endswith("item-not-found")

def test_validation_error(client, auth_headers):
    r = client.post("/items", json={"name": ""}, headers=auth_headers)
    assert r.status_code == 422
    body = r.json()
    _assert_problem(body, status=422, code="validation_error")
    assert "errors" in body and len(body["errors"]) >= 1
