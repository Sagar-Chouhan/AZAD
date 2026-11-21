"""System Activity Log routes.

2026-10-01: added per-module scope. A programme shows rows whose
user_id is mapped to it in user_program_mapping, plus rows written with
a role_name that belongs to that programme (handles mobile logins
whose log row has NULL user_id).
"""
from fastapi import APIRouter
from typing import Optional
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor

router = APIRouter(prefix="/api/activity-log", tags=["Activity Log"])


# role_name values that belong to a programme regardless of
# user_program_mapping. Hard-coded because the roles table has no
# program_code column and the business mapping is stable.
_PROGRAM_ROLE_NAMES = {
    "FLP": ("FLP (Mobile)", "FLP (Mobile User)"),
    "MGJ": ("Mobiliser",),
    "AK":  ("Sangini",),
    "WWW": ("Mobiliser (WWW)",),
}


def _program_scope_sql(program: Optional[str]):
    """Return (sql_fragment, params) that filters system_activity_log rows
    to those belonging to the given programme, or (None, []) when no
    scoping is requested."""
    if not program:
        return None, []
    code = program.strip().upper()
    role_names = _PROGRAM_ROLE_NAMES.get(code, ())
    frag = (
        "(l.user_id IN (SELECT user_id FROM user_program_mapping WHERE program_code = %s)"
    )
    params = [code]
    if role_names:
        placeholders = ", ".join(["%s"] * len(role_names))
        frag += f" OR l.role_name IN ({placeholders})"
        params.extend(role_names)
    frag += ")"
    return frag, params


@router.get("")
def list_activity_log(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    source: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    program: Optional[str] = None,
    page: int = 1,
    limit: int = 50
):
    offset = (page - 1) * limit
    with get_cursor() as cur:
        conditions = []
        params = []

        prog_sql, prog_params = _program_scope_sql(program)
        if prog_sql:
            conditions.append(prog_sql)
            params.extend(prog_params)

        if user_id:
            conditions.append("l.user_id = %s")
            params.append(user_id)
        if action:
            conditions.append("l.action = %s")
            params.append(action)
        if source:
            conditions.append("l.source = %s")
            params.append(source)
        if start_date:
            conditions.append("l.created_at >= %s::timestamptz")
            params.append(start_date)
        if end_date:
            conditions.append("l.created_at <= (%s::date + INTERVAL '1 day')")
            params.append(end_date)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        # ---- Total count (filtered)
        cur.execute(f"SELECT COUNT(*) as total FROM system_activity_log l {where}", params)
        total = cur.fetchone()["total"]

        # ---- Dropdowns: programme-scoped so each tab is self-contained.
        drop_where_parts = []
        drop_params = []
        if prog_sql:
            drop_where_parts.append(prog_sql)
            drop_params.extend(prog_params)
        drop_where = ("WHERE " + " AND ".join(drop_where_parts)) if drop_where_parts else ""

        cur.execute(f"SELECT DISTINCT l.action FROM system_activity_log l {drop_where} ORDER BY 1", drop_params)
        actions = [r["action"] for r in cur.fetchall()]

        # 2026-10-01: dedupe by user_id — the log stores the user_name
        # as captured at login time, so a rename or typo creates ghost
        # rows. Join `users` for the current display name; include a
        # final COALESCE so deleted users still surface (as whatever
        # name the log last had).
        cur.execute(
            f"""SELECT l.user_id AS user_id,
                       COALESCE(MAX(u.name), MAX(l.user_name)) AS user_name
                FROM system_activity_log l
                LEFT JOIN mis_user u ON u.id = l.user_id AND u.deleted_at IS NULL
                {drop_where}
                {'AND' if drop_where else 'WHERE'} l.user_id IS NOT NULL
                GROUP BY l.user_id
                ORDER BY LOWER(COALESCE(MAX(u.name), MAX(l.user_name)))""",
            drop_params,
        )
        users = [{"id": r["user_id"], "name": r["user_name"]} for r in cur.fetchall()]

        # ---- Stats (programme-scoped, today only)
        today_where_parts = ["l.created_at >= CURRENT_DATE"]
        today_params = []
        if prog_sql:
            today_where_parts.append(prog_sql)
            today_params.extend(prog_params)
        today_where = "WHERE " + " AND ".join(today_where_parts)

        cur.execute(f"SELECT COUNT(*) as today_count FROM system_activity_log l {today_where}", today_params)
        today_count = cur.fetchone()["today_count"]

        cur.execute(f"SELECT COUNT(DISTINCT l.user_id) as active_users FROM system_activity_log l {today_where}", today_params)
        active_users = cur.fetchone()["active_users"]

        # ---- Main query
        cur.execute(f"""
            SELECT l.id, l.user_id, l.user_name, l.role_name, l.action,
                   l.resource_type, l.resource_id, l.ip_address, l.city,
                   l.description, l.source, l.created_at
            FROM system_activity_log l
            {where}
            ORDER BY l.created_at DESC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        rows = cur.fetchall()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "today_count": today_count,
        "active_users": active_users,
        "available_actions": actions,
        "available_users": users,
        "data": rows,
        "program": program,
    }
