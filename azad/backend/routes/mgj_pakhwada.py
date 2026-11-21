"""MGJ Pakhwada — perspective-building & sports sessions + attendance."""
from fastapi import APIRouter, HTTPException, Request
from typing import Optional, List
from pydantic import BaseModel
import sys, os, io, csv
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from routes._role_scope import enforce_role_scope, _resolve_user

router = APIRouter(prefix="/api/mgj-pakhwada", tags=["MGJ Pakhwada"])

# Indian financial year (Apr-Mar) quarters
def _quarter_for(month: int) -> str:
    if 4 <= month <= 6:
        return "Q1"
    if 7 <= month <= 9:
        return "Q2"
    if 10 <= month <= 12:
        return "Q3"
    return "Q4"


def _ensure_pakhwada_schema():
    try:
        with get_cursor() as cur:
            cur.execute("ALTER TABLE mgj_pakhwada_sessions ADD COLUMN IF NOT EXISTS conducted_date date;")
    except Exception:
        pass

_ensure_pakhwada_schema()


# =============================================================================
# MODELS
# =============================================================================

class SessionCreate(BaseModel):
    session_type: str                            # 'INPUT' | 'SPORTS'
    session_month: int                           # 1..12
    session_year: int                            # e.g. 2025
    session_topic: str
    planned_date: Optional[str] = None           # YYYY-MM-DD
    conducted_date: Optional[str] = None         # YYYY-MM-DD
    centre_code: Optional[str] = None
    group_number: Optional[str] = None
    # 2026-07-28: multi-area / multi-mobiliser fields (nullable for back-compat).
    # group_number stays populated with the first area's group so the
    # existing attendance-roster query still works.
    area_codes: Optional[List[str]] = None
    mobiliser_names: Optional[List[str]] = None


class AttendanceItem(BaseModel):
    member_id: int
    status: str                                  # 'Present' | 'Absent' | 'Late' | '1:1 Session'


class AttendanceSubmit(BaseModel):
    items: List[AttendanceItem] = []
    home_visit_count: Optional[int] = 0
    attendance_status: str = "Submitted"         # 'Draft' | 'Submitted'
    remarks: Optional[str] = None                # session-level remark
    conducted_date: Optional[str] = None         # YYYY-MM-DD


# =============================================================================
# Validation
# =============================================================================

def _validate(s: SessionCreate):
    if s.session_type not in ("INPUT", "SPORTS"):
        raise HTTPException(status_code=400, detail="Session Type must be INPUT or SPORTS")
    if not isinstance(s.session_month, int) or not (1 <= s.session_month <= 12):
        raise HTTPException(status_code=400, detail="Month must be 1..12")
    if not isinstance(s.session_year, int) or s.session_year < 2000 or s.session_year > 2100:
        raise HTTPException(status_code=400, detail="Year is required and must be a 4-digit year")
    # No future sessions (rule added 2026-05-26). Frontend dropdowns
    # already restrict the picker, but a direct API call could still
    # try to submit a future (year, month) — reject it here.
    _today = date.today()
    if (s.session_year > _today.year) or (
        s.session_year == _today.year and s.session_month > _today.month
    ):
        raise HTTPException(
            status_code=400,
            detail="Session year/month cannot be in the future",
        )
    topic = (s.session_topic or "").strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Session/Topic name is required")
    return topic


# =============================================================================
# LIST
# =============================================================================

@router.get("")
def list_sessions(
    request: Request,
    session_type: Optional[str] = None,           # 'INPUT' | 'SPORTS'
    month: Optional[int] = None,                  # 1..12
    year: Optional[int] = None,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    topic: Optional[str] = None,
    status: Optional[str] = None,
    mobiliser_name: Optional[str] = None,
    group_number: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
):
    # 2026-07-29: enforce role scope so PI/DL/SL/Mobiliser only see rows
    # within their assigned geography — plugs the cross-state data leak.
    _s = enforce_role_scope(request, state_code=state_code,
                            district_code=district_code,
                            centre_code=centre_code)
    state_code    = _s.get('state_code')
    district_code = _s.get('district_code')
    centre_code   = _s.get('centre_code')
    offset = (page - 1) * limit
    with get_cursor() as cur:
        conds = ["s.deleted_at IS NULL"]
        params: List = []
        if session_type:
            conds.append("s.session_type = %s"); params.append(session_type)
        if month:
            conds.append("s.session_month = %s"); params.append(month)
        if year:
            conds.append("s.session_year = %s"); params.append(year)
        # mgj_pakhwada_sessions only carries centre_code — expand state/district
        # via the central_centres lookup.
        if state_code:
            conds.append("s.centre_code IN (SELECT centre_code FROM central_centres WHERE state_code = %s)")
            params.append(state_code)
        if district_code:
            conds.append("s.centre_code IN (SELECT centre_code FROM central_centres WHERE district_code = %s)")
            params.append(district_code)
        if centre_code:
            conds.append("s.centre_code = %s"); params.append(centre_code)
        if date_from:
            conds.append("s.planned_date >= %s::date"); params.append(date_from)
        if date_to:
            conds.append("s.planned_date <= %s::date"); params.append(date_to)
        if topic:
            conds.append("s.session_topic ILIKE %s"); params.append(f"%{topic}%")
        if status:
            conds.append("s.status = %s"); params.append(status)
        # 2026-08-10: Mobiliser Name + Group Name filters (new list-page filters).
        # mobiliser_name → matches if the value ILIKEs ANY element of the
        # session.mobiliser_names[] array. Partial match keeps it forgiving
        # for free-text values ("Sundar" matches "Sundar Kumar").
        # group_number → case-insensitive trimmed exact match, mirroring the
        # pattern used in list_members_for_session.
        if mobiliser_name and mobiliser_name.strip():
            conds.append(
                "EXISTS (SELECT 1 FROM unnest(COALESCE(s.mobiliser_names, ARRAY[]::text[])) mn "
                "WHERE mn ILIKE %s)"
            )
            params.append(f"%{mobiliser_name.strip()}%")
        if group_number and group_number.strip():
            conds.append("TRIM(LOWER(COALESCE(s.group_number, ''))) = TRIM(LOWER(%s))")
            params.append(group_number)
        where = " AND ".join(conds)

        cur.execute(f"SELECT COUNT(*) as total FROM mgj_pakhwada_sessions s WHERE {where}", params)
        total = cur.fetchone()["total"]

        cur.execute(f"""
            SELECT s.*,
                   COALESCE(nc.centre_name, '') as centre_name,
                   (SELECT COUNT(*) FROM mgj_pakhwada_attendance a
                    JOIN mgj_members m ON a.member_id = m.id AND m.deleted_at IS NULL AND LOWER(COALESCE(m.status,'')) != 'walkout'
                    WHERE a.session_id = s.id AND a.status = 'Present'
                      AND (s.centre_code IS NULL OR m.centre_code = s.centre_code)
                      AND (s.group_number IS NULL OR TRIM(s.group_number) = '' OR TRIM(LOWER(COALESCE(m.group_number,''))) = ANY(SELECT TRIM(LOWER(g)) FROM unnest(string_to_array(s.group_number, ',')) g WHERE TRIM(g) <> ''))
                      AND (s.area_codes IS NULL OR array_length(s.area_codes, 1) IS NULL OR array_length(s.area_codes, 1) = 0 OR m.area_code = ANY(s.area_codes))
                   ) as present_count,
                   (SELECT COUNT(*) FROM mgj_pakhwada_attendance a
                    JOIN mgj_members m ON a.member_id = m.id AND m.deleted_at IS NULL AND LOWER(COALESCE(m.status,'')) != 'walkout'
                    WHERE a.session_id = s.id AND a.status = 'Absent'
                      AND (s.centre_code IS NULL OR m.centre_code = s.centre_code)
                      AND (s.group_number IS NULL OR TRIM(s.group_number) = '' OR TRIM(LOWER(COALESCE(m.group_number,''))) = ANY(SELECT TRIM(LOWER(g)) FROM unnest(string_to_array(s.group_number, ',')) g WHERE TRIM(g) <> ''))
                      AND (s.area_codes IS NULL OR array_length(s.area_codes, 1) IS NULL OR array_length(s.area_codes, 1) = 0 OR m.area_code = ANY(s.area_codes))
                   ) as absent_count,
                   (CASE WHEN s.session_type = 'SPORTS' THEN 0 ELSE (
                     SELECT COUNT(*) FROM mgj_pakhwada_attendance a
                     JOIN mgj_members m ON a.member_id = m.id AND m.deleted_at IS NULL AND LOWER(COALESCE(m.status,'')) != 'walkout'
                     WHERE a.session_id = s.id AND a.status = '1:1 Session'
                       AND (s.centre_code IS NULL OR m.centre_code = s.centre_code)
                       AND (s.group_number IS NULL OR TRIM(s.group_number) = '' OR TRIM(LOWER(COALESCE(m.group_number,''))) = ANY(SELECT TRIM(LOWER(g)) FROM unnest(string_to_array(s.group_number, ',')) g WHERE TRIM(g) <> ''))
                       AND (s.area_codes IS NULL OR array_length(s.area_codes, 1) IS NULL OR array_length(s.area_codes, 1) = 0 OR m.area_code = ANY(s.area_codes))
                   ) END) as one_to_one_count
            FROM mgj_pakhwada_sessions s
            LEFT JOIN central_centres nc ON s.centre_code = nc.centre_code AND nc.deleted_at IS NULL
            WHERE {where}
            ORDER BY s.session_year DESC, s.session_month DESC, s.planned_date DESC NULLS LAST, s.id DESC
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        rows = cur.fetchall()

    return {"total": total, "page": page, "limit": limit, "data": rows}


# =============================================================================
# EXPORT
# =============================================================================

@router.get("/export/excel")
def export_sessions(
    request: Request,
    session_type: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    topic: Optional[str] = None,
    status: Optional[str] = None,
    mobiliser_name: Optional[str] = None,
    group_number: Optional[str] = None,
):
    _s = enforce_role_scope(request, state_code=state_code,
                            district_code=district_code,
                            centre_code=centre_code)
    state_code    = _s.get('state_code')
    district_code = _s.get('district_code')
    centre_code   = _s.get('centre_code')
    with get_cursor() as cur:
        conds = ["s.deleted_at IS NULL"]
        params: List = []
        if state_code:
            conds.append("s.centre_code IN (SELECT centre_code FROM central_centres WHERE state_code = %s)")
            params.append(state_code)
        if district_code:
            conds.append("s.centre_code IN (SELECT centre_code FROM central_centres WHERE district_code = %s)")
            params.append(district_code)
        if session_type: conds.append("s.session_type = %s"); params.append(session_type)
        if month: conds.append("s.session_month = %s"); params.append(month)
        if year: conds.append("s.session_year = %s"); params.append(year)
        if centre_code: conds.append("s.centre_code = %s"); params.append(centre_code)
        if date_from: conds.append("s.planned_date >= %s::date"); params.append(date_from)
        if date_to: conds.append("s.planned_date <= %s::date"); params.append(date_to)
        if topic: conds.append("s.session_topic ILIKE %s"); params.append(f"%{topic}%")
        if status: conds.append("s.status = %s"); params.append(status)
        # 2026-08-10: export also honours the two new filters so the CSV
        # matches what the user is looking at in the list.
        if mobiliser_name and mobiliser_name.strip():
            conds.append(
                "EXISTS (SELECT 1 FROM unnest(COALESCE(s.mobiliser_names, ARRAY[]::text[])) mn "
                "WHERE mn ILIKE %s)"
            )
            params.append(f"%{mobiliser_name.strip()}%")
        if group_number and group_number.strip():
            conds.append("TRIM(LOWER(COALESCE(s.group_number, ''))) = TRIM(LOWER(%s))")
            params.append(group_number)
        where = " AND ".join(conds)
        cur.execute(f"""
            SELECT s.session_type, s.session_month, s.session_year, s.quarter,
                   s.session_topic, s.planned_date, s.conducted_date,
                   COALESCE(nc.centre_name, '') as centre_name,
                   s.group_number, s.status, s.home_visit_count,
                   (SELECT COUNT(*) FROM mgj_pakhwada_attendance a
                    JOIN mgj_members m ON a.member_id = m.id AND m.deleted_at IS NULL AND LOWER(COALESCE(m.status,'')) != 'walkout'
                    WHERE a.session_id = s.id AND a.status = 'Present'
                      AND (s.centre_code IS NULL OR m.centre_code = s.centre_code)
                      AND (s.group_number IS NULL OR TRIM(s.group_number) = '' OR TRIM(LOWER(COALESCE(m.group_number,''))) = ANY(SELECT TRIM(LOWER(g)) FROM unnest(string_to_array(s.group_number, ',')) g WHERE TRIM(g) <> ''))
                      AND (s.area_codes IS NULL OR array_length(s.area_codes, 1) IS NULL OR array_length(s.area_codes, 1) = 0 OR m.area_code = ANY(s.area_codes))
                   ) as present_count,
                   (SELECT COUNT(*) FROM mgj_pakhwada_attendance a
                    JOIN mgj_members m ON a.member_id = m.id AND m.deleted_at IS NULL AND LOWER(COALESCE(m.status,'')) != 'walkout'
                    WHERE a.session_id = s.id AND a.status = 'Absent'
                      AND (s.centre_code IS NULL OR m.centre_code = s.centre_code)
                      AND (s.group_number IS NULL OR TRIM(s.group_number) = '' OR TRIM(LOWER(COALESCE(m.group_number,''))) = ANY(SELECT TRIM(LOWER(g)) FROM unnest(string_to_array(s.group_number, ',')) g WHERE TRIM(g) <> ''))
                      AND (s.area_codes IS NULL OR array_length(s.area_codes, 1) IS NULL OR array_length(s.area_codes, 1) = 0 OR m.area_code = ANY(s.area_codes))
                   ) as absent_count,
                   (CASE WHEN s.session_type = 'SPORTS' THEN 0 ELSE (
                     SELECT COUNT(*) FROM mgj_pakhwada_attendance a
                     JOIN mgj_members m ON a.member_id = m.id AND m.deleted_at IS NULL AND LOWER(COALESCE(m.status,'')) != 'walkout'
                     WHERE a.session_id = s.id AND a.status = '1:1 Session'
                       AND (s.centre_code IS NULL OR m.centre_code = s.centre_code)
                       AND (s.group_number IS NULL OR TRIM(s.group_number) = '' OR TRIM(LOWER(COALESCE(m.group_number,''))) = ANY(SELECT TRIM(LOWER(g)) FROM unnest(string_to_array(s.group_number, ',')) g WHERE TRIM(g) <> ''))
                       AND (s.area_codes IS NULL OR array_length(s.area_codes, 1) IS NULL OR array_length(s.area_codes, 1) = 0 OR m.area_code = ANY(s.area_codes))
                   ) END) as one_to_one_count
            FROM mgj_pakhwada_sessions s
            LEFT JOIN central_centres nc ON s.centre_code = nc.centre_code AND nc.deleted_at IS NULL
            WHERE {where} ORDER BY s.session_year DESC, s.session_month DESC, s.planned_date DESC NULLS LAST
        """, params)
        rows = cur.fetchall()

    is_sports_only = (session_type == "SPORTS")
    output = io.StringIO()
    writer = csv.writer(output)
    if is_sports_only:
        writer.writerow([
            'Session Type', 'Month', 'Year', 'Quarter',
            'Topic', 'Planned Date', 'Conducted Date', 'Centre', 'Group Number',
            'Status', 'Present', 'Absent'
        ])
        for r in rows:
            writer.writerow([
                r['session_type'], r['session_month'], r['session_year'], r['quarter'] or '',
                r['session_topic'], str(r['planned_date'] or ''), str(r['conducted_date'] or ''),
                r['centre_name'], r['group_number'] or '',
                r['status'], r['present_count'], r['absent_count'],
            ])
    else:
        writer.writerow([
            'Session Type', 'Month', 'Year', 'Quarter',
            'Topic', 'Planned Date', 'Conducted Date', 'Centre', 'Group Number',
            'Status', 'Present', 'Absent', '1:1 Session'
        ])
        for r in rows:
            writer.writerow([
                r['session_type'], r['session_month'], r['session_year'], r['quarter'] or '',
                r['session_topic'], str(r['planned_date'] or ''), str(r['conducted_date'] or ''),
                r['centre_name'], r['group_number'] or '',
                r['status'], r['present_count'], r['absent_count'],
                0 if r['session_type'] == 'SPORTS' else (r.get('one_to_one_count') or 0),
            ])
    from export_helper import csv_string_to_xlsx_response
    return csv_string_to_xlsx_response(output.getvalue(), f"MGJ_Pakhwada_Sessions_{date.today().isoformat()}.xlsx")


# =============================================================================
# DETAIL  (with attendance roster)
# =============================================================================

@router.get("/{session_id}")
def get_session(session_id: int):
    with get_cursor() as cur:
        cur.execute("""
            SELECT s.*,
                   COALESCE(nc.centre_name, '') as centre_name
            FROM mgj_pakhwada_sessions s
            LEFT JOIN central_centres nc ON s.centre_code = nc.centre_code AND nc.deleted_at IS NULL
            WHERE s.id = %s AND s.deleted_at IS NULL
        """, (session_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Pakhwada session not found")
        sess_areas = row.get("area_codes") or []
        _raw = (row.get("group_number") or "").strip()
        selected_groups = [g.strip().lower() for g in _raw.split(",") if g.strip()]

        conds = ["a.session_id = %s", "m.deleted_at IS NULL"]
        params = [session_id]

        if isinstance(sess_areas, (list, tuple)) and len(sess_areas) > 0:
            conds.append("m.area_code = ANY(%s)")
            params.append(list(sess_areas))

        if selected_groups:
            conds.append("TRIM(LOWER(COALESCE(m.group_number,''))) = ANY(%s)")
            params.append(selected_groups)

        where_sql = " AND ".join(conds)

        cur.execute(f"""
            SELECT a.member_id, a.status,
                   m.enrollment_number, m.name, m.group_number,
                   COALESCE(na.area_name, '') as area_name,
                   m.status as member_status
            FROM mgj_pakhwada_attendance a
            LEFT JOIN mgj_members m ON a.member_id = m.id
            LEFT JOIN central_areas na ON m.area_code = na.area_code AND na.deleted_at IS NULL
            WHERE {where_sql}
            ORDER BY m.enrollment_number
        """, tuple(params))
        attendance = cur.fetchall()
    out = dict(row)
    out["attendance"] = attendance
    out["present_count"] = sum(1 for a in attendance if a["status"] == "Present")
    out["absent_count"] = sum(1 for a in attendance if a["status"] == "Absent")
    out["one_to_one_count"] = 0 if out.get("session_type") == "SPORTS" else sum(1 for a in attendance if a["status"] == "1:1 Session")
    return out


# =============================================================================
# CREATE
# =============================================================================

@router.post("")
def create_session(body: SessionCreate):
    topic = _validate(body)
    quarter = _quarter_for(body.session_month)
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO mgj_pakhwada_sessions
                (session_type, session_month, session_year, quarter, session_topic,
                 planned_date, conducted_date, centre_code, group_number, area_codes, mobiliser_names,
                 status, attendance_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Planned', 'Pending')
            RETURNING id
        """, (
            body.session_type, body.session_month, body.session_year, quarter, topic,
            body.planned_date or None, body.conducted_date or None, body.centre_code or None, body.group_number or None,
            body.area_codes or None, body.mobiliser_names or None,
        ))
        new_id = cur.fetchone()["id"]
    return {"id": new_id, "quarter": quarter, "message": "Pakhwada session created"}


# =============================================================================
# UPDATE
# =============================================================================

@router.put("/{session_id}")
def update_session(session_id: int, body: SessionCreate):
    topic = _validate(body)
    quarter = _quarter_for(body.session_month)
    with get_cursor() as cur:
        cur.execute("SELECT id FROM mgj_pakhwada_sessions WHERE id = %s AND deleted_at IS NULL", (session_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Pakhwada session not found")
        cur.execute("""
            UPDATE mgj_pakhwada_sessions SET
                session_type = %s, session_month = %s, session_year = %s, quarter = %s,
                session_topic = %s, planned_date = %s, conducted_date = %s, centre_code = %s, group_number = %s,
                area_codes = %s, mobiliser_names = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (
            body.session_type, body.session_month, body.session_year, quarter,
            topic, body.planned_date or None, body.conducted_date or None, body.centre_code or None, body.group_number or None,
            body.area_codes or None, body.mobiliser_names or None,
            session_id,
        ))
    return {"message": "Pakhwada session updated", "quarter": quarter}
    return {"message": "Pakhwada session updated", "quarter": quarter}


# =============================================================================
# DELETE
# =============================================================================

@router.delete("/{session_id}")
def delete_session(session_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT id FROM mgj_pakhwada_sessions WHERE id = %s AND deleted_at IS NULL", (session_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Pakhwada session not found")
        cur.execute("UPDATE mgj_pakhwada_sessions SET deleted_at = NOW() WHERE id = %s", (session_id,))
    return {"message": "Pakhwada session deleted"}


# =============================================================================
# MEMBERS for the attendance modal — scoped to the session's centre
# =============================================================================

@router.get("/{session_id}/members")
def list_members_for_session(session_id: int, request: Request):
    """Return the roster eligible to mark attendance for a Pakhwada session.

    Relaxed 2026-08-10 (client request): the earlier "strict centre + group"
    matching (2026-05-26) turned out to block ~40% of sessions because
    session.group_number and member.group_number are free-text and diverge
    in practice ('Group ROHINI' vs 'Group Z', 'G-02' vs 'G 02', ...). Users
    couldn't mark attendance for members visibly on the roster elsewhere.

    Refined 2026-08-10 (v2): for role=mobiliser, additionally restrict the
    roster to members whose mgj_members.mobiliser_name matches the caller's
    users.name. Prevents one Mobiliser at a centre from seeing another
    Mobiliser's members. PI / DL / State Lead / Admin still see the full
    centre roster (the scope filter above them).

    New behaviour:
      • Always return the full centre roster when the session has a centre.
      • For role=mobiliser, additionally filter by mobiliser_name = caller.
      • Compute an `is_in_session_group` boolean per row (case-insensitive,
        trimmed match against the session's group_number). Frontend uses it
        to pre-check checkboxes for the "expected" attendees while still
        letting the Mobiliser mark anyone at their centre as Present /
        Absent / 1:1 Session.
      • Session with no centre still returns an empty roster (defensive).
    """
    caller = _resolve_user(request)
    is_mobiliser = bool(caller and (caller.get("role_name") or "").lower() == "mobiliser")
    caller_name = (caller or {}).get("user_name") or ""

    with get_cursor() as cur:
        cur.execute(
            "SELECT centre_code, group_number, area_codes FROM mgj_pakhwada_sessions "
            "WHERE id = %s AND deleted_at IS NULL",
            (session_id,),
        )
        sess = cur.fetchone()
        if not sess:
            raise HTTPException(status_code=404, detail="Pakhwada session not found")

        centre_code = sess["centre_code"]
        # 2026-09-25: session.group_number now stores the SELECTED groups
        # from the Add Session "Select Groups" multi-select, comma-joined
        # (e.g. "Group A, Group B"). Split it back into a list and use it
        # to hard-filter the attendance roster to members of those groups.
        # Old rows with a single group work as a one-element list.
        _raw = (sess.get("group_number") or "").strip()
        selected_groups = [g.strip().lower() for g in _raw.split(",") if g.strip()]

        if not centre_code:
            return []

        # 2026-08-10 v2: for Mobiliser role, restrict roster to members
        # whose mobiliser_name matches the caller's users.name. If the
        # column is blank on the caller (misconfigured user), skip the
        # extra filter — fail-open matches the rest of the scope layer.
        mob_filter = ""
        # Params order matches SQL: is_in_session_group (twice), session_id, centre_code, then any *_filter appends.
        params = [selected_groups, selected_groups, session_id, centre_code]
        if is_mobiliser and caller_name.strip():
            mob_filter = " AND TRIM(LOWER(COALESCE(m.mobiliser_name,''))) = TRIM(LOWER(%s))"
            params.append(caller_name)

        # 2026-08-20: if the session was created for one or more specific
        # areas, restrict the roster to members from THOSE areas only.
        # Sessions with no area_codes (older rows / centre-wide sessions)
        # keep the previous behaviour: full centre roster.
        area_filter = ""
        sess_areas = sess.get("area_codes") or []
        if isinstance(sess_areas, (list, tuple)) and len(sess_areas) > 0:
            area_filter = " AND m.area_code = ANY(%s)"
            params.append(list(sess_areas))

        # 2026-09-25: restrict roster to members belonging to any of the
        # session's selected groups (comma-split from group_number).
        group_filter = ""
        if selected_groups:
            group_filter = " AND TRIM(LOWER(COALESCE(m.group_number,''))) = ANY(%s)"
            params.append(selected_groups)

        cur.execute(
            f"""
            SELECT m.id, m.enrollment_number, m.name, m.group_number,
                   m.area_code, m.centre_code,
                   COALESCE(na.area_name, '') AS area_name,
                   m.status AS member_status,
                   ma.status AS attendance_status,
                   (TRIM(LOWER(COALESCE(m.group_number,''))) = ANY(%s)
                    AND COALESCE(array_length(%s, 1), 0) > 0) AS is_in_session_group
            FROM mgj_members m
            LEFT JOIN central_areas na ON m.area_code = na.area_code AND na.deleted_at IS NULL
            LEFT JOIN mgj_pakhwada_attendance ma
                   ON ma.session_id = %s AND ma.member_id = m.id
            WHERE m.deleted_at IS NULL
              AND m.centre_code = %s
              {mob_filter}
              {area_filter}
              {group_filter}
            ORDER BY m.enrollment_number
            """,
            tuple(params),
        )
        rows = cur.fetchall()

        # 2026-11-16: Compute trainee attendance progress summary across INPUT and SPORTS
        _DEFAULT_PAKH = lambda: {
            'input':  {'present': 0, 'absent': 0, 'one_on_one': 0, 'late': 0, 'total': 0},
            'sports': {'present': 0, 'absent': 0, 'one_on_one': 0, 'late': 0, 'total': 0},
        }
        _pakh_by_id = {}
        _member_ids = [r['id'] for r in rows]
        if _member_ids:
            cur.execute("""
                SELECT a.member_id, s.session_type, a.status, COUNT(*) AS c
                FROM mgj_pakhwada_attendance a
                JOIN mgj_pakhwada_sessions   s ON s.id = a.session_id
                WHERE a.member_id = ANY(%s)
                  AND s.deleted_at IS NULL
                  AND s.attendance_status = 'Submitted'
                GROUP BY a.member_id, s.session_type, a.status
            """, (_member_ids,))
            _STATUS_KEY = {'Present': 'present', 'Absent': 'absent', '1:1 Session': 'one_on_one', 'Late': 'late'}
            for pr in cur.fetchall():
                stype = 'input' if pr['session_type'] == 'INPUT' else 'sports' if pr['session_type'] == 'SPORTS' else None
                key   = _STATUS_KEY.get(pr['status'])
                if not stype or not key:
                    continue
                summary = _pakh_by_id.setdefault(pr['member_id'], _DEFAULT_PAKH())
                summary[stype][key]     += int(pr['c'])
                summary[stype]['total'] += int(pr['c'])
        data_out = []
        for r in rows:
            row = dict(r)
            row['pakhwada_summary'] = _pakh_by_id.get(row['id'], _DEFAULT_PAKH())
            data_out.append(row)
        return data_out


# =============================================================================
# ATTENDANCE submit
# =============================================================================

@router.post("/{session_id}/attendance")
def submit_attendance(session_id: int, body: AttendanceSubmit):
    if body.attendance_status not in ("Draft", "Submitted"):
        raise HTTPException(status_code=400, detail="attendance_status must be Draft or Submitted")
    for it in body.items:
        if it.status not in ("Present", "Absent", "Late", "1:1 Session"):
            raise HTTPException(status_code=400, detail=f"Invalid status {it.status!r}")

    with get_cursor() as cur:
        cur.execute("SELECT id, session_type FROM mgj_pakhwada_sessions WHERE id = %s AND deleted_at IS NULL", (session_id,))
        sess = cur.fetchone()
        if not sess:
            raise HTTPException(status_code=404, detail="Pakhwada session not found")

        # 2026-11-16: 1:1 sessions apply only to INPUT; coerce to Present if SPORTS
        is_sports = (sess.get("session_type") == "SPORTS")

        # Replace attendance rows wholesale
        cur.execute("DELETE FROM mgj_pakhwada_attendance WHERE session_id = %s", (session_id,))
        for it in body.items:
            final_status = "Present" if (is_sports and it.status == "1:1 Session") else it.status
            cur.execute(
                "INSERT INTO mgj_pakhwada_attendance (session_id, member_id, status) VALUES (%s, %s, %s)",
                (session_id, it.member_id, final_status),
            )

        new_session_status = "Conducted" if body.attendance_status == "Submitted" else "Planned"
        cond_date = (body.conducted_date or "").strip() or None
        cur.execute("""
            UPDATE mgj_pakhwada_sessions
            SET home_visit_count = %s,
                attendance_status = %s,
                status = %s,
                remarks = %s,
                conducted_date = COALESCE(%s::date, conducted_date),
                updated_at = NOW()
            WHERE id = %s
        """, (body.home_visit_count or 0, body.attendance_status, new_session_status, body.remarks, cond_date, session_id))

    return {"message": "Attendance saved", "attendance_status": body.attendance_status, "status": new_session_status}


# =============================================================================
# AUTOCOMPLETE — distinct topics for the search
# =============================================================================

@router.get("/autocomplete/topics")
def autocomplete_topics():
    with get_cursor() as cur:
        cur.execute("""
            SELECT DISTINCT session_topic FROM mgj_pakhwada_sessions
            WHERE deleted_at IS NULL ORDER BY session_topic
        """)
        return [r["session_topic"] for r in cur.fetchall()]
