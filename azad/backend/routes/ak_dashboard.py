"""AK (Azad Kishori) Dashboard — aggregations across the AK programme.

Distinct from the FLP / MGJ dashboards. Reads only ak_* tables. Returns
two endpoints designed for a single dashboard page:

  GET /api/ak-dashboard/stats   - top-level KPIs for the summary strip
  GET /api/ak-dashboard/charts  - chart-ready data series for every panel

Filters: state_code, district_code, centre_code, batch_id, month, date_from, date_to.
"""
from fastapi import APIRouter, Request
from typing import Optional
from datetime import date
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor

# 2026-08-11: role-scope enforcement — Specialist (Rajasthan-scoped)
# users must only see their state's leaders on the AK Home dashboard.
from routes._role_scope import enforce_role_scope

router = APIRouter(prefix="/api/ak-dashboard", tags=["AK Dashboard"])


def _leader_filters(state_code, district_code, centre_code, batch_id,
                    date_from, date_to, alias="l"):
    """Build the WHERE for ak_leaders. We join centres lazily for the
    district filter since ak_leaders only stores state_code + centre_code,
    not district_code."""
    conds = [f"{alias}.deleted_at IS NULL"]
    params: list = []
    need_centre_join = False
    if state_code:    conds.append(f"{alias}.state_code = %s");   params.append(state_code)
    if district_code:
        need_centre_join = True
        conds.append("c.district_code = %s"); params.append(district_code)
    if centre_code:   conds.append(f"{alias}.centre_code = %s");  params.append(centre_code)
    if batch_id:      conds.append(f"{alias}.batch_id = %s");     params.append(int(batch_id))
    if date_from:     conds.append(f"{alias}.created_at >= %s");  params.append(date_from)
    if date_to:       conds.append(f"{alias}.created_at < (%s::date + INTERVAL '1 day')"); params.append(date_to)
    return " AND ".join(conds), params, need_centre_join


@router.get("/stats")
def stats(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    """Six KPI numbers for the top strip."""
    scoped = enforce_role_scope(
        request,
        state_code=state_code,
        district_code=district_code,
        centre_code=centre_code,
    )
    state_code    = scoped.get('state_code')
    district_code = scoped.get('district_code')
    centre_code   = scoped.get('centre_code')
    where_l, params_l, join_centres = _leader_filters(state_code, district_code, centre_code, batch_id, date_from, date_to, "l")
    leaders_join = " LEFT JOIN central_centres c ON l.centre_code = c.centre_code " if join_centres else ""

    # Light filters for the rest (most non-leader tables only carry state_code/centre_code).
    # 2026-06-08: has_batch now actually filters by batch_id (was unused). ak_alaps has
    # batch_id; ak_alumni / ak_assessments / ak_addas / ak_trainings do not.
    def _geo_where(alias, has_district=False, has_batch=False, date_col='created_at'):
        conds = [f"{alias}.deleted_at IS NULL"] if alias != "ass" else ["1=1"]  # ak_assessments has no soft-delete
        params: list = []
        if state_code:  conds.append(f"{alias}.state_code = %s");  params.append(state_code)
        if district_code:
            conds.append(f"{alias}.centre_code IN (SELECT centre_code FROM central_centres WHERE district_code = %s)")
            params.append(district_code)
        if centre_code: conds.append(f"{alias}.centre_code = %s"); params.append(centre_code)
        if has_batch and batch_id:
            conds.append(f"{alias}.batch_id = %s"); params.append(int(batch_id))
        # 2026-10-03: honour the dashboard duration filter. Each caller
        # may pick its own date column; default is `created_at`. The
        # Trainings KPI passes `training_date` so the duration reflects
        # when the training was actually held.
        if date_from: conds.append(f"{alias}.{date_col} >= %s"); params.append(date_from)
        if date_to:   conds.append(f"{alias}.{date_col} < (%s::date + INTERVAL '1 day')"); params.append(date_to)
        return " AND ".join(conds), params

    with get_cursor() as cur:
        # 1. Total Kishoris (leaders) + 2. Active + 3. Dropout
        # 2026-06-01: Dropout count surfaced as its own KPI tile (was
        # only reachable via the list filter before). Status values
        # 'Walkout' and 'Dropout' both count as Dropout for the tile.
        # 2026-10-13 (user ask): Total + Active count against created_at
        # (when the leader was enrolled). Dropout counts against
        # walkout_date (when the leader dropped out) so the Dropout tile
        # + the AK list Status=Dropout + Duration filter report the
        # same number. Falls back to created_at::date when walkout_date
        # is NULL (defensive for historical rows).
        cur.execute(f"""
            SELECT COUNT(*) total,
                   COUNT(*) FILTER (WHERE l.status='Active') AS active
            FROM ak_leaders l {leaders_join}
            WHERE {where_l}
        """, params_l)
        r = cur.fetchone()
        total_kishoris   = r["total"]
        active_kishoris  = r["active"]

        # Dropout tile: separate query that uses walkout_date for
        # the duration filter. All other filters (state, district,
        # centre, batch) stay identical.
        _d_conds = ["l.deleted_at IS NULL",
                    "l.status IN ('Walkout','Dropout')"]
        _d_params = []
        _d_need_centre = False
        if state_code:    _d_conds.append("l.state_code = %s");  _d_params.append(state_code)
        if district_code:
            _d_need_centre = True
            _d_conds.append("c.district_code = %s"); _d_params.append(district_code)
        if centre_code:   _d_conds.append("l.centre_code = %s"); _d_params.append(centre_code)
        if batch_id:      _d_conds.append("l.batch_id = %s");    _d_params.append(int(batch_id))
        # 2026-10-13 v2: Dropout count ignores Duration (point-in-time
        # snapshot). Only geo + batch filters narrow the count.
        _d_where = " AND ".join(_d_conds)
        _d_join = " LEFT JOIN central_centres c ON l.centre_code = c.centre_code " if _d_need_centre else ""
        cur.execute(f"SELECT COUNT(*) AS c FROM ak_leaders l {_d_join} WHERE {_d_where}", _d_params)
        dropout_kishoris = cur.fetchone()["c"]

        # 3. Active Addas
        w, p = _geo_where("a")
        cur.execute(f"""
            SELECT COUNT(*) c FROM ak_addas a
            WHERE {w} AND a.status = 'Active'
        """, p)
        active_addas = cur.fetchone()["c"]

        # 4. Trainings conducted — 2026-10-03: duration filter uses
        # training_date (actual event date), not created_at.
        w, p = _geo_where("t", date_col="training_date")
        cur.execute(f"SELECT COUNT(*) c FROM ak_trainings t WHERE {w}", p)
        total_trainings = cur.fetchone()["c"]

        # 5. Assessments (no soft-delete column)
        conds = ["1=1"]; pa: list = []
        if state_code:  conds.append("state_code = %s");  pa.append(state_code)
        if district_code:
            conds.append("centre_code IN (SELECT centre_code FROM central_centres WHERE district_code = %s)")
            pa.append(district_code)
        if centre_code: conds.append("centre_code = %s"); pa.append(centre_code)
        # 2026-10-03: duration filter here too.
        if date_from:   conds.append("created_at >= %s");  pa.append(date_from)
        if date_to:     conds.append("created_at < (%s::date + INTERVAL '1 day')"); pa.append(date_to)
        cur.execute(f"SELECT COUNT(*) c FROM ak_assessments WHERE {' AND '.join(conds)}", pa)
        total_assessments = cur.fetchone()["c"]

        # 6. ALAP graduates (alaps + alumni headcount as the post-leader phase)
        # 2026-06-08: Apply geo + batch filters so DL/PI/SL see only
        # their own scope's ALAP count, not the all-India total.
        w_al, p_al = _geo_where("al", has_batch=True)
        cur.execute(f"SELECT COUNT(*) c FROM ak_alaps al WHERE {w_al}", p_al)
        alaps = cur.fetchone()["c"]

        # Bonus headline counts surfaced in sub-sections
        # 2026-06-08: same — geo-scope ak_alumni so the headline matches
        # the user's role-floored scope. ak_alumni has no batch_id.
        w_au, p_au = _geo_where("au")
        cur.execute(f"SELECT COUNT(*) c FROM ak_alumni au WHERE {w_au}", p_au)
        alumni = cur.fetchone()["c"]

        # Sangini Community Outreach: Chaupals & Home Visits
        s_conds = ["deleted_at IS NULL"]
        s_params = []
        if batch_id:
            cur.execute("SELECT name FROM ak_batches WHERE id = %s", (batch_id,))
            b_row = cur.fetchone()
            if b_row and b_row["name"]:
                s_conds.append("batch ILIKE %s")
                s_params.append(f"%{b_row['name'].strip()}%")
        if date_from:
            s_conds.append("month >= %s::date")
            s_params.append(date_from)
        if date_to:
            s_conds.append("month <= (%s::date + INTERVAL '1 month')")
            s_params.append(date_to)

        s_where = " AND ".join(s_conds)
        cur.execute(f"""
            SELECT 
                COALESCE(SUM(choupals), 0)::int AS chaupals_count,
                COALESCE(SUM(choupal_participants), 0)::int AS chaupal_participants,
                COALESCE(SUM(choupal_male), 0)::int AS chaupal_male,
                COALESCE(SUM(choupal_female), 0)::int AS chaupal_female,
                COALESCE(SUM(home_visits), 0)::int AS home_visits_count,
                COALESCE(SUM(home_visit_participants), 0)::int AS home_visit_participants,
                COALESCE(SUM(home_visit_male), 0)::int AS home_visit_male,
                COALESCE(SUM(home_visit_female), 0)::int AS home_visit_female
            FROM sangini_entries
            WHERE {s_where}
        """, s_params)
        sangini_stats = cur.fetchone() or {}

    return {
        "total_kishoris":          total_kishoris,
        "active_kishoris":         active_kishoris,
        "dropout_kishoris":        dropout_kishoris,
        "active_addas":            active_addas,
        "total_trainings":         total_trainings,
        "total_assessments":       total_assessments,
        "total_alaps":             alaps,
        "total_alumni":            alumni,
        "chaupal_count":           sangini_stats.get("chaupals_count", 0),
        "chaupal_participants":    sangini_stats.get("chaupal_participants", 0),
        "chaupal_male":            sangini_stats.get("chaupal_male", 0),
        "chaupal_female":          sangini_stats.get("chaupal_female", 0),
        "home_visit_count":        sangini_stats.get("home_visits_count", 0),
        "home_visit_participants": sangini_stats.get("home_visit_participants", 0),
        "home_visit_male":         sangini_stats.get("home_visit_male", 0),
        "home_visit_female":       sangini_stats.get("home_visit_female", 0),
    }


@router.get("/charts")
def charts(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    # 2026-06-01: Year filter for the Education chart. Applied only to
    # education_distribution (the other series stay unfiltered by year
    # so the dashboard's overall picture doesn't shift when the user
    # focuses one chart).
    education_year: Optional[int] = None,
):
    """Chart-ready data series for every panel on the AK dashboard."""
    scoped = enforce_role_scope(
        request,
        state_code=state_code,
        district_code=district_code,
        centre_code=centre_code,
    )
    state_code    = scoped.get('state_code')
    district_code = scoped.get('district_code')
    centre_code   = scoped.get('centre_code')
    where_l, params_l, join_centres = _leader_filters(state_code, district_code, centre_code, batch_id, date_from, date_to, "l")
    leaders_join = " LEFT JOIN central_centres c ON l.centre_code = c.centre_code " if join_centres else ""

    # 2026-06-08: Same simple geo helper as in /stats so secondary
    # tables (alaps, alumni, assessments, alap_trainings) are also
    # role-scoped. Without this DL/PI see all-India counts for ALAP
    # / Alumni / Assessment cards even when their state+centre is
    # pinned, which is what motivated this fix.
    def _geo_where(alias, has_batch=False, no_soft_delete=False, date_col='created_at'):
        conds = ["1=1"] if no_soft_delete else [f"{alias}.deleted_at IS NULL"]
        params: list = []
        if state_code:  conds.append(f"{alias}.state_code = %s");  params.append(state_code)
        if district_code:
            conds.append(f"{alias}.centre_code IN (SELECT centre_code FROM central_centres WHERE district_code = %s)")
            params.append(district_code)
        if centre_code: conds.append(f"{alias}.centre_code = %s"); params.append(centre_code)
        if has_batch and batch_id:
            conds.append(f"{alias}.batch_id = %s"); params.append(int(batch_id))
        # 2026-10-03: honour the dashboard duration filter. date_col
        # defaults to created_at; training queries override to
        # training_date so the picker narrows by the actual event date.
        if date_from: conds.append(f"{alias}.{date_col} >= %s"); params.append(date_from)
        if date_to:   conds.append(f"{alias}.{date_col} < (%s::date + INTERVAL '1 day')"); params.append(date_to)
        return " AND ".join(conds), params

    out: dict = {}
    with get_cursor() as cur:
        # 2026-10-04: Kishoris by state + batch (stacked bar).
        # Tamil Nadu (S33) excluded until the programme starts there.
        cur.execute(f"""
            SELECT COALESCE(s.state_name, l.state_code, 'Unknown') AS state_name,
                   COALESCE(b.name, 'Unassigned')                   AS batch_name,
                   COUNT(*)                                         AS count
            FROM ak_leaders l
            LEFT JOIN central_states s ON l.state_code = s.state_code
            LEFT JOIN ak_batches b     ON b.id = l.batch_id
            {leaders_join}
            WHERE {where_l} AND COALESCE(l.state_code, '') <> 'S33'
            GROUP BY s.state_name, l.state_code, b.name
            ORDER BY count DESC
        """, params_l)
        out["kishoris_by_state"] = [dict(r) for r in cur.fetchall()]
        # Backfill: when no state filter is active, every active state from
        # central_states should appear on the chart — even states that have zero
        # leaders yet (e.g. West Bengal pre-onboarding). Without this the
        # donut hides states that have no data.
        if not state_code:
            cur.execute(
                "SELECT state_name FROM central_states "
                "WHERE deleted_at IS NULL AND state_code <> 'S33' "
                "ORDER BY state_name"
            )
            present = {r['state_name'] for r in out["kishoris_by_state"] if r.get('state_name')}
            for r in cur.fetchall():
                if r['state_name'] not in present:
                    out["kishoris_by_state"].append({'state_name': r['state_name'], 'batch_name': 'Unassigned', 'count': 0})

        # Status split (Active / Walkout)
        cur.execute(f"""
            SELECT l.status, COUNT(*) c
            FROM ak_leaders l {leaders_join}
            WHERE {where_l}
            GROUP BY l.status
        """, params_l)
        out["status_split"] = cur.fetchall()

        # Education distribution — 2026-06-01: optional year filter.
        # Year resolved from year_of_joining first, falling back to
        # EXTRACT(YEAR FROM created_at) so legacy rows without the
        # explicit column still cluster into the right cohort.
        where_edu = where_l
        params_edu = list(params_l)
        if education_year:
            where_edu = where_edu + " AND COALESCE(l.year_of_joining, EXTRACT(YEAR FROM l.created_at)::int) = %s"
            params_edu.append(int(education_year))
        cur.execute(f"""
            SELECT COALESCE(l.current_education, '—') AS education, COUNT(*) c
            FROM ak_leaders l {leaders_join}
            WHERE {where_edu}
            GROUP BY l.current_education
            ORDER BY c DESC
        """, params_edu)
        out["education_distribution"] = cur.fetchall()

        # Available years for the Education chart's year selector. Sorted
        # newest-first so the dropdown opens with the most recent cohort
        # at the top.
        cur.execute(f"""
            SELECT DISTINCT COALESCE(l.year_of_joining, EXTRACT(YEAR FROM l.created_at)::int) AS y
            FROM ak_leaders l {leaders_join}
            WHERE {where_l}
              AND COALESCE(l.year_of_joining, EXTRACT(YEAR FROM l.created_at)::int) IS NOT NULL
            ORDER BY y DESC
        """, params_l)
        out["education_years"] = [int(r["y"]) for r in cur.fetchall() if r.get("y") is not None]

        # ────────────────────────────────────────────────────────────
        # 2026-11-17: State-wise & Centre-wise Education Charts (Alumni & AK Leaders)
        # ────────────────────────────────────────────────────────────
        # 1. Alumni Education (State-wise & Centre-wise)
        w_au_edu, p_au_edu = _geo_where("a")
        cur.execute(f"""
            WITH alumni_raw AS (
                SELECT COALESCE(s.state_name, a.state_code, 'Unknown') AS state_name,
                       COALESCE(NULLIF(TRIM(COALESCE(lt.educational_status, a.educational_status)), ''), 'Not Specified') AS raw_edu
                FROM ak_alumni a
                LEFT JOIN central_states s ON a.state_code = s.state_code
                LEFT JOIN LATERAL (
                    SELECT educational_status FROM ak_alumni_tracking
                    WHERE alumni_id = a.id AND educational_status IS NOT NULL AND TRIM(educational_status) <> ''
                    ORDER BY created_at DESC LIMIT 1
                ) lt ON true
                WHERE {w_au_edu}
            ),
            normalized AS (
                SELECT state_name,
                       CASE
                           WHEN raw_edu ILIKE '%%post%%grad%%' OR raw_edu ILIKE '%%ma%%' THEN 'Post Graduation'
                           WHEN raw_edu ILIKE '%%b.ed%%' OR raw_edu ILIKE '%%bed%%' THEN 'B.Ed'
                           WHEN raw_edu ILIKE '%%grad%%' OR raw_edu ILIKE '%%b.a%%' OR raw_edu ILIKE '%%ba%%' OR raw_edu ILIKE '%%bsc%%' OR raw_edu ILIKE '%%b.tech%%' OR raw_edu ILIKE '%%ug%%' THEN 'Graduation'
                           WHEN raw_edu ILIKE '%%12%%' THEN '12th'
                           WHEN raw_edu ILIKE '%%11%%' THEN '11th'
                           WHEN raw_edu ILIKE '%%10%%' THEN '10th'
                           WHEN raw_edu ILIKE '%%9%%' THEN '9th'
                           WHEN raw_edu ILIKE '%%8%%' THEN '8th'
                           WHEN raw_edu ILIKE '%%studying%%' AND raw_edu ILIKE '%%working%%' THEN 'Studying & Working'
                           WHEN raw_edu ILIKE '%%studying%%' THEN 'Studying'
                           WHEN raw_edu ILIKE '%%working%%' THEN 'Working'
                           WHEN raw_edu ILIKE '%%gnm%%' OR raw_edu ILIKE '%%journalis%%' THEN 'Diploma / Vocational'
                           WHEN raw_edu IS NULL OR TRIM(raw_edu) = '' OR raw_edu ILIKE '%%not specified%%' OR raw_edu = '—' THEN 'Not Specified'
                           ELSE 'Other'
                       END AS education
                FROM alumni_raw
            )
            SELECT state_name, education, COUNT(*) as count
            FROM normalized
            GROUP BY state_name, education
            ORDER BY state_name, count DESC
        """, p_au_edu)
        out["alumni_education_by_state"] = [dict(r) for r in cur.fetchall()]

        cur.execute(f"""
            WITH alumni_raw AS (
                SELECT COALESCE(c.centre_name, a.centre_code, 'Unknown') AS centre_name,
                       COALESCE(NULLIF(TRIM(COALESCE(lt.educational_status, a.educational_status)), ''), 'Not Specified') AS raw_edu
                FROM ak_alumni a
                LEFT JOIN central_centres c ON a.centre_code = c.centre_code
                LEFT JOIN LATERAL (
                    SELECT educational_status FROM ak_alumni_tracking
                    WHERE alumni_id = a.id AND educational_status IS NOT NULL AND TRIM(educational_status) <> ''
                    ORDER BY created_at DESC LIMIT 1
                ) lt ON true
                WHERE {w_au_edu}
            ),
            normalized AS (
                SELECT centre_name,
                       CASE
                           WHEN raw_edu ILIKE '%%post%%grad%%' OR raw_edu ILIKE '%%ma%%' THEN 'Post Graduation'
                           WHEN raw_edu ILIKE '%%b.ed%%' OR raw_edu ILIKE '%%bed%%' THEN 'B.Ed'
                           WHEN raw_edu ILIKE '%%grad%%' OR raw_edu ILIKE '%%b.a%%' OR raw_edu ILIKE '%%ba%%' OR raw_edu ILIKE '%%bsc%%' OR raw_edu ILIKE '%%b.tech%%' OR raw_edu ILIKE '%%ug%%' THEN 'Graduation'
                           WHEN raw_edu ILIKE '%%12%%' THEN '12th'
                           WHEN raw_edu ILIKE '%%11%%' THEN '11th'
                           WHEN raw_edu ILIKE '%%10%%' THEN '10th'
                           WHEN raw_edu ILIKE '%%9%%' THEN '9th'
                           WHEN raw_edu ILIKE '%%8%%' THEN '8th'
                           WHEN raw_edu ILIKE '%%studying%%' AND raw_edu ILIKE '%%working%%' THEN 'Studying & Working'
                           WHEN raw_edu ILIKE '%%studying%%' THEN 'Studying'
                           WHEN raw_edu ILIKE '%%working%%' THEN 'Working'
                           WHEN raw_edu ILIKE '%%gnm%%' OR raw_edu ILIKE '%%journalis%%' THEN 'Diploma / Vocational'
                           WHEN raw_edu IS NULL OR TRIM(raw_edu) = '' OR raw_edu ILIKE '%%not specified%%' OR raw_edu = '—' THEN 'Not Specified'
                           ELSE 'Other'
                       END AS education
                FROM alumni_raw
            )
            SELECT centre_name, education, COUNT(*) as count
            FROM normalized
            GROUP BY centre_name, education
            ORDER BY centre_name, count DESC
        """, p_au_edu)
        out["alumni_education_by_centre"] = [dict(r) for r in cur.fetchall()]

        # 2. AK Leaders Education (State-wise & Centre-wise) — sourced from ak_leaders
        cur.execute(f"""
            SELECT COALESCE(s.state_name, l.state_code, 'Unknown') AS state_name,
                   CASE
                       WHEN l.current_education ILIKE '%%post%%grad%%' OR l.current_education ILIKE '%%ma%%' THEN 'Post Graduation'
                       WHEN l.current_education ILIKE '%%b.ed%%' OR l.current_education ILIKE '%%bed%%' THEN 'B.Ed'
                       WHEN l.current_education ILIKE '%%grad%%' OR l.current_education ILIKE '%%b.a%%' OR l.current_education ILIKE '%%ba%%' OR l.current_education ILIKE '%%bsc%%' OR l.current_education ILIKE '%%b.tech%%' OR l.current_education ILIKE '%%ug%%' THEN 'Graduation'
                       WHEN l.current_education ILIKE '%%12%%' THEN '12th'
                       WHEN l.current_education ILIKE '%%11%%' THEN '11th'
                       WHEN l.current_education ILIKE '%%10%%' THEN '10th'
                       WHEN l.current_education ILIKE '%%9%%' THEN '9th'
                       WHEN l.current_education ILIKE '%%8%%' THEN '8th'
                       WHEN l.current_education ILIKE '%%diploma%%' OR l.current_education ILIKE '%%iti%%' THEN 'Diploma / Vocational'
                       WHEN l.current_education IS NULL OR TRIM(l.current_education) = '' OR l.current_education = '—' OR l.current_education ILIKE '%%not specified%%' THEN 'Not Specified'
                       ELSE 'Other'
                   END AS education,
                   COUNT(*) AS count
            FROM ak_leaders l
            LEFT JOIN central_states s ON l.state_code = s.state_code
            {leaders_join}
            WHERE {where_l}
            GROUP BY 1, 2
            ORDER BY 1, count DESC
        """, params_l)
        out["leader_education_by_state"] = [dict(r) for r in cur.fetchall()]

        cur.execute(f"""
            SELECT COALESCE(c.centre_name, l.centre_code, 'Unknown') AS centre_name,
                   CASE
                       WHEN l.current_education ILIKE '%%post%%grad%%' OR l.current_education ILIKE '%%ma%%' THEN 'Post Graduation'
                       WHEN l.current_education ILIKE '%%b.ed%%' OR l.current_education ILIKE '%%bed%%' THEN 'B.Ed'
                       WHEN l.current_education ILIKE '%%grad%%' OR l.current_education ILIKE '%%b.a%%' OR l.current_education ILIKE '%%ba%%' OR l.current_education ILIKE '%%bsc%%' OR l.current_education ILIKE '%%b.tech%%' OR l.current_education ILIKE '%%ug%%' THEN 'Graduation'
                       WHEN l.current_education ILIKE '%%12%%' THEN '12th'
                       WHEN l.current_education ILIKE '%%11%%' THEN '11th'
                       WHEN l.current_education ILIKE '%%10%%' THEN '10th'
                       WHEN l.current_education ILIKE '%%9%%' THEN '9th'
                       WHEN l.current_education ILIKE '%%8%%' THEN '8th'
                       WHEN l.current_education ILIKE '%%diploma%%' OR l.current_education ILIKE '%%iti%%' THEN 'Diploma / Vocational'
                       WHEN l.current_education IS NULL OR TRIM(l.current_education) = '' OR l.current_education = '—' OR l.current_education ILIKE '%%not specified%%' THEN 'Not Specified'
                       ELSE 'Other'
                   END AS education,
                   COUNT(*) AS count
            FROM ak_leaders l
            LEFT JOIN central_centres c ON l.centre_code = c.centre_code
            WHERE {where_l}
            GROUP BY 1, 2
            ORDER BY 1, count DESC
        """, params_l)
        out["leader_education_by_centre"] = [dict(r) for r in cur.fetchall()]

        # Age buckets (10-12, 13-15, 16-18, 19+)
        cur.execute(f"""
            SELECT COUNT(*) FILTER (WHERE l.age BETWEEN 10 AND 12) AS bucket_10_12,
                   COUNT(*) FILTER (WHERE l.age BETWEEN 13 AND 15) AS bucket_13_15,
                   COUNT(*) FILTER (WHERE l.age BETWEEN 16 AND 18) AS bucket_16_18,
                   COUNT(*) FILTER (WHERE l.age >= 19)             AS bucket_19_plus
            FROM ak_leaders l {leaders_join}
            WHERE {where_l}
        """, params_l)
        out["age_buckets"] = cur.fetchone() or {}

        # Programme journey funnel (counts at each stage)
        # 2026-06-08: All four legs of the funnel now respect the role-
        # floor scope. ak_alap_trainings has only state_code (no centre);
        # for a centre-scoped DL the centre filter still lands via the
        # ak_alaps→ak_alap_trainings JOIN below.
        cur.execute(f"SELECT COUNT(*) c FROM ak_leaders l {leaders_join} WHERE {where_l}", params_l)
        n_kishoris = cur.fetchone()["c"]
        w_al, p_al = _geo_where("al", has_batch=True)
        cur.execute(f"SELECT COUNT(*) c FROM ak_alaps al WHERE {w_al}", p_al)
        n_alaps = cur.fetchone()["c"]
        # ak_alap_trainings only carries state_code (no centre/district/batch).
        # Apply at least the state filter so a DL doesn't see other states'
        # ALAP-training rows; tighter scoping would need a schema change.
        w_at_conds = ["t.deleted_at IS NULL"]
        p_at: list = []
        if state_code: w_at_conds.append("t.state_code = %s"); p_at.append(state_code)
        cur.execute(f"SELECT COUNT(*) c FROM ak_alap_trainings t WHERE {' AND '.join(w_at_conds)}", p_at)
        n_alap_trainings = cur.fetchone()["c"]
        w_au, p_au = _geo_where("au")
        cur.execute(f"SELECT COUNT(*) c FROM ak_alumni au WHERE {w_au}", p_au)
        n_alumni = cur.fetchone()["c"]
        out["journey_funnel"] = [
            {"stage": "Kishori Enrolled",   "count": n_kishoris},
            {"stage": "ALAP Stage",         "count": n_alaps},
            {"stage": "ALAP Training",      "count": n_alap_trainings},
            {"stage": "Alumni",             "count": n_alumni},
        ]

        # Monthly enrolment trend (last 6 months covering filtered window)
        cur.execute(f"""
            SELECT TO_CHAR(DATE_TRUNC('month', l.created_at), 'Mon YYYY') AS label,
                   DATE_TRUNC('month', l.created_at) AS month_ts,
                   COUNT(*) AS count
            FROM ak_leaders l {leaders_join}
            WHERE {where_l}
            GROUP BY month_ts
            ORDER BY month_ts
        """, params_l)
        out["monthly_enrolment"] = cur.fetchall()

        # Training coverage by category
        w_t = ["t.deleted_at IS NULL"]; p_t: list = []
        if state_code:  w_t.append("t.state_code = %s");  p_t.append(state_code)
        if district_code:
            w_t.append("t.centre_code IN (SELECT centre_code FROM central_centres WHERE district_code = %s)")
            p_t.append(district_code)
        if centre_code: w_t.append("t.centre_code = %s"); p_t.append(centre_code)
        # 2026-10-07 (user ask): honour the dashboard's Batch filter so
        # every training-based panel scopes to batch_id when set.
        if batch_id:    w_t.append("t.batch_id = %s");    p_t.append(int(batch_id))
        # 2026-10-03: duration filter uses training_date.
        if date_from:   w_t.append("t.training_date >= %s"); p_t.append(date_from)
        if date_to:     w_t.append("t.training_date < (%s::date + INTERVAL '1 day')"); p_t.append(date_to)
        cur.execute(f"""
            SELECT COALESCE(t.category, '—') AS category, COUNT(*) c
            FROM ak_trainings t
            WHERE {' AND '.join(w_t)}
            GROUP BY t.category
            ORDER BY c DESC
        """, p_t)
        out["trainings_by_category"] = cur.fetchall()

        # Addas — members reached, by state
        w_a = ["a.deleted_at IS NULL"]; p_a: list = []
        if state_code:  w_a.append("a.state_code = %s");  p_a.append(state_code)
        if district_code:
            w_a.append("a.centre_code IN (SELECT centre_code FROM central_centres WHERE district_code = %s)")
            p_a.append(district_code)
        if centre_code: w_a.append("a.centre_code = %s"); p_a.append(centre_code)
        if batch_id:    w_a.append("a.batch_id = %s");     p_a.append(int(batch_id))
        # 2026-10-04: exclude Tamil Nadu (S33) until the programme starts there.

        # Subquery for adda meeting attendance and sessions (respects date filter when provided)
        d_conds = []
        d_params = []
        if date_from:
            d_conds.append("detail_date >= %s")
            d_params.append(date_from)
        if date_to:
            d_conds.append("detail_date < (%s::date + INTERVAL '1 day')")
            d_params.append(date_to)
        d_where = f"WHERE {' AND '.join(d_conds)}" if d_conds else ""
        d_sub = f"""
            LEFT JOIN (
                SELECT adda_id,
                       COUNT(*) AS session_count,
                       SUM(attendance) AS total_attendance
                FROM ak_adda_details
                {d_where}
                GROUP BY adda_id
            ) d ON d.adda_id = a.id
        """

        # 1. State-wise Adda Details
        cur.execute(f"""
            SELECT COALESCE(s.state_name, a.state_code, 'Unknown') AS state_name,
                   COUNT(a.id) AS adda_count,
                   COALESCE(SUM(d.session_count), 0)::int AS sessions,
                   COALESCE(SUM(
                       CASE 
                           WHEN COALESCE(d.session_count, 0) > 0 
                           THEN LEAST(a.adda_members, ROUND(d.total_attendance::numeric / d.session_count)::int)
                           ELSE 0 
                       END
                   ), 0)::int AS present_trainees,
                   COALESCE(SUM(a.adda_members), 0) AS members_reached,
                   COALESCE(SUM(d.total_attendance), 0)::int AS total_attendance,
                   COALESCE(SUM(d.total_attendance), 0)::int AS total_present,
                   CASE WHEN COALESCE(SUM(d.session_count), 0) > 0
                        THEN ROUND(COALESCE(SUM(d.total_attendance), 0)::numeric / SUM(d.session_count), 1)
                        ELSE 0 END AS avg_present
            FROM ak_addas a
            LEFT JOIN central_states s ON a.state_code = s.state_code
            {d_sub}
            WHERE {' AND '.join(w_a)} AND COALESCE(a.state_code, '') <> 'S33'
            GROUP BY s.state_name, a.state_code
            ORDER BY members_reached DESC
        """, d_params + p_a)
        out["addas_by_state"] = [dict(r) for r in cur.fetchall()]

        # 2. Batch-wise Adda Details
        cur.execute(f"""
            SELECT COALESCE(NULLIF(b.name, ''), 'Unassigned') AS batch_name,
                   a.batch_id,
                   COALESCE(s.state_name, a.state_code, '') AS state_name,
                   COUNT(a.id) AS adda_count,
                   COALESCE(SUM(d.session_count), 0)::int AS sessions,
                   COALESCE(SUM(
                       CASE 
                           WHEN COALESCE(d.session_count, 0) > 0 
                           THEN LEAST(a.adda_members, ROUND(d.total_attendance::numeric / d.session_count)::int)
                           ELSE 0 
                       END
                   ), 0)::int AS present_trainees,
                   COALESCE(SUM(a.adda_members), 0) AS members_reached,
                   COALESCE(SUM(d.total_attendance), 0)::int AS total_attendance,
                   COALESCE(SUM(d.total_attendance), 0)::int AS total_present,
                   CASE WHEN COALESCE(SUM(d.session_count), 0) > 0
                        THEN ROUND(COALESCE(SUM(d.total_attendance), 0)::numeric / SUM(d.session_count), 1)
                        ELSE 0 END AS avg_present
            FROM ak_addas a
            LEFT JOIN ak_batches b ON a.batch_id = b.id
            LEFT JOIN central_states s ON a.state_code = s.state_code
            {d_sub}
            WHERE {' AND '.join(w_a)} AND COALESCE(a.state_code, '') <> 'S33'
            GROUP BY b.name, a.batch_id, s.state_name, a.state_code
            ORDER BY b.name NULLS LAST, s.state_name
        """, d_params + p_a)
        out["addas_by_batch"] = [dict(r) for r in cur.fetchall()]

        # 3. Combined batch & state breakdown
        cur.execute(f"""
            SELECT COALESCE(NULLIF(b.name, ''), 'Unassigned') AS batch_name,
                   a.batch_id,
                   COALESCE(s.state_name, a.state_code, 'Unknown') AS state_name,
                   COUNT(a.id) AS adda_count,
                   COALESCE(SUM(d.session_count), 0)::int AS sessions,
                   COALESCE(SUM(
                       CASE 
                           WHEN COALESCE(d.session_count, 0) > 0 
                           THEN LEAST(a.adda_members, ROUND(d.total_attendance::numeric / d.session_count)::int)
                           ELSE 0 
                       END
                   ), 0)::int AS present_trainees,
                   COALESCE(SUM(a.adda_members), 0) AS members_reached,
                   COALESCE(SUM(d.total_attendance), 0)::int AS total_attendance,
                   COALESCE(SUM(d.total_attendance), 0)::int AS total_present,
                   CASE WHEN COALESCE(SUM(d.session_count), 0) > 0
                        THEN ROUND(COALESCE(SUM(d.total_attendance), 0)::numeric / SUM(d.session_count), 1)
                        ELSE 0 END AS avg_present
            FROM ak_addas a
            LEFT JOIN ak_batches b ON a.batch_id = b.id
            LEFT JOIN central_states s ON a.state_code = s.state_code
            {d_sub}
            WHERE {' AND '.join(w_a)} AND COALESCE(a.state_code, '') <> 'S33'
            GROUP BY b.name, a.batch_id, s.state_name, a.state_code
            ORDER BY b.name NULLS LAST, s.state_name
        """, d_params + p_a)
        out["addas_by_batch_state"] = [dict(r) for r in cur.fetchall()]
        # Backfill: same logic as kishoris_by_state — when there's no state
        # filter, surface every active state from central_states even if no Adda
        # data exists yet, so the Outreach table is comprehensive.
        if not state_code:
            cur.execute(
                "SELECT state_name FROM central_states "
                "WHERE deleted_at IS NULL AND state_code <> 'S33' "
                "ORDER BY state_name"
            )
            present = {r['state_name'] for r in out["addas_by_state"] if r.get('state_name')}
            for r in cur.fetchall():
                if r['state_name'] not in present:
                    out["addas_by_state"].append({
                        'state_name': r['state_name'],
                        'adda_count': 0,
                        'sessions': 0,
                        'present_trainees': 0,
                        'members_reached': 0,
                        'total_attendance': 0,
                        'total_present': 0,
                        'avg_present': 0,
                    })

        # Assessments — pre/post split (assessment_type column)
        # 2026-06-08: Scope by user's geo so DL/PI/SL see only their
        # centre/district/state's assessments. ak_assessments has no
        # soft-delete column → no_soft_delete=True.
        w_as, p_as = _geo_where("ass", no_soft_delete=True)
        cur.execute(f"""
            SELECT COALESCE(ass.assessment_type, '—') AS type, COUNT(*) c
            FROM ak_assessments ass
            WHERE {w_as}
            GROUP BY ass.assessment_type
        """, p_as)
        out["assessments_split"] = cur.fetchall()

        # Alumni post-programme engagement — Working, Studying, or both
        # 2026-10-07 (user ask): are_you_working / are_you_studying
        # moved from ak_alumni to ak_alumni_tracking (Transformation
        # Tracking view). Pull them from each alumnus' LATEST tracking
        # row via LEFT JOIN LATERAL, honouring the dashboard's
        # date_from/date_to filter on tracking.created_at. Falls back
        # to the ak_alumni column for legacy alumni with no tracking
        # entry. Geo / batch filters flow through _geo_where('au').
        w_au2, p_au2 = _geo_where("au")
        _lt_conds = []
        _lt_params = []
        if date_from:
            _lt_conds.append("created_at >= %s"); _lt_params.append(date_from)
        if date_to:
            _lt_conds.append("created_at < (%s::date + interval '1 day')")
            _lt_params.append(date_to)
        _lt_where = "WHERE alumni_id = au.id" + (
            " AND " + " AND ".join(_lt_conds) if _lt_conds else ""
        )
        cur.execute(f"""
            SELECT
              COUNT(*) AS total,
              COUNT(*) FILTER (WHERE LOWER(COALESCE(lt.are_you_working, au.are_you_working, 'No'))
                              IN ('yes','y','true'))   AS working,
              COUNT(*) FILTER (WHERE LOWER(COALESCE(lt.are_you_studying, au.are_you_studying, 'No'))
                              IN ('yes','y','true')) AS studying,
              COUNT(*) FILTER (WHERE LOWER(COALESCE(lt.are_you_working, au.are_you_working, 'No'))
                                  IN ('yes','y','true')
                              AND LOWER(COALESCE(lt.are_you_studying, au.are_you_studying, 'No'))
                                  IN ('yes','y','true')) AS both
            FROM ak_alumni au
            LEFT JOIN LATERAL (
                SELECT are_you_working, are_you_studying
                  FROM ak_alumni_tracking
                  {_lt_where}
                  ORDER BY created_at DESC
                  LIMIT 1
            ) lt ON true
            WHERE {w_au2}
        """, _lt_params + p_au2)
        r = cur.fetchone() or {}
        out["alumni_engagement"] = {
            "working":          r.get("working", 0),
            "studying":         r.get("studying", 0),
            "both":             r.get("both", 0),
            "neither":          (r.get("total", 0) or 0) - max(r.get("working", 0) or 0, r.get("studying", 0) or 0),
            "total":            r.get("total", 0),
        }

        # ────────────────────────────────────────────────────────────
        # 2026-06-01 NEW SECTIONS — Socio-economic Profile, Trainings,
        # Adda Activities. All three reuse the same leader scope filter
        # so the dashboard sections stay consistent under one set of
        # top-level filters.
        # ────────────────────────────────────────────────────────────

        # Socio: Family Monthly Income bands (₹). Buckets chosen to
        # spread the typical AK cohort spectrum sensibly: below 5k,
        # 5k-10k, 10k-20k, 20k-50k, 50k+, plus an "Unknown" bucket
        # for rows that haven't captured income yet.
        cur.execute(f"""
            SELECT band, COUNT(*) AS c FROM (
              SELECT CASE
                WHEN l.family_monthly_income IS NULL OR l.family_monthly_income = 0 THEN 'Unknown'
                WHEN l.family_monthly_income < 5000  THEN '< 5k'
                WHEN l.family_monthly_income < 10000 THEN '5k - 10k'
                WHEN l.family_monthly_income < 20000 THEN '10k - 20k'
                WHEN l.family_monthly_income < 50000 THEN '20k - 50k'
                ELSE '50k+'
              END AS band,
              CASE
                WHEN l.family_monthly_income IS NULL OR l.family_monthly_income = 0 THEN 99
                WHEN l.family_monthly_income < 5000  THEN 1
                WHEN l.family_monthly_income < 10000 THEN 2
                WHEN l.family_monthly_income < 20000 THEN 3
                WHEN l.family_monthly_income < 50000 THEN 4
                ELSE 5
              END AS ord
              FROM ak_leaders l {leaders_join}
              WHERE {where_l}
            ) x
            GROUP BY band, ord
            ORDER BY ord
        """, params_l)
        out["socio_income_bands"] = [dict(r) for r in cur.fetchall()]

        # Socio: Category breakdown. NULL/empty category rolled into
        # 'Unknown' so the chart doesn't end up with a no-label slice.
        cur.execute(f"""
            SELECT COALESCE(NULLIF(l.category, ''), 'Unknown') AS category, COUNT(*) c
            FROM ak_leaders l {leaders_join}
            WHERE {where_l}
            GROUP BY category
            ORDER BY c DESC
        """, params_l)
        out["socio_category"] = cur.fetchall()

        # Socio: Religion breakdown.
        cur.execute(f"""
            SELECT COALESCE(NULLIF(l.religion, ''), 'Unknown') AS religion, COUNT(*) c
            FROM ak_leaders l {leaders_join}
            WHERE {where_l}
            GROUP BY religion
            ORDER BY c DESC
        """, params_l)
        out["socio_religion"] = cur.fetchall()

        # Trainings — 2026-06-01 v3: replaced the stat-strip + topics
        # table with a single category-level series that fuses session
        # count and attendance count, drawn as a grouped bar chart by
        # the frontend. training_summary + top_training_topics stay in
        # the payload for back-compat with any other reader.
        w_t = ["t.deleted_at IS NULL"]; p_t: list = []
        if state_code:  w_t.append("t.state_code = %s");  p_t.append(state_code)
        if district_code:
            w_t.append("t.centre_code IN (SELECT centre_code FROM central_centres WHERE district_code = %s)")
            p_t.append(district_code)
        if centre_code: w_t.append("t.centre_code = %s"); p_t.append(centre_code)
        # 2026-10-07 (user ask): honour the dashboard's Batch filter so
        # every training-based panel scopes to batch_id when set.
        if batch_id:    w_t.append("t.batch_id = %s");    p_t.append(int(batch_id))
        # 2026-10-03: duration filter uses training_date; shared across
        # training_summary / top_training_topics / training_by_category_with_attendance.
        if date_from:   w_t.append("t.training_date >= %s"); p_t.append(date_from)
        if date_to:     w_t.append("t.training_date < (%s::date + INTERVAL '1 day')"); p_t.append(date_to)
        cur.execute(f"""
            SELECT
              COUNT(DISTINCT t.id) AS sessions,
              COUNT(tp.id) AS participants,
              COUNT(*) FILTER (WHERE LOWER(COALESCE(tp.attendance,'')) = 'present') AS present
            FROM ak_trainings t
            LEFT JOIN ak_training_participants tp ON tp.training_id = t.id
            WHERE {' AND '.join(w_t)}
        """, p_t)
        ts = cur.fetchone() or {}
        sessions     = ts.get("sessions", 0)     or 0
        participants = ts.get("participants", 0) or 0
        present      = ts.get("present", 0)      or 0
        attendance_pct = int(round(100 * present / participants)) if participants else 0
        out["training_summary"] = {
            "sessions":       sessions,
            "participants":   participants,
            "present":        present,
            "attendance_pct": attendance_pct,
        }

        # Top 5 training topics by session count (kept for back-compat).
        cur.execute(f"""
            SELECT COALESCE(NULLIF(t.topic_name, ''), 'Untitled') AS topic_name, COUNT(*) c
            FROM ak_trainings t
            WHERE {' AND '.join(w_t)}
            GROUP BY topic_name
            ORDER BY c DESC, topic_name
            LIMIT 5
        """, p_t)
        out["top_training_topics"] = cur.fetchall()

        # NEW: trainings by category WITH attendance count alongside.
        # Drives the v3 grouped-bar chart on the Trainings card.
        cur.execute(f"""
            SELECT COALESCE(t.category, '—') AS category,
                   COUNT(DISTINCT t.id) AS sessions,
                   COUNT(*) FILTER (WHERE LOWER(COALESCE(tp.attendance,'')) = 'present') AS present
            FROM ak_trainings t
            LEFT JOIN ak_training_participants tp ON tp.training_id = t.id
            WHERE {' AND '.join(w_t)}
            GROUP BY t.category
            ORDER BY sessions DESC, t.category
        """, p_t)
        out["training_by_category_with_attendance"] = cur.fetchall()

        # 2026-10-04: per-training-topic Expected vs Attended for the
        # redesigned Trainings vs Attendance chart. Each row = one topic
        # (session series) with the total participants recorded + the
        # number marked Present. Expected uses total participant rows so
        # the comparison is apples-to-apples at the topic level.
        cur.execute(f"""
            SELECT COALESCE(NULLIF(t.topic_name, ''), '—') AS topic_name,
                   COUNT(DISTINCT t.id)                        AS sessions,
                   COUNT(*)                                    AS expected,
                   COUNT(*) FILTER (WHERE LOWER(COALESCE(tp.attendance,'')) = 'present') AS present
            FROM ak_trainings t
            LEFT JOIN ak_training_participants tp ON tp.training_id = t.id
            WHERE {' AND '.join(w_t)}
            GROUP BY t.topic_name
            ORDER BY expected DESC, topic_name
        """, p_t)
        out["training_by_topic_with_attendance"] = cur.fetchall()

        # 2026-10-05 (user ask): per-STATE × per-TOPIC Expected vs
        # Attended. The dashboard's Training chart now groups by state;
        # the FE picks a topic from a dropdown (default = All Topics,
        # which sums across topics within each state). Honours the same
        # w_t filter chain so state/district/centre/batch/date-range
        # work exactly as they do for the other training panels.
        # 2026-10-07 (user ask): add month dimension so the FE can
        # filter by month in-chart. month_sort is used for sorting;
        # month_label (e.g. 'Oct 2026') is the user-visible value.
        # 2026-10-07 / 2026-11-17: State, Centre/Location, Batch, Month hierarchy
        # for Training Expected vs Attended comparison.
        cur.execute(f"""
            SELECT COALESCE(TO_CHAR(DATE_TRUNC('month', t.training_date), 'Mon YYYY'),
                            'No Date')                             AS month_label,
                   DATE_TRUNC('month', t.training_date)             AS month_sort,
                   COALESCE(NULLIF(ns.state_name, ''),
                            NULLIF(t.state_code, ''),
                            'Unknown')                              AS state_name,
                   t.state_code                                     AS state_code,
                   COALESCE(NULLIF(c.centre_name, ''),
                            NULLIF(t.centre_code, ''),
                            'Unknown')                              AS centre_name,
                   t.centre_code                                     AS centre_code,
                   COALESCE(NULLIF(t.topic_name, ''), '—')          AS topic_name,
                   COALESCE(NULLIF(b.name, ''), 'Unassigned')       AS batch_name,
                   t.batch_id                                       AS batch_id,
                   COALESCE(NULLIF(b.year, ''), '')                 AS batch_year,
                   COUNT(DISTINCT t.id)                              AS sessions,
                   COUNT(*)                                          AS expected,
                   COUNT(*) FILTER (WHERE LOWER(COALESCE(tp.attendance,'')) = 'present') AS present
            FROM ak_trainings t
            LEFT JOIN ak_training_participants tp ON tp.training_id = t.id
            LEFT JOIN central_states ns ON ns.state_code = t.state_code
            LEFT JOIN central_centres c ON c.centre_code = t.centre_code
            LEFT JOIN ak_batches b ON b.id = t.batch_id
            WHERE {' AND '.join(w_t)}
            GROUP BY month_sort, state_name, t.state_code, c.centre_name, t.centre_code, t.topic_name, b.name, t.batch_id, b.year
            ORDER BY month_sort NULLS LAST, state_name, centre_name, batch_name, topic_name
        """, p_t)
        out["training_by_state_topic"] = cur.fetchall()

        # 2026-06-01 (v7): Education Progression — REWORKED to be
        # batch-wise per user spec. For each batch, we measure the
        # cohort funnel as a descending staircase:
        #
        #   Enrolled         → all leaders in the batch
        #   Passed Class 8   → those currently at Class 9 or above
        #   Passed Class 10  → those currently at Class 11 or above
        #   Passed Class 12  → those currently at Graduation
        #
        # Because each later gate is a subset of the previous one, the
        # series is monotonically non-increasing — it can only stay
        # flat (everybody continued) or trend downward (some dropped
        # out). It can never trend upward, which matches the cohort
        # retention semantics the user asked for.
        #
        # Frontend can request a single batch via ?batch_id=… ; with
        # no batch filter we return every batch's row so the dropdown
        # can populate itself in one round-trip.
        #
        # %% escapes inside ILIKE so psycopg2's printf-style binding
        # doesn't mistake them for parameter placeholders.
        ep_where = where_l
        ep_params = list(params_l)
        # We always want a batch grouping for this chart so leaders
        # without a batch_id are dropped from the funnel (their
        # progression is meaningless without a baseline cohort).
        ep_where = ep_where + " AND l.batch_id IS NOT NULL"
        cur.execute(f"""
            WITH ranked AS (
              SELECT l.batch_id,
                     COALESCE(l.status, 'Active') AS status,
                     CASE
                       WHEN l.current_education ILIKE '%%graduate%%'         THEN 14
                       WHEN l.current_education ILIKE '%%post%%graduate%%'   THEN 14
                       WHEN l.current_education ILIKE '%%higher secondary%%' THEN 12
                       WHEN l.current_education ILIKE '%%12%%'               THEN 12
                       WHEN l.current_education ILIKE '%%11%%'               THEN 11
                       WHEN l.current_education ILIKE '%%secondary%%'        THEN 10
                       WHEN l.current_education ILIKE '%%10%%'               THEN 10
                       WHEN l.current_education ILIKE '%%9%%'                THEN 9
                       WHEN l.current_education ILIKE '%%middle%%'           THEN 8
                       WHEN l.current_education ILIKE '%%8%%'                THEN 8
                       ELSE 0
                     END AS edu_rank
              FROM ak_leaders l {leaders_join}
              WHERE {ep_where}
            )
            SELECT r.batch_id,
                   COALESCE(b.name, 'Batch ' || r.batch_id::text) AS batch_name,
                   -- 2026-06-01 (v9): expose the raw year field so the
                   -- frontend can derive X-axis labels (e.g. "2020-24"
                   -- for All-Batches view, [2020,2021,...] for focused).
                   COALESCE(b.year, '')                           AS batch_year,
                   COUNT(*)                                       AS enrolled,
                   COUNT(*) FILTER (WHERE edu_rank >=  9)         AS passed_class_8,
                   COUNT(*) FILTER (WHERE edu_rank >= 11)         AS passed_class_10,
                   COUNT(*) FILTER (WHERE edu_rank >= 14)         AS passed_class_12,
                   COUNT(*) FILTER (WHERE LOWER(r.status) = 'active')               AS still_active,
                   COUNT(*) FILTER (WHERE r.status IN ('Walkout','Dropout')) AS dropped_off
            FROM ranked r
            LEFT JOIN ak_batches b ON r.batch_id = b.id
            GROUP BY r.batch_id, b.name, b.year
            ORDER BY batch_name
        """, ep_params)
        out["education_progression"] = [
            {
                "batch_id":        r["batch_id"],
                "batch_name":      r["batch_name"],
                "batch_year":      r.get("batch_year") or "",
                "enrolled":        int(r["enrolled"]        or 0),
                "passed_class_8":  int(r["passed_class_8"]  or 0),
                "passed_class_10": int(r["passed_class_10"] or 0),
                "passed_class_12": int(r["passed_class_12"] or 0),
                "still_active":    int(r["still_active"]    or 0),
                "dropped_off":     int(r["dropped_off"]     or 0),
            }
            for r in cur.fetchall()
        ]

        # NEW: Family Engagement Indicators.
        # family_members histogram (1-2, 3-4, 5-6, 7+, Unknown)
        cur.execute(f"""
            SELECT band, COUNT(*) AS c FROM (
              SELECT CASE
                WHEN l.family_members IS NULL THEN 'Unknown'
                WHEN l.family_members BETWEEN 1 AND 2 THEN '1 - 2'
                WHEN l.family_members BETWEEN 3 AND 4 THEN '3 - 4'
                WHEN l.family_members BETWEEN 5 AND 6 THEN '5 - 6'
                ELSE '7+'
              END AS band,
              CASE
                WHEN l.family_members IS NULL THEN 99
                WHEN l.family_members BETWEEN 1 AND 2 THEN 1
                WHEN l.family_members BETWEEN 3 AND 4 THEN 2
                WHEN l.family_members BETWEEN 5 AND 6 THEN 3
                ELSE 4
              END AS ord
              FROM ak_leaders l {leaders_join}
              WHERE {where_l}
            ) x
            GROUP BY band, ord
            ORDER BY ord
        """, params_l)
        out["family_size_distribution"] = [dict(r) for r in cur.fetchall()]

        # per_capita_income histogram (8 revised bands per user request 2026-11-17)
        cur.execute(f"""
            SELECT band, COUNT(*) AS c FROM (
              SELECT CASE
                WHEN l.per_capita_income IS NULL OR l.per_capita_income = 0 THEN 'Unknown'
                WHEN l.per_capita_income < 1000  THEN 'Less than 1000'
                WHEN l.per_capita_income < 2001  THEN '1000 - 2000'
                WHEN l.per_capita_income < 3001  THEN '2001 - 3000'
                WHEN l.per_capita_income < 4001  THEN '3001 - 4000'
                WHEN l.per_capita_income < 5001  THEN '4001 - 5000'
                WHEN l.per_capita_income < 6001  THEN '5001 - 6000'
                WHEN l.per_capita_income < 7001  THEN '6001 - 7000'
                ELSE 'More than 7000'
              END AS band,
              CASE
                WHEN l.per_capita_income IS NULL OR l.per_capita_income = 0 THEN 99
                WHEN l.per_capita_income < 1000  THEN 1
                WHEN l.per_capita_income < 2001  THEN 2
                WHEN l.per_capita_income < 3001  THEN 3
                WHEN l.per_capita_income < 4001  THEN 4
                WHEN l.per_capita_income < 5001  THEN 5
                WHEN l.per_capita_income < 6001  THEN 6
                WHEN l.per_capita_income < 7001  THEN 7
                ELSE 8
              END AS ord
              FROM ak_leaders l {leaders_join}
              WHERE {where_l}
            ) x
            GROUP BY band, ord
            ORDER BY ord
        """, params_l)
        out["per_capita_income_bands"] = [dict(r) for r in cur.fetchall()]

        # NEW: State-wise insights for JP (Jaipur) and Delhi.
        # The state_code values come from the central_states master.
        # We resolve them dynamically (match on name LIKE) so a
        # state_code rename doesn't silently zero the card.
        cur.execute("""
            SELECT state_code, state_name
            FROM central_states
            WHERE deleted_at IS NULL
              AND (state_name ILIKE 'Jaipur%' OR state_name ILIKE 'Rajasthan%' OR state_name ILIKE 'Delhi%')
        """)
        state_map = {}
        for r in cur.fetchall():
            n = (r["state_name"] or "").lower()
            if n.startswith("delhi"):
                state_map["Delhi"] = r["state_code"]
            else:
                # Jaipur is the AK programme's Jaipur (Rajasthan) base.
                state_map["JP"] = r["state_code"]

        def _state_summary(sc):
            """Headline numbers for one state — total/active leaders,
            active addas, trainings, training attendance, higher-ed
            count. Returns None when the state has no rows."""
            if not sc:
                return None
            # Leaders + higher education
            cur.execute("""
                SELECT COUNT(*) total,
                       COUNT(*) FILTER (WHERE status='Active') active,
                       COUNT(*) FILTER (WHERE current_education IN
                                       ('11th','12th','Graduate+','Graduate','Post-Graduate','Higher Secondary')) higher
                FROM ak_leaders
                WHERE state_code = %s AND deleted_at IS NULL
            """, (sc,))
            lr = cur.fetchone() or {}
            # Addas
            cur.execute("SELECT COUNT(*) c FROM ak_addas WHERE state_code = %s AND deleted_at IS NULL AND COALESCE(status,'Active') = 'Active'", (sc,))
            addas = (cur.fetchone() or {}).get("c", 0) or 0
            # Trainings + attendance
            cur.execute("""
                SELECT COUNT(DISTINCT t.id) sessions,
                       COUNT(*) FILTER (WHERE LOWER(COALESCE(tp.attendance,'')) = 'present') present
                FROM ak_trainings t
                LEFT JOIN ak_training_participants tp ON tp.training_id = t.id
                WHERE t.state_code = %s AND t.deleted_at IS NULL
            """, (sc,))
            tr = cur.fetchone() or {}
            return {
                "state_code":          sc,
                "total_leaders":       lr.get("total", 0) or 0,
                "active_leaders":      lr.get("active", 0) or 0,
                "higher_education":    lr.get("higher", 0) or 0,
                "active_addas":        addas,
                "trainings":           tr.get("sessions", 0) or 0,
                "training_attendance": tr.get("present", 0) or 0,
            }

        out["state_compare"] = {
            "JP":    _state_summary(state_map.get("JP")),
            "Delhi": _state_summary(state_map.get("Delhi")),
        }

        # Adda Activities summary — active addas count + total
        # monthly-meeting rows in ak_adda_details + total attendance
        # across those rows (scoped by the adda's geo).
        w_aa = ["a.deleted_at IS NULL", "COALESCE(a.status,'Active') = 'Active'"]
        p_aa: list = []
        if state_code:  w_aa.append("a.state_code = %s");  p_aa.append(state_code)
        if district_code:
            w_aa.append("a.centre_code IN (SELECT centre_code FROM central_centres WHERE district_code = %s)")
            p_aa.append(district_code)
        if centre_code: w_aa.append("a.centre_code = %s"); p_aa.append(centre_code)
        cur.execute(f"SELECT COUNT(*) c FROM ak_addas a WHERE {' AND '.join(w_aa)}", p_aa)
        active_addas_count = (cur.fetchone() or {}).get("c", 0) or 0

        cur.execute(f"""
            SELECT COUNT(*) AS meetings,
                   COALESCE(SUM(d.attendance), 0) AS attendance
            FROM ak_adda_details d
            JOIN ak_addas a ON d.adda_id = a.id
            WHERE {' AND '.join(w_aa)}
        """, p_aa)
        ad = cur.fetchone() or {}
        out["adda_activities_summary"] = {
            "active_addas":      active_addas_count,
            "monthly_meetings":  ad.get("meetings", 0) or 0,
            "total_attendance":  ad.get("attendance", 0) or 0,
        }

        # 2026-11-14: Centre-wise Community Outreach (Chaupal & Home Visits)
        s_conds = ["s.deleted_at IS NULL"]
        s_params = []
        if batch_id:
            cur.execute("SELECT name FROM ak_batches WHERE id = %s", (batch_id,))
            b_row = cur.fetchone()
            if b_row and b_row["name"]:
                s_conds.append("s.batch ILIKE %s")
                s_params.append(f"%{b_row['name'].strip()}%")
        if date_from:
            s_conds.append("s.month >= %s::date")
            s_params.append(date_from)
        if date_to:
            s_conds.append("s.month <= (%s::date + INTERVAL '1 month')")
            s_params.append(date_to)

        centre_expr = """COALESCE(
            (SELECT cc.centre_name FROM central_centres cc JOIN mis_user u ON u.centre_code = cc.centre_code WHERE LOWER(u.name) = LOWER(s.sangini_name) AND u.centre_code IS NOT NULL AND u.centre_code != '' LIMIT 1),
            (SELECT cc.centre_name FROM ak_leaders l JOIN ak_addas a ON a.leader_id = l.id LEFT JOIN central_centres cc ON a.centre_code = cc.centre_code WHERE LOWER(l.name) = LOWER(s.sangini_name) AND l.deleted_at IS NULL AND a.deleted_at IS NULL ORDER BY a.id LIMIT 1),
            'Other'
        )"""

        centre_code_expr = """COALESCE(
            (SELECT cc.centre_code FROM central_centres cc JOIN mis_user u ON u.centre_code = cc.centre_code WHERE LOWER(u.name) = LOWER(s.sangini_name) AND u.centre_code IS NOT NULL AND u.centre_code != '' LIMIT 1),
            (SELECT a.centre_code FROM ak_leaders l JOIN ak_addas a ON a.leader_id = l.id WHERE LOWER(l.name) = LOWER(s.sangini_name) AND l.deleted_at IS NULL AND a.deleted_at IS NULL ORDER BY a.id LIMIT 1)
        )"""

        if centre_code:
            s_conds.append(f"{centre_code_expr} = %s")
            s_params.append(centre_code)
        elif district_code:
            s_conds.append(f"{centre_code_expr} IN (SELECT centre_code FROM central_centres WHERE district_code = %s)")
            s_params.append(district_code)
        elif state_code:
            s_conds.append(f"{centre_code_expr} IN (SELECT centre_code FROM central_centres WHERE state_code = %s)")
            s_params.append(state_code)

        state_expr = """COALESCE(
            (SELECT cs.state_name FROM central_centres cc JOIN mis_user u ON u.centre_code = cc.centre_code LEFT JOIN central_states cs ON cc.state_code = cs.state_code WHERE LOWER(u.name) = LOWER(s.sangini_name) AND u.centre_code IS NOT NULL AND u.centre_code != '' LIMIT 1),
            (SELECT cs.state_name FROM ak_leaders l JOIN ak_addas a ON a.leader_id = l.id LEFT JOIN central_centres cc ON a.centre_code = cc.centre_code LEFT JOIN central_states cs ON cc.state_code = cs.state_code WHERE LOWER(l.name) = LOWER(s.sangini_name) AND l.deleted_at IS NULL AND a.deleted_at IS NULL ORDER BY a.id LIMIT 1),
            'Other'
        )"""

        # 1. State-wise outreach (for Admin & Super Admin)
        cur.execute(f"""
            SELECT 
                {state_expr} AS state_name,
                COALESCE(SUM(s.choupals), 0)::int AS chaupals,
                COALESCE(SUM(s.choupal_participants), 0)::int AS choupal_participants,
                COALESCE(SUM(s.choupal_male), 0)::int AS choupal_male,
                COALESCE(SUM(s.choupal_female), 0)::int AS choupal_female,
                COALESCE(SUM(s.home_visits), 0)::int AS home_visits,
                COALESCE(SUM(s.home_visit_participants), 0)::int AS home_visit_participants,
                COALESCE(SUM(s.home_visit_male), 0)::int AS home_visit_male,
                COALESCE(SUM(s.home_visit_female), 0)::int AS home_visit_female
            FROM sangini_entries s
            WHERE {' AND '.join(s_conds)}
            GROUP BY 1
            ORDER BY state_name
        """, s_params)
        out["state_outreach"] = [dict(r) for r in cur.fetchall()]

        # 2. Centre-wise outreach
        cur.execute(f"""
            SELECT 
                {centre_expr} AS centre_name,
                COALESCE(SUM(s.choupals), 0)::int AS chaupals,
                COALESCE(SUM(s.choupal_participants), 0)::int AS choupal_participants,
                COALESCE(SUM(s.choupal_male), 0)::int AS choupal_male,
                COALESCE(SUM(s.choupal_female), 0)::int AS choupal_female,
                COALESCE(SUM(s.home_visits), 0)::int AS home_visits,
                COALESCE(SUM(s.home_visit_participants), 0)::int AS home_visit_participants,
                COALESCE(SUM(s.home_visit_male), 0)::int AS home_visit_male,
                COALESCE(SUM(s.home_visit_female), 0)::int AS home_visit_female
            FROM sangini_entries s
            WHERE {' AND '.join(s_conds)}
            GROUP BY 1
            ORDER BY centre_name
        """, s_params)
        out["centre_outreach"] = [dict(r) for r in cur.fetchall()]

        # 3. Batch-wise outreach
        cur.execute(f"""
            SELECT 
                TRIM(b) AS batch_name,
                COALESCE(SUM(s.choupals), 0)::int AS chaupals,
                COALESCE(SUM(s.choupal_participants), 0)::int AS choupal_participants,
                COALESCE(SUM(s.choupal_male), 0)::int AS choupal_male,
                COALESCE(SUM(s.choupal_female), 0)::int AS choupal_female,
                COALESCE(SUM(s.home_visits), 0)::int AS home_visits,
                COALESCE(SUM(s.home_visit_participants), 0)::int AS home_visit_participants,
                COALESCE(SUM(s.home_visit_male), 0)::int AS home_visit_male,
                COALESCE(SUM(s.home_visit_female), 0)::int AS home_visit_female
            FROM sangini_entries s,
                 unnest(string_to_array(COALESCE(s.batch, 'Unassigned'), ',')) b
            WHERE {' AND '.join(s_conds)} AND TRIM(b) <> ''
            GROUP BY 1
            ORDER BY 1
        """, s_params)
        out["batch_outreach"] = [dict(r) for r in cur.fetchall()]

    return out
