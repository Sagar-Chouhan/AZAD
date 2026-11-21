from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

MEDIA_ROOT = Path(__file__).resolve().parents[2] / "uploads"

MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # 200 MB

ALLOWED_EXTENSIONS = {
    "image": {".jpg", ".jpeg", ".png", ".webp", ".gif"},
    "pdf": {".pdf"},
    "ppt": {".ppt", ".pptx"},
    "video": {".mp4", ".webm", ".mov", ".mkv"},
}

ALLOWED_MIME_TYPES = {
    "image": ["image/jpeg", "image/png", "image/webp", "image/gif"],
    "pdf": ["application/pdf"],
    "ppt": ["application/vnd.ms-powerpoint", "application/vnd.openxmlformats-officedocument.presentationml.presentation"],
    "video": ["video/mp4", "video/webm", "video/quicktime", "video/x-matroska"],
}


def _validate(upload: UploadFile, kind: str) -> str:
    allowed_ext = ALLOWED_EXTENSIONS.get(kind.lower())
    if allowed_ext is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported upload kind: {kind}",
        )

    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in allowed_ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Allowed formats: {', '.join(sorted(allowed_ext))}",
        )

    # MIME type validation
    allowed_mime = ALLOWED_MIME_TYPES.get(kind.lower())
    if allowed_mime:
        mime_type = upload.content_type
        if not mime_type or mime_type not in allowed_mime:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type for {kind}. Allowed MIME types: {', '.join(allowed_mime)}",
            )

    return suffix


def save_upload(upload: UploadFile, kind: str, folder: str) -> str:
    """Persist an upload and return the public URL path."""
    suffix = _validate(upload, kind)

    # Size check: seek to the end rather than reading the file into memory.
    upload.file.seek(0, 2)
    size = upload.file.tell()
    upload.file.seek(0)

    if size > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File is larger than 200 MB.",
        )

    target_dir = MEDIA_ROOT / folder
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{suffix}"
    target_path = target_dir / filename

    with target_path.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

    return f"/uploads/{folder}/{filename}"


def delete_upload(url_path: str | None) -> None:
    """Remove a previously saved file. Missing files are ignored."""
    if not url_path:
        return

    relative = url_path.removeprefix("/uploads/")
    # Prevent path traversal
    try:
        target = (MEDIA_ROOT / relative).resolve()
        # Ensure the target is within MEDIA_ROOT
        target.relative_to(MEDIA_ROOT.resolve())
    except (ValueError, AttributeError):
        # Ignore attempts to traverse directories or invalid paths
        return

    try:
        target.unlink(missing_ok=True)
    except OSError:
        pass
