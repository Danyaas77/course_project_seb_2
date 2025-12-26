from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx

from app.config import Settings, get_settings


class NotificationError(Exception):
    def __init__(self, *, code: str, detail: str, status: int = 502):
        self.code = code
        self.detail = detail
        self.status = status
        super().__init__(detail)


@dataclass
class NotificationClient:
    settings: Settings
    timeout_seconds: float = 5.0
    max_attempts: int = 3
    backoff_seconds: float = 0.2
    transport: Optional[httpx.BaseTransport] = field(default=None)

    def _validate_url(self) -> str:
        url = self.settings.notify_webhook_url
        if not url:
            raise NotificationError(
                code="notification_not_configured",
                detail="Notification endpoint is not configured",
                status=503,
            )
        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise NotificationError(
                code="notification_insecure_scheme",
                detail="Notification endpoint must use HTTPS",
                status=400,
            )
        host = (parsed.hostname or "").lower()
        allowed_hosts = self.settings.notify_allowed_hosts
        if allowed_hosts and host not in allowed_hosts:
            raise NotificationError(
                code="notification_host_blocked",
                detail="Notification endpoint host is not allowlisted",
                status=400,
            )
        return url

    def _build_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.settings.notify_token:
            headers["Authorization"] = f"Bearer {self.settings.notify_token}"
        return headers

    def send(self, payload: Dict[str, Any]) -> httpx.Response:
        url = self._validate_url()
        headers = self._build_headers()
        timeout = httpx.Timeout(
            timeout=self.timeout_seconds,
            connect=self.timeout_seconds / 2,
            read=self.timeout_seconds,
            write=self.timeout_seconds / 2,
        )
        last_exc: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                with httpx.Client(timeout=timeout, transport=self.transport) as client:
                    response = client.post(url, json=payload, headers=headers)
                if 200 <= response.status_code < 300:
                    return response
                detail = (
                    f"Notification endpoint returned {response.status_code}"
                    if response.text == ""
                    else f"Notification endpoint returned {response.status_code}: {response.text[:200]}"
                )
                raise NotificationError(
                    code="notification_bad_status",
                    detail=detail,
                    status=502,
                )
            except NotificationError:
                raise
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt == self.max_attempts:
                    break
                time.sleep(self.backoff_seconds * attempt)
        raise NotificationError(
            code="notification_failed",
            detail="Notification could not be delivered",
            status=504,
        ) from last_exc


def build_notification_client() -> NotificationClient:
    return NotificationClient(settings=get_settings())
