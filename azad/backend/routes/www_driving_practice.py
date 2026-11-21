"""WWW Driving Practice — list + CRUD.

Without the normalized www_driving_practices table the routes read
mis_azad.www_driving_practice, the spreadsheet import, whose columns
line up one-for-one with the API's fields.
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

router = APIRouter(prefix="/api/www-driving-practices", tags=["WWW Driving Practice"])

# 2026-08-26: DP list sort whitelist. Keys come from the frontend Sort By
# dropdown; values are safe ORDER BY fragments (never interpolate raw input).
# "Date Added" uses p.id (monotonic insertion order) so historic rows —
# which all share the tracking-migration created_at — still order sensibly.
_DP_LEGACY_SORT = {
    "name_asc":     "p.name ASC, p.id DESC",
    "name_desc":    "p.name DESC, p.id DESC",
    "added_newest": "p.created_at DESC NULLS LAST, p.id DESC",
    "added_oldest": "p.created_at ASC NULLS LAST, p.id ASC",
    "enroll_asc":   "_te.enrollment_no ASC NULLS LAST, p.id DESC",
}
_DP_LEGACY_SORT_DEFAULT = "p.ds_start_date DESC NULLS LAST, p.id DESC"
_DP_NORM_SORT = {
    "name_asc":     "t.name ASC, p.id DESC",
    "name_desc":    "t.name DESC, p.id DESC",
    "added_newest": "p.created_at DESC, p.id DESC",
    "added_oldest": "p.created_at ASC, p.id ASC",
    "enroll_asc":   "t.enrollment_no ASC NULLS LAST, p.id DESC",
}
_DP_NORM_SORT_DEFAULT = "p.created_at DESC"


def _legacy_row_select():
    """SELECT list mapping a www_driving_practice row onto API field names."""
    return (
        "SELECT p.id, p.enrollment_id AS trainee_id, "
        "       p.ds_start_date, p.ds_end_date, "
        "       p.onground_start_date, p.onground_end_date, "
        "       p.ds_duration_days, p.onground_duration_days, "
        "       p.created_at, "
        "       " + _legacy.enroll_no() + ", p.name, COALESCE(NULLIF(TRIM(_te.mobile), ''), NULLIF(TRIM(p.mobile), '')) AS mobile, COALESCE(NULLIF(TRIM(_te.type_of_enrollment), ''), NULLIF(TRIM(p.enrollment_type), '')) AS enrollment_type, "
        "       _te.enrollment_date AS date_of_joining, "
        "       " + _legacy.geo_cols() + ", "
        "       COALESCE(NULLIF(TRIM(_te.batch), ''), NULLIF(TRIM(p.batch), '')) AS batch_name, NULL::int AS batch_id "
        "FROM mis_azad.www_driving_practice p " + _legacy.geo_joins("p")
        + _legacy.trainee_join("p")
    )


def _legacy_filters(state_code, centre_code, batch_id, enrollment_type,
                    name, date_from=None, date_to=None, district_code=None):
    """WHERE clause + params shared by the legacy list and export paths."""
    conds = [
        "NULLIF(TRIM(p.name), '') IS NOT NULL",
        "(p.ds_start_date IS NOT NULL OR p.onground_start_date IS NOT NULL)",
        "p.deleted_at IS NULL",
    ]
    params = []
    if state_code:      conds.append(_legacy.state_filter());      params.append(state_code)
    if district_code:   conds.append(_legacy.district_filter());   params.append(district_code)
    if centre_code:     conds.append(_legacy.centre_filter("p"));  params.append(centre_code)
    if enrollment_type: conds.append("p.enrollment_type = %s");    params.append(enrollment_type)
    if name:
        conds.append("(" + _legacy.name_match("p.name") + " OR _te.enrollment_no ILIKE %s)")
        params.append(_legacy.name_pattern(name))
        params.append(_legacy.name_pattern(name))
    if date_from:       conds.append("p.ds_start_date >= %s");     params.append(date_from)
    if date_to:         conds.append("p.ds_end_date <= %s");       params.append(date_to)
    if batch_id:
        conds.append("NULLIF(TRIM(p.batch), '') = "
                     "(SELECT name FROM mis_azad.www_master_batches WHERE id = %s)")
        params.append(batch_id)
    return "WHERE " + " AND ".join(conds), params


class DPCreate(BaseModel):
    trainee_id: int
    ds_start_date: Optional[date] = None
    ds_end_date: Optional[date] = None
    onground_start_date: Optional[date] = None
    onground_end_date: Optional[date] = None


class DPUpdate(BaseModel):
    ds_start_date: Optional[date] = None
    ds_end_date: Optional[date] = None
    onground_start_date: Optional[date] = None
    onground_end_date: Optional[date] = None


def _row_select():
    return (
        "SELECT p.id, p.trainee_id, p.ds_start_date, p.ds_end_date, "
        "       p.onground_start_date, p.onground_end_date, p.created_at, "
        "       t.enrollment_no, t.name, t.mobile, t.enrollment_type, "
        "       t.enrollment_date AS date_of_joining, "
        "       t.state_code, t.centre_code, t.district_code, d.district_name, "
        "       COALESCE(b.name, NULL) AS batch_name, b.id AS batch_id "
        "FROM www_driving_practices p "
        "JOIN www_enrollment t ON t.id = p.trainee_id "
        "LEFT JOIN www_master_batches b ON b.id = t.batch_id "
        "LEFT JOIN central_districts d ON d.district_code = t.district_code "
    )


@router.get("")
def list_practices(
    request: Request,
    enrollment_id: Optional[int] = None,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    name: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort_by: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
):
    page = max(page, 1); limit = max(limit, 1); offset = (page - 1) * limit
    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        # ---- LEGACY FALLBACK: www_driving_practices absent -> www_driving_practice ----
        if not _legacy.table_exists(cur, "www_driving_practices"):
            lwhere, lparams = _legacy_filters(
                state_code, centre_code, batch_id, None, name, date_from, date_to, district_code=district_code)
            if enrollment_id:
                lwhere += " AND p.enrollment_id = %s"; lparams.append(enrollment_id)
            cur.execute(
                "SELECT COUNT(*) AS total FROM mis_azad.www_driving_practice p "
                + _legacy.geo_joins("p") + _legacy.trainee_join("p") + lwhere,
                lparams,
            )
            total = cur.fetchone()["total"]
            cur.execute(
                _legacy_row_select() + lwhere +
                " ORDER BY " + _DP_LEGACY_SORT.get(sort_by, _DP_LEGACY_SORT_DEFAULT) + " LIMIT %s OFFSET %s",
                lparams + [limit, offset],
            )
            rows = cur.fetchall()
            return {"total": total, "page": page, "limit": limit, "data": rows}

        conds = ["p.deleted_at IS NULL"]
        params = []
        if state_code:  conds.append("t.state_code = %s");  params.append(state_code)
        if district_code: conds.append("t.district_code = %s"); params.append(district_code)
        if centre_code: conds.append("t.centre_code = %s"); params.append(centre_code)
        if batch_id:    conds.append("t.batch_id = %s");    params.append(batch_id)
        if name:        conds.append(_legacy.name_match("t.name"));    params.append(_legacy.name_pattern(name))
        if date_from:   conds.append("p.ds_start_date >= %s"); params.append(date_from)
        if date_to:     conds.append("p.ds_end_date <= %s");   params.append(date_to)
        where = "WHERE " + " AND ".join(conds)
        cur.execute(
            "SELECT COUNT(*) AS total FROM www_driving_practices p "
            "JOIN www_enrollment t ON t.id = p.trainee_id " + where,
            params,
        )
        total = cur.fetchone()["total"]
        sql = _row_select() + where + " ORDER BY " + _DP_NORM_SORT.get(sort_by, _DP_NORM_SORT_DEFAULT) + " LIMIT %s OFFSET %s"
        cur.execute(sql, params + [limit, offset])
        rows = cur.fetchall()
        return {"total": total, "page": page, "limit": limit, "data": rows}


@router.get("/{practice_id}")
def get_practice(request: Request, practice_id: int):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_driving_practices"):
            cur.execute(_legacy_row_select() + "WHERE p.id = %s", (practice_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Driving practice record not found.")
            _scope.guard_detail(request, row)
            return row

        cur.execute(_row_select() + "WHERE p.id = %s AND p.deleted_at IS NULL", (practice_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Driving practice record not found.")
    _scope.guard_detail(request, row)
    return row


@router.post("")
def create_practice(body: DPCreate):
    if body.ds_end_date and body.ds_start_date and body.ds_end_date < body.ds_start_date:
        raise HTTPException(400, "Driving School End Date must be on or after Start Date.")
    if body.onground_end_date and body.onground_start_date and body.onground_end_date < body.onground_start_date:
        raise HTTPException(400, "Onground End Date must be on or after Start Date.")

    def _days(a, b):
        return (b - a).days + 1 if a and b else None

    with get_cursor() as cur:
        # 2026-08-18 (Ashish): flow guard -- picker ki rok server par bhi.
        _legacy.assert_flow(cur, body.trainee_id, requires="ll", stage="Driving Practice")
        if not _legacy.table_exists(cur, "www_driving_practices"):
            cur.execute(
                "INSERT INTO mis_azad.www_driving_practice "
                "    (enrollment_id, name, mobile, enrollment_type, "
                "     state, district, centre, area, batch, "
                "     ds_start_date, ds_end_date, ds_duration_days, "
                "     onground_start_date, onground_end_date, onground_duration_days) "
                "SELECT e.id, e.name, e.mobile, e.type_of_enrollment, "
                "       e.state, e.district, e.centre, e.area, e.batch, "
                "       %s, %s, %s, %s, %s, %s "
                "FROM mis_azad.www_enrollment e WHERE e.id = %s "
                "RETURNING id",
                (body.ds_start_date, body.ds_end_date,
                 _days(body.ds_start_date, body.ds_end_date),
                 body.onground_start_date, body.onground_end_date,
                 _days(body.onground_start_date, body.onground_end_date),
                 body.trainee_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Trainee not found.")
            return {"id": row["id"], "ok": True}

        cur.execute("SELECT 1 FROM www_enrollment WHERE id = %s", (body.trainee_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Trainee not found.")
        cur.execute(
            "INSERT INTO www_driving_practices "
            "(trainee_id, ds_start_date, ds_end_date, onground_start_date, onground_end_date) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (body.trainee_id, body.ds_start_date, body.ds_end_date,
             body.onground_start_date, body.onground_end_date),
        )
        new_id = cur.fetchone()["id"]
    return {"id": new_id, "ok": True}


@router.put("/{practice_id}")
def update_practice(practice_id: int, body: DPUpdate):
    payload = body.model_dump(exclude_unset=True)
    if "ds_end_date" in payload and "ds_start_date" in payload             and payload["ds_end_date"] and payload["ds_start_date"]             and payload["ds_end_date"] < payload["ds_start_date"]:
        raise HTTPException(400, "Driving School End Date must be on or after Start Date.")
    if "onground_end_date" in payload and "onground_start_date" in payload             and payload["onground_end_date"] and payload["onground_start_date"]             and payload["onground_end_date"] < payload["onground_start_date"]:
        raise HTTPException(400, "Onground End Date must be on or after Start Date.")
    fields = []
    params = []
    for k, v in payload.items():
        fields.append(f"{k} = %s"); params.append(v)
    if not fields:
        return {"ok": True}
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_driving_practices"):
            # Same column names on both sides — only the table differs.
            cur.execute(
                "UPDATE mis_azad.www_driving_practice SET " + ", ".join(fields) +
                " WHERE id = %s",
                params + [practice_id],
            )
        else:
            cur.execute(
                "UPDATE www_driving_practices SET " + ", ".join(fields) +
                " WHERE id = %s AND deleted_at IS NULL",
                params + [practice_id],
            )
        if cur.rowcount == 0:
            raise HTTPException(404, "Driving practice record not found.")
    return {"ok": True}


@router.delete("/{practice_id}")
def delete_practice(practice_id: int):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_driving_practices"):
            # 2026-08-19 (Ashish): pehle ye row ko HAMESHA ke liye mita deta tha.
            # Ab deleted_at bhar dete hain -- row DB me bachi rehti hai, bas har
            # list se hat jati hai. Wapas laani ho to deleted_at = NULL.
            cur.execute("UPDATE mis_azad.www_driving_practice SET deleted_at = NOW() "
                        "WHERE id = %s AND deleted_at IS NULL", (practice_id,))
        else:
            cur.execute(
                "UPDATE www_driving_practices SET deleted_at = now() "
                "WHERE id = %s AND deleted_at IS NULL",
                (practice_id,),
            )
        if cur.rowcount == 0:
            raise HTTPException(404, "Driving practice record not found.")
    return {"ok": True}


# =============================================================================
# EXPORT (Excel) — 2026-08-07
# Section-wise xlsx with:
#   1. Trainee Details              (Enrollment No, Name, Mobile, Type,
#                                    State, District, Centre, Area, Batch)
#   2. Driving School Practice      (DS Start, DS End, DS Duration Days)
#   3. Onground Practice            (Onground Start, Onground End, Onground
#                                    Duration Days)
#   4. System                       (Created At)
# Sends the same filters as list_practices so the export matches what's on
# screen. Legacy status_internal fallback preserved.
# =============================================================================
@router.get("/export/excel")
def export_practices_excel(
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
        has_table = _legacy.table_exists(cur, "www_driving_practices")

        if not has_table:
            where, lparams = _legacy_filters(
                state_code, centre_code, batch_id, enrollment_type,
                name, date_from, date_to, district_code=district_code)
            cur.execute(
                "SELECT " + _legacy.enroll_no() + ", p.id AS id, p.name, COALESCE(NULLIF(TRIM(_te.mobile), ''), NULLIF(TRIM(p.mobile), '')) AS mobile, COALESCE(NULLIF(TRIM(_te.type_of_enrollment), ''), NULLIF(TRIM(p.enrollment_type), '')) AS enrollment_type, "
                "       p.state AS state_name, p.district AS district_name, "
                "       " + _legacy.centre_expr("p.centre") + " AS centre_name, "
                "       COALESCE(NULLIF(TRIM(_te.area), ''), NULLIF(TRIM(p.area), '')) AS area_name, "
                "       COALESCE(NULLIF(TRIM(_te.batch), ''), NULLIF(TRIM(p.batch), '')) AS batch_name, "
                "       p.ds_start_date, p.ds_end_date, p.ds_duration_days, "
                "       p.onground_start_date, p.onground_end_date, "
                "       p.onground_duration_days, "
                "       NULL::timestamptz AS created_at "
                "FROM mis_azad.www_driving_practice p " + _legacy.geo_joins("p") +
                _legacy.trainee_join("p") + where +
                " ORDER BY p.ds_start_date DESC NULLS LAST, p.id DESC",
                lparams,
            )
            rows = cur.fetchall()
        else:
            conds = ["p.deleted_at IS NULL"]
            params = []
            if state_code:      conds.append("t.state_code = %s");        params.append(state_code)
            if centre_code:     conds.append("t.centre_code = %s");       params.append(centre_code)
            if batch_id:        conds.append("t.batch_id = %s");          params.append(batch_id)
            if enrollment_type: conds.append("t.enrollment_type = %s");   params.append(enrollment_type)
            if name:            conds.append(_legacy.name_match("t.name"));          params.append(_legacy.name_pattern(name))
            if date_from:       conds.append("p.ds_start_date >= %s");    params.append(date_from)
            if date_to:         conds.append("p.ds_end_date <= %s");      params.append(date_to)
            where = "WHERE " + " AND ".join(conds)
            cur.execute(
                "SELECT p.id, p.ds_start_date, p.ds_end_date, "
                "       p.onground_start_date, p.onground_end_date, p.created_at, "
                "       t.enrollment_no, t.name, t.mobile, t.enrollment_type, "
                "       t.state_code, t.district_code, t.centre_code, t.area_code, "
                "       s.state_name, d.district_name, c.centre_name, a.area_name, "
                "       b.name AS batch_name "
                "FROM www_driving_practices p "
                "JOIN www_enrollment t ON t.id = p.trainee_id "
                "LEFT JOIN central_states    s ON s.state_code    = t.state_code "
                "LEFT JOIN central_districts d ON d.district_code = t.district_code "
                "LEFT JOIN central_centres   c ON c.centre_code   = t.centre_code "
                "LEFT JOIN www_areas     a ON a.area_code     = t.area_code "
                "LEFT JOIN www_master_batches b ON b.id = t.batch_id " +
                where + " ORDER BY p.created_at DESC",
                params,
            )
            rows = cur.fetchall()

    def _g(r, k):
        v = r.get(k)
        return "" if v is None else v

    def _days(r, stored_key, start_key, end_key):
        # The import stores both durations; derive one only when the column
        # is absent (normalized branch) or blank.
        stored = r.get(stored_key)
        if stored not in (None, ""):
            return stored
        a, b = r.get(start_key), r.get(end_key)
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
    ds_headers      = ["DS Start Date", "DS End Date", "DS Duration (Days)"]
    onground_headers = ["Onground Start Date", "Onground End Date", "Onground Duration (Days)"]
    system_headers  = ["Created At"]
    all_headers = trainee_headers + ds_headers + onground_headers + system_headers

    n_t, n_ds, n_on, n_s = (len(trainee_headers), len(ds_headers),
                            len(onground_headers), len(system_headers))
    group_headers = [
        (1, n_t, "Trainee Details"),
        (n_t + 1, n_t + n_ds, "Driving School Practice"),
        (n_t + n_ds + 1, n_t + n_ds + n_on, "Onground Practice"),
        (n_t + n_ds + n_on + 1, n_t + n_ds + n_on + n_s, "System"),
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
            _g(r, "ds_start_date"), _g(r, "ds_end_date"),
            _days(r, "ds_duration_days", "ds_start_date", "ds_end_date"),
            _g(r, "onground_start_date"), _g(r, "onground_end_date"),
            _days(r, "onground_duration_days",
                  "onground_start_date", "onground_end_date"),
            _g(r, "created_at"),
        ])

    # 2026-08-26: WWW tracking columns (Created By / Updated By / Updated At)
    from routes._www_export_tracking import WWW_TRACK_HEADERS as _WT_H, www_tracking_cells as _wt_cells
    all_headers = list(all_headers) + _WT_H
    # 2026-09-19: Record Info banner over Created By + Updated By.
    group_headers = list(group_headers) + [(len(all_headers) - len(_WT_H) + 1, len(all_headers), "Record Info")]
    _wt_rows = _wt_cells(rows, "mis_azad.www_driving_practice", "id")
    for _wi in range(len(data_rows)):
        data_rows[_wi] = list(data_rows[_wi]) + (_wt_rows[_wi] if _wi < len(_wt_rows) else ["", ""])
    sheets = [{
        "name": "Driving Practices",
        "group_headers": group_headers,
        "headers": all_headers,
        "rows": data_rows,
    }]
    return multi_sheet_xlsx_response_v2(
        sheets,
        f"WWW_Driving_Practices_{_d.today().isoformat()}.xlsx",
    )
