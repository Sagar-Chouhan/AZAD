"""State Lead Dashboard API routes."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
# 2026-10-04: METRIC_CATEGORIES used by the rewritten
# /target-vs-achievement endpoint (same category mapping as Reporting).
try:
    from routes.targets import METRIC_CATEGORIES
except Exception:
    METRIC_CATEGORIES = {}

router = APIRouter(prefix="/api/state-dashboard", tags=["State Dashboard"])


def _build_sl_flp_filter(state_code=None, district_code=None, centre_code=None, include_inactive=False):
    """Build FLP filter conditions for State Lead dashboard.

    2026-10-04: added include_inactive. Default False (preserves
    the Active-only behaviour for KPI cards that count active FLPs).
    Pass True for things that must match the Survey List / other
    FLP-list screens, which include Walkouts / Dropouts etc."""
    conditions = ["f.deleted_at IS NULL"]
    if not include_inactive:
        conditions.append("f.status = 'Active'")
    params = []
    if state_code:
        conditions.append("""(f.district_code IN (SELECT district_code FROM central_districts WHERE state_code = %s)
            OR f.centre_code IN (SELECT centre_code FROM central_centres WHERE state_code = %s))""")
        params.extend([state_code, state_code])
    if district_code:
        conditions.append("f.district_code = %s")
        params.append(district_code)
    if centre_code:
        conditions.append("f.centre_code = %s")
        params.append(centre_code)
    return " AND ".join(conditions), params


@router.get("/summary")
def get_state_dashboard_summary(state_code: Optional[str] = None,
                                 district_code: Optional[str] = None,
                                 centre_code: Optional[str] = None,
                                 month: Optional[str] = None):
    """Get summary cards: Total Centres, Total FLPs, Total Surveys, Total Trainings."""
    with get_cursor() as cur:
        # Total Centres
        if centre_code:
            cur.execute("SELECT COUNT(*) as count FROM central_centres WHERE centre_code = %s AND LOWER(status) = 'active'", (centre_code,))
        elif district_code:
            cur.execute("SELECT COUNT(*) as count FROM central_centres WHERE district_code = %s AND LOWER(status) = 'active'", (district_code,))
        elif state_code:
            cur.execute("SELECT COUNT(*) as count FROM central_centres WHERE state_code = %s AND LOWER(status) = 'active'", (state_code,))
        else:
            cur.execute("SELECT COUNT(*) as count FROM central_centres WHERE LOWER(status) = 'active'")
        total_centres = cur.fetchone()["count"]

        flp_where, flp_params = _build_sl_flp_filter(state_code, district_code, centre_code)

        cur.execute(f"SELECT COUNT(*) as count FROM flps f WHERE {flp_where}", flp_params)
        total_flps = cur.fetchone()["count"]

        # 2026-10-04: Survey List counts Walkout/Dropout trainees too;
        # dashboard must match. Build a second filter without the Active
        # predicate (via include_inactive=True) and use it for the
        # surveys count only. Keeps total_flps unchanged.
        if state_code or district_code or centre_code:
            sv_where, sv_params = _build_sl_flp_filter(state_code, district_code, centre_code, include_inactive=True)
            cur.execute(f"SELECT COUNT(*) as count FROM surveys s JOIN flps f ON s.flp_id = f.id WHERE {sv_where}", sv_params)
        else:
            cur.execute("SELECT COUNT(*) as count FROM surveys")
        total_surveys = cur.fetchone()["count"]

        # Trainings — use centre_code on trainings table + fallback to old centre_id
        t_conditions = ["1=1"]
        t_params = []
        if centre_code:
            t_conditions.append("(t.centre_code = %s OR t.centre_id IN (SELECT DISTINCT ct.centre_id FROM centre_targets ct WHERE ct.centre_code = %s AND ct.centre_id > 0))")
            t_params.extend([centre_code, centre_code])
        elif district_code:
            t_conditions.append("t.centre_code IN (SELECT centre_code FROM central_centres WHERE district_code = %s)")
            t_params.append(district_code)
        elif state_code:
            t_conditions.append("""(t.centre_code IN (SELECT centre_code FROM central_centres WHERE state_code = %s)
                OR t.centre_id IN (SELECT c.id FROM central_centres c JOIN central_states s ON c.state_id = s.id
                    JOIN central_states ns ON LOWER(s.state_name) LIKE '%%' || LOWER(ns.state_name) || '%%'
                    WHERE ns.state_code = %s))""")
            t_params.extend([state_code, state_code])
        t_where = " AND ".join(t_conditions)
        cur.execute(f"SELECT COUNT(DISTINCT t.id) as count FROM trainings t WHERE {t_where}", t_params)
        total_trainings = cur.fetchone()["count"]

    return {
        "total_centres": total_centres,
        "total_flps": total_flps,
        "total_surveys": total_surveys,
        "total_trainings": total_trainings
    }


@router.get("/age-distribution")
def get_age_distribution(state_code: Optional[str] = None,
                         district_code: Optional[str] = None,
                         centre_code: Optional[str] = None):
    """Get FLP age group distribution for pie chart."""
    with get_cursor() as cur:
        conditions = ["f.deleted_at IS NULL", "f.status = 'Active'", "f.date_of_birth IS NOT NULL"]
        params = []
        if state_code:
            conditions.append("""(f.district_code IN (SELECT district_code FROM central_districts WHERE state_code = %s)
                OR f.centre_code IN (SELECT centre_code FROM central_centres WHERE state_code = %s))""")
            params.extend([state_code, state_code])
        if district_code:
            conditions.append("f.district_code = %s")
            params.append(district_code)
        if centre_code:
            conditions.append("f.centre_code = %s")
            params.append(centre_code)

        where = " AND ".join(conditions)
        cur.execute(f"""
            SELECT age_range, count FROM (
                SELECT
                    CASE
                        WHEN EXTRACT(YEAR FROM AGE(NOW(), f.date_of_birth)) BETWEEN 18 AND 21 THEN '18-21'
                        WHEN EXTRACT(YEAR FROM AGE(NOW(), f.date_of_birth)) > 21
                             AND EXTRACT(YEAR FROM AGE(NOW(), f.date_of_birth)) <= 25 THEN '21-25'
                        WHEN EXTRACT(YEAR FROM AGE(NOW(), f.date_of_birth)) > 25 THEN '25+'
                        ELSE NULL
                    END as age_range,
                    COUNT(*) as count
                FROM flps f
                WHERE {where}
                GROUP BY age_range
            ) sub
            WHERE age_range IS NOT NULL
            ORDER BY CASE age_range WHEN '18-21' THEN 1 WHEN '21-25' THEN 2 WHEN '25+' THEN 3 END
        """, params)
        rows = cur.fetchall()

        total = sum(r['count'] for r in rows)
        result = []
        for r in rows:
            pct = round(r['count'] / total * 100, 1) if total > 0 else 0
            result.append({
                "range": r['age_range'],
                "count": r['count'],
                "percentage": pct
            })

    return {"data": result, "total": total}


@router.get("/survey-summary")
def get_survey_summary(state_code: Optional[str] = None,
                       district_code: Optional[str] = None,
                       centre_code: Optional[str] = None):
    """Get survey summary: total done, enrolled count."""
    with get_cursor() as cur:
        flp_where, flp_params = _build_sl_flp_filter(state_code, district_code, centre_code)

        cur.execute(f"SELECT COUNT(*) as total_done FROM surveys s JOIN flps f ON s.flp_id = f.id WHERE {flp_where}", flp_params)
        total_done = cur.fetchone()["total_done"]

        # www_pipeline is an optional table (not present in every deploy).
        # Guard the count with to_regclass so the endpoint doesn't 500 when
        # the WWW module hasn't been provisioned in this DB.
        total_enrolled = 0
        cur.execute("SELECT to_regclass('mis_azad.www_pipeline') AS t")
        if cur.fetchone()["t"] is not None:
            cur.execute(f"""
                SELECT COUNT(*) as total_enrolled
                FROM www_pipeline wp JOIN flps f ON wp.surveyed_by_flp_id = f.id
                WHERE wp.stage = 'Enrolled' AND {flp_where}
            """, flp_params)
            total_enrolled = cur.fetchone()["total_enrolled"]

    return {"total_done": total_done, "total_enrolled": total_enrolled}


@router.get("/training-progress")
def get_training_progress(state_code: Optional[str] = None,
                          district_code: Optional[str] = None,
                          centre_code: Optional[str] = None):
    """Get training-wise participation counts aggregated by phase."""
    with get_cursor() as cur:
        conditions = []
        params = []
        if centre_code:
            conditions.append("(t.centre_code = %s OR t.centre_id IN (SELECT DISTINCT ct.centre_id FROM centre_targets ct WHERE ct.centre_code = %s AND ct.centre_id > 0))")
            params.extend([centre_code, centre_code])
        elif district_code:
            conditions.append("t.centre_code IN (SELECT centre_code FROM central_centres WHERE district_code = %s)")
            params.append(district_code)
        elif state_code:
            conditions.append("""(t.centre_code IN (SELECT centre_code FROM central_centres WHERE state_code = %s)
                OR t.centre_id IN (SELECT c.id FROM central_centres c JOIN central_states s ON c.state_id = s.id
                    JOIN central_states ns ON LOWER(s.state_name) LIKE '%%' || LOWER(ns.state_name) || '%%'
                    WHERE ns.state_code = %s))""")
            params.extend([state_code, state_code])

        where = ("AND " + " AND ".join(conditions)) if conditions else ""

        cur.execute(f"""
            SELECT t.phase, COUNT(DISTINCT tp.flp_id) as participants
            FROM trainings t
            JOIN training_participants tp ON tp.training_id = t.id
            WHERE 1=1 {where}
            GROUP BY t.phase ORDER BY t.phase
        """, params)
        rows = cur.fetchall()

        all_phases = ['Phase I', 'Phase II', 'Phase III', 'Phase IV']
        phase_data = {r['phase']: r['participants'] for r in rows}

        # Get total FLPs
        flp_where, flp_params = _build_sl_flp_filter(state_code, district_code, centre_code)
        cur.execute(f"SELECT COUNT(*) as count FROM flps f WHERE {flp_where}", flp_params)
        total_flps = cur.fetchone()["count"]

        result = []
        for phase in all_phases:
            result.append({
                "phase": phase,
                "participants": phase_data.get(phase, 0),
                "total_flps": total_flps
            })

    return {"phases": result, "total_flps": total_flps}


@router.get("/target-vs-achievement")
def get_target_vs_achievement(state_code: Optional[str] = None,
                               district_code: Optional[str] = None,
                               centre_code: Optional[str] = None,
                               month: Optional[str] = None):
    """Get target vs achievement data for all metrics, aggregated across centres.

    2026-10-04: rewritten to read from flp_targets + centre_reports
    (joined by flp_id) instead of the deprecated centre_targets table,
    so the chart matches the Reporting-page table (which already uses
    the same source via /api/targets + /api/reports). Response shape
    unchanged: {"data": [{metric_key, category, target, achieved, percentage}]}."""
    if not month:
        raise HTTPException(status_code=400, detail="month parameter is required (YYYY-MM)")

    with get_cursor() as cur:
        # Geo scope on central_centres (nc.*) -- used for both
        # the targets JOIN and the achievements JOIN below.
        if centre_code:
            geo_cond = "nc.centre_code = %s"
            geo_params = [centre_code]
        elif district_code:
            geo_cond = "nc.district_code = %s"
            geo_params = [district_code]
        elif state_code:
            geo_cond = "nc.state_code = %s"
            geo_params = [state_code]
        else:
            geo_cond = "1=1"
            geo_params = []

        # Targets from flp_targets (same source as the Reporting table)
        cur.execute(f"""
            SELECT ft.metric_key, SUM(ft.target_value) as total_target
              FROM flp_targets ft
              JOIN central_centres nc ON ft.centre_code = nc.centre_code
             WHERE ft.target_month = %s AND {geo_cond}
             GROUP BY ft.metric_key
             ORDER BY ft.metric_key
        """, [month] + geo_params)
        target_rows = cur.fetchall()

        if not target_rows:
            return {"data": []}

        targets_map = {}
        for t in target_rows:
            targets_map[t['metric_key']] = {
                'category': METRIC_CATEGORIES.get(t['metric_key'], 'unknown'),
                'target': int(t['total_target'] or 0),
            }

        # Achievements from centre_reports via flp_id -> flps -> central_centres
        # (same source as the Reporting table at /api/reports).
        cur.execute(f"""
            SELECT cr.metric_key, SUM(cr.achieved_value) as total_achieved
              FROM centre_reports cr
              JOIN flps f ON cr.flp_id = f.id
              JOIN central_centres nc ON nc.centre_code = f.centre_code
             WHERE cr.report_month = %s
               AND cr.status = 'Submitted'
               AND f.deleted_at IS NULL
               AND {geo_cond}
             GROUP BY cr.metric_key
        """, [month] + geo_params)
        achievements_map = {r['metric_key']: int(r['total_achieved'] or 0) for r in cur.fetchall()}

        result = []
        for mk, tdata in targets_map.items():
            achieved = achievements_map.get(mk, 0)
            target   = tdata['target']
            pct      = round(achieved / target * 100, 1) if target > 0 else 0
            result.append({
                'metric_key': mk,
                'category':   tdata['category'],
                'target':     target,
                'achieved':   achieved,
                'percentage': min(pct, 100),
            })

    return {"data": result}


@router.get("/survey-map-points")
def get_survey_map_points(state_code: Optional[str] = None,
                          district_code: Optional[str] = None,
                          centre_code: Optional[str] = None,
                          limit: int = 500):
    """Get survey GPS coordinates for map plotting."""
    with get_cursor() as cur:
        conditions = ["s.gps_lat IS NOT NULL", "s.gps_lng IS NOT NULL",
                       "s.gps_lat != 0", "s.gps_lng != 0"]
        params = []
        if state_code:
            conditions.append("""f.id IN (SELECT f2.id FROM flps f2 WHERE f2.deleted_at IS NULL AND
                (f2.district_code IN (SELECT district_code FROM central_districts WHERE state_code = %s)
                OR f2.centre_code IN (SELECT centre_code FROM central_centres WHERE state_code = %s)))""")
            params.extend([state_code, state_code])
        if district_code:
            conditions.append("f.district_code = %s")
            params.append(district_code)
        if centre_code:
            conditions.append("f.centre_code = %s")
            params.append(centre_code)

        where = " AND ".join(conditions)
        cur.execute(f"""
            SELECT s.gps_lat as lat, s.gps_lng as lng,
                   s.sec_b_basti as basti,
                   COALESCE(nd.district_name, s.sec_b_district, '') as district,
                   COALESCE(na.area_name, s.sec_b_area, '') as area,
                   f.name as flp_name, s.date as survey_date
            FROM surveys s
            JOIN flps f ON s.flp_id = f.id
            LEFT JOIN central_districts nd ON f.district_code = nd.district_code
            LEFT JOIN central_areas na ON s.sec_b_area = na.area_code
            WHERE {where}
            ORDER BY s.date DESC
            LIMIT %s
        """, params + [limit])
        rows = cur.fetchall()

    return [dict(r) for r in rows]