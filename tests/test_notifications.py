from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import httpx

from app.config import get_settings, reload_settings
from app.notifications import NotificationClient, build_notification_client


def _create_user(client, auth_headers, name):
    response = client.post("/users", json={"name": name}, headers=auth_headers)
    assert response.status_code == 201
    return response.json()


def _create_chore(client, auth_headers, owner_id):
    response = client.post(
        "/chores",
        json={
            "title": "Windows",
            "cadence": "monthly",
            "description": "Clean windows",
            "owner_id": owner_id,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


def _create_assignment(client, auth_headers, user_id, chore_id):
    response = client.post(
        "/assignments",
        json={
            "user_id": user_id,
            "chore_id": chore_id,
            "due_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "status": "pending",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


def test_notify_rejects_host_not_in_allowlist(
    client, auth_headers, monkeypatch
):
    monkeypatch.setenv("NOTIFY_WEBHOOK_URL", "https://evil.example.com/hook")
    monkeypatch.setenv("NOTIFY_ALLOWED_HOSTS", "hooks.example.com")
    reload_settings()
    owner = _create_user(client, auth_headers, name="Owner")
    roommate = _create_user(client, auth_headers, name="Roommate")
    chore = _create_chore(client, auth_headers, owner_id=owner["id"])
    assignment = _create_assignment(
        client, auth_headers, user_id=roommate["id"], chore_id=chore["id"]
    )

    response = client.post(
        f"/assignments/{assignment['id']}/notify", headers=auth_headers
    )

    assert response.status_code == 400
    problem = response.json()
    assert problem["code"] == "notification_host_blocked"


def test_notify_succeeds_with_allowed_host(
    client, auth_headers, monkeypatch
):
    monkeypatch.setenv(
        "NOTIFY_WEBHOOK_URL",
        "https://hooks.example.com/webhook",
    )
    monkeypatch.setenv("NOTIFY_ALLOWED_HOSTS", "hooks.example.com")
    monkeypatch.setenv("NOTIFY_TOKEN", "notif-secret")
    reload_settings()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer notif-secret"
        body = json.loads(request.content.decode())
        assert "assignment_id" in body
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)

    def override_notification_client():
        return NotificationClient(
            settings=get_settings(),
            transport=transport,
        )

    client.app.dependency_overrides[build_notification_client] = (
        override_notification_client
    )

    try:
        owner = _create_user(client, auth_headers, name="Owner")
        roommate = _create_user(client, auth_headers, name="Roommate")
        chore = _create_chore(client, auth_headers, owner_id=owner["id"])
        assignment = _create_assignment(
            client, auth_headers, user_id=roommate["id"], chore_id=chore["id"]
        )

        response = client.post(
            f"/assignments/{assignment['id']}/notify", headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json() == {"status": "queued"}
    finally:
        client.app.dependency_overrides.pop(build_notification_client, None)
