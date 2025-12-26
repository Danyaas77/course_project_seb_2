from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Settings(BaseModel):
    """
    Centralised runtime configuration loaded from environment variables.
    """

    model_config = ConfigDict(frozen=True)

    app_api_key: str = Field(alias="APP_API_KEY")
    attachments_dir: Path = Field(default=Path("attachments"), alias="ATTACHMENTS_DIR")
    notify_webhook_url: Optional[str] = Field(default=None, alias="NOTIFY_WEBHOOK_URL")
    notify_allowed_hosts: List[str] = Field(
        default_factory=list, alias="NOTIFY_ALLOWED_HOSTS"
    )
    notify_token: Optional[str] = Field(default=None, alias="NOTIFY_TOKEN")

    @field_validator("app_api_key")
    @classmethod
    def ensure_api_key(cls, value: str) -> str:
        if not value:
            raise ValueError("APP_API_KEY must be configured")
        return value

    @field_validator("attachments_dir", mode="before")
    @classmethod
    def prepare_dir(cls, value: str | Path | None) -> Path:
        raw_path = Path(value) if value else Path("attachments")
        raw_path.mkdir(parents=True, exist_ok=True)
        resolved = raw_path.resolve()
        if not resolved.is_dir():
            raise ValueError("Attachments path must be a directory")
        return resolved

    @field_validator("notify_allowed_hosts", mode="before")
    @classmethod
    def split_hosts(cls, value: str | List[str] | None) -> List[str]:
        if not value:
            return []
        if isinstance(value, str):
            return [
                host.strip().lower()
                for host in value.split(",")
                if host.strip()
            ]
        return [host.lower() for host in value]


def _environment_payload() -> dict[str, object]:
    return {
        "APP_API_KEY": os.environ.get("APP_API_KEY", ""),
        "ATTACHMENTS_DIR": os.environ.get("ATTACHMENTS_DIR"),
        "NOTIFY_WEBHOOK_URL": os.environ.get("NOTIFY_WEBHOOK_URL"),
        "NOTIFY_ALLOWED_HOSTS": os.environ.get("NOTIFY_ALLOWED_HOSTS"),
        "NOTIFY_TOKEN": os.environ.get("NOTIFY_TOKEN"),
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Load settings once per process. Tests can call `reload_settings()` after
    adjusting environment variables.
    """

    return Settings(**_environment_payload())


def reload_settings() -> None:
    """
    Helper for tests to reload settings after moving environment variables.
    """

    get_settings.cache_clear()  # type: ignore[attr-defined]
