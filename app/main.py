import os
import secrets
from datetime import datetime, timezone
from enum import Enum
from http import HTTPStatus
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="SecDev Course App", version="0.1.0")


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
    problem: Dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": str(request.url.path),
        "correlation_id": str(uuid4()),
    }
    if code:
        problem["code"] = code
    if extra:
        problem.update(extra)
    return problem


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    problem = build_problem(
        request,
        status=exc.status,
        title=exc.title,
        detail=exc.detail,
        type_=exc.type_,
        code=exc.code,
        extra=exc.extra,
    )
    return JSONResponse(status_code=exc.status, content=problem)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    try:
        title = HTTPStatus(exc.status_code).phrase  # type: ignore[arg-type]
    except ValueError:
        title = "HTTP Error"
    problem = build_problem(
        request,
        status=exc.status_code,
        title=title,
        detail=detail,
        code="http_error",
    )
    return JSONResponse(status_code=exc.status_code, content=problem)


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
    problem = build_problem(
        request,
        status=422,
        title="Unprocessable Entity",
        detail="Request validation failed",
        type_="https://example.com/problems/validation-error",
        code="validation_error",
        extra={"errors": simplified_errors},
    )
    return JSONResponse(status_code=422, content=problem)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Deliberately hide implementation details from clients.
    problem = build_problem(
        request,
        status=500,
        title="Internal Server Error",
        detail="The server encountered an internal error",
        type_="https://example.com/problems/internal-error",
        code="internal_error",
    )
    return JSONResponse(status_code=500, content=problem)


@app.get("/health")
def health():
    return {"status": "ok"}


# Example storage for demo/testing purposes


def _initial_state() -> Dict[str, Any]:
    return {
        "items": [],
        "users": {},
        "chores": {},
        "assignments": {},
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

API_KEY_ENV_VAR = "APP_API_KEY"


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
    update_data = payload.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] is not None:
        assignment["status"] = update_data["status"]
    if "due_at" in update_data and update_data["due_at"] is not None:
        assignment["due_at"] = update_data["due_at"]
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
