
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Final


_TRAINEE_IMAGE_RE: Final = re.compile(
    r"^www_trainee_(?P<trainee_id>\d+)_[^/]+"
    r"(?P<extension>\.jpg|\.jpeg|\.png|\.webp|\.gif)$",
    re.IGNORECASE,
)

_SUPPORTED_EXTENSIONS: Final = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _image_directory() -> Path:
    configured_directory = os.getenv("PARTICIPANT_IMAGE_DIRECTORY")

    if configured_directory:
        return Path(configured_directory).expanduser().resolve()

    app_directory = Path(__file__).resolve().parents[2]

    return (
        app_directory
        / "storage"
        / "uploads"
        / "participants"
        / "2025"
    )


def _build_image_index() -> dict[int, str]:
    directory = _image_directory()

    if not directory.is_dir():
        return {}

    image_index: dict[int, str] = {}

    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue

        if path.suffix.lower() not in _SUPPORTED_EXTENSIONS:
            continue

        match = _TRAINEE_IMAGE_RE.fullmatch(path.name)

        if not match:
            continue

        trainee_id = int(match.group("trainee_id"))

        # One image per trainee ID
        image_index.setdefault(trainee_id, path.name)

    return image_index


_IMAGE_INDEX = _build_image_index()


def participant_image_url(
    participant_id: int,
    stored_image: str | None = None,
) -> str | None:
    """
    Return a participant's unique image.

    Priority:
    1. Real stored participant image (S3 bucket URL or folder path).
    2. Image whose filename contains this participant's ID.
    3. None if no participant-specific image is available.
    """

    if stored_image and isinstance(stored_image, str):
        image = stored_image.strip()

        # S3 bucket or external URL
        if image.lower().startswith(
            ("http://", "https://", "blob:", "data:")
        ):
            return image

        # Local folder path or filename
        clean_img = image.lstrip("/")
        if clean_img.lower().startswith("app/"):
            clean_img = clean_img[4:]

        if clean_img:
            return clean_img

    return _IMAGE_INDEX.get(participant_id)


def deduplicate_participant_images(items: list[dict]) -> list[dict]:
    """Ensure duplicate fallback images are avoided while preserving real participant images."""
    for item in items:
        participant_id = item.get("participant_id")
        image = item.get("image")

        if image and isinstance(image, str) and image.strip():
            # Real image exists (S3 URL or folder path), preserve it
            continue

        fallback_image = (
            _IMAGE_INDEX.get(int(participant_id))
            if participant_id is not None
            else None
        )

        if fallback_image:
            item["image"] = fallback_image

    return items