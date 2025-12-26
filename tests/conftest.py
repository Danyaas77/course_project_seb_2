# tests/conftest.py
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]  # корень репозитория
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import API_KEY_ENV_VAR, app, reset_app_state  # noqa: E402


@pytest.fixture(autouse=True)
def reset_db():
    reset_app_state()
    yield
    reset_app_state()


@pytest.fixture
def api_key(monkeypatch):
    value = "test-secret"
    monkeypatch.setenv(API_KEY_ENV_VAR, value)
    return value


@pytest.fixture
def client(api_key):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(api_key):
    return {"X-API-Key": api_key}
