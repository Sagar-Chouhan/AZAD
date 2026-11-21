"""WWW Commitment module.

Adds a per-centre / per-month / per-category commitment (target) grid and
a Commitment-vs-Achievement dashboard. Achievement is computed live from
the existing WWW record tables (no separate achievement store):

  Enrollment          -> mis_azad.www_enrollment.enrollment_date
  Learning License    -> mis_azad.www_ll.date_of_ll
  Permanent License   -> mis_azad.www_pl.date_of_pl
  Entity BKS          -> mis_azad.www_bks.date_of_bks_conducted

Geography for the achievement queries is resolved by _www_legacy.geo_joins,
identical to how every other WWW list resolves centre_code from the row's
text "state/district/centre" columns.

Endpoints:
  GET  /api/www-commitments/financial-years       fixed FY list + current FY
  GET  /api/www-commitments                       grid (0..48 rows)
  POST /api/www-commitments/save                  batch upsert (12*4 rows)
  GET  /api/www-commitments/dashboard             commitment vs achievement
                                                  per month per category

RBAC: read-open to every authenticated WWW user (list/dashboard are scoped
by scope_geo). Save is restricted to Super Admin, Admin, State Lead,
District Lead, and PI (checked against caller's role via get_current_user).
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Optional, List, Any
from pydantic import BaseModel
import sys, os
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from routes._www_scope import scope_geo, DENY
from routes._www_legacy import geo_joins
from routes._role_scope import get_current_user

router = APIRouter(prefix="/api/www-commitments", tags=["WWW Commitments"])


# ---------------------------------------------------------------------------
# Categories + FY constants
# ---------------------------------------------------------------------------
CATEGORIES = ("Enrollment", "PL", "Employment", "NTT", "BKS")
CATEGORY_SET = set(CATEGORIES)

FY_OPTIONS = (
    "2022-23", "2023-24", "2024-25", "2025-26", "2026-27",
    "2027-28", "2028-29", "2029-30", "2030-31",
)

# Roles allowed to save
SAVE_ROLES = {"super admin", "admin", "state lead", "district lead", "project incharge (pi)", "pi"}


def _current_fy() -> str:
    """Return the current financial year as 'YYYY-YY'. April is the boundary."""
    t = date.today()
    y = t.year if t.month >= 4 else t.year - 1
    return f"{y}-{str(y + 1)[2:]}"


def _check_save_permission(request: Request) -> None:
    """Raise 403 if the caller's role is not in SAVE_ROLES."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    role = (user.get("role_name") or "").strip().lower()
    if role not in SAVE_ROLES:
        raise HTTPException(status_code=403, detail="You are not allowed to save commitments")


# ---------------------------------------------------------------------------
# Financial year metadata
# ---------------------------------------------------------------------------
@router.get("/financial-years")
def financial_years():
    return {
        "options": list(FY_OPTIONS),
        "current": _current_fy(),
    }


# ---------------------------------------------------------------------------
# Grid read
# ---------------------------------------------------------------------------
@router.get("")
def list_grid(request: Request,
              centre_code: Optional[str] = None,
              financial_year: Optional[str] = None):
    """Return the commitment grid rows for a centre + FY. Empty list when the
    caller has not saved anything yet — the client renders zeros in that
    case. RBAC scope_geo applied so a PI cannot request another centre."""
    _, _, centre_code = scope_geo(request, None, None, centre_code)
    if centre_code == DENY:
        return {"centre_code": None, "financial_year": financial_year, "rows": []}
    if not centre_code or not financial_year:
        return {"centre_code": centre_code, "financial_year": financial_year, "rows": []}
    if financial_year not in FY_OPTIONS:
        raise HTTPException(status_code=400, detail="Unknown financial year")
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT month_num, category, target_count
              FROM mis_azad.www_commitments
             WHERE centre_code = %s AND financial_year = %s AND deleted_at IS NULL
             ORDER BY month_num, category
            """,
            (centre_code, financial_year),
        )
        rows = cur.fetchall()
    return {"centre_code": centre_code, "financial_year": financial_year, "rows": rows}


# ---------------------------------------------------------------------------
# Batch upsert
# ---------------------------------------------------------------------------
class CommitmentRow(BaseModel):
    month_num: int          # 1..12 (calendar; April=4, ..., March=3)
    category: str
    target_count: int


class CommitmentSaveBody(BaseModel):
    centre_code: str
    financial_year: str
    rows: List[CommitmentRow]


@router.post("/save")
def save_grid(request: Request, body: CommitmentSaveBody):
    _check_save_permission(request)
    if body.financial_year not in FY_OPTIONS:
        raise HTTPException(status_code=400, detail="Unknown financial year")
    if not body.centre_code or not body.centre_code.strip():
        raise HTTPException(status_code=400, detail="centre_code is required")
    # RBAC: caller may only save for a centre that scope_geo accepts.
    _, _, scoped = scope_geo(request, None, None, body.centre_code)
    if scoped == DENY or (scoped and scoped != body.centre_code):
        raise HTTPException(status_code=403, detail="This centre is outside your scope")
    for r in body.rows:
        if r.month_num < 1 or r.month_num > 12:
            raise HTTPException(status_code=400, detail="month_num must be 1..12")
        if r.category not in CATEGORY_SET:
            raise HTTPException(status_code=400, detail=f"Unknown category: {r.category}")
        if r.target_count < 0:
            raise HTTPException(status_code=400, detail="target_count must be >= 0")
    saved = 0
    with get_cursor() as cur:
        for r in body.rows:
            cur.execute(
                """
                INSERT INTO mis_azad.www_commitments
                    (centre_code, financial_year, month_num, category, target_count)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (centre_code, financial_year, month_num, category)
                    WHERE deleted_at IS NULL
                DO UPDATE SET target_count = EXCLUDED.target_count,
                              updated_at   = NOW()
                """,
                (body.centre_code, body.financial_year, r.month_num, r.category, r.target_count),
            )
            saved += 1
    return {"saved": saved, "message": "Commitments saved"}


# ---------------------------------------------------------------------------
# Commitment vs Achievement dashboard
# ---------------------------------------------------------------------------
# 2026-10-04 (forward-fix): tuple is (table, date_col, distinct_col).
# distinct_col must exist on that table. www_enrollment has no
# enrollment_id -> use s.id (each row is already one unique enrollment).
# PL / Employment have enrollment_id -> use that so trainees with
# multiple PL or employment rows don't double-count. NTT / BKS fall
# back to s.id defensively (no numbers in dispute for those categories).
_ACHIEVEMENT_SOURCES = {
    "Enrollment":  ("mis_azad.www_enrollment",   "enrollment_date",       "s.id"),
    "PL":          ("mis_azad.www_pl",           "date_of_pl",            "s.enrollment_id"),
    "Employment":  ("mis_azad.www_employment",   "date_of_job",           "s.enrollment_id"),
    "NTT":         ("mis_azad.www_ntt_training", "start_date",            "s.id"),
    "BKS":         ("mis_azad.www_bks",          "date_of_bks_conducted", "s.id"),
}


def _fy_bounds(fy: str):
    """('2026-27') -> (date(2026,4,1), date(2027,3,31))."""
    a, b = fy.split("-")
    y1 = int(a)
    return date(y1, 4, 1), date(y1 + 1, 3, 31)


def _achievement_by_month(cur, table: str, date_col: str, centre_code: Optional[str], fy: str, state_code: Optional[str] = None, district_code: Optional[str] = None, extra_where: Optional[str] = None, distinct_col: str = "s.id"):
    """Return {calendar_month: count} for the given centre + FY. Uses
    _www_legacy.geo_joins to resolve centre from the row's text columns.

    2026-09-29: added state_code so the dashboard filter can narrow
    achievement to a single state (via geo_joins' _gs alias).
    2026-10-04: added COUNT(DISTINCT) semantics (matches KPI cards),
    optional district_code (for DL scope), and optional extra_where
    (used by Employment to filter current_status='On Job')."""
    start, end = _fy_bounds(fy)
    joins = geo_joins("s")
    conds = ["(s.deleted_at IS NULL)",
             f"({date_col})::date >= %s",
             f"({date_col})::date <= %s"]
    params: List[Any] = [start, end]
    if centre_code:
        conds.append("_gc.centre_code = %s"); params.append(centre_code)
    else:
        if state_code:
            conds.append("_gs.state_code = %s"); params.append(state_code)
        if district_code:
            conds.append("_gd.district_code = %s"); params.append(district_code)
    if extra_where:
        conds.append(extra_where)
    cur.execute(
        f"""
        SELECT EXTRACT(MONTH FROM ({date_col})::date)::int AS m,
               COUNT(DISTINCT {distinct_col}) AS c
          FROM {table} s
          {joins}
         WHERE {" AND ".join(conds)}
         GROUP BY 1
         ORDER BY 1
        """,
        params,
    )
    out = {i: 0 for i in range(1, 13)}
    for row in cur.fetchall():
        m = row["m"]
        if m in out:
            out[m] = int(row["c"])
    return out


@router.get("/dashboard")
def dashboard(request: Request,
              centre_code: Optional[str] = None,
              state_code: Optional[str] = None,
              financial_year: Optional[str] = None):
    """Return per-month commitment + achievement for each category so the
    frontend can render 4 Chart.js bar charts (one per category).

    When centre_code is None or the caller is unscoped, the achievement is
    computed across every centre the caller can see and the commitment is
    the sum across those centres.

    2026-09-29: state_code was added so the WWW Home dashboard filter
    (which only exposes state + centre) can narrow the chart down for
    admin / super_admin. RBAC still wins -- DL / SL / PI cannot request
    a state outside their own."""
    financial_year = financial_year or _current_fy()
    if financial_year not in FY_OPTIONS:
        raise HTTPException(status_code=400, detail="Unknown financial year")
    # 2026-10-04: keep district_code from scope_geo so DL commitments
    # can be narrowed to the DL's own district (previously discarded).
    state_code, district_code, centre_code = scope_geo(request, state_code, None, centre_code)
    if centre_code == DENY or state_code == DENY:
        return {"financial_year": financial_year, "centre_code": None, "categories": [
            {"category": c, "months": [0]*12, "commitment": [0]*12, "achievement": [0]*12}
            for c in CATEGORIES
        ]}

    # FY month order: April(4), May(5), ..., Dec(12), Jan(1), Feb(2), Mar(3).
    fy_month_order = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]
    fy_month_labels = ["April", "May", "June", "July", "August", "September",
                       "October", "November", "December", "January", "February", "March"]

    with get_cursor() as cur:
        # Commitment per (month, category)
        commit_conds = ["deleted_at IS NULL", "financial_year = %s"]
        commit_params = [financial_year]
        if centre_code:
            commit_conds.append("centre_code = %s"); commit_params.append(centre_code)
        elif state_code:
            # 2026-10-04: subquery was reading central_centres whose
            # centre_codes do NOT match the WWW-style codes stored in
            # www_commitments.centre_code (see _www_scope.py). Use
            # www_centres instead. If scope_geo also pinned a district
            # (DL role), narrow by district too.
            if district_code:
                commit_conds.append(
                    "centre_code IN (SELECT centre_code FROM mis_azad.central_centres "
                    "WHERE state_code = %s AND district_code = %s)"
                )
                commit_params.append(state_code); commit_params.append(district_code)
            else:
                commit_conds.append("centre_code IN (SELECT centre_code FROM mis_azad.central_centres WHERE state_code = %s)"); commit_params.append(state_code)
        cur.execute(
            f"""
            SELECT month_num, category, SUM(target_count)::int AS target_count
              FROM mis_azad.www_commitments
             WHERE {" AND ".join(commit_conds)}
             GROUP BY month_num, category
            """,
            commit_params,
        )
        commit_map = {c: {i: 0 for i in range(1, 13)} for c in CATEGORIES}
        for row in cur.fetchall():
            if row["category"] in commit_map:
                commit_map[row["category"]][row["month_num"]] = int(row["target_count"] or 0)

        # Achievement per (category, month)
        # 2026-10-04: Employment gets a current_status='On Job' predicate
        # so chart totals match the KPI card. District is now carried
        # through so DL scopes narrow correctly.
        _EXTRA = {
            # 2026-10-04: live/stage column is what_is_your_current_status (not current_status).
            "Employment": "s.what_is_your_current_status = 'On Job'",
        }
        ach_map = {}
        for cat in CATEGORIES:
            table, dcol, dist_col = _ACHIEVEMENT_SOURCES[cat]
            ach_map[cat] = _achievement_by_month(
                cur, table, dcol, centre_code, financial_year,
                state_code=state_code, district_code=district_code,
                extra_where=_EXTRA.get(cat),
                distinct_col=dist_col,
            )

    result = []
    for cat in CATEGORIES:
        commit_series    = [commit_map[cat][m] for m in fy_month_order]
        achieve_series   = [ach_map[cat][m]    for m in fy_month_order]
        result.append({
            "category":     cat,
            "months":       fy_month_labels,
            "commitment":   commit_series,
            "achievement":  achieve_series,
        })
    return {"financial_year": financial_year, "centre_code": centre_code, "categories": result}
