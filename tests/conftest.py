# tests/conftest.py
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]  # корень репозитория
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import reload_settings  # noqa: E402
from app.main import API_KEY_ENV_VAR, app, reset_app_state  # noqa: E402


@pytest.fixture(autouse=True)
def reset_db():
    reset_app_state()
    yield
    reset_app_state()


@pytest.fixture(autouse=True)
def attachments_root(tmp_path, monkeypatch):
    root = tmp_path / "attachments"
    root.mkdir()
    monkeypatch.setenv("ATTACHMENTS_DIR", str(root))
    reload_settings()
    yield root
    reload_settings()


@pytest.fixture
def api_key(monkeypatch):
    value = "test-secret"
    monkeypatch.setenv(API_KEY_ENV_VAR, value)
    reload_settings()
    yield value
    reload_settings()


@pytest.fixture
def client(api_key):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(api_key):
    return {"X-API-Key": api_key}
