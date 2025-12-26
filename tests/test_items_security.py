from uuid import UUID

from fastapi.testclient import TestClient

from app import main as main_module


def _assert_problem(payload, *, status: int, code: str):
    assert payload["status"] == status
    assert payload["code"] == code
    assert payload["title"]
    assert payload["detail"]
    UUID(payload["correlation_id"])


def test_create_item_requires_api_key(client):
    r = client.post("/items", json={"name": "Widget"})
    assert r.status_code == 401
    body = r.json()
    _assert_problem(body, status=401, code="unauthorized")
    assert body["type"].endswith("invalid-api-key")


def test_create_item_rejects_wrong_api_key(client):
    r = client.post(
        "/items",
        json={"name": "Widget"},
        headers={"X-API-Key": "wrong"},
    )
    assert r.status_code == 401
    body = r.json()
    _assert_problem(body, status=401, code="unauthorized")


def test_internal_error_is_sanitized(api_key, auth_headers, monkeypatch):
    class BoomList(list):
        def append(self, item):
            raise RuntimeError("boom")

    monkeypatch.setitem(main_module._DB, "items", BoomList())

    with TestClient(main_module.app, raise_server_exceptions=False) as test_client:
        response = test_client.post(
            "/items", json={"name": "ValidName"}, headers=auth_headers
        )

    assert response.status_code == 500
    body = response.json()
    _assert_problem(body, status=500, code="internal_error")
    assert body["detail"] == "The server encountered an internal error"
