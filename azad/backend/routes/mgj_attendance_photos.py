"""Attendance-session photos with geotag — shared across MGJ Pakhwada
(Input/Sports) and Leader Training attendance.

Each photo is tied to a (source_type, source_id):
  source_type = 'pakhwada'         source_id = mgj_pakhwada_sessions.id
  source_type = 'leader_training'  source_id = mgj_leader_trainings.id

Files are stored on disk under UPLOAD_DIR with a UUID filename; the browser
sends latitude/longitude captured at upload time (may be NULL when the
browser blocks geolocation, e.g. on file:// pages). Soft delete keeps the
row for audit and removes the disk file. Pattern mirrors
routes/mgj_campaign_images.py so upload/serve/delete stay consistent.
"""
import os
import sys
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from config import UPLOAD_DIR


router = APIRouter(prefix="/api/mgj-attendance-photos", tags=["MGJ Attendance Photos"])

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_SOURCES = {"pakhwada", "leader_training"}


def _num(v):
    try:
        return float(v) if v not in (None, "", "null", "undefined") else None
    except (TypeError, ValueError):
        return None


@router.post("/{source_type}/{source_id}")
async def upload_attendance_photo(
    source_type: str,
    source_id: int,
    file: UploadFile = File(...),
    latitude: Optional[str] = Form(None),
    longitude: Optional[str] = Form(None),
):
    if source_type not in ALLOWED_SOURCES:
        raise HTTPException(status_code=400, detail="Invalid source_type")
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"Only image files allowed ({', '.join(sorted(ALLOWED_EXT))})",
        )

    content = await file.read()
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large (max {MAX_FILE_BYTES // (1024*1024)} MB)")
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    lat, lon = _num(latitude), _num(longitude)

    with get_cursor() as cur:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        saved_name = f"mgj_att_{source_type}_{source_id}_{uuid.uuid4()}{ext}"
        disk_path = os.path.join(UPLOAD_DIR, saved_name)
        with open(disk_path, "wb") as f:
            f.write(content)
        file_url = f"/uploads/{saved_name}"

        cur.execute(
            """
            INSERT INTO mgj_attendance_photos
                (source_type, source_id, file_name, file_path, file_size, mime_type, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, source_type, source_id, file_name, file_path, file_size,
                      mime_type, latitude, longitude, uploaded_at
            """,
            (source_type, source_id, file.filename, file_url, len(content),
             file.content_type or "", lat, lon),
        )
        row = cur.fetchone()

    return dict(row)


@router.get("/{source_type}/{source_id}")
def list_attendance_photos(source_type: str, source_id: int):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, source_type, source_id, file_name, file_path, file_size,
                   mime_type, latitude, longitude, uploaded_at
              FROM mgj_attendance_photos
             WHERE source_type = %s AND source_id = %s AND deleted_at IS NULL
             ORDER BY uploaded_at DESC, id DESC
            """,
            (source_type, source_id),
        )
        return [dict(r) for r in cur.fetchall()]


@router.delete("/{photo_id}")
def delete_attendance_photo(photo_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT id, file_path, deleted_at FROM mgj_attendance_photos WHERE id = %s", (photo_id,))
        row = cur.fetchone()
        if not row or row.get("deleted_at"):
            raise HTTPException(status_code=404, detail="Photo not found")

        file_path = row["file_path"] or ""
        if file_path.startswith("/uploads/"):
            disk_path = os.path.realpath(os.path.join(UPLOAD_DIR, file_path[len("/uploads/"):]))
            if disk_path.startswith(os.path.realpath(UPLOAD_DIR)) and os.path.isfile(disk_path):
                try:
                    os.remove(disk_path)
                except OSError:
                    pass

        cur.execute("UPDATE mgj_attendance_photos SET deleted_at = NOW() WHERE id = %s", (photo_id,))
    return {"message": "Photo deleted", "id": photo_id}
