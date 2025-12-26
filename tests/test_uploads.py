from pathlib import Path
from uuid import UUID

import pytest

from app.main import MAX_UPLOAD_BYTES, UPLOAD_DIR_ENV_VAR

PNG = b"\x89PNG\r\n\x1a\n"


@pytest.fixture
def upload_dir(tmp_path, monkeypatch) -> Path:
    base = tmp_path / "uploads"
    monkeypatch.setenv(UPLOAD_DIR_ENV_VAR, str(base))
    return base


def test_upload_rejects_large_file(client, auth_headers, upload_dir):
    payload = PNG + (b"0" * (MAX_UPLOAD_BYTES + 1))
    response = client.post(
        "/uploads",
        files={"file": ("big.png", payload, "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == 413
    body = response.json()
    assert body["code"] == "upload_too_large"


def test_upload_rejects_bad_magic(client, auth_headers, upload_dir):
    payload = b"not an image"
    response = client.post(
        "/uploads",
        files={"file": ("weird.png", payload, "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == 415
    body = response.json()
    assert body["code"] == "upload_bad_type"


def test_upload_rejects_traversal_filename(client, auth_headers, upload_dir):
    response = client.post(
        "/uploads",
        files={"file": ("../../escape.png", PNG + b"content", "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "upload_bad_name"


def test_upload_succeeds_with_uuid_name(client, auth_headers, upload_dir):
    payload = PNG + b"\x00" * 10
    response = client.post(
        "/uploads",
        files={"file": ("photo.png", payload, "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    UUID(body["id"])
    assert body["filename"].endswith(".png")
    assert Path(body["filename"]).name == body["filename"]
    saved_path = upload_dir / body["filename"]
    assert saved_path.exists()
    assert saved_path.read_bytes() == payload
