from datetime import datetime, timezone
from typing import Dict

import httpx

from app import main as main_module
from app.main import (
    ASSIGNMENT_WEBHOOK_ALLOWLIST_ENV,
    ASSIGNMENT_WEBHOOK_RETRIES_ENV,
    ASSIGNMENT_WEBHOOK_URL_ENV,
)


def _create_assignment_for_testing(client, headers) -> Dict[str, int]:
    user = client.post("/users", json={"name": "WebhookUser"}, headers=headers).json()
    chore = client.post(
        "/chores",
        json={
            "title": "Ping webhook",
            "cadence": "daily",
            "description": "Notify on completion",
            "owner_id": user["id"],
        },
        headers=headers,
    ).json()
    assignment = client.post(
        "/assignments",
        json={
            "user_id": user["id"],
            "chore_id": chore["id"],
            "due_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
        },
        headers=headers,
    ).json()
    return assignment


def test_webhook_policy_enforced(client, auth_headers, monkeypatch):
    assignment = _create_assignment_for_testing(client, auth_headers)

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("boom", request=request)

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(main_module, "_WEBHOOK_TRANSPORT_OVERRIDE", transport)
    # Blocked host fails fast with 400
    monkeypatch.setenv(ASSIGNMENT_WEBHOOK_URL_ENV, "https://blocked.example.com/hook")
    monkeypatch.setenv(ASSIGNMENT_WEBHOOK_ALLOWLIST_ENV, "allowed.example.com")

    blocked = client.patch(
        f"/assignments/{assignment['id']}",
        json={"status": "completed"},
        headers=auth_headers,
    )

    assert blocked.status_code == 400
    assert blocked.json()["code"] == "webhook_host_blocked"

    # Allowed host but transport fails => 502 from retries
    monkeypatch.setenv(ASSIGNMENT_WEBHOOK_ALLOWLIST_ENV, "notify.example.com")
    monkeypatch.setenv(ASSIGNMENT_WEBHOOK_URL_ENV, "https://notify.example.com/hook")
    monkeypatch.setenv(ASSIGNMENT_WEBHOOK_RETRIES_ENV, "1")

    failed = client.patch(
        f"/assignments/{assignment['id']}",
        json={"status": "completed"},
        headers=auth_headers,
    )

    assert failed.status_code == 502
    body = failed.json()
    assert body["code"] == "webhook_failed"
    assert body["detail"] == "Failed to deliver webhook"
