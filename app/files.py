from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Final

PNG_MAGIC: Final = b"\x89PNG\r\n\x1a\n"
JPEG_SOI: Final = b"\xff\xd8"
JPEG_EOI: Final = b"\xff\xd9"
MAX_ATTACHMENT_BYTES: Final = 5_000_000
ALLOWED_MIME_EXT: Final = {"image/png": ".png", "image/jpeg": ".jpg"}


class AttachmentError(Exception):
    def __init__(self, *, code: str, detail: str, status: int = 400):
        self.code = code
        self.detail = detail
        self.status = status
        super().__init__(detail)


@dataclass(frozen=True)
class AttachmentMeta:
    filename: str
    content_type: str
    size: int


def sniff_mime_type(data: bytes) -> str | None:
    if data.startswith(PNG_MAGIC):
        return "image/png"
    if data.startswith(JPEG_SOI) and data.endswith(JPEG_EOI):
        return "image/jpeg"
    return None


def ensure_within_root(path: Path, root: Path) -> None:
    if not str(path).startswith(str(root)):
        raise AttachmentError(
            code="attachment_path_violation",
            detail="Attachment path escapes root directory",
            status=400,
        )
    for parent in path.parents:
        if parent.is_symlink():
            raise AttachmentError(
                code="attachment_symlink_parent",
                detail="Attachment root contains a symlinked directory",
                status=400,
            )


def save_attachment(root: Path, data: bytes) -> AttachmentMeta:
    if len(data) == 0:
        raise AttachmentError(
            code="attachment_empty",
            detail="Attachment payload is empty",
            status=400,
        )
    if len(data) > MAX_ATTACHMENT_BYTES:
        raise AttachmentError(
            code="attachment_too_large",
            detail="Attachment exceeds size limit",
            status=413,
        )
    content_type = sniff_mime_type(data)
    if content_type not in ALLOWED_MIME_EXT:
        raise AttachmentError(
            code="attachment_type_unsupported",
            detail="Attachment must be PNG or JPEG image",
            status=415,
        )
    root = root.resolve(strict=True)
    filename = f"{uuid.uuid4()}{ALLOWED_MIME_EXT[content_type]}"
    path = (root / filename).resolve()
    ensure_within_root(path, root)
    path.write_bytes(data)
    return AttachmentMeta(
        filename=filename,
        content_type=content_type,
        size=len(data),
    )
