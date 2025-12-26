from __future__ import annotations

import base64
from pathlib import Path

from app.files import MAX_ATTACHMENT_BYTES, PNG_MAGIC


def _create_user(client, auth_headers):
    response = client.post("/users", json={"name": "Uploader"}, headers=auth_headers)
    assert response.status_code == 201
    return response.json()


def _create_chore(client, auth_headers, owner_id):
    response = client.post(
        "/chores",
        json={
            "title": "Clean sink",
            "cadence": "weekly",
            "description": "Kitchen duties",
            "owner_id": owner_id,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


def test_upload_attachment_success(client, auth_headers, attachments_root: Path):
    user = _create_user(client, auth_headers)
    chore = _create_chore(client, auth_headers, owner_id=user["id"])
    payload = PNG_MAGIC + b"\x00" * 10

    response = client.post(
        f"/chores/{chore['id']}/attachments",
        headers=auth_headers,
        json={"content": base64.b64encode(payload).decode()},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["filename"].endswith(".png")
    saved_file = attachments_root / body["filename"]
    assert saved_file.exists()
    assert saved_file.read_bytes() == payload


def test_upload_attachment_rejects_bad_type(client, auth_headers):
    user = _create_user(client, auth_headers)
    chore = _create_chore(client, auth_headers, owner_id=user["id"])

    response = client.post(
        f"/chores/{chore['id']}/attachments",
        headers=auth_headers,
        json={"content": base64.b64encode(b"not an image").decode()},
    )

    assert response.status_code == 415
    problem = response.json()
    assert problem["code"] == "attachment_type_unsupported"


def test_upload_attachment_rejects_large_file(client, auth_headers):
    user = _create_user(client, auth_headers)
    chore = _create_chore(client, auth_headers, owner_id=user["id"])
    payload = PNG_MAGIC + b"\x00" * (MAX_ATTACHMENT_BYTES + 1)

    response = client.post(
        f"/chores/{chore['id']}/attachments",
        headers=auth_headers,
        json={"content": base64.b64encode(payload).decode()},
    )

    assert response.status_code == 413
    problem = response.json()
    assert problem["code"] == "attachment_too_large"
