"""Role and User CRUD routes.

LIVE build 2026-09-17: stage users.py (WWW Mobiliser accounts + Reset Password
body) with live's real-user INSERT/UPDATE statements (no state/district/centre
codes written from the form)."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
from passlib.context import CryptContext
import sys, os, io, csv, re
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from models.user import RoleCreate, UserCreate, UserUpdate
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["Roles & Users"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ResetPasswordBody(BaseModel):
    new_password: Optional[str] = None


# ============================================================================
# 2026-08-26: WWW Mobiliser (role_id=11) is stored in www_mobilisers, NOT
# users. All /api/users CRUD for that role is transparently routed here so
# the mobile app's /api/www-mobilisers/auth/login can authenticate them.
# ids returned for these virtual "users" are offset by _WWWMOB_OFFSET to
# guarantee they never collide with a real users.id.
# ============================================================================
_WWWMOB_ROLE_ID = 11
_WWWMOB_OFFSET  = 10_000_000
_WWWMOB_ROLE_NAME = "Mobiliser (WWW)"

def _wwwmob_vid(real_id: int) -> int:
    return _WWWMOB_OFFSET + int(real_id)

def _wwwmob_is(user_id: int) -> bool:
    return int(user_id) >= _WWWMOB_OFFSET

def _wwwmob_real_id(virtual_id: int) -> int:
    return int(virtual_id) - _WWWMOB_OFFSET

_GEO_BRACKET_RE = re.compile(r"\[([^\]|]*)\|([^\]|]*)\|([^\]|]*)\]\s*$")

def _wwwmob_parse_geo(geo_scope):
    """Extract (state_code, district_code, centre_code) from a geo_scope
    string that the User Management form composes as
    'Centre, District [ST|DS|CT]'. Returns (None, None, None) when the
    trailing bracket isn't present or is blank."""
    if not geo_scope:
        return (None, None, None)
    m = _GEO_BRACKET_RE.search(geo_scope)
    if not m:
        return (None, None, None)
    s = (m.group(1) or "").strip() or None
    d = (m.group(2) or "").strip() or None
    c = (m.group(3) or "").strip() or None
    return (s, d, c)

def _wwwmob_compose_geo(m) -> str:
    """Compose a display-friendly geo_scope string from a www_mobilisers
    row. Mirrors what the User Management form saves for real users."""
    st = (m.get("state_code")   or "").strip()
    ds = (m.get("district_code") or "").strip()
    ct = (m.get("centre_code")  or "").strip()
    st_name = (m.get("state_name")   or st or "").strip()
    ds_name = (m.get("district_name") or ds or "").strip()
    ct_name = (m.get("centre_name")  or ct or "").strip()
    if ct_name and st_name:
        head = ct_name + (", " + ds_name if ds_name else "") + ", " + st_name
    elif ds_name and st_name:
        head = ds_name + ", " + st_name
    elif st_name:
        head = st_name
    else:
        head = "National (All Centres)"
    tail = " [" + st + "|" + ds + "|" + ct + "]" if (st or ds or ct) else ""
    return head + tail

def _wwwmob_row_as_user(row) -> dict:
    """Map a www_mobilisers row (as returned by the SELECT below) to the
    same dict shape /api/users emits so the frontend list/detail can
    render it without any branching."""
    return {
        "id":          _wwwmob_vid(row["id"]),
        "name":        row.get("name") or "",
        "email":       row.get("email") or "",
        "phone":       row.get("mobile") or "",
        "role_id":     _WWWMOB_ROLE_ID,
        "geo_scope":   _wwwmob_compose_geo(row),
        "status":      row.get("status") or "Active",
        "last_login":  row.get("last_login_at"),
        "created_at":  row.get("created_at"),
        "role_name":   _WWWMOB_ROLE_NAME,
        "username":    row.get("mobiliser_id") or "",
    }

_WWWMOB_SELECT_SQL = """
    SELECT m.id, m.mobiliser_id, m.name, m.email, m.mobile,
           m.state_code, m.district_code, m.centre_code,
           m.status, m.last_login_at, m.created_at,
           COALESCE(ns.state_name,    m.state_code)    AS state_name,
           COALESCE(nd.district_name, m.district_code) AS district_name,
           COALESCE(nc.centre_name,   m.centre_code)   AS centre_name
    FROM www_mobilisers m
    LEFT JOIN central_states    ns ON m.state_code    = ns.state_code
    LEFT JOIN central_districts nd ON m.district_code = nd.district_code
    LEFT JOIN central_centres   nc ON m.centre_code   = nc.centre_code
    WHERE m.deleted_at IS NULL
"""


@router.get("/users/export/excel")
def export_users_excel(role_id: Optional[int] = None, status: Optional[str] = None):
    """Export user list as CSV."""
    with get_cursor() as cur:
        where = "WHERE u.deleted_at IS NULL"
        params = []
        if role_id:
            where += " AND u.role_id = %s"; params.append(role_id)
        if status:
            where += " AND u.status = %s"; params.append(status)
        cur.execute(f"""
            SELECT u.name, u.email, r.name as role_name, u.geo_scope, u.status, u.last_login, u.created_at
            FROM mis_user u JOIN roles r ON u.role_id = r.id {where} ORDER BY u.name
        """, params)
        rows = cur.fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Email', 'Role', 'Geo Scope', 'Status', 'Last Login', 'Created At'])
    for r in rows:
        writer.writerow([r['name'], r['email'], r['role_name'], r['geo_scope'] or '', r['status'] or '',
                         str(r['last_login'] or ''), str(r['created_at'] or '')])
    from datetime import date
    from export_helper import csv_string_to_xlsx_response
    return csv_string_to_xlsx_response(output.getvalue(), f"Users_Export_{date.today().isoformat()}.xlsx")


@router.get("/roles")
def list_roles(page: int = 1, limit: int = 10):
    offset = (page - 1) * limit
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) as total FROM roles")
        total = cur.fetchone()["total"]
        cur.execute("""
            SELECT r.id, r.name, r.description, r.created_at,
                   (SELECT COUNT(*) FROM mis_user u WHERE u.role_id = r.id AND u.deleted_at IS NULL) as user_count
            FROM roles r ORDER BY r.id
            LIMIT %s OFFSET %s
        """, (limit, offset))
        return {"total": total, "page": page, "limit": limit, "data": cur.fetchall()}

@router.post("/roles")
def create_role(role: RoleCreate):
    with get_cursor() as cur:
        cur.execute("INSERT INTO roles (name, description) VALUES (%s, %s) RETURNING *", (role.name, role.description))
        return cur.fetchone()

@router.get("/roles/{role_id}")
def get_role(role_id: int):
    with get_cursor() as cur:
        cur.execute("""
            SELECT r.id, r.name, r.description, r.created_at,
                   (SELECT COUNT(*) FROM mis_user u WHERE u.role_id = r.id AND u.deleted_at IS NULL) as user_count
            FROM roles r WHERE r.id = %s
        """, (role_id,))
        role = cur.fetchone()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return dict(role)

@router.put("/roles/{role_id}")
def update_role(role_id: int, role: RoleCreate):
    with get_cursor() as cur:
        cur.execute("UPDATE roles SET name = %s, description = %s WHERE id = %s RETURNING *", (role.name, role.description, role_id))
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Role not found")
        return result


@router.get("/users")
def list_users(role_id: Optional[int] = None, status: Optional[str] = None,
               name: Optional[str] = None, geo_scope: Optional[str] = None,
               state_code: Optional[str] = None, district_code: Optional[str] = None,
               centre_code: Optional[str] = None,
               page: int = 1, limit: int = 10):
    offset = (page - 1) * limit
    with get_cursor() as cur:
        where = "WHERE u.deleted_at IS NULL"
        params = []
        if role_id:
            where += " AND u.role_id = %s"
            params.append(role_id)
        if status:
            where += " AND u.status = %s"
            params.append(status)
        # geo_scope is a free-text label like "Delhi", "East Delhi, East Delhi",
        # "Delhi Centre", etc. The earlier code tried IN(...) with exact match,
        # which silently dropped any user whose geo_scope had a comma, suffix,
        # or extra word. Switch to ILIKE substring matching so the state /
        # district / centre filters match users whose scope CONTAINS the
        # corresponding name.
        if state_code:
            where += (
                " AND ("
                "EXISTS (SELECT 1 FROM central_states ns       WHERE ns.state_code = %s    AND u.geo_scope ILIKE '%%' || ns.state_name    || '%%') OR "
                "EXISTS (SELECT 1 FROM central_districts nd    WHERE nd.state_code = %s    AND u.geo_scope ILIKE '%%' || nd.district_name || '%%') OR "
                "EXISTS (SELECT 1 FROM central_centres nc      WHERE nc.state_code = %s    AND u.geo_scope ILIKE '%%' || nc.centre_name   || '%%')"
                ")"
            )
            params.extend([state_code, state_code, state_code])
        if district_code:
            where += (
                " AND ("
                "EXISTS (SELECT 1 FROM central_districts nd    WHERE nd.district_code = %s AND u.geo_scope ILIKE '%%' || nd.district_name || '%%') OR "
                "EXISTS (SELECT 1 FROM central_centres nc      WHERE nc.district_code = %s AND u.geo_scope ILIKE '%%' || nc.centre_name   || '%%')"
                ")"
            )
            params.extend([district_code, district_code])
        if centre_code:
            where += (
                " AND EXISTS (SELECT 1 FROM central_centres nc WHERE nc.centre_code = %s   AND u.geo_scope ILIKE '%%' || nc.centre_name   || '%%')"
            )
            params.append(centre_code)
        if name:
            # Match against name OR email so the User Management "Name" filter
            # can also be used as a quick email-search.
            where += " AND (u.name ILIKE %s OR u.email ILIKE %s)"
            params.append(f"%{name}%")
            params.append(f"%{name}%")
        if geo_scope:
            where += " AND u.geo_scope ILIKE %s"
            params.append(f"%{geo_scope}%")

        # Count total
        cur.execute(f"""
            SELECT COUNT(*) as count
            FROM mis_user u JOIN roles r ON u.role_id = r.id
            {where}
        """, params)
        total = cur.fetchone()["count"]

        # Fetch page
        cur.execute(f"""
            SELECT u.id, u.name, u.email, u.phone, u.role_id, u.geo_scope, u.status, u.last_login, u.created_at,
                   r.name as role_name, u.username
            FROM mis_user u JOIN roles r ON u.role_id = r.id
            {where}
            ORDER BY u.name
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        _u_rows = list(cur.fetchall())
        _u_total = total

        # 2026-08-26: Mobiliser (WWW) rows live in www_mobilisers; merge
        # them in so the User Management list shows them alongside real
        # users. Applies when the role filter is absent or explicitly 11.
        _rid = role_id
        if _rid is None or int(_rid) == _WWWMOB_ROLE_ID:
            _mob_where = ["m.deleted_at IS NULL"]
            _mob_params = []
            if status:
                _mob_where.append("m.status = %s"); _mob_params.append(status)
            if name:
                _mob_where.append("(m.name ILIKE %s OR m.email ILIKE %s OR m.mobiliser_id ILIKE %s)")
                _mob_params.extend([f"%{name}%", f"%{name}%", f"%{name}%"])
            if state_code:
                _mob_where.append("m.state_code = %s"); _mob_params.append(state_code)
            if district_code:
                _mob_where.append("m.district_code = %s"); _mob_params.append(district_code)
            if centre_code:
                _mob_where.append("m.centre_code = %s"); _mob_params.append(centre_code)
            _mob_where_sql = " AND ".join(_mob_where)
            cur.execute("SELECT COUNT(*) AS c FROM www_mobilisers m WHERE " + _mob_where_sql, _mob_params)
            _mob_total = cur.fetchone()["c"]
            _u_total += _mob_total
            # Only fetch page rows if the users query didn't already fill
            # the page. Simple strategy: if users returned fewer than
            # `limit` rows, top up with mobilisers.
            if len(_u_rows) < limit:
                _need = limit - len(_u_rows)
                cur.execute(_WWWMOB_SELECT_SQL + " AND " + _mob_where_sql +
                            " ORDER BY m.name LIMIT %s OFFSET %s",
                            _mob_params + [_need, max(0, offset - total)])
                for r in cur.fetchall():
                    _u_rows.append(_wwwmob_row_as_user(dict(r)))
        return {"total": _u_total, "page": page, "limit": limit, "data": _u_rows}

@router.post("/users")
def create_user(user: UserCreate):
    # 2026-08-26: Mobiliser (WWW) role writes to www_mobilisers.
    if getattr(user, "role_id", None) == _WWWMOB_ROLE_ID:
        return _wwwmob_create_from_user(user)
    """Create a new user — or revive a soft-deleted one.

    The DB enforces a column-level unique constraint on `email` and
    `username`, so a row that has been soft-deleted (`deleted_at IS NOT
    NULL`) still occupies that key. Trying to INSERT another row with the
    same email/username as a soft-deleted record blew up with
    `psycopg2.errors.UniqueViolation`.

    Behaviour:
      - If an ACTIVE user already has the same email or username (case-
        insensitive, matching login lookup), return 400.
      - If a SOFT-DELETED user has it, REVIVE that row in place (clear
        `deleted_at`, update the supplied fields, return the resurrected
        record). This matches typical admin intent — they expect "create"
        to bring the person back, not fail mysteriously.
      - Otherwise INSERT a fresh row.
    """
    hashed = pwd_context.hash(user.password)
    uname = user.username or user.email.split('@')[0]

    with get_cursor() as cur:
        # Look up any existing row with this username (case-insensitive
        # to match the login lookup). Email is NO LONGER part of the
        # uniqueness check — multiple user accounts can share an email,
        # which is needed for the duplicate-account workflow where one
        # PI covers multiple centres (e.g. `sujal.jaipur` and
        # `sujal.jodhpur` both at sujal@…). Username remains the
        # canonical login identifier and stays unique.
        cur.execute(
            """
            SELECT id, deleted_at
              FROM mis_user
             WHERE LOWER(username) = LOWER(%s)
             ORDER BY (deleted_at IS NULL) DESC, id ASC
             LIMIT 1
            """,
            (uname,),
        )
        existing = cur.fetchone()

        if existing and existing["deleted_at"] is None:
            # An active user already owns this username — block.
            raise HTTPException(
                status_code=400,
                detail="A user with this username already exists",
            )

        if existing and existing["deleted_at"] is not None:
            # Soft-deleted row in the way — revive it with the new details.
            cur.execute(
                """
                UPDATE mis_user
                   SET name          = %s,
                       email         = %s,
                       password_hash = %s,
                       role_id       = %s,
                       geo_scope     = %s,
                       status        = %s,
                       username      = %s,
                       phone         = %s,
                       deleted_at    = NULL,
                       updated_at    = NOW()
                 WHERE id = %s
             RETURNING id, name, email, phone, role_id, geo_scope, status, username, created_at
                """,
                (
                    user.name, user.email, hashed, user.role_id, user.geo_scope,
                    user.status, uname, user.phone, existing["id"],
                ),
            )
            return cur.fetchone()

        # No collision — fresh insert.
        cur.execute(
            """INSERT INTO mis_user (name, email, password_hash, role_id, geo_scope, status, username, phone)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id, name, email, phone, role_id, geo_scope, status, username, created_at""",
            (user.name, user.email, hashed, user.role_id, user.geo_scope, user.status, uname, user.phone),
        )
        return cur.fetchone()

@router.get("/users/{user_id}")
def get_user(user_id: int):
    # 2026-08-26: virtual id → www_mobilisers row.
    if _wwwmob_is(user_id):
        return _wwwmob_get(user_id)
    with get_cursor() as cur:
        cur.execute("""
            SELECT u.id, u.name, u.email, u.phone, u.role_id, u.geo_scope, u.status, u.last_login, u.created_at,
                   r.name as role_name, u.username
            FROM mis_user u JOIN roles r ON u.role_id = r.id
            WHERE u.id = %s AND u.deleted_at IS NULL
        """, (user_id,))
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(user)

@router.post("/users/{user_id}/reset-password")
def reset_password(user_id: int, body: Optional[ResetPasswordBody] = None):
    # 2026-08-30: accept an optional new_password from the Reset Password modal.
    # When supplied it is set (min 6 chars); otherwise fall back to the default.
    new_pw = ((body.new_password or "").strip() if body else "")
    if new_pw:
        if len(new_pw) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        target_pw, msg = new_pw, "Password updated successfully"
    else:
        target_pw, msg = "zaq@123", "Password reset to default"
    # virtual id → www_mobilisers row.
    if _wwwmob_is(user_id):
        return _wwwmob_reset_password(user_id, target_pw, msg)
    hashed = pwd_context.hash(target_pw)
    with get_cursor() as cur:
        cur.execute(
            "UPDATE mis_user SET password_hash = %s WHERE id = %s AND deleted_at IS NULL RETURNING id",
            (hashed, user_id)
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": msg}

@router.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    # 2026-08-26: virtual id → www_mobilisers row.
    if _wwwmob_is(user_id):
        return _wwwmob_update(user_id, user)
    hashed = pwd_context.hash(user.password) if user.password else None
    uname = user.username
    with get_cursor() as cur:
        # Check for duplicate username if changed
        if uname:
            cur.execute("SELECT id FROM mis_user WHERE username = %s AND id != %s AND deleted_at IS NULL", (uname, user_id))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="A user with this username already exists")
        if hashed:
            cur.execute(
                """UPDATE mis_user SET name=%s, email=%s, password_hash=%s, role_id=%s, geo_scope=%s, status=%s, phone=%s, username=COALESCE(%s, username)
                   WHERE id=%s AND deleted_at IS NULL RETURNING *""",
                (user.name, user.email, hashed, user.role_id, user.geo_scope, user.status, user.phone, uname, user_id)
            )
        else:
            cur.execute(
                """UPDATE mis_user SET name=%s, email=%s, role_id=%s, geo_scope=%s, status=%s, phone=%s, username=COALESCE(%s, username)
                   WHERE id=%s AND deleted_at IS NULL RETURNING *""",
                (user.name, user.email, user.role_id, user.geo_scope, user.status, user.phone, uname, user_id)
            )
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        return result


@router.delete("/users/{user_id}")
def delete_user(user_id: int):
    """Soft-delete a user by setting deleted_at."""
    # 2026-08-26: virtual id → www_mobilisers row.
    if _wwwmob_is(user_id):
        return _wwwmob_delete(user_id)
    with get_cursor() as cur:
        cur.execute("UPDATE mis_user SET deleted_at = NOW() WHERE id = %s AND deleted_at IS NULL RETURNING id, name", (user_id,))
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": f"User '{result['name']}' deleted successfully"}


# ============================================================================
# 2026-08-26 — www_mobilisers CRUD helpers reached via /api/users routes.
# Kept private (leading underscore) so nothing else imports them.
# ============================================================================
def _wwwmob_get(virtual_id: int):
    real_id = _wwwmob_real_id(virtual_id)
    with get_cursor() as cur:
        cur.execute(_WWWMOB_SELECT_SQL + " AND m.id = %s", (real_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        return _wwwmob_row_as_user(dict(row))

def _wwwmob_create_from_user(user):
    mob_id = (user.username or (user.email.split("@")[0] if user.email else "")).strip()
    if not mob_id:
        raise HTTPException(status_code=400, detail="username is required for Mobiliser (WWW) role")
    if not user.password or len(user.password) < 6:
        raise HTTPException(status_code=400, detail="password must be at least 6 characters")
    st, ds, ct = _wwwmob_parse_geo(user.geo_scope)
    hashed = pwd_context.hash(user.password)
    with get_cursor() as cur:
        cur.execute(
            "SELECT id FROM www_mobilisers WHERE LOWER(mobiliser_id) = LOWER(%s) AND deleted_at IS NULL",
            (mob_id,),
        )
        if cur.fetchone():
            raise HTTPException(status_code=409, detail="A mobiliser with this ID already exists")
        cur.execute(
            """
            INSERT INTO www_mobilisers
              (mobiliser_id, name, password_hash, mobile, email,
               state_code, district_code, centre_code, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (mob_id, (user.name or "").strip(), hashed,
             getattr(user, "phone", None), user.email,
             st, ds, ct, (user.status or "Active")),
        )
        new_id = cur.fetchone()["id"]
        cur.execute(_WWWMOB_SELECT_SQL + " AND m.id = %s", (new_id,))
        row = dict(cur.fetchone())
    return _wwwmob_row_as_user(row)

def _wwwmob_update(virtual_id: int, user):
    real_id = _wwwmob_real_id(virtual_id)
    st, ds, ct = _wwwmob_parse_geo(getattr(user, "geo_scope", None))
    new_mob_id = (getattr(user, "username", None) or "").strip() or None
    with get_cursor() as cur:
        if new_mob_id:
            cur.execute(
                "SELECT id FROM www_mobilisers WHERE LOWER(mobiliser_id) = LOWER(%s) AND id != %s AND deleted_at IS NULL",
                (new_mob_id, real_id),
            )
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="A mobiliser with this ID already exists")
        pw_hash = pwd_context.hash(user.password) if getattr(user, "password", None) else None
        if pw_hash:
            cur.execute(
                """
                UPDATE www_mobilisers
                   SET name=%s, email=%s, mobile=%s,
                       state_code=%s, district_code=%s, centre_code=%s,
                       status=%s, password_hash=%s,
                       mobiliser_id=COALESCE(%s, mobiliser_id),
                       updated_at=NOW()
                 WHERE id=%s AND deleted_at IS NULL RETURNING id
                """,
                (user.name, user.email, getattr(user, "phone", None),
                 st, ds, ct, user.status, pw_hash, new_mob_id, real_id),
            )
        else:
            cur.execute(
                """
                UPDATE www_mobilisers
                   SET name=%s, email=%s, mobile=%s,
                       state_code=%s, district_code=%s, centre_code=%s,
                       status=%s,
                       mobiliser_id=COALESCE(%s, mobiliser_id),
                       updated_at=NOW()
                 WHERE id=%s AND deleted_at IS NULL RETURNING id
                """,
                (user.name, user.email, getattr(user, "phone", None),
                 st, ds, ct, user.status, new_mob_id, real_id),
            )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        cur.execute(_WWWMOB_SELECT_SQL + " AND m.id = %s", (real_id,))
        row = dict(cur.fetchone())
    return _wwwmob_row_as_user(row)

def _wwwmob_delete(virtual_id: int):
    real_id = _wwwmob_real_id(virtual_id)
    with get_cursor() as cur:
        cur.execute(
            "UPDATE www_mobilisers SET deleted_at = NOW() WHERE id = %s AND deleted_at IS NULL RETURNING id, name",
            (real_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User \"{row['name']}\" deleted successfully"}

def _wwwmob_reset_password(virtual_id: int, target_pw: str = "zaq@123", msg: str = "Password reset to default"):
    real_id = _wwwmob_real_id(virtual_id)
    hashed = pwd_context.hash(target_pw)
    with get_cursor() as cur:
        cur.execute(
            "UPDATE www_mobilisers SET password_hash=%s, updated_at=NOW() WHERE id=%s AND deleted_at IS NULL RETURNING id",
            (hashed, real_id),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
    return {"message": msg}
