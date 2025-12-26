from datetime import datetime, timedelta, timezone


def _create_user(client, headers, name="Alice"):
    response = client.post("/users", json={"name": name}, headers=headers)
    assert response.status_code == 201
    return response.json()


def _create_chore(client, headers, owner_id, **overrides):
    payload = {
        "title": "Wash dishes",
        "cadence": "daily",
        "description": "Evening chores",
        "owner_id": owner_id,
    }
    payload.update(overrides)
    response = client.post("/chores", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


def _future_due_date(days=1):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _create_assignment(client, headers, user_id, chore_id, **overrides):
    payload = {
        "user_id": user_id,
        "chore_id": chore_id,
        "due_at": _future_due_date(),
        "status": "pending",
    }
    payload.update(overrides)
    response = client.post("/assignments", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


def test_chore_crud_flow(client, auth_headers):
    user = _create_user(client, auth_headers)
    chore = _create_chore(client, auth_headers, user["id"])

    response = client.get("/chores", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1

    update_payload = {
        "title": "Take out trash",
        "cadence": "weekly",
        "description": "Before collection day",
        "owner_id": user["id"],
    }
    response = client.put(
        f"/chores/{chore['id']}", json=update_payload, headers=auth_headers
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["title"] == "Take out trash"
    assert updated["cadence"] == "weekly"

    response = client.get(f"/chores/{chore['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["description"] == "Before collection day"

    response = client.delete(f"/chores/{chore['id']}", headers=auth_headers)
    assert response.status_code == 204

    response = client.get("/chores", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_chore_cadence_validation(client, auth_headers):
    user = _create_user(client, auth_headers)
    response = client.post(
        "/chores",
        json={
            "title": "Laundry",
            "cadence": "yearly",
            "description": "Too rare",
            "owner_id": user["id"],
        },
        headers=auth_headers,
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"


def test_assignments_and_stats_flow(client, auth_headers):
    owner = _create_user(client, auth_headers, name="Dana")
    roommate = _create_user(client, auth_headers, name="Sam")
    chore = _create_chore(client, auth_headers, owner["id"], title="Mop floor")
    assignment = _create_assignment(
        client, auth_headers, user_id=roommate["id"], chore_id=chore["id"]
    )

    response = client.get("/assignments", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["status"] == "pending"

    response = client.patch(
        f"/assignments/{assignment['id']}",
        json={"status": "completed"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

    response = client.get(
        "/assignments", params={"status": "completed"}, headers=auth_headers
    )
    assert response.status_code == 200
    assert len(response.json()) == 1

    stats = client.get("/stats", headers=auth_headers).json()
    assert stats["total_users"] == 2
    assert stats["total_chores"] == 1
    assert stats["assignments"]["total"] == 1
    assert stats["assignments"]["by_status"]["completed"] == 1
    assert stats["assignments"]["overdue"] == 0
