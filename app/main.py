import os
import secrets
from datetime import datetime, timezone
from enum import Enum
from http import HTTPStatus
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from fastapi import (
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="SecDev Course App", version="0.1.0")

API_KEY_ENV_VAR = "APP_API_KEY"
CORRELATION_ID_HEADER = "X-Correlation-ID"
UPLOAD_DIR_ENV_VAR = "UPLOAD_DIR"
MAX_UPLOAD_BYTES = 5_000_000
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_SOI = b"\xff\xd8"
JPEG_EOI = b"\xff\xd9"
ALLOWED_UPLOAD_TYPES = {"image/png": ".png", "image/jpeg": ".jpg"}
ASSIGNMENT_WEBHOOK_URL_ENV = "ASSIGNMENT_WEBHOOK_URL"
ASSIGNMENT_WEBHOOK_ALLOWLIST_ENV = "ASSIGNMENT_WEBHOOK_ALLOWLIST"
ASSIGNMENT_WEBHOOK_TIMEOUT_ENV = "ASSIGNMENT_WEBHOOK_TIMEOUT_SECONDS"
ASSIGNMENT_WEBHOOK_RETRIES_ENV = "ASSIGNMENT_WEBHOOK_MAX_RETRIES"
_WEBHOOK_TRANSPORT_OVERRIDE: httpx.BaseTransport | None = None


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get(CORRELATION_ID_HEADER) or str(uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers[CORRELATION_ID_HEADER] = correlation_id
    return response


class ApiError(Exception):
    def __init__(
        self,
        *,
        status: int,
        title: str,
        detail: str,
        type_: str = "about:blank",
        code: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        self.status = status
        self.title = title
        self.detail = detail
        self.type_ = type_
        self.code = code
        self.extra = extra or {}
        super().__init__(detail)


def build_problem(
    request: Request,
    *,
    status: int,
    title: str,
    detail: str,
    type_: str = "about:blank",
    code: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    correlation_id = getattr(request.state, "correlation_id", str(uuid4()))
    if type_ == "about:blank" and code:
        type_ = f"https://example.com/problems/{code.replace('_', '-')}"
    problem: Dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": str(request.url.path),
        "correlation_id": correlation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if code:
        problem["code"] = code
    if extra:
        problem.update(extra)
    return problem


def problem_response(
    request: Request,
    *,
    status: int,
    title: str,
    detail: str,
    type_: str = "about:blank",
    code: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    problem = build_problem(
        request,
        status=status,
        title=title,
        detail=detail,
        type_=type_,
        code=code,
        extra=extra,
    )
    return JSONResponse(
        status_code=status,
        content=problem,
        media_type="application/problem+json",
        headers={CORRELATION_ID_HEADER: problem["correlation_id"]},
    )


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return problem_response(
        request,
        status=exc.status,
        title=exc.title,
        detail=exc.detail,
        type_=exc.type_,
        code=exc.code,
        extra=exc.extra,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Mask untrusted details coming from upstream exceptions.
    detail = "The request could not be processed"
    try:
        title = HTTPStatus(exc.status_code).phrase  # type: ignore[arg-type]
    except ValueError:
        title = "HTTP Error"
    return problem_response(
        request,
        status=exc.status_code,
        title=title,
        detail=detail,
        code="http_error",
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    request: Request, exc: RequestValidationError
):
    simplified_errors: List[Dict[str, Any]] = []
    for err in exc.errors():
        simplified_errors.append(
            {
                "field": ".".join(str(part) for part in err.get("loc", [])),
                "message": err.get("msg", "validation error"),
            }
        )
    return problem_response(
        request,
        status=422,
        title="Unprocessable Entity",
        detail="Request validation failed",
        type_="https://example.com/problems/validation-error",
        code="validation_error",
        extra={"errors": simplified_errors},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Deliberately hide implementation details from clients.
    return problem_response(
        request,
        status=500,
        title="Internal Server Error",
        detail="The server encountered an internal error",
        type_="https://example.com/problems/internal-error",
        code="internal_error",
    )


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.environ.get(API_KEY_ENV_VAR)
    if not expected:
        raise ApiError(
            status=500,
            title="Internal Server Error",
            detail="API key not configured",
            type_="https://example.com/problems/configuration-error",
            code="config_error",
        )
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise ApiError(
            status=401,
            title="Unauthorized",
            detail="Invalid API key",
            type_="https://example.com/problems/invalid-api-key",
            code="unauthorized",
        )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/uploads", status_code=201)
def upload_attachment(
    file: UploadFile = File(...),
    _: None = Depends(require_api_key),
):
    """
    Accepts small image uploads, validates magic bytes, and stores them under a UUID name.
    """
    return _save_upload(file)


# Example storage for demo/testing purposes


def _initial_state() -> Dict[str, Any]:
    return {
        "items": [],
        "users": {},
        "chores": {},
        "assignments": {},
        "uploads": {},
        "sequence": {
            "user": 1,
            "chore": 1,
            "assignment": 1,
        },
    }


_DB = _initial_state()


def reset_app_state() -> None:
    """
    Helper used by tests to reset in-memory state between runs.
    """
    _DB.clear()
    _DB.update(_initial_state())


def _next_sequence(name: str) -> int:
    sequence = _DB["sequence"][name]
    _DB["sequence"][name] += 1
    return sequence


def _parse_iso_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)

def _validate_upload_filename(filename: str) -> None:
    if not filename:
        raise ApiError(
            status=400,
            title="Bad Request",
            detail="Filename is required",
            code="upload_bad_name",
        )
    if Path(filename).name != filename or ".." in filename or "/" in filename or "\\" in filename:
        raise ApiError(
            status=400,
            title="Bad Request",
            detail="Invalid filename",
            code="upload_bad_name",
        )


def _read_upload_bytes(upload: UploadFile) -> bytes:
    data = bytearray()
    chunk_size = 1024 * 1024
    while True:
        chunk = upload.file.read(chunk_size)
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > MAX_UPLOAD_BYTES:
            raise ApiError(
                status=413,
                title="Payload Too Large",
                detail="Upload exceeds size limit",
                code="upload_too_large",
            )
    return bytes(data)


def _sniff_upload_type(payload: bytes) -> Optional[str]:
    if payload.startswith(PNG_MAGIC):
        return "image/png"
    if payload.startswith(JPEG_SOI) and payload.endswith(JPEG_EOI):
        return "image/jpeg"
    return None


def _resolve_upload_dir() -> Path:
    base_dir = Path(os.environ.get(UPLOAD_DIR_ENV_VAR, "uploads"))
    if base_dir.exists() and base_dir.is_symlink():
        raise ApiError(
            status=400,
            title="Bad Request",
            detail="Upload directory must not be a symlink",
            code="upload_dir_invalid",
        )
    base_dir.mkdir(parents=True, exist_ok=True)
    resolved = base_dir.resolve()
    return resolved


def _persist_upload(payload: bytes, mime: str) -> Dict[str, Any]:
    base_dir = _resolve_upload_dir()
    extension = ALLOWED_UPLOAD_TYPES[mime]
    upload_id = str(uuid4())
    filename = f"{upload_id}{extension}"
    target = (base_dir / filename).resolve()
    if not str(target).startswith(str(base_dir)):
        raise ApiError(
            status=400,
            title="Bad Request",
            detail="Upload path is not allowed",
            code="upload_path_traversal",
        )
    if any(parent.is_symlink() for parent in target.parents):
        raise ApiError(
            status=400,
            title="Bad Request",
            detail="Upload path crosses a symlink",
            code="upload_path_traversal",
        )
    with open(target, "wb") as fh:
        fh.write(payload)
    record = {"id": upload_id, "mime": mime, "size": len(payload), "filename": filename}
    _DB["uploads"][upload_id] = record
    return record


def _save_upload(upload: UploadFile) -> Dict[str, Any]:
    _validate_upload_filename(upload.filename)
    payload = _read_upload_bytes(upload)
    mime = _sniff_upload_type(payload)
    if not mime or mime not in ALLOWED_UPLOAD_TYPES:
        raise ApiError(
            status=415,
            title="Unsupported Media Type",
            detail="Only png and jpeg images are supported",
            code="upload_bad_type",
            extra={"received_type": upload.content_type},
        )
    return _persist_upload(payload, mime)


class SafeHttpClient:
    def __init__(
        self,
        *,
        allow_hosts: Sequence[str],
        timeout: float = 2.0,
        max_retries: int = 1,
        transport: httpx.BaseTransport | None = None,
    ):
        if not allow_hosts:
            raise ValueError("allow_hosts is required")
        self.allow_hosts = {host.lower() for host in allow_hosts if host}
        self.timeout = timeout
        self.max_retries = max(max_retries, 0)
        self.transport = transport

    def _validated_url(self, raw_url: str) -> tuple[str, str]:
        parsed = urlparse(raw_url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme not in {"http", "https"}:
            raise ApiError(
                status=400,
                title="Bad Request",
                detail="Webhook scheme must be http or https",
                code="webhook_invalid_scheme",
            )
        if host not in self.allow_hosts:
            raise ApiError(
                status=400,
                title="Bad Request",
                detail="Destination host is not allow-listed",
                code="webhook_host_blocked",
            )
        if not host:
            raise ApiError(
                status=400,
                title="Bad Request",
                detail="Webhook host missing",
                code="webhook_host_blocked",
            )
        return parsed.geturl(), host

    def post_json(self, url: str, payload: Dict[str, Any]) -> None:
        normalized_url, host = self._validated_url(url)
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
                    response = client.post(normalized_url, json=payload)
                response.raise_for_status()
                return
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_exc = exc
                if attempt >= self.max_retries:
                    raise ApiError(
                        status=502,
                        title="Bad Gateway",
                        detail="Failed to deliver webhook",
                        type_="https://example.com/problems/webhook-delivery-failed",
                        code="webhook_failed",
                        extra={"host": host, "reason": exc.__class__.__name__},
                    )
        if last_exc:
            raise last_exc


def _notify_assignment_completed(assignment: Dict[str, Any]) -> None:
    webhook_url = os.environ.get(ASSIGNMENT_WEBHOOK_URL_ENV)
    if not webhook_url:
        return
    allow_hosts_env = os.environ.get(ASSIGNMENT_WEBHOOK_ALLOWLIST_ENV, "")
    allow_hosts = {host.strip().lower() for host in allow_hosts_env.split(",") if host.strip()}
    parsed = urlparse(webhook_url)
    if parsed.hostname and not allow_hosts:
        allow_hosts.add(parsed.hostname.lower())
    if not allow_hosts:
        raise ApiError(
            status=500,
            title="Internal Server Error",
            detail="Webhook allowlist is empty",
            code="webhook_config_invalid",
        )
    if parsed.hostname and parsed.hostname.lower() not in allow_hosts:
        raise ApiError(
            status=400,
            title="Bad Request",
            detail="Destination host is not allow-listed",
            code="webhook_host_blocked",
        )
    timeout_seconds = float(os.environ.get(ASSIGNMENT_WEBHOOK_TIMEOUT_ENV, "2.0"))
    max_retries = int(os.environ.get(ASSIGNMENT_WEBHOOK_RETRIES_ENV, "1"))
    client = SafeHttpClient(
        allow_hosts=allow_hosts,
        timeout=timeout_seconds,
        max_retries=max_retries,
        transport=_WEBHOOK_TRANSPORT_OVERRIDE,
    )
    status_value = (
        assignment["status"].value
        if isinstance(assignment["status"], AssignmentStatus)
        else assignment["status"]
    )
    client.post_json(
        webhook_url,
        {
            "assignment_id": assignment["id"],
            "user_id": assignment["user_id"],
            "chore_id": assignment["chore_id"],
            "status": status_value,
        },
    )


class ItemCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[A-Za-z0-9 _\-]+$",
        description="Human readable item name",
    )

    @field_validator("name", mode="before")
    @classmethod
    def strip_and_validate(cls, value: str) -> str:
        if value is None:
            raise ValueError("name must be provided")
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must be 1..100 chars after trimming")
        return stripped


@app.post("/items")
def create_item(
    payload: ItemCreate,
    _: None = Depends(require_api_key),
):
    item = {"id": len(_DB["items"]) + 1, "name": payload.name}
    _DB["items"].append(item)
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise ApiError(
        status=404,
        title="Not Found",
        detail="Item not found",
        type_="https://example.com/problems/item-not-found",
        code="not_found",
    )


class ChoreCadence(str, Enum):
    daily = "daily"
    weekly = "weekly"
    biweekly = "biweekly"
    monthly = "monthly"
    adhoc = "adhoc"


class AssignmentStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    skipped = "skipped"


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=60)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("name must contain visible characters")
        return trimmed


class UserRead(UserCreate):
    id: int


class ChoreBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    cadence: ChoreCadence
    description: Optional[str] = Field(default=None, max_length=500)

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("title must contain visible characters")
        return trimmed


class ChoreCreate(ChoreBase):
    owner_id: int = Field(..., gt=0)


class ChoreUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    cadence: Optional[ChoreCadence] = None
    description: Optional[str] = Field(default=None, max_length=500)
    owner_id: Optional[int] = Field(default=None, gt=0)

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("title must contain visible characters")
        return trimmed


class ChoreRead(ChoreBase):
    id: int
    owner_id: int


class AssignmentBase(BaseModel):
    user_id: int = Field(..., gt=0)
    chore_id: int = Field(..., gt=0)
    due_at: datetime

    @field_validator("due_at", mode="before")
    @classmethod
    def parse_due_at(cls, value: Any) -> Any:
        if isinstance(value, str):
            return _parse_iso_datetime(value)
        return value

    @field_validator("due_at")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class AssignmentCreate(AssignmentBase):
    status: AssignmentStatus = AssignmentStatus.pending


class AssignmentUpdate(BaseModel):
    status: Optional[AssignmentStatus] = None
    due_at: Optional[datetime] = None

    @field_validator("due_at", mode="before")
    @classmethod
    def parse_due_at(cls, value: Any) -> Any:
        if isinstance(value, str):
            return _parse_iso_datetime(value)
        return value

    @field_validator("due_at")
    @classmethod
    def ensure_timezone(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return value
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class AssignmentRead(AssignmentBase):
    id: int
    status: AssignmentStatus


class AssignmentStats(BaseModel):
    total: int
    by_status: Dict[str, int]
    overdue: int


class StatsResponse(BaseModel):
    total_users: int
    total_chores: int
    assignments: AssignmentStats


def _get_user_or_404(user_id: int) -> Dict[str, Any]:
    user = _DB["users"].get(user_id)
    if not user:
        raise ApiError(
            status=404,
            title="Not Found",
            detail="User not found",
            type_="https://example.com/problems/user-not-found",
            code="user_not_found",
        )
    return user


def _get_chore_or_404(chore_id: int) -> Dict[str, Any]:
    chore = _DB["chores"].get(chore_id)
    if not chore:
        raise ApiError(
            status=404,
            title="Not Found",
            detail="Chore not found",
            type_="https://example.com/problems/chore-not-found",
            code="chore_not_found",
        )
    return chore


def _get_assignment_or_404(assignment_id: int) -> Dict[str, Any]:
    assignment = _DB["assignments"].get(assignment_id)
    if not assignment:
        raise ApiError(
            status=404,
            title="Not Found",
            detail="Assignment not found",
            type_="https://example.com/problems/assignment-not-found",
            code="assignment_not_found",
        )
    return assignment


@app.post("/users", status_code=201, response_model=UserRead)
def create_user(
    payload: UserCreate,
    _: None = Depends(require_api_key),
):
    user_id = _next_sequence("user")
    user = {"id": user_id, "name": payload.name}
    _DB["users"][user_id] = user
    return user


@app.get("/users", response_model=List[UserRead])
def list_users(_: None = Depends(require_api_key)):
    return list(_DB["users"].values())


@app.post("/chores", status_code=201, response_model=ChoreRead)
def create_chore(
    payload: ChoreCreate,
    _: None = Depends(require_api_key),
):
    _get_user_or_404(payload.owner_id)
    chore_id = _next_sequence("chore")
    chore = {
        "id": chore_id,
        "title": payload.title,
        "cadence": payload.cadence,
        "description": payload.description,
        "owner_id": payload.owner_id,
    }
    _DB["chores"][chore_id] = chore
    return chore


@app.get("/chores", response_model=List[ChoreRead])
def list_chores(_: None = Depends(require_api_key)):
    return list(_DB["chores"].values())


@app.get("/chores/{chore_id}", response_model=ChoreRead)
def get_chore(chore_id: int, _: None = Depends(require_api_key)):
    return _get_chore_or_404(chore_id)


@app.put("/chores/{chore_id}", response_model=ChoreRead)
def update_chore(
    chore_id: int,
    payload: ChoreUpdate,
    _: None = Depends(require_api_key),
):
    chore = _get_chore_or_404(chore_id).copy()
    update_data = payload.model_dump(exclude_unset=True)
    owner_id = update_data.get("owner_id")
    if owner_id is not None:
        _get_user_or_404(owner_id)
    chore.update(update_data)
    _DB["chores"][chore_id] = chore
    return chore


@app.delete("/chores/{chore_id}", status_code=204)
def delete_chore(chore_id: int, _: None = Depends(require_api_key)):
    _get_chore_or_404(chore_id)
    _DB["chores"].pop(chore_id, None)
    for assignment_id, assignment in list(_DB["assignments"].items()):
        if assignment["chore_id"] == chore_id:
            _DB["assignments"].pop(assignment_id, None)
    return None


@app.post("/assignments", status_code=201, response_model=AssignmentRead)
def create_assignment(
    payload: AssignmentCreate,
    _: None = Depends(require_api_key),
):
    _get_user_or_404(payload.user_id)
    _get_chore_or_404(payload.chore_id)
    assignment_id = _next_sequence("assignment")
    assignment = {
        "id": assignment_id,
        "user_id": payload.user_id,
        "chore_id": payload.chore_id,
        "due_at": payload.due_at,
        "status": payload.status,
    }
    _DB["assignments"][assignment_id] = assignment
    return assignment


@app.get("/assignments", response_model=List[AssignmentRead])
def list_assignments(
    status: Optional[AssignmentStatus] = Query(default=None),
    _: None = Depends(require_api_key),
):
    assignments = list(_DB["assignments"].values())
    if status is not None:
        assignments = [a for a in assignments if a["status"] == status]
    return assignments


@app.patch("/assignments/{assignment_id}", response_model=AssignmentRead)
def update_assignment(
    assignment_id: int,
    payload: AssignmentUpdate,
    _: None = Depends(require_api_key),
):
    assignment = _get_assignment_or_404(assignment_id).copy()
    previous_status = assignment["status"]
    update_data = payload.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] is not None:
        assignment["status"] = update_data["status"]
    if "due_at" in update_data and update_data["due_at"] is not None:
        assignment["due_at"] = update_data["due_at"]
    should_notify = (
        assignment["status"] == AssignmentStatus.completed
        and previous_status != AssignmentStatus.completed
    )
    if should_notify:
        _notify_assignment_completed(assignment)
    _DB["assignments"][assignment_id] = assignment
    return assignment


@app.get("/stats", response_model=StatsResponse)
def get_stats(_: None = Depends(require_api_key)):
    assignments = list(_DB["assignments"].values())
    by_status: Dict[str, int] = {status.value: 0 for status in AssignmentStatus}
    for assignment in assignments:
        key = assignment["status"].value
        by_status[key] = by_status.get(key, 0) + 1
    now = datetime.now(timezone.utc)
    overdue = sum(
        1
        for assignment in assignments
        if assignment["status"] != AssignmentStatus.completed
        and assignment["due_at"] < now
    )
    payload = StatsResponse(
        total_users=len(_DB["users"]),
        total_chores=len(_DB["chores"]),
        assignments=AssignmentStats(
            total=len(assignments),
            by_status=by_status,
            overdue=overdue,
        ),
    )
    return payload
