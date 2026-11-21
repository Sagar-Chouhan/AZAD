"""MGJ Dashboard — aggregations across the MGJ module.

Mirrors backend/routes/dashboard.py (FLP dashboard) shape so the frontend
can reuse the same wiring patterns. Reads only from mgj_* tables so the
two programmes remain isolated.

Endpoints:
  GET /api/mgj-dashboard/stats
  GET /api/mgj-dashboard/charts
  GET /api/mgj-dashboard/drill-down/members?chart=...&value=...
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Optional
from datetime import date
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from routes._role_scope import enforce_role_scope
from jose import jwt, JWTError
from config import JWT_SECRET, JWT_ALGORITHM

router = APIRouter(prefix="/api/mgj-dashboard", tags=["MGJ Dashboard"])


# 2026-08-03 — MGJ Dashboard mobiliser scoping.
# Mirror of the fix landed this morning in routes/mgj.py::list_mgj.
# When the caller is a Mobiliser, every mgj_members-derived count /
# chart on the dashboard must be narrowed to members that mobiliser
# actually owns (mgj_members.mobiliser_name = users.name of the JWT
# caller). Without this, KPI cards, charts, socio-economic breakdown
# and drill-down all leak centre-wide member data even though the
# MGJ List page is already correctly scoped.
#
# Deliberately DOES NOT modify routes/_role_scope.enforce_role_scope
# (that helper pins geo codes only; mobiliser ownership is orthogonal
# and endpoint-specific). Non-Mobiliser roles are untouched.
def _caller_role_and_name(request: Optional[Request]):
    """Return (role_lower, user_name) for the JWT-authenticated caller
    or (None, None). Never raises — fail-open matches _role_scope."""
    if request is None:
        return (None, None)
    try:
        auth = request.headers.get("authorization", "")
    except Exception:
        return (None, None)
    if not auth.startswith("Bearer "):
        return (None, None)
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return (None, None)
    try:
        user_id = int(payload.get("sub", 0))
    except (TypeError, ValueError):
        return (None, None)
    if user_id <= 0:
        return (None, None)
    with get_cursor() as cur:
        cur.execute(
            "SELECT u.name, LOWER(r.name) AS role_name "
            "  FROM mis_user u JOIN roles r ON r.id = u.role_id "
            " WHERE u.id = %s AND u.deleted_at IS NULL",
            (user_id,),
        )
        row = cur.fetchone()
    if not row:
        return (None, None)
    return (row["role_name"], row["name"])


def _common_filters(state_code: Optional[str], district_code: Optional[str],
                    centre_code: Optional[str], status: Optional[str],
                    date_from: Optional[date], date_to: Optional[date],
                    table_alias: str = "m",
                    request: Optional[Request] = None,
                    group_number: Optional[str] = None):
    """Build a WHERE-clause fragment + params list for a member-style
    table (currently only mgj_members, alias 'm').

    NOTE on district_code (fixed 2026-05-25): mgj_members has a
    `district_code` column, but in practice it is NULL/empty for every
    row — districts are derived from the centre. So a literal
    `m.district_code = %s` filter silently returns 0 members and the
    Home Dashboard's "MGJ Members" KPI shows 0 the moment a district is
    picked. We resolve the district via `central_centres` instead, the same
    pattern this file already uses for sessions (line ~65) and alumni
    (line ~109). state_code and centre_code ARE populated on
    mgj_members, so those still filter directly.
    """
    conds = [f"{table_alias}.deleted_at IS NULL"]
    params: list = []
    # 2026-08-03 — Server-side mobiliser scope. When the JWT caller is
    # a Mobiliser, force `mobiliser_name = caller.name` on every
    # mgj_members-derived aggregate so the dashboard matches the MGJ
    # List page (which was fixed this morning). All other roles fall
    # through unchanged. Skipped when `request` was not passed (defensive
    # — e.g. callers that predate this signature bump).
    _caller_role, _caller_name = _caller_role_and_name(request)
    if _caller_role == "mobiliser" and _caller_name:
        conds.append(f"TRIM({table_alias}.mobiliser_name) ILIKE TRIM(%s)")
        params.append(_caller_name)
    if state_code:    conds.append(f"{table_alias}.state_code = %s");    params.append(state_code)
    if district_code:
        conds.append(f"{table_alias}.centre_code IN (SELECT centre_code FROM central_centres WHERE district_code = %s)")
        params.append(district_code)
    if centre_code:   conds.append(f"{table_alias}.centre_code = %s");   params.append(centre_code)
    # 2026-08-06 — Group Name filter (new Dashboard dropdown). Column
    # `mgj_members.group_number` stores the group NAME string (matches
    # mgj_master_groups.name), so exact-match on the caller's picked
    # group name. Only applies to member-style tables (alias == 'm');
    # pakhwada / alumni aggregates don't carry group_number natively.
    if group_number and table_alias == "m":
        conds.append(f"{table_alias}.group_number = %s"); params.append(group_number)
    # 2026-07-24: Dashboard's Status filter uses the FLP-style label
    # 'Dropout', but member records land in the DB with status='Walkout'
    # (matching Walkout/Dropout parity done for AK in task #397). Treat
    # 'Dropout' as an alias so the dashboard filter returns those rows.
    if status == 'Dropout':
        conds.append(f"{table_alias}.status IN ('Walkout', 'Dropout')")
    elif status:
        conds.append(f"{table_alias}.status = %s"); params.append(status)
    if date_from:     conds.append(f"{table_alias}.created_at >= %s");   params.append(date_from)
    if date_to:       conds.append(f"{table_alias}.created_at < (%s::date + INTERVAL '1 day')"); params.append(date_to)
    return " AND ".join(conds), params


# ── /stats ───────────────────────────────────────────────────────────────

@router.get("/stats")
def stats(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    group_number: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    """Top-row KPIs. Mirrors the 5 FLP KPI cards but with MGJ semantics.

    2026-07-29: state/district/centre filter params are now pinned to the
    caller's assigned scope via enforce_role_scope, so a PI (Sourav, WB)
    can never see other states' KPIs regardless of what the frontend sends
    or a DevTools/curl user forges."""
    scoped = enforce_role_scope(
        request,
        state_code=state_code,
        district_code=district_code,
        centre_code=centre_code,
    )
    state_code    = scoped.get('state_code')
    district_code = scoped.get('district_code')
    centre_code   = scoped.get('centre_code')
    where_members, params_m = _common_filters(state_code, district_code, centre_code, status, date_from, date_to, "m", request=request, group_number=group_number)
    # mgj_pakhwada_sessions only carries `centre_code` natively. State and
    # district scopes are expanded via centre-membership subqueries against
    # central_centres (same pattern used elsewhere — list endpoints, mgj_alumni
    # block below, etc.). Direct `s.state_code` / `s.district_code` filters
    # would 500 with "column does not exist".
    where_sessions = ["s.deleted_at IS NULL"]
    params_s: list = []
    if state_code:
        where_sessions.append("s.centre_code IN (SELECT centre_code FROM central_centres WHERE state_code = %s)")
        params_s.append(state_code)
    if district_code:
        where_sessions.append("s.centre_code IN (SELECT centre_code FROM central_centres WHERE district_code = %s)")
        params_s.append(district_code)
    if centre_code:   where_sessions.append("s.centre_code = %s");   params_s.append(centre_code)
    if date_from:     where_sessions.append("s.planned_date >= %s"); params_s.append(date_from)
    if date_to:       where_sessions.append("s.planned_date <= %s"); params_s.append(date_to)
    where_sessions_sql = " AND ".join(where_sessions)

    with get_cursor() as cur:
        # Geo-scoped counts: states / districts / centres respect the
        # filter so picking (or being pinned to) a state / district /
        # centre shows only that sub-tree's counts. 2026-07-29: centre_code
        # and district_code branches added so PI (pinned to centre) sees
        # 1/1/1 and DL (pinned to district) sees 1/1/N — previously only
        # state_code narrowed the counts.
        if centre_code:
            states = districts = centres = 1
        elif district_code:
            states = districts = 1
            cur.execute("SELECT COUNT(*) c FROM central_centres WHERE district_code = %s AND deleted_at IS NULL", (district_code,))
            centres = cur.fetchone()["c"]
        elif state_code:
            states = 1
            cur.execute("SELECT COUNT(*) c FROM central_districts WHERE state_code = %s AND deleted_at IS NULL", (state_code,))
            districts = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) c FROM central_centres WHERE state_code = %s AND deleted_at IS NULL", (state_code,))
            centres = cur.fetchone()["c"]
        else:
            cur.execute("SELECT (SELECT COUNT(*) FROM central_states WHERE deleted_at IS NULL) s, (SELECT COUNT(*) FROM central_districts WHERE deleted_at IS NULL) d, (SELECT COUNT(*) FROM central_centres WHERE deleted_at IS NULL) c")
            r = cur.fetchone()
            states, districts, centres = r["s"], r["d"], r["c"]

        cur.execute(f"SELECT COUNT(*) c FROM mgj_members m WHERE {where_members}", params_m)
        total_members = cur.fetchone()["c"]
        cur.execute(f"SELECT COUNT(*) c FROM mgj_members m WHERE {where_members} AND m.status = 'Active'", params_m)
        active_members = cur.fetchone()["c"]

        # Leaders count: scoped by member geography. mgj_leaders has no
        # geo columns of its own; we join through mgj_members.
        cur.execute(f"""
            SELECT COUNT(*) c FROM mgj_leaders l
            JOIN mgj_members m ON l.member_id = m.id
            WHERE l.deleted_at IS NULL AND l.status = 'Active' AND {where_members}
        """, params_m)
        active_leaders = cur.fetchone()["c"]

        cur.execute(f"SELECT COUNT(*) c FROM mgj_pakhwada_sessions s WHERE {where_sessions_sql}", params_s)
        total_sessions = cur.fetchone()["c"]

        # Alumni counted as a "soft" sub-stat for completeness.
        alumni_conds = ["a.deleted_at IS NULL"]
        alumni_params: list = []
        if state_code:    alumni_conds.append("a.state_code = %s");    alumni_params.append(state_code)
        if district_code:
            alumni_conds.append("a.centre_code IN (SELECT centre_code FROM central_centres WHERE district_code = %s)")
            alumni_params.append(district_code)
        if centre_code:   alumni_conds.append("a.centre_code = %s");   alumni_params.append(centre_code)
        cur.execute(f"SELECT COUNT(*) c FROM mgj_alumni a WHERE {' AND '.join(alumni_conds)}", alumni_params)
        total_alumni = cur.fetchone()["c"]

    return {
        "states": states,
        "total_districts": districts,
        "total_centres": centres,
        "total_members": total_members,
        "active_members": active_members,
        "active_leaders": active_leaders,
        "total_sessions": total_sessions,
        "total_alumni": total_alumni,
    }


# ── /charts ──────────────────────────────────────────────────────────────

@router.get("/charts")
def charts(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    group_number: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    where_members, params_m = _common_filters(state_code, district_code, centre_code, status, date_from, date_to, "m", request=request, group_number=group_number)

    out: dict = {}
    with get_cursor() as cur:
        # 1. Members by State (pie)
        cur.execute(f"""
            SELECT COALESCE(s.state_name, m.state_code, 'Unknown') AS state_name,
                   COUNT(*) AS count
            FROM mgj_members m
            LEFT JOIN central_states s ON m.state_code = s.state_code
            WHERE {where_members}
            GROUP BY s.state_name, m.state_code
            ORDER BY count DESC
        """, params_m)
        out["members_by_state"] = cur.fetchall()

        # 2. State-wise breakdown for table (Total / Active / Dropout)
        cur.execute(f"""
            SELECT COALESCE(s.state_name, m.state_code, 'Unknown') AS state_name,
                   COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE m.status = 'Active') AS active,
                   COUNT(*) FILTER (WHERE m.status IS DISTINCT FROM 'Active') AS dropout
            FROM mgj_members m
            LEFT JOIN central_states s ON m.state_code = s.state_code
            WHERE {where_members}
            GROUP BY s.state_name, m.state_code
            ORDER BY total DESC
        """, params_m)
        out["state_member_breakdown"] = cur.fetchall()

        # 3. Member stage (mirrors FLP's 5-segment status pie).
        # Single query computing each member's furthest-reached stage.
        cur.execute(f"""
            WITH base AS (
                SELECT m.id, m.name
                FROM mgj_members m
                WHERE {where_members}
            ), stages AS (
                SELECT b.id,
                       CASE
                         WHEN EXISTS (SELECT 1 FROM mgj_alumni a WHERE LOWER(a.name) = LOWER(b.name) AND a.deleted_at IS NULL) THEN 'Alumni'
                         WHEN EXISTS (SELECT 1 FROM mgj_leader_training_participants ltp
                                      JOIN mgj_leaders l ON l.id = ltp.leader_id
                                      WHERE l.member_id = b.id AND l.deleted_at IS NULL) THEN 'Leader Trained'
                         WHEN EXISTS (SELECT 1 FROM mgj_leaders l WHERE l.member_id = b.id AND l.deleted_at IS NULL AND l.status = 'Active') THEN 'Promoted to Leader'
                         WHEN EXISTS (SELECT 1 FROM mgj_pakhwada_attendance pa WHERE pa.member_id = b.id) THEN 'In Pakhwada'
                         ELSE 'Enrolled'
                       END AS stage
                FROM base b
            )
            SELECT stage, COUNT(*) AS count FROM stages GROUP BY stage
        """, params_m)
        rows = {r["stage"]: r["count"] for r in cur.fetchall()}
        ordered_stages = ["Enrolled", "In Pakhwada", "Promoted to Leader", "Leader Trained", "Alumni"]
        out["member_stage_breakdown"] = [{"stage": s, "count": rows.get(s, 0)} for s in ordered_stages]

        # 4. Age distribution by state (stacked bar — three series).
        cur.execute(f"""
            SELECT COALESCE(s.state_name, m.state_code, 'Unknown') AS state_name,
                   COUNT(*) FILTER (WHERE m.age_at_enrollment < 20) AS less_than_20,
                   COUNT(*) FILTER (WHERE m.age_at_enrollment BETWEEN 20 AND 25) AS twenty_to_twentyfive,
                   COUNT(*) FILTER (WHERE m.age_at_enrollment > 25) AS above_25
            FROM mgj_members m
            LEFT JOIN central_states s ON m.state_code = s.state_code
            WHERE {where_members}
            GROUP BY s.state_name, m.state_code
            ORDER BY state_name
        """, params_m)
        out["age_distribution"] = cur.fetchall()

        # 4a. Socio-economic profile used by the MGJ dashboard. These are
        # read-only aggregates over existing member/leader profiles; no source
        # records are created or modified. Leader series use the linked member
        # profile because mgj_leaders intentionally stores only role metadata.
        leader_from = """
            FROM mgj_leaders l
            JOIN mgj_members m ON l.member_id = m.id
            WHERE l.deleted_at IS NULL
              AND LOWER(COALESCE(l.status, 'Active')) = 'active'
              AND {where_members}
        """

        cur.execute(f"SELECT COUNT(*) AS count FROM mgj_members m WHERE {where_members}", params_m)
        member_total = cur.fetchone()["count"]
        cur.execute(f"SELECT COUNT(*) AS count {leader_from.format(where_members=where_members)}", params_m)
        leader_total = cur.fetchone()["count"]
        out["socio_totals"] = {"members": member_total, "leaders": leader_total}

        def _profile_distribution(column: str, label: str):
            cur.execute(f"""
                SELECT COALESCE(NULLIF(TRIM(m.{column}), ''), 'Not specified') AS {label},
                       COUNT(*) AS count
                FROM mgj_members m
                WHERE {where_members}
                GROUP BY 1 ORDER BY count DESC, 1
            """, params_m)
            members = cur.fetchall()
            cur.execute(f"""
                SELECT COALESCE(NULLIF(TRIM(m.{column}), ''), 'Not specified') AS {label},
                       COUNT(*) AS count
                {leader_from.format(where_members=where_members)}
                GROUP BY 1 ORDER BY count DESC, 1
            """, params_m)
            return {"members": members, "leaders": cur.fetchall()}

        out["socio_caste"] = _profile_distribution("caste_category", "label")
        out["socio_religion"] = _profile_distribution("community_religion", "label")
        out["socio_working"] = _profile_distribution("is_working", "label")

        cur.execute(f"""
            SELECT CASE
                     WHEN m.per_capita_income IS NULL THEN 'Not specified'
                     WHEN m.per_capita_income < 2000  THEN 'Below ₹2,000'
                     WHEN m.per_capita_income < 5000  THEN '₹2,000 – ₹4,999'
                     WHEN m.per_capita_income < 10000 THEN '₹5,000 – ₹9,999'
                     ELSE '₹10,000 and above'
                   END AS label,
                   COUNT(*) AS count,
                   CASE
                     WHEN m.per_capita_income IS NULL THEN 5
                     WHEN m.per_capita_income < 2000  THEN 1
                     WHEN m.per_capita_income < 5000  THEN 2
                     WHEN m.per_capita_income < 10000 THEN 3
                     ELSE 4
                   END AS sort_order
            FROM mgj_members m
            WHERE {where_members}
            GROUP BY 1, 3 ORDER BY sort_order
        """, params_m)
        out["socio_per_capita_income"] = cur.fetchall()

        cur.execute(f"""
            SELECT COALESCE(NULLIF(TRIM(m.education), ''), 'Not specified') AS label,
                   COUNT(*) AS count
            FROM mgj_members m
            WHERE {where_members}
            GROUP BY 1 ORDER BY count DESC, 1
        """, params_m)
        out["socio_education"] = cur.fetchall()

        cur.execute(f"""
            SELECT COALESCE(
                     NULLIF(TRIM(m.work_nature), ''),
                     NULLIF(TRIM(m.occupation), ''),
                     'Not specified'
                   ) AS label,
                   COUNT(*) AS count
            FROM mgj_members m
            WHERE {where_members}
              AND LOWER(COALESCE(m.is_working, '')) = 'yes'
            GROUP BY 1 ORDER BY count DESC, 1
        """, params_m)
        out["socio_where_working"] = cur.fetchall()

        # 5. Pakhwada sessions by type (doughnut).
        # mgj_pakhwada_sessions only carries centre_code, so state and
        # district filters must hop through central_centres.
        where_s = ["s.deleted_at IS NULL"]
        params_s: list = []
        sess_join = ""
        if state_code or district_code:
            sess_join = "LEFT JOIN central_centres c ON s.centre_code = c.centre_code"
            if state_code:    where_s.append("c.state_code = %s");    params_s.append(state_code)
            if district_code: where_s.append("c.district_code = %s"); params_s.append(district_code)
        if centre_code:   where_s.append("s.centre_code = %s");   params_s.append(centre_code)
        if date_from:     where_s.append("s.planned_date >= %s"); params_s.append(date_from)
        if date_to:       where_s.append("s.planned_date <= %s"); params_s.append(date_to)
        ws = " AND ".join(where_s)
        cur.execute(f"""
            SELECT session_type, COUNT(*) AS count
            FROM mgj_pakhwada_sessions s
            {sess_join}
            WHERE {ws}
            GROUP BY session_type
        """, params_s)
        out["pakhwada_by_type"] = cur.fetchall()

        # 6. Pakhwada sessions by quarter (horizontal bar).
        cur.execute(f"""
            SELECT quarter, COUNT(*) AS count
            FROM mgj_pakhwada_sessions s
            {sess_join}
            WHERE {ws}
            GROUP BY quarter
            ORDER BY quarter
        """, params_s)
        out["pakhwada_by_quarter"] = cur.fetchall()

        # 7. Attendance status across all pakhwada attendance rows.
        # Hop through mgj_pakhwada_sessions for centre_code, then through
        # central_centres for state/district scoping.
        att_conds = ["1=1"]
        att_params: list = []
        att_join = ""
        if state_code or district_code or centre_code or date_from or date_to:
            att_join = "JOIN mgj_pakhwada_sessions s ON pa.session_id = s.id"
            if state_code or district_code:
                att_join += " LEFT JOIN central_centres c ON s.centre_code = c.centre_code"
                if state_code:    att_conds.append("c.state_code = %s");    att_params.append(state_code)
                if district_code: att_conds.append("c.district_code = %s"); att_params.append(district_code)
            if centre_code:   att_conds.append("s.centre_code = %s");   att_params.append(centre_code)
            if date_from:     att_conds.append("s.planned_date >= %s"); att_params.append(date_from)
            if date_to:       att_conds.append("s.planned_date <= %s"); att_params.append(date_to)
        cur.execute(f"""
            SELECT pa.status, COUNT(*) AS count
            FROM mgj_pakhwada_attendance pa {att_join}
            WHERE {' AND '.join(att_conds)}
            GROUP BY pa.status
        """, att_params)
        out["pakhwada_attendance_status"] = cur.fetchall()

        # 8 + 9 + 10. Monthly trends from Overall Activities.
        # mgj_monthly_activities only carries centre_code, so we always
        # JOIN to central_centres to get state/district context for both
        # the filters and the leader-log per-state aggregation.
        # 2026-10-01: fallback to mgj_master_batches.state_code when the
        # centre_code on a mgj_monthly_activities row cannot be resolved
        # via central_centres (e.g. legacy rows stored as literal "None").
        # Keeps state-only PIs from losing their state-wide numbers.
        ma_conds = ["ma.deleted_at IS NULL"]
        ma_params: list = []
        if state_code:
            ma_conds.append("(c.state_code = %s OR mb.state_code = %s)")
            ma_params.append(state_code); ma_params.append(state_code)
        # 2026-10-07 (user ask): district/centre fall back to the
        # batch's state when the activity row has centre_code=NULL,
        # so batch-only entries aren't dropped when a specific centre
        # is picked. Requires state_code to also be set (which the
        # dashboard sends alongside district/centre).
        if district_code:
            if state_code:
                ma_conds.append("(c.district_code = %s OR (ma.centre_code IS NULL AND mb.state_code = %s))")
                ma_params.append(district_code); ma_params.append(state_code)
            else:
                ma_conds.append("c.district_code = %s"); ma_params.append(district_code)
        if centre_code:
            if state_code:
                ma_conds.append("(ma.centre_code = %s OR (ma.centre_code IS NULL AND mb.state_code = %s))")
                ma_params.append(centre_code); ma_params.append(state_code)
            else:
                ma_conds.append("ma.centre_code = %s"); ma_params.append(centre_code)
        # 2026-10-07 (user ask): ma.month stores the first-of-month
        # (DATE). Normalize incoming date_from/date_to to the enclosing
        # month so a mid-month pick (e.g. 15 Apr) still includes April
        # activities (whose ma.month = 2026-04-01).
        if date_from:     ma_conds.append("ma.month >= DATE_TRUNC('month', %s::date)"); ma_params.append(date_from)
        if date_to:       ma_conds.append("ma.month <= DATE_TRUNC('month', %s::date)"); ma_params.append(date_to)
        ma_join = ("LEFT JOIN central_centres c ON ma.centre_code = c.centre_code "
                   "LEFT JOIN mgj_master_batches mb ON mb.id = ma.batch_id")
        cur.execute(f"""
            SELECT TO_CHAR(ma.month, 'Mon YYYY') AS label,
                   ma.month,
                   SUM(COALESCE(ma.pakhwada_participants, 0)) AS pakhwada,
                   SUM(COALESCE(ma.sports_participants,   0)) AS sports
            FROM mgj_monthly_activities ma {ma_join}
            WHERE {' AND '.join(ma_conds)}
            GROUP BY ma.month
            ORDER BY ma.month
        """, ma_params)
        out["monthly_participants"] = cur.fetchall()

        # 9. Monthly parent engagement (stacked bar: male / female / male-only).
        cur.execute(f"""
            SELECT TO_CHAR(ma.month, 'Mon YYYY') AS label,
                   ma.month,
                   SUM(COALESCE(ma.parent_meeting_male,   0)) AS parent_male,
                   SUM(COALESCE(ma.parent_meeting_female, 0)) AS parent_female,
                   SUM(COALESCE(ma.male_only_meetings,    0)) AS male_only
            FROM mgj_monthly_activities ma {ma_join}
            WHERE {' AND '.join(ma_conds)}
            GROUP BY ma.month
            ORDER BY ma.month
        """, ma_params)
        out["monthly_parent_engagement"] = cur.fetchall()

        # 10. Leader-log totals YTD (per state — bar chart).
        # 2026-05-26: Vaccinations + Unpaid-Care-Boys dropped from the form;
        # excluded from the total so the chart matches what users can now
        # enter. Historical values for those columns are preserved in the DB
        # but no longer contribute to dashboard sums.
        # 2026-10-01: COALESCE central_centres.state_code with the batch's
        # state_code so orphan activity rows (centre_code="None") land
        # under their real state in the per-state chart.
        cur.execute(f"""
            SELECT COALESCE(st.state_name, mbst.state_name, c.state_code, mb.state_code, 'Unknown') AS state_name,
                   SUM(COALESCE(ma.leader_community_actions, 0)
                     + COALESCE(ma.leader_www_forms,         0)) AS total
            FROM mgj_monthly_activities ma {ma_join}
            LEFT JOIN central_states st   ON c.state_code  = st.state_code
            LEFT JOIN central_states mbst ON mb.state_code = mbst.state_code
            WHERE {' AND '.join(ma_conds)}
            GROUP BY COALESCE(st.state_name, mbst.state_name, c.state_code, mb.state_code, 'Unknown')
            ORDER BY total DESC
        """, ma_params)
        out["leader_log_totals"] = cur.fetchall()

        # 11. Alumni working-status distribution (doughnut).
        alumni_conds2 = ["a.deleted_at IS NULL"]
        alumni_params2: list = []
        if state_code:  alumni_conds2.append("a.state_code = %s");  alumni_params2.append(state_code)
        if centre_code: alumni_conds2.append("a.centre_code = %s"); alumni_params2.append(centre_code)
        cur.execute(f"""
            SELECT COALESCE(working_status, 'Unknown') AS status, COUNT(*) AS count
            FROM mgj_alumni a
            WHERE {' AND '.join(alumni_conds2)}
            GROUP BY working_status
            ORDER BY count DESC
        """, alumni_params2)
        out["alumni_working_status"] = cur.fetchall()

    return out


# ── /mis — section-shaped data for the new MGJ MIS dashboard ─────────────

@router.get("/mis")
def mis(
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    """Single round-trip for the new MGJ MIS dashboard. Mirrors the Excel
    Overall Activities sheet layout — five major sections + an activity
    heatmap. Every series is filterable by state/district/centre/duration.

    mgj_monthly_activities is the workhorse (32 numeric cols × 6 records
    on stage). Geography hops via central_centres because the activity rows
    only carry centre_code natively.
    """
    # Common WHERE + JOIN for mgj_monthly_activities ma JOIN central_centres c
    # 2026-10-01: fallback to mgj_master_batches.state_code when the
    # centre_code on a mgj_monthly_activities row cannot be resolved
    # via central_centres (e.g. legacy rows stored as literal "None").
    # Keeps state-only PIs from losing their state-wide numbers.
    ma_conds = ["ma.deleted_at IS NULL"]
    ma_params: list = []
    if state_code:
        ma_conds.append("(c.state_code = %s OR mb.state_code = %s)")
        ma_params.append(state_code); ma_params.append(state_code)
    # 2026-10-07 (user ask): see /charts same comment above.
    if district_code:
        if state_code:
            ma_conds.append("(c.district_code = %s OR (ma.centre_code IS NULL AND mb.state_code = %s))")
            ma_params.append(district_code); ma_params.append(state_code)
        else:
            ma_conds.append("c.district_code = %s"); ma_params.append(district_code)
    if centre_code:
        if state_code:
            ma_conds.append("(ma.centre_code = %s OR (ma.centre_code IS NULL AND mb.state_code = %s))")
            ma_params.append(centre_code); ma_params.append(state_code)
        else:
            ma_conds.append("ma.centre_code = %s"); ma_params.append(centre_code)
    # 2026-10-07 (user ask): see /charts same comment above.
    if date_from:     ma_conds.append("ma.month >= DATE_TRUNC('month', %s::date)"); ma_params.append(date_from)
    if date_to:       ma_conds.append("ma.month <= DATE_TRUNC('month', %s::date)"); ma_params.append(date_to)
    ma_join  = ("LEFT JOIN central_centres c ON ma.centre_code = c.centre_code "
                "LEFT JOIN mgj_master_batches mb ON mb.id = ma.batch_id")
    ma_where = " AND ".join(ma_conds)

    out: dict = {}
    with get_cursor() as cur:

        # ----- Section 1: Monthly Activities — totals + monthly trend -----
        cur.execute(f"""
            SELECT
              COALESCE(SUM(ma.pakhwada_planned),     0) AS pakhwada_planned,
              COALESCE(SUM(ma.pakhwada_conducted),   0) AS pakhwada_conducted,
              COALESCE(SUM(ma.pakhwada_participants),0) AS pakhwada_participants,
              COALESCE(SUM(ma.pakhwada_direct),      0) AS pakhwada_direct,
              COALESCE(SUM(ma.pakhwada_one_to_one),  0) AS pakhwada_one_to_one,
              COALESCE(SUM(ma.sports_sessions),      0) AS sports_sessions,
              COALESCE(SUM(ma.sports_participants),  0) AS sports_participants,
              COALESCE(SUM(ma.hh_visits),            0) AS hh_visits,
              COALESCE(SUM(ma.parent_meeting_total), 0) AS parent_meeting_total,
              COALESCE(SUM(ma.parent_meeting_male),  0) AS parent_meeting_male,
              COALESCE(SUM(ma.parent_meeting_female),0) AS parent_meeting_female,
              COALESCE(SUM(ma.male_only_meetings),   0) AS male_only_meetings,
              COALESCE(SUM(ma.assignments_completed),0) AS assignments_completed,
              COALESCE(SUM(ma.canopy_activities),    0) AS canopy_activities,
              COALESCE(SUM(ma.mike_prachar),         0) AS mike_prachar,
              -- WWW funnel was replaced 2026-05-26: now 3 stages
              -- (interested / registered / enrollment). The old
              -- www_enabled_women + www_enrollments columns are still
              -- in the DB for historical data, just no longer aggregated
              -- into the dashboard.
              COALESCE(SUM(ma.www_women_interested), 0) AS www_women_interested,
              COALESCE(SUM(ma.www_women_registered), 0) AS www_women_registered,
              COALESCE(SUM(ma.www_women_enrollment), 0) AS www_women_enrollment,
              COALESCE(SUM(ma.gbv_reached),          0) AS gbv_reached,
              COALESCE(SUM(ma.leader_community_actions),0) AS leader_community_actions,
              COALESCE(SUM(ma.leader_www_forms),     0) AS leader_www_forms,
              COALESCE(SUM(ma.synergy_meetings),     0) AS synergy_meetings,
              COALESCE(SUM(ma.synergy_participants), 0) AS synergy_participants,
              COALESCE(SUM(ma.leader_monthly_meetings),0)  AS leader_monthly_meetings,
              COALESCE(SUM(ma.leader_monthly_participants),0) AS leader_monthly_participants,
              COALESCE(SUM(ma.alumni_meet_participants),0) AS alumni_meet_participants,
              COALESCE(SUM(ma.baseline_count),       0) AS baseline_count,
              COALESCE(SUM(ma.midline_y1),           0) AS midline_y1,
              COALESCE(SUM(ma.midline_y2),           0) AS midline_y2,
              COALESCE(SUM(ma.endline_count),        0) AS endline_count,
              COUNT(*)                                  AS entries
            FROM mgj_monthly_activities ma {ma_join}
            WHERE {ma_where}
        """, ma_params)
        out["totals"] = cur.fetchone() or {}

        # Monthly trend rows — used by the timeline, heatmap, and trend chart
        cur.execute(f"""
            SELECT TO_CHAR(ma.month, 'Mon YYYY') AS label,
                   ma.month,
                   SUM(COALESCE(ma.pakhwada_conducted,   0)) AS pakhwada,
                   SUM(COALESCE(ma.sports_sessions,      0)) AS sports,
                   SUM(COALESCE(ma.parent_meeting_total, 0)) AS parent_meetings,
                   SUM(COALESCE(ma.assignments_completed,0)) AS assignments,
                   SUM(COALESCE(ma.pakhwada_participants,0)
                     + COALESCE(ma.sports_participants,  0)
                     + COALESCE(ma.parent_meeting_total, 0)) AS total_engagement,
                   -- 2026-10-07 (user ask): per-month GBV reached so the
                   -- GBV card's trend line plots the same metric its KPI
                   -- shows (`gbv_reached`), not the generic engagement sum.
                   SUM(COALESCE(ma.gbv_reached, 0)) AS gbv_reached
            FROM mgj_monthly_activities ma {ma_join}
            WHERE {ma_where}
            GROUP BY ma.month
            ORDER BY ma.month
        """, ma_params)
        out["monthly_trend"] = cur.fetchall()

        # Quarter-wise totals — for the quarter-comparison bars
        cur.execute(f"""
            SELECT EXTRACT(QUARTER FROM ma.month)::INT AS quarter,
                   EXTRACT(YEAR    FROM ma.month)::INT AS yr,
                   SUM(COALESCE(ma.pakhwada_conducted, 0))   AS pakhwada,
                   SUM(COALESCE(ma.sports_sessions, 0))      AS sports,
                   SUM(COALESCE(ma.assignments_completed,0)) AS assignments,
                   SUM(COALESCE(ma.parent_meeting_total, 0)) AS parent
            FROM mgj_monthly_activities ma {ma_join}
            WHERE {ma_where}
            GROUP BY yr, quarter
            ORDER BY yr, quarter
        """, ma_params)
        out["quarter_totals"] = cur.fetchall()

        # ----- Real Pakhwada Sessions (from mgj_pakhwada_sessions, NOT the
        # monthly KPI form). The dashboard previously read pakhwada totals
        # from mgj_monthly_activities (the manually-typed monthly KPI form),
        # which diverged from what PIs actually log in the Pakhwada Session
        # tab. These two queries now pull straight from the session table so
        # the dashboard matches the Pakhwada Sessions list 1:1.
        ps_conds = ["s.deleted_at IS NULL"]
        ps_params: list = []
        ps_join = ""
        if state_code or district_code:
            ps_join = "LEFT JOIN central_centres c ON s.centre_code = c.centre_code"
            if state_code:    ps_conds.append("c.state_code = %s");    ps_params.append(state_code)
            if district_code: ps_conds.append("c.district_code = %s"); ps_params.append(district_code)
        if centre_code:   ps_conds.append("s.centre_code = %s");   ps_params.append(centre_code)
        if date_from:     ps_conds.append("s.planned_date >= %s"); ps_params.append(date_from)
        if date_to:       ps_conds.append("s.planned_date <= %s"); ps_params.append(date_to)
        ps_where = " AND ".join(ps_conds)

        # Pakhwada Coverage — planned total vs conducted count
        cur.execute(f"""
            SELECT COUNT(*)                                     AS planned,
                   COUNT(*) FILTER (WHERE s.status = 'Conducted') AS conducted
            FROM mgj_pakhwada_sessions s {ps_join}
            WHERE {ps_where}
        """, ps_params)
        out["pakhwada_coverage"] = cur.fetchone() or {"planned": 0, "conducted": 0}

        # Monthly Sessions — INPUT vs SPORTS counted by month of planned_date
        cur.execute(f"""
            SELECT TO_CHAR(DATE_TRUNC('month', s.planned_date), 'Mon YYYY') AS label,
                   DATE_TRUNC('month', s.planned_date)         AS month,
                   COUNT(*) FILTER (WHERE s.session_type = 'INPUT')  AS input_sessions,
                   COUNT(*) FILTER (WHERE s.session_type = 'SPORTS') AS sports_sessions
            FROM mgj_pakhwada_sessions s {ps_join}
            WHERE {ps_where}
            GROUP BY DATE_TRUNC('month', s.planned_date)
            ORDER BY DATE_TRUNC('month', s.planned_date)
        """, ps_params)
        out["pakhwada_sessions_monthly"] = cur.fetchall()

        # 2026-10-05 (user ask):
        #   * The old 'Pakhwada Attendance by Location' chart was removed.
        #   * 'Monthly Sessions — Pakhwada (Input)' and 'Monthly Sessions —
        #     Pakhwada (Sports)' now show ATTENDANCE RATE (%) broken down
        #     by month × location × topic. These two queries emit one row
        #     per (month, centre, topic) with present/total counts and the
        #     attendance_pct ready for the chart.
        _loc_join = ps_join if ps_join else "LEFT JOIN central_centres c ON s.centre_code = c.centre_code"
        def _att_rate_sql(session_type):
            # 2026-10-07 (user ask): count DISTINCT members rather than
            # attendance ROWS. Each attendance row is one member × one
            # session, so summing them double-counted a member who
            # attended several sessions and let totals exceed the
            # centre's roster (e.g. North Kolkata, 196 members).
            # 'total' = unique members marked in the (month, centre,
            # topic) bucket. 'present' = unique members marked Present
            # at least once. attendance_pct = present / total × 100.
            return f"""
                SELECT DATE_TRUNC('month', s.planned_date) AS month,
                       TO_CHAR(DATE_TRUNC('month', s.planned_date), 'Mon YYYY') AS month_label,
                       COALESCE(c.centre_name, s.centre_code, 'Unknown') AS centre_name,
                       COALESCE(NULLIF(TRIM(s.session_topic), ''), 'Unspecified') AS topic,
                       COUNT(DISTINCT pa.member_id) FILTER (WHERE pa.status = 'Present') AS present,
                       COUNT(DISTINCT pa.member_id)                                      AS total,
                       CASE WHEN COUNT(DISTINCT pa.member_id) > 0
                            THEN ROUND(100.0 * COUNT(DISTINCT pa.member_id) FILTER (WHERE pa.status = 'Present')
                                            / COUNT(DISTINCT pa.member_id), 1)
                            ELSE 0 END AS attendance_pct
                  FROM mgj_pakhwada_sessions s
             LEFT JOIN mgj_pakhwada_attendance pa ON pa.session_id = s.id
                       {_loc_join}
                 WHERE {ps_where}
                   AND s.session_type = '{session_type}'
                   -- 2026-10-07 (user ask): drafts/planned shouldn't
                   -- feed the two monthly Pakhwada attendance charts.
                   -- Only sessions that are both Conducted and whose
                   -- attendance roster was Submitted count.
                   AND s.status = 'Conducted'
                   AND s.attendance_status = 'Submitted'
                 GROUP BY DATE_TRUNC('month', s.planned_date),
                          c.centre_name, s.centre_code, s.session_topic
                HAVING COUNT(DISTINCT pa.member_id) > 0
                 ORDER BY DATE_TRUNC('month', s.planned_date),
                          centre_name, topic
            """
        cur.execute(_att_rate_sql('INPUT'), ps_params)
        out["pakhwada_input_monthly_attendance"] = cur.fetchall()
        cur.execute(_att_rate_sql('SPORTS'), ps_params)
        out["pakhwada_sports_monthly_attendance"] = cur.fetchall()

        # Location-wise attendance rate over time (for Pakhwada Input & Sports line charts)
        def _loc_rate_sql(session_type):
            return f"""
                SELECT DATE_TRUNC('month', s.planned_date) AS month,
                       TO_CHAR(DATE_TRUNC('month', s.planned_date), 'Mon YYYY') AS month_label,
                       COALESCE(c.centre_name, s.centre_code, 'Unknown') AS location,
                       COUNT(DISTINCT pa.member_id) FILTER (WHERE pa.status = 'Present') AS present,
                       COUNT(DISTINCT pa.member_id) AS total,
                       CASE WHEN COUNT(DISTINCT pa.member_id) > 0
                            THEN ROUND(100.0 * COUNT(DISTINCT pa.member_id) FILTER (WHERE pa.status = 'Present')
                                            / COUNT(DISTINCT pa.member_id), 1)
                            ELSE 0 END AS attendance_pct
                  FROM mgj_pakhwada_sessions s
             LEFT JOIN mgj_pakhwada_attendance pa ON pa.session_id = s.id
                       {_loc_join}
                 WHERE {ps_where}
                   AND s.session_type = '{session_type}'
                   AND s.status = 'Conducted'
                 GROUP BY DATE_TRUNC('month', s.planned_date),
                          c.centre_name, s.centre_code
                HAVING COUNT(DISTINCT pa.member_id) > 0
                 ORDER BY DATE_TRUNC('month', s.planned_date) ASC,
                          location ASC
            """
        cur.execute(_loc_rate_sql('INPUT'), ps_params)
        out["pakhwada_input_location_trend"] = cur.fetchall()
        cur.execute(_loc_rate_sql('SPORTS'), ps_params)
        out["pakhwada_sports_location_trend"] = cur.fetchall()

        # Location-wise Pakhwada Coverage (Planned vs Conducted)
        cur.execute(f"""
            SELECT COALESCE(c.centre_name, s.centre_code, 'Unknown') AS location,
                   COUNT(*) AS planned,
                   COUNT(*) FILTER (WHERE s.status = 'Conducted') AS conducted
            FROM mgj_pakhwada_sessions s
            {_loc_join}
            WHERE {ps_where}
            GROUP BY COALESCE(c.centre_name, s.centre_code, 'Unknown')
            ORDER BY planned DESC, location ASC
        """, ps_params)
        out["pakhwada_coverage_by_location"] = cur.fetchall()

        # Pakhwada Similar Dates summary
        cur.execute(f"""
            SELECT s.planned_date::text AS planned_date,
                   TO_CHAR(s.planned_date, 'DD Mon YYYY') AS date_label,
                   COUNT(DISTINCT s.id) AS session_count,
                   COUNT(DISTINCT s.id) FILTER (WHERE s.session_type = 'INPUT') AS input_count,
                   COUNT(DISTINCT s.id) FILTER (WHERE s.session_type = 'SPORTS') AS sports_count,
                   COUNT(DISTINCT s.id) FILTER (WHERE s.status = 'Conducted') AS conducted_count,
                   STRING_AGG(DISTINCT COALESCE(c.centre_name, s.centre_code), ', ') AS locations,
                   STRING_AGG(DISTINCT COALESCE(NULLIF(TRIM(s.session_topic), ''), 'Unspecified'), ' | ') AS topics,
                   COUNT(DISTINCT pa.member_id) AS total_members,
                   COUNT(DISTINCT pa.member_id) FILTER (WHERE pa.status = 'Present') AS present_members,
                   CASE WHEN COUNT(DISTINCT pa.member_id) > 0
                        THEN ROUND(100.0 * COUNT(DISTINCT pa.member_id) FILTER (WHERE pa.status = 'Present') / COUNT(DISTINCT pa.member_id), 1)
                        ELSE 0 END AS attendance_pct
            FROM mgj_pakhwada_sessions s
            {_loc_join}
            LEFT JOIN mgj_pakhwada_attendance pa ON pa.session_id = s.id
            WHERE {ps_where} AND s.planned_date IS NOT NULL
            GROUP BY s.planned_date
            ORDER BY s.planned_date DESC
            LIMIT 25
        """, ps_params)
        out["pakhwada_similar_dates"] = cur.fetchall()

        # Leadership Training with Attendance
        lt_conds = ["t.deleted_at IS NULL"]
        lt_params: list = []
        if state_code:
            lt_conds.append("t.state_code = %s")
            lt_params.append(state_code)
        if date_from:
            lt_conds.append("t.created_at >= %s")
            lt_params.append(date_from)
        if date_to:
            lt_conds.append("t.created_at <= (%s::date + interval '1 day')")
            lt_params.append(date_to)
        lt_where = " AND ".join(lt_conds)

        cur.execute(f"""
            SELECT t.id, t.state_code, t.phase, t.month, t.year, t.type_of_training,
                   t.created_at::text AS created_at,
                   COALESCE(s.state_name, t.state_code, '') AS state_name,
                   COALESCE(b.name, '') AS batch_name,
                   (SELECT STRING_AGG(tp.name, ', ' ORDER BY tt.position, tp.name)
                      FROM mgj_leader_training_topics tt
                      JOIN mgj_leader_topics tp ON tt.topic_id = tp.id
                     WHERE tt.training_id = t.id) AS topics_summary,
                   (SELECT COUNT(*) FROM mgj_leader_training_participants p WHERE p.training_id = t.id) AS participant_count,
                   (SELECT COUNT(*) FROM mgj_leader_training_attendance a WHERE a.training_id = t.id AND a.status = 'Present') AS present_count,
                   (SELECT COUNT(*) FROM mgj_leader_training_attendance a WHERE a.training_id = t.id AND a.status = 'Absent') AS absent_count
            FROM mgj_leader_trainings t
            LEFT JOIN central_states s ON t.state_code = s.state_code
            LEFT JOIN mgj_master_leader_batches b ON t.batch_id = b.id
            WHERE {lt_where}
            ORDER BY t.created_at DESC, t.id DESC
            LIMIT 50
        """, lt_params)
        out["leadership_trainings"] = cur.fetchall()

        # ----- Section 2: Campaigns & Activities — per-campaign breakdown -----
        # mgj_monthly_campaigns is a per-month child table. Join through
        # the parent monthly entry to pick up centre, then state.
        # 2026-10-01: fallback to mgj_master_batches.state_code (same reason
        # as the ma_join block above). Keeps Campaigns from showing empty
        # when the activity row's centre_code is a stray "None" string.
        # 2026-10-07 (user ask): (a) also filter soft-deleted parent
        # monthly_activities so Campaign Participation doesn't inflate
        # with campaigns under deleted monthly entries. mgj_monthly_
        # campaigns has no deleted_at of its own, so the parent's
        # soft-delete flag is the only check. (b) normalize ma.month
        # date comparisons to the enclosing month -- same fix as the
        # ma_conds builder above.
        camp_conds = ["ma.deleted_at IS NULL"]
        camp_params: list = []
        camp_join  = ("JOIN mgj_monthly_activities ma ON mc.entry_id = ma.id "
                      "LEFT JOIN central_centres c ON ma.centre_code = c.centre_code "
                      "LEFT JOIN mgj_master_batches mb2 ON mb2.id = ma.batch_id")
        if state_code:
            camp_conds.append("(c.state_code = %s OR mb2.state_code = %s)")
            camp_params.append(state_code); camp_params.append(state_code)
        # 2026-10-07 (user ask): same batch-state fallback as ma_conds
        # — campaigns under batch-only activities (centre_code=NULL)
        # weren't surfacing when a user picked a specific centre.
        if district_code:
            if state_code:
                camp_conds.append("(c.district_code = %s OR (ma.centre_code IS NULL AND mb2.state_code = %s))")
                camp_params.append(district_code); camp_params.append(state_code)
            else:
                camp_conds.append("c.district_code = %s"); camp_params.append(district_code)
        if centre_code:
            if state_code:
                camp_conds.append("(ma.centre_code = %s OR (ma.centre_code IS NULL AND mb2.state_code = %s))")
                camp_params.append(centre_code); camp_params.append(state_code)
            else:
                camp_conds.append("ma.centre_code = %s"); camp_params.append(centre_code)
        if date_from:     camp_conds.append("ma.month >= DATE_TRUNC('month', %s::date)"); camp_params.append(date_from)
        if date_to:       camp_conds.append("ma.month <= DATE_TRUNC('month', %s::date)"); camp_params.append(date_to)
        # 2026-10-06 (user ask): also group by campaign_name so the
        # Campaign Participation donut shows every campaign as its own
        # slice (not just the three types), and the tooltip can reveal
        # the actual campaign name on hover.
        cur.execute(f"""
            SELECT COALESCE(NULLIF(TRIM(mc.campaign_name), ''), 'Unnamed') AS campaign_name,
                   COALESCE(mc.campaign_type, 'Other')                     AS campaign_type,
                   COUNT(*)                                                AS events,
                   SUM(COALESCE(mc.participants, 0))                       AS participants
            FROM mgj_monthly_campaigns mc {camp_join}
            WHERE {' AND '.join(camp_conds)}
            GROUP BY mc.campaign_name, mc.campaign_type
            ORDER BY participants DESC NULLS LAST, campaign_name
        """, camp_params)
        out["campaigns"] = cur.fetchall()

        # ----- Section 5: Leaders' Log — per-state breakdown -----
        # 2026-05-26: vaccinations + unpaid_care_boys columns dropped from the
        # form. Removed from this aggregation so dashboard matches form scope.
        # 2026-10-01: COALESCE central_centres.state_code with the batch's
        # state_code so orphan activity rows (centre_code="None") are
        # grouped under their real state instead of "Unknown".
        cur.execute(f"""
            SELECT COALESCE(st.state_name, mbst.state_name, c.state_code, mb.state_code, 'Unknown') AS state_name,
                   SUM(COALESCE(ma.leader_community_actions, 0)) AS community_actions,
                   SUM(COALESCE(ma.leader_www_forms,         0)) AS www_forms
            FROM mgj_monthly_activities ma {ma_join}
            LEFT JOIN central_states st   ON c.state_code  = st.state_code
            LEFT JOIN central_states mbst ON mb.state_code = mbst.state_code
            WHERE {ma_where}
            GROUP BY COALESCE(st.state_name, mbst.state_name, c.state_code, mb.state_code, 'Unknown')
            ORDER BY (SUM(COALESCE(ma.leader_community_actions,0))
                    + SUM(COALESCE(ma.leader_www_forms,        0))) DESC
        """, ma_params)
        out["leaders_by_state"] = cur.fetchall()

        # ----- Section 6: Annual Activities — surveys -----
        # Returns the four absolute counts (already in totals) plus the
        # mgj_alumni headline count for the "Alumni Tracking" tile.
        alumni_conds = ["a.deleted_at IS NULL"]
        alumni_params: list = []
        if state_code:  alumni_conds.append("a.state_code = %s");  alumni_params.append(state_code)
        if centre_code: alumni_conds.append("a.centre_code = %s"); alumni_params.append(centre_code)
        cur.execute(f"""
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE COALESCE(a.attended_alumni_meet,'') = 'Yes') AS attended
            FROM mgj_alumni a
            WHERE {' AND '.join(alumni_conds)}
        """, alumni_params)
        out["alumni"] = cur.fetchone() or {}

    return out


# ── /drill-down/members ──────────────────────────────────────────────────

# ── /socio-economic ──────────────────────────────────────────────────────
# Aggregate socio-economic profile of Members and Leaders (side-by-side).
# 2026-07-13 — added per user request. Reuses _common_filters so the
# section honours the same State / District / Centre / Date filters as
# the rest of the MGJ dashboard. Leaders = members whose id is in
# mgj_leaders.member_id AND leader is not soft-deleted.
#
# Bucket definitions (kept as class-level constants so the frontend can
# render bars in the same left-to-right order):
#   age_bucket:
#     '<18', '18-24', '25-30', '31-40', '41+', 'Not Specified'
#   per_capita_bucket:
#     '<₹2k', '₹2k-5k', '₹5k-10k', '₹10k+', 'Not Specified'
#   caste  : General, OBC, SC, ST, Other, Not Specified
#   religion : Hindu, Muslim, Sikh, Christian, Buddhist, Jain, Other, Not Specified
#   education (buckets are normalised: exact-match then trimmed on comma):
#     'Illiterate','Below 5','5th-8th','9th-10th','11th-12th',
#     'Diploma','Graduate','Post-Graduate','Other','Not Specified'
#   working  : Yes, No, Not Specified

@router.get("/socio-economic")
def socio_economic(request: Request,
                   state_code: Optional[str] = None,
                   district_code: Optional[str] = None,
                   centre_code: Optional[str] = None,
                   group_number: Optional[str] = None,
                   status: Optional[str] = None,
                   date_from: Optional[date] = None,
                   date_to: Optional[date] = None):
    where, params = _common_filters(state_code, district_code, centre_code,
                                    status, date_from, date_to, "m",
                                    request=request, group_number=group_number)

    # Bucket-CASE snippets, shared across the two audiences.
    # 2026-08-08: age_at_enrollment is NULL for every current MGJ member,
    # so the whole age chart was landing in 'Not Specified' and rendering
    # empty. Fall back to a DOB-derived current age when age_at_enrollment
    # is missing so the chart always has classified data.
    EFF_AGE = "COALESCE(m.age_at_enrollment, EXTRACT(YEAR FROM AGE(m.date_of_birth))::int)"
    # 2026-10-04: user ask -> narrower 5-band age split (13-14, 15-17,
    # 18-19, 20-21, 22-24). Teen bands may show empty on stage/live since
    # most MGJ members are 18+ but the categories are now explicit.
    AGE_CASE = (
        "CASE "
        f"WHEN {EFF_AGE} IS NULL THEN 'Not Specified' "
        f"WHEN {EFF_AGE} BETWEEN 13 AND 14 THEN '13-14' "
        f"WHEN {EFF_AGE} BETWEEN 15 AND 17 THEN '15-17' "
        f"WHEN {EFF_AGE} BETWEEN 18 AND 19 THEN '18-19' "
        f"WHEN {EFF_AGE} BETWEEN 20 AND 21 THEN '20-21' "
        f"WHEN {EFF_AGE} BETWEEN 22 AND 24 THEN '22-24' "
        "ELSE 'Other' END"
    )
    PCI_CASE = (
        "CASE "
        "WHEN m.per_capita_income IS NULL THEN 'Not Specified' "
        "WHEN m.per_capita_income < 2000  THEN '<₹2k' "
        "WHEN m.per_capita_income < 5000  THEN '₹2k-5k' "
        "WHEN m.per_capita_income < 10000 THEN '₹5k-10k' "
        "ELSE '₹10k+' END"
    )
    # NOT: caste/religion/education can hold free-text 'Others: xxx'.
    # We normalise by taking the substring before ':' and title-casing;
    # anything unknown falls into 'Other'. Nulls become 'Not Specified'.
    CASTE_CASE = (
        "CASE "
        "WHEN m.caste_category IS NULL OR TRIM(m.caste_category) = '' THEN 'Not Specified' "
        "WHEN m.caste_category IN ('General','OBC','SC','ST') THEN m.caste_category "
        "ELSE 'Other' END"
    )
    RELIG_CASE = (
        "CASE "
        "WHEN m.community_religion IS NULL OR TRIM(m.community_religion) = '' THEN 'Not Specified' "
        "WHEN m.community_religion IN ('Hindu','Muslim','Sikh','Christian','Buddhist','Jain') THEN m.community_religion "
        "ELSE 'Other' END"
    )
    EDU_CASE = (
        "CASE "
        "WHEN m.education IS NULL OR TRIM(m.education) = '' THEN 'Not Specified' "
        "WHEN m.education ILIKE 'Illiterate' THEN 'Illiterate' "
        # NOTE: `%` is doubled to `%%` because these strings are executed
        # via psycopg2 %s parameter substitution — a bare `%` gets eaten
        # as a placeholder and blows up with 'IndexError: list index out
        # of range'. PostgreSQL sees the literal `%`.
        "WHEN m.education ILIKE 'Below 5%%' THEN 'Below 5' "
        "WHEN m.education ILIKE '5th%%' OR m.education ILIKE '6th%%' OR m.education ILIKE '7th%%' OR m.education ILIKE '8th%%' THEN '5th-8th' "
        "WHEN m.education ILIKE '9th%%' OR m.education ILIKE '10th%%' THEN '9th-10th' "
        "WHEN m.education ILIKE '11th%%' OR m.education ILIKE '12th%%' THEN '11th-12th' "
        "WHEN m.education ILIKE 'Diploma%%' THEN 'Diploma' "
        "WHEN m.education ILIKE 'Graduate%%' OR m.education ILIKE 'Bachelor%%' THEN 'Graduate' "
        "WHEN m.education ILIKE 'Post-Graduate%%' OR m.education ILIKE 'PG%%' OR m.education ILIKE 'Master%%' THEN 'Post-Graduate' "
        "ELSE 'Other' END"
    )
    WORKING_CASE = (
        "CASE "
        "WHEN m.is_working IS NULL OR TRIM(m.is_working) = '' THEN 'Not Specified' "
        "WHEN m.is_working ILIKE 'Yes' THEN 'Yes' "
        "WHEN m.is_working ILIKE 'No'  THEN 'No' "
        "ELSE 'Other' END"
    )

    # Leader-scope predicate: only members promoted (and leader row not
    # soft-deleted). We do NOT filter on leader.status here — the intent
    # is 'the leader cohort as recognised in the roster', which includes
    # Active, Walkout, and Dropout (matching how the KPI card counts them
    # elsewhere in the dashboard).
    LEADER_JOIN = ("EXISTS (SELECT 1 FROM mgj_leaders l "
                   "WHERE l.member_id = m.id AND l.deleted_at IS NULL)")

    def _bucket_pair(bucket_expr: str, order_list: list):
        """Run the same GROUP-BY twice — once for all members, once for
        leaders only — and merge the results into a single dict keyed by
        bucket label. Returns {"labels": [...], "members": [...], "leaders": [...]}.
        Buckets are returned in the order given by `order_list`; empty
        buckets show as zero. Any bucket that appears in the data but
        NOT in order_list is appended at the end (defensive)."""
        base = f"SELECT {bucket_expr} AS bkt, COUNT(*) AS n FROM mgj_members m WHERE {where} GROUP BY 1"
        base_ldr = f"SELECT {bucket_expr} AS bkt, COUNT(*) AS n FROM mgj_members m WHERE {where} AND {LEADER_JOIN} GROUP BY 1"
        with get_cursor() as cur:
            cur.execute(base, params)
            m_map = {row["bkt"]: int(row["n"] or 0) for row in cur.fetchall()}
            cur.execute(base_ldr, params)
            l_map = {row["bkt"]: int(row["n"] or 0) for row in cur.fetchall()}
        labels = list(order_list)
        # Append any data-only labels not in the ordered list.
        for k in list(m_map.keys()) + list(l_map.keys()):
            if k and k not in labels:
                labels.append(k)
        return {
            "labels":  labels,
            "members": [m_map.get(k, 0) for k in labels],
            "leaders": [l_map.get(k, 0) for k in labels],
        }

    out = {
        "age":       _bucket_pair(AGE_CASE,     ["<18", "18-24", "25-30", "31-40", "41+", "Not Specified"]),
        "caste":     _bucket_pair(CASTE_CASE,   ["General", "OBC", "SC", "ST", "Other", "Not Specified"]),
        "per_capita_income": _bucket_pair(PCI_CASE, ["<₹2k", "₹2k-5k", "₹5k-10k", "₹10k+", "Not Specified"]),
        "religion":  _bucket_pair(RELIG_CASE,   ["Hindu", "Muslim", "Sikh", "Christian", "Buddhist", "Jain", "Other", "Not Specified"]),
        "education": _bucket_pair(EDU_CASE,     ["Illiterate", "Below 5", "5th-8th", "9th-10th", "11th-12th", "Diploma", "Graduate", "Post-Graduate", "Other", "Not Specified"]),
        "working":   _bucket_pair(WORKING_CASE, ["Yes", "No", "Other", "Not Specified"]),
    }

    # ------------------------------------------------------------------
    # location: state-wise Active vs Dropout counts (user request 2026-07-14).
    # Bucket definition:
    #   active   = LOWER(status) = 'active'
    #   dropout  = LOWER(status) IN ('dropout','walkout')
    # State label uses central_states.state_name, falling back to state_code.
    # ------------------------------------------------------------------
    LOC_SQL = f"""
        SELECT COALESCE(s.state_name, m.state_code, 'Unknown') AS state,
               COUNT(*) AS members,
               SUM(CASE WHEN LOWER(m.status) = 'active' THEN 1 ELSE 0 END) AS active,
               SUM(CASE WHEN LOWER(m.status) IN ('dropout','walkout') THEN 1 ELSE 0 END) AS dropout
        FROM mgj_members m
        LEFT JOIN central_states s ON s.state_code = m.state_code
        WHERE {where}
        GROUP BY 1
        ORDER BY 1
    """
    # 2026-08-27: per-state Leader count (member geography) for the new
    # Leader column; and the true Members total (COUNT) so the table matches
    # the card/list instead of active+dropout (which omits Draft members).
    LEAD_SQL = f"""
        SELECT COALESCE(s.state_name, m.state_code, 'Unknown') AS state, COUNT(*) AS leaders
        FROM mgj_leaders l
        JOIN mgj_members m ON l.member_id = m.id
        LEFT JOIN central_states s ON s.state_code = m.state_code
        WHERE l.deleted_at IS NULL AND l.status = 'Active' AND {where}
        GROUP BY 1
    """
    with get_cursor() as cur:
        cur.execute(LOC_SQL, params)
        loc_rows = cur.fetchall()
        cur.execute(LEAD_SQL, params)
        lead_map = {r["state"]: int(r["leaders"] or 0) for r in cur.fetchall()}
    out["location"] = {
        "labels":  [r["state"] for r in loc_rows],
        "members": [int(r["members"] or 0) for r in loc_rows],
        "active":  [int(r["active"] or 0) for r in loc_rows],
        "dropout": [int(r["dropout"] or 0) for r in loc_rows],
        "leaders": [lead_map.get(r["state"], 0) for r in loc_rows],
    }

    # Group Mapping: group_name, mobiliser_name, active, dropout, total
    with get_cursor() as cur:
        cur.execute(f"""
            SELECT COALESCE(NULLIF(TRIM(mg.name), ''), NULLIF(TRIM(m.group_number), ''), 'Unassigned') AS group_name,
                   COALESCE(MAX(NULLIF(TRIM(mg.mobiliser_name), '')), MAX(NULLIF(TRIM(m.mobiliser_name), '')), '—') AS mobiliser_name,
                   COUNT(*) FILTER (WHERE LOWER(COALESCE(m.status, '')) = 'active') AS active,
                   COUNT(*) FILTER (WHERE LOWER(COALESCE(m.status, '')) IN ('dropout', 'walkout')) AS dropout,
                   COUNT(*) AS total
            FROM mgj_members m
            LEFT JOIN mgj_master_groups mg ON (mg.name = m.group_number OR mg.id::text = m.group_number) AND mg.deleted_at IS NULL
            WHERE {where}
            GROUP BY COALESCE(NULLIF(TRIM(mg.name), ''), NULLIF(TRIM(m.group_number), ''), 'Unassigned')
            ORDER BY group_name ASC
        """, params)
        out["group_mapping"] = cur.fetchall()

    # ------------------------------------------------------------------
    # where_working ("Nature of Work" chart): buckets built from
    # mgj_members.work_nature, which is the categorical multi-select
    # answer ("Factory work", "Patient care", "Self-employment",
    # "Construction", ...). Values are stored comma-separated when the
    # user picks more than one option, so we split them with
    # unnest(string_to_array(...)) and count members per bucket
    # (a member with two selections shows up once in each bucket, but
    # not twice within the same bucket thanks to COUNT DISTINCT).
    # Free-text "Self-employment/Other:<text>" and legacy "Other:<text>"
    # collapse to clean buckets so user-typed strings don't leak onto
    # the chart. Members with is_working = 'Yes' only.
    #
    # 2026-08-03 — user request: every canonical option from the Add-MGJ
    # form must appear as a bar even with zero members. The canonical
    # list is mirrored verbatim from index.html (checkbox values on the
    # `mgjWorkNature` field). Anything that surfaces in the DB but
    # isn't in the canonical list (data drift) is appended at the end
    # so no data gets hidden. The previous top-8 truncation is dropped —
    # the canonical list is only 8 options long, so truncation would
    # defeat the "always show all" guarantee.
    # ------------------------------------------------------------------
    # psycopg2 treats a bare '%' as the start of a placeholder, so the
    # LIKE wildcard MUST be escaped as '%%' inside a parameterised query.
    WW_BASE = (
        "CASE "
        "WHEN TRIM(v) ILIKE 'Self-employment/Other:%%' THEN 'Self-employment/Other' "
        "WHEN TRIM(v) ILIKE 'Other:%%' THEN 'Other' "
        "ELSE TRIM(v) END"
    )
    # Canonical option list — verbatim from index.html Add-MGJ form
    # (input[name="mgjWorkNature"] checkbox values). Keep in sync with
    # that form; changes here must land there too.
    WW_CANONICAL = [
        "Factory work", "Construction", "Patient care", "Caregiving",
        "Self-employment", "Family business", "Domestic work", "Other",
    ]
    WW_MEMBER_SQL = f"""
        SELECT {WW_BASE} AS w, COUNT(DISTINCT m.id) AS n
        FROM mgj_members m,
             LATERAL unnest(string_to_array(COALESCE(m.work_nature, ''), ',')) AS v
        WHERE {where}
          AND LOWER(COALESCE(m.is_working,'')) = 'yes'
          AND TRIM(v) <> ''
        GROUP BY 1
    """
    WW_LEADER_SQL = f"""
        SELECT {WW_BASE} AS w, COUNT(DISTINCT m.id) AS n
        FROM mgj_members m,
             LATERAL unnest(string_to_array(COALESCE(m.work_nature, ''), ',')) AS v
        WHERE {where}
          AND LOWER(COALESCE(m.is_working,'')) = 'yes'
          AND TRIM(v) <> ''
          AND {LEADER_JOIN}
        GROUP BY 1
    """
    with get_cursor() as cur:
        cur.execute(WW_MEMBER_SQL, params)
        m_rows = cur.fetchall()
        cur.execute(WW_LEADER_SQL, params)
        l_rows = cur.fetchall()
    m_map = {r["w"]: int(r["n"] or 0) for r in m_rows}
    l_map = {r["w"]: int(r["n"] or 0) for r in l_rows}
    # Build the label list: canonical order first (every option, zero
    # if not in the data), then any drift labels the DB surfaced that
    # aren't in the canonical list — appended alphabetised so nothing
    # gets hidden.
    labels = list(WW_CANONICAL)
    extras = sorted({k for k in list(m_map.keys()) + list(l_map.keys())
                     if k and k not in WW_CANONICAL})
    labels.extend(extras)
    m_data = [m_map.get(k, 0) for k in labels]
    l_data = [l_map.get(k, 0) for k in labels]
    out["where_working"] = {
        "labels":  labels,
        "members": m_data,
        "leaders": l_data,
    }
    # Totals for the sub-header ("N members, K leaders").
    with get_cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS n FROM mgj_members m WHERE {where}", params)
        out["total_members"] = int(cur.fetchone()["n"] or 0)
        cur.execute(f"SELECT COUNT(*) AS n FROM mgj_members m WHERE {where} AND {LEADER_JOIN}", params)
        out["total_leaders"] = int(cur.fetchone()["n"] or 0)
    return out


@router.get("/drill-down/members")
def drill_down_members(request: Request, chart: str, value: str,
                       state_code: Optional[str] = None,
                       district_code: Optional[str] = None,
                       centre_code: Optional[str] = None,
                       group_number: Optional[str] = None,
                       status: Optional[str] = None,
                       date_from: Optional[date] = None,
                       date_to: Optional[date] = None):
    """Return members matching a chart click. Mirrors FLP's drill-down."""
    where, params = _common_filters(state_code, district_code, centre_code, status, date_from, date_to, "m", request=request, group_number=group_number)

    if chart == "members_by_state":
        # value = state name
        where += " AND COALESCE(s.state_name, m.state_code, 'Unknown') = %s"
        params.append(value)
    elif chart == "age_group":
        if value == "Less than 20":
            where += " AND m.age_at_enrollment < 20"
        elif value == "20 to 25":
            where += " AND m.age_at_enrollment BETWEEN 20 AND 25"
        elif value == "Above 25":
            where += " AND m.age_at_enrollment > 25"
        else:
            raise HTTPException(status_code=400, detail="Unknown age group")
    elif chart == "member_stage":
        # Use the same CTE shape as the charts endpoint, then filter by stage.
        pass  # handled below in a different code path
    else:
        raise HTTPException(status_code=400, detail="Unknown chart")

    with get_cursor() as cur:
        if chart == "member_stage":
            where_m, params_m = _common_filters(state_code, district_code, centre_code, status, date_from, date_to, "m", request=request, group_number=group_number)
            cur.execute(f"""
                WITH base AS (
                    SELECT m.id, m.name, m.enrollment_number, m.gender, m.age_at_enrollment,
                           m.state_code, m.centre_code, m.status,
                           COALESCE(s.state_name, m.state_code, 'Unknown') AS state_name
                    FROM mgj_members m
                    LEFT JOIN central_states s ON m.state_code = s.state_code
                    WHERE {where_m}
                ), stages AS (
                    SELECT b.*,
                           CASE
                             WHEN EXISTS (SELECT 1 FROM mgj_alumni a WHERE LOWER(a.name) = LOWER(b.name) AND a.deleted_at IS NULL) THEN 'Alumni'
                             WHEN EXISTS (SELECT 1 FROM mgj_leader_training_participants ltp
                                          JOIN mgj_leaders l ON l.id = ltp.leader_id
                                          WHERE l.member_id = b.id AND l.deleted_at IS NULL) THEN 'Leader Trained'
                             WHEN EXISTS (SELECT 1 FROM mgj_leaders l WHERE l.member_id = b.id AND l.deleted_at IS NULL AND l.status = 'Active') THEN 'Promoted to Leader'
                             WHEN EXISTS (SELECT 1 FROM mgj_pakhwada_attendance pa WHERE pa.member_id = b.id) THEN 'In Pakhwada'
                             ELSE 'Enrolled'
                           END AS stage
                    FROM base b
                )
                SELECT id, name, enrollment_number, gender, age_at_enrollment, state_name, state_code, status
                FROM stages WHERE stage = %s
                ORDER BY name
                LIMIT 200
            """, params_m + [value])
        else:
            cur.execute(f"""
                SELECT m.id, m.name, m.enrollment_number, m.gender, m.age_at_enrollment,
                       COALESCE(s.state_name, m.state_code, 'Unknown') AS state_name,
                       m.state_code, m.status
                FROM mgj_members m
                LEFT JOIN central_states s ON m.state_code = s.state_code
                WHERE {where}
                ORDER BY m.name
                LIMIT 200
            """, params)
        return {"data": cur.fetchall()}
