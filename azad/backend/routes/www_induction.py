"""WWW Induction — list + create induction records.

Backed by mis_azad.www_inductions (one row per induction event, joined
with www_trainees and www_master_batches for display).

On deployments without that normalized schema the routes fall back to
mis_azad.www_induction, the spreadsheet import that carries the same
data one row per trainee.  See routes/_www_legacy.py for the geography
mapping the fallback needs.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from datetime import date
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from routes import _www_legacy as _legacy
from routes import _www_scope as _scope
from routes._www_list_sort import www_list_order

router = APIRouter(prefix="/api/www-inductions", tags=["WWW Induction"])


class InductionCreate(BaseModel):
    trainee_id: int
    start_date: date
    end_date: date


@router.get("")
def list_inductions(
    request: Request,
    enrollment_id: Optional[int] = None,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    enrollment_type: Optional[str] = None,
    name: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort_by: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
):
    """List induction records joined with the trainee + batch master."""
    page = max(page, 1); limit = max(limit, 1); offset = (page - 1) * limit
    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        # ---- LEGACY FALLBACK: www_inductions absent -> read www_induction ----
        if not _legacy.table_exists(cur, "www_inductions"):
            lconds = ["i.start_date IS NOT NULL", "i.deleted_at IS NULL"]
            lparams = []
            if state_code:      lconds.append(_legacy.state_filter());      lparams.append(state_code)
            if district_code:   lconds.append(_legacy.district_filter());   lparams.append(district_code)
            if centre_code:     lconds.append(_legacy.centre_filter("i"));  lparams.append(centre_code)
            if enrollment_type: lconds.append("i.enrollment_type = %s");    lparams.append(enrollment_type)
            if name:            lconds.append("(" + _legacy.name_match("i.name") + " OR _te.enrollment_no ILIKE %s)");           lparams.append(_legacy.name_pattern(name)); lparams.append(_legacy.name_pattern(name))
            if date_from:       lconds.append("i.start_date >= %s");        lparams.append(date_from)
            if date_to:         lconds.append("i.end_date <= %s");          lparams.append(date_to)
            if batch_id:
                # Legacy stores the batch label, not a master id.
                lconds.append("NULLIF(TRIM(i.batch), '') = "
                              "(SELECT name FROM mis_azad.www_master_batches WHERE id = %s)")
                lparams.append(batch_id)
            lwhere = "WHERE " + " AND ".join(lconds)
            if enrollment_id:
                lwhere += " AND i.enrollment_id = %s"; lparams.append(enrollment_id)
            joins = _legacy.geo_joins("i") + _legacy.trainee_join("i")
            cur.execute(
                "SELECT COUNT(*) AS total FROM mis_azad.www_induction i " + joins + lwhere,
                lparams,
            )
            total = cur.fetchone()["total"]
            cur.execute(
                "SELECT i.id, i.start_date, i.end_date, "
                "       i.enrollment_id AS trainee_id, " + _legacy.enroll_no() + ", i.name, COALESCE(NULLIF(TRIM(_te.mobile), ''), NULLIF(TRIM(i.mobile), '')) AS mobile, "
                # 2026-08-13: the list shows DOB / Date of Joining; www_induction
                # carries neither, so both come off the enrollment join (_te).
                "       _te.date_of_birth, _te.enrollment_date AS date_of_joining, "
                "       COALESCE(NULLIF(TRIM(_te.type_of_enrollment), ''), NULLIF(TRIM(i.enrollment_type), '')) AS enrollment_type, " + _legacy.geo_cols() + ", "
                "       COALESCE(NULLIF(TRIM(_te.batch), ''), NULLIF(TRIM(i.batch), '')) AS batch_name, NULL::int AS batch_id, "
                "       i.created_at "
                "FROM mis_azad.www_induction i " + joins + lwhere +
                " ORDER BY " + www_list_order(sort_by, "i.name", "i.created_at", "i.created_at DESC NULLS LAST, i.id DESC", date_col="i.start_date") + " LIMIT %s OFFSET %s",
                lparams + [limit, offset],
            )
            rows = cur.fetchall()
            return {"total": total, "page": page, "limit": limit, "data": rows}

        conds = ["i.deleted_at IS NULL"]
        params = []
        if state_code:
            conds.append("t.state_code = %s"); params.append(state_code)
        if centre_code:
            conds.append("t.centre_code = %s"); params.append(centre_code)
        if batch_id:
            conds.append("t.batch_id = %s"); params.append(batch_id)
        if enrollment_type:
            conds.append("t.enrollment_type = %s"); params.append(enrollment_type)
        if name:
            conds.append(_legacy.name_match("t.name")); params.append(_legacy.name_pattern(name))
        if date_from:
            conds.append("i.start_date >= %s"); params.append(date_from)
        if date_to:
            conds.append("i.end_date <= %s"); params.append(date_to)
        where = "WHERE " + " AND ".join(conds)
        cur.execute(
            "SELECT COUNT(*) AS total FROM www_inductions i "
            "JOIN www_enrollment t ON t.id = i.trainee_id " + where,
            params,
        )
        total = cur.fetchone()["total"]
        sql = (
            "SELECT i.id, i.start_date, i.end_date, "
            "       t.id AS trainee_id, t.enrollment_no, t.name, t.mobile, "
            "       t.date_of_birth, t.enrollment_date AS date_of_joining, "
            "       t.enrollment_type, t.state_code, t.centre_code, "
            "       COALESCE(b.name, NULL) AS batch_name, b.id AS batch_id "
            "FROM www_inductions i "
            "JOIN www_enrollment t ON t.id = i.trainee_id "
            "LEFT JOIN www_master_batches b ON b.id = t.batch_id "
            + where + " ORDER BY " + www_list_order(sort_by, "i.name", "i.created_at", "i.created_at DESC NULLS LAST, i.id DESC", date_col="i.start_date") + " LIMIT %s OFFSET %s"
        )
        cur.execute(sql, params + [limit, offset])
        rows = cur.fetchall()
        return {"total": total, "page": page, "limit": limit, "data": rows}


@router.post("")
def create_induction(body: InductionCreate):
    if body.end_date < body.start_date:
        raise HTTPException(400, "End date must be on or after start date.")
    days = (body.end_date - body.start_date).days + 1
    with get_cursor() as cur:
        # 2026-08-18 (Ashish): flow guard -- picker ki rok server par bhi.
        _legacy.assert_flow(cur, body.trainee_id, stage="Induction")
        if not _legacy.table_exists(cur, "www_inductions"):
            # No trainee master here — www_enrollment plays that role, and the
            # induction row carries its own copy of the trainee's identity.
            cur.execute(
                "INSERT INTO mis_azad.www_induction "
                "    (enrollment_id, name, mobile, enrollment_type, "
                "     state, district, centre, area, batch, "
                "     start_date, end_date, duration_days) "
                "SELECT e.id, e.name, e.mobile, e.type_of_enrollment, "
                "       e.state, e.district, e.centre, e.area, e.batch, "
                "       %s, %s, %s "
                "FROM mis_azad.www_enrollment e WHERE e.id = %s "
                "RETURNING id",
                (body.start_date, body.end_date, days, body.trainee_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Trainee not found.")
            return {"id": row["id"], "ok": True}

        cur.execute("SELECT 1 FROM www_enrollment WHERE id = %s", (body.trainee_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Trainee not found.")
        cur.execute(
            "INSERT INTO www_inductions (trainee_id, start_date, end_date) "
            "VALUES (%s, %s, %s) RETURNING id",
            (body.trainee_id, body.start_date, body.end_date),
        )
        row = cur.fetchone()
    return {"id": row["id"], "ok": True}


@router.get("/{induction_id}")
def get_induction(request: Request, induction_id: int):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_inductions"):
            cur.execute(
                "SELECT i.id, i.start_date, i.end_date, "
                "       i.created_at, "
                "       i.enrollment_id AS trainee_id, " + _legacy.enroll_no() + ", i.name, COALESCE(NULLIF(TRIM(_te.mobile), ''), NULLIF(TRIM(i.mobile), '')) AS mobile, "
                "       COALESCE(NULLIF(TRIM(_te.type_of_enrollment), ''), NULLIF(TRIM(i.enrollment_type), '')) AS enrollment_type, " + _legacy.geo_cols() + ", "
                "       _gs.state_name, _gc.centre_name, "
                # 2026-09-14: resolve the area CODE stored in i.area to its name
                # (View showed the raw code). Falls back to the code if unmatched.
                "       COALESCE((SELECT a.area_name FROM mis_azad.www_areas a "
                "                  WHERE a.area_code = NULLIF(TRIM(i.area), '') "
                "                    AND a.deleted_at IS NULL LIMIT 1), "
                "                 NULLIF(TRIM(i.area), ''), NULLIF(TRIM(_te.area), '')) AS area_name, "
                "       COALESCE(NULLIF(TRIM(_te.batch), ''), NULLIF(TRIM(i.batch), '')) AS batch_name, NULL::int AS batch_id "
                "FROM mis_azad.www_induction i " + _legacy.geo_joins("i") +
                _legacy.trainee_join("i") +
                "WHERE i.id = %s",
                (induction_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Induction not found.")
            _scope.guard_detail(request, row)
            return row

        sql = (
            "SELECT i.id, i.start_date, i.end_date, i.created_at, "
            "       t.id AS trainee_id, t.enrollment_no, t.name, t.mobile, "
            "       t.enrollment_type, t.state_code, t.centre_code, t.district_code, "
            "       s.state_name, c.centre_name, d.district_name, "
            "       COALESCE(b.name, NULL) AS batch_name, b.id AS batch_id "
            "FROM www_inductions i "
            "JOIN www_enrollment t ON t.id = i.trainee_id "
            "LEFT JOIN www_master_batches b ON b.id = t.batch_id "
            "LEFT JOIN central_states  s ON s.state_code  = t.state_code "
            "LEFT JOIN central_centres c ON c.centre_code = t.centre_code "
            "LEFT JOIN central_districts d ON d.district_code = t.district_code "
            "WHERE i.id = %s AND i.deleted_at IS NULL"
        )
        cur.execute(sql, (induction_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Induction not found.")
    _scope.guard_detail(request, row)
    return row
    
class InductionUpdate(BaseModel):
    start_date: date
    end_date: date


@router.put("/{induction_id}")
def update_induction(induction_id: int, body: InductionUpdate):
    if body.end_date < body.start_date:
        raise HTTPException(400, "End date must be on or after start date.")
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_inductions"):
            cur.execute(
                "UPDATE mis_azad.www_induction "
                "   SET start_date=%s, end_date=%s, duration_days=%s WHERE id=%s",
                (body.start_date, body.end_date,
                 (body.end_date - body.start_date).days + 1, induction_id),
            )
        else:
            cur.execute(
                "UPDATE www_inductions SET start_date=%s, end_date=%s "
                "WHERE id=%s AND deleted_at IS NULL",
                (body.start_date, body.end_date, induction_id),
            )
        if cur.rowcount == 0:
            raise HTTPException(404, "Induction not found.")
    return {"ok": True}


@router.delete("/{induction_id}")
def delete_induction(induction_id: int):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_inductions"):
            # 2026-08-19 (Ashish): pehle ye row ko HAMESHA ke liye mita deta tha.
            # Ab deleted_at bhar dete hain -- row DB me bachi rehti hai, bas har
            # list se hat jati hai. Wapas laani ho to deleted_at = NULL.
            cur.execute("UPDATE mis_azad.www_induction SET deleted_at = NOW() "
                        "WHERE id = %s AND deleted_at IS NULL", (induction_id,))
        else:
            cur.execute(
                "UPDATE www_inductions SET deleted_at = now() "
                "WHERE id = %s AND deleted_at IS NULL",
                (induction_id,),
            )
        if cur.rowcount == 0:
            raise HTTPException(404, "Induction not found.")
    return {"ok": True}


# =============================================================================
# EXPORT (Excel) — 2026-08-07
# Section-wise xlsx with:
#   1. Trainee Details     (Enrollment No, Name, Mobile, Type, State,
#                           District, Centre, Area, Batch)
#   2. Induction Details   (Start Date, End Date, Duration (Days))
#   3. System              (Created At)
# Sends the same filters as list_inductions so the export matches what's on
# screen. Legacy www_ll_form fallback preserved.
# =============================================================================
@router.get("/export/excel")
def export_inductions_excel(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    enrollment_type: Optional[str] = None,
    name: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    from datetime import date as _d
    from export_helper import multi_sheet_xlsx_response_v2

    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        has_table = _legacy.table_exists(cur, "www_inductions")

        if not has_table:
            lconds = ["i.start_date IS NOT NULL", "i.deleted_at IS NULL"]
            lparams = []
            if state_code:      lconds.append(_legacy.state_filter());     lparams.append(state_code)
            if district_code:   lconds.append(_legacy.district_filter());  lparams.append(district_code)
            if centre_code:     lconds.append(_legacy.centre_filter("i")); lparams.append(centre_code)
            if enrollment_type: lconds.append("i.enrollment_type = %s");   lparams.append(enrollment_type)
            if name:            lconds.append(_legacy.name_match("i.name"));          lparams.append(_legacy.name_pattern(name))
            if date_from:       lconds.append("i.start_date >= %s");       lparams.append(date_from)
            if date_to:         lconds.append("i.end_date <= %s");         lparams.append(date_to)
            if batch_id:
                lconds.append("NULLIF(TRIM(i.batch), '') = "
                              "(SELECT name FROM mis_azad.www_master_batches WHERE id = %s)")
                lparams.append(batch_id)
            where = "WHERE " + " AND ".join(lconds)
            cur.execute(
                "SELECT " + _legacy.enroll_no() + ", i.id AS id, i.name, COALESCE(NULLIF(TRIM(_te.mobile), ''), NULLIF(TRIM(i.mobile), '')) AS mobile, COALESCE(NULLIF(TRIM(_te.type_of_enrollment), ''), NULLIF(TRIM(i.enrollment_type), '')) AS enrollment_type, "
                "       i.state AS state_name, i.district AS district_name, "
                "       " + _legacy.centre_expr("i.centre") + " AS centre_name, "
                "       COALESCE(NULLIF(TRIM(_te.area), ''), NULLIF(TRIM(i.area), '')) AS area_name, "
                "       COALESCE(NULLIF(TRIM(_te.batch), ''), NULLIF(TRIM(i.batch), '')) AS batch_name, "
                "       i.start_date, i.end_date, i.duration_days, "
                "       i.created_at "
                "FROM mis_azad.www_induction i " + _legacy.geo_joins("i") +
                _legacy.trainee_join("i") + where +
                " ORDER BY i.start_date DESC NULLS LAST, i.id DESC",
                lparams,
            )
            rows = cur.fetchall()
        else:
            conds = ["i.deleted_at IS NULL"]
            params = []
            if state_code:      conds.append("t.state_code = %s");        params.append(state_code)
            if centre_code:     conds.append("t.centre_code = %s");       params.append(centre_code)
            if batch_id:        conds.append("t.batch_id = %s");          params.append(batch_id)
            if enrollment_type: conds.append("t.enrollment_type = %s");   params.append(enrollment_type)
            if name:            conds.append(_legacy.name_match("t.name"));          params.append(_legacy.name_pattern(name))
            if date_from:       conds.append("i.start_date >= %s");       params.append(date_from)
            if date_to:         conds.append("i.end_date <= %s");         params.append(date_to)
            where = "WHERE " + " AND ".join(conds)
            cur.execute(
                "SELECT i.id, i.start_date, i.end_date, i.created_at, "
                "       t.enrollment_no, t.name, t.mobile, t.enrollment_type, "
                "       t.state_code, t.district_code, t.centre_code, t.area_code, "
                "       s.state_name, d.district_name, c.centre_name, a.area_name, "
                "       b.name AS batch_name "
                "FROM www_inductions i "
                "JOIN www_enrollment t ON t.id = i.trainee_id "
                "LEFT JOIN central_states    s ON s.state_code    = t.state_code "
                "LEFT JOIN central_districts d ON d.district_code = t.district_code "
                "LEFT JOIN central_centres   c ON c.centre_code   = t.centre_code "
                "LEFT JOIN www_areas     a ON a.area_code     = t.area_code "
                "LEFT JOIN www_master_batches b ON b.id = t.batch_id " +
                where + " ORDER BY i.created_at DESC",
                params,
            )
            rows = cur.fetchall()

    def _g(r, k):
        v = r.get(k)
        return "" if v is None else v

    def _days(r):
        # The import already stores the duration; only fall back to deriving
        # it when that column is absent (normalized branch) or blank.
        stored = r.get("duration_days")
        if stored not in (None, ""):
            return stored
        a, b = r.get("start_date"), r.get("end_date")
        try:
            if a and b:
                return (b - a).days + 1
        except Exception:
            pass
        return ""

    trainee_headers = [
        "Enrollment No.", "Name", "Mobile", "Enrollment Type",
        "State", "District", "Centre", "Area", "Batch",
    ]
    ind_headers = ["Start Date", "End Date", "Duration (Days)"]
    system_headers = ["Created At"]
    all_headers = trainee_headers + ind_headers + system_headers

    n_t, n_i, n_s = len(trainee_headers), len(ind_headers), len(system_headers)
    group_headers = [
        (1, n_t, "Trainee Details"),
        (n_t + 1, n_t + n_i, "Induction Details"),
        (n_t + n_i + 1, n_t + n_i + n_s, "System"),
    ]

    data_rows = []
    for r in rows:
        data_rows.append([
            _g(r, "enrollment_no"), _g(r, "name"), _g(r, "mobile"), _g(r, "enrollment_type"),
            _g(r, "state_name") or _g(r, "state_code"),
            _g(r, "district_name") or _g(r, "district_code"),
            _g(r, "centre_name") or _g(r, "centre_code"),
            _g(r, "area_name") or _g(r, "area_code"),
            _g(r, "batch_name"),
            _g(r, "start_date"), _g(r, "end_date"), _days(r),
            _g(r, "created_at"),
        ])

    # 2026-08-26: WWW tracking columns (Created By / Updated By / Updated At)
    from routes._www_export_tracking import WWW_TRACK_HEADERS as _WT_H, www_tracking_cells as _wt_cells
    all_headers = list(all_headers) + _WT_H
    # 2026-09-19: Record Info banner over Created By + Updated By.
    group_headers = list(group_headers) + [(len(all_headers) - len(_WT_H) + 1, len(all_headers), "Record Info")]
    _wt_rows = _wt_cells(rows, "mis_azad.www_induction", "id")
    for _wi in range(len(data_rows)):
        data_rows[_wi] = list(data_rows[_wi]) + (_wt_rows[_wi] if _wi < len(_wt_rows) else ["", ""])
    sheets = [{
        "name": "Inductions",
        "group_headers": group_headers,
        "headers": all_headers,
        "rows": data_rows,
    }]
    return multi_sheet_xlsx_response_v2(
        sheets,
        f"WWW_Inductions_{_d.today().isoformat()}.xlsx",
    )
