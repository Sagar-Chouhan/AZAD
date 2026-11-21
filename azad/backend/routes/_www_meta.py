"""WWW tracking helpers — current-user stamping + date format.

Loaded by:
  * database.get_cursor — reads the ContextVar and stamps a Postgres
    session-local `app.current_user_id` so a BEFORE INSERT/UPDATE
    trigger can auto-fill created_by/updated_by.
  * main.py — the HTTP middleware that decodes the Bearer JWT on each
    request and writes the user id into the ContextVar.
  * All WWW export endpoints — imports `format_dt_ap` to render
    Updated At as "26-Aug-2026 10:30 AM" in the xlsx.

Contextvars propagate across Starlette's sync-endpoint threadpool
(anyio.to_thread.run_sync), so setting the value in async middleware
is visible inside every sync WWW route.
"""
from contextvars import ContextVar
from typing import Optional
from datetime import datetime

_current_user_id: ContextVar[Optional[int]] = ContextVar(
    "_www_current_user_id", default=None
)


def set_current_user_id(uid):
    """Store the caller's user id for this request/thread. Called by
    the HTTP middleware after JWT decode."""
    try:
        _current_user_id.set(int(uid) if uid else None)
    except (TypeError, ValueError):
        _current_user_id.set(None)


def get_current_user_id():
    """Return the caller's user id, or None if unauthenticated."""
    return _current_user_id.get()


def format_dt_ap(dt):
    """Render a datetime as '26-Aug-2026 10:30 AM'. Returns '' on None,
    and passes strings through the same handful of layouts psycopg2 or
    JSON might emit."""
    if dt is None or dt == "":
        return ""
    if isinstance(dt, str):
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f%z",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
        ):
            try:
                dt = datetime.strptime(dt, fmt)
                break
            except ValueError:
                continue
        else:
            return dt  # unparseable; return raw string unchanged
    try:
        return dt.strftime("%d-%b-%Y %I:%M %p")
    except Exception:
        return str(dt)
