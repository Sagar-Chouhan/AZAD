"""WWW Permanent License (the actual PL — separate from PL Stories).

Without the normalized www_permanent_licenses table the routes read
mis_azad.www_pl, the spreadsheet import.  www_pl holds a single renewal
inline (date_of_renewal / new_pl_number), which the renewals endpoint
surfaces as one row.  It has no mobile column, so that field comes back
null in the legacy path.
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

router = APIRouter(prefix="/api/www-permanent-licenses", tags=["WWW Permanent License"])


def _legacy_row_select():
    """SELECT list mapping a www_pl row onto the API's field names."""
    return (
        "SELECT p.id, p.enrollment_id AS trainee_id, "
        "       p.date_of_pl, p.pl_number, "
        "       p.duration_in_days AS duration_days, "
        "       p.attempts_taken_to_clear_pl AS attempts_taken, "
        "       p.reason_for_delay, "
        "       p.created_at, "
        # 2026-08-12: www_pl carries no mobile column, so this was hardcoded
        # NULL and the Mobile box on the PL view/edit screen was always blank.
        # The enrollment this row already joins to has the number.
        "       " + _legacy.enroll_no() + ", p.name, _te.mobile, "
        "       COALESCE(NULLIF(TRIM(_te.type_of_enrollment), ''), NULLIF(TRIM(p.type_of_enrollment), '')) AS enrollment_type, "
        "       p.date_of_birth, p.date_of_joining, "
        "       " + _legacy.geo_cols() + ", "
        "       COALESCE(NULLIF(TRIM(_te.batch), ''), NULLIF(TRIM(p.batch_number), '')) AS batch_name, "
        "       NULL::int AS batch_id, "
        + _legacy.trainee_status("p") +
        "FROM mis_azad.www_pl p " + _legacy.geo_joins("p") + _legacy.trainee_join("p")
    )


def _legacy_filters(state_code, centre_code, batch_id, enrollment_type,
                    name, date_from=None, date_to=None, district_code=None):
    """WHERE clause + params shared by the legacy list and export paths."""
    # 2026-09-15: was ["p.date_of_pl IS NOT NULL", "p.deleted_at IS NULL"] which
    # hid 147 real PL records that simply have no date_of_pl entered yet.
    conds = ["p.deleted_at IS NULL"]
    params = []
    if state_code:      conds.append(_legacy.state_filter());      params.append(state_code)
    if district_code:   conds.append(_legacy.district_filter());   params.append(district_code)
    if centre_code:     conds.append(_legacy.centre_filter("p"));  params.append(centre_code)
    if enrollment_type: conds.append("p.type_of_enrollment = %s"); params.append(enrollment_type)
    if name:            conds.append("(" + _legacy.name_match("p.name") + " OR _te.enrollment_no ILIKE %s)");           params.append(_legacy.name_pattern(name)); params.append(_legacy.name_pattern(name))
    if date_from:       conds.append("p.date_of_pl >= %s");        params.append(date_from)
    if date_to:         conds.append("p.date_of_pl <= %s");        params.append(date_to)
    if batch_id:
        conds.append("NULLIF(TRIM(p.batch_number), '') = "
                     "(SELECT name FROM mis_azad.www_master_batches WHERE id = %s)")
        params.append(batch_id)
    return "WHERE " + " AND ".join(conds), params


# API field -> www_pl column.  Same set the PLUpdate model exposes.
_LEGACY_UPDATE_MAP = {
    "date_of_pl":     "date_of_pl",
    "pl_number":      "pl_number",
    "duration_days":  "duration_in_days",
    "attempts_taken": "attempts_taken_to_clear_pl",
    "reason_for_delay": "reason_for_delay",
}


class PLCreate(BaseModel):
    trainee_id: int
    date_of_pl: date
    pl_number: str
    duration_days: Optional[int] = None
    attempts_taken: Optional[int] = None
    reason_for_delay: Optional[str] = None


class PLUpdate(BaseModel):
    date_of_pl: Optional[date] = None
    pl_number: Optional[str] = None
    duration_days: Optional[int] = None
    attempts_taken: Optional[int] = None
    reason_for_delay: Optional[str] = None


class RenewalCreate(BaseModel):
    renewal_date: date
    new_pl_number: str
    attempts_taken: Optional[int] = None


def _row_select():
    return (
        "SELECT p.id, p.trainee_id, p.date_of_pl, p.pl_number, p.duration_days, p.attempts_taken, p.created_at, "
        "       t.enrollment_no, t.name, t.mobile, t.enrollment_type, t.date_of_birth, t.enrollment_date AS date_of_joining, "
        "       t.state_code, t.district_code, t.centre_code, d.district_name, "
        "       COALESCE(b.name, NULL) AS batch_name, b.id AS batch_id "
        "FROM www_permanent_licenses p "
        "JOIN www_enrollment t ON t.id = p.trainee_id "
        "LEFT JOIN www_master_batches b ON b.id = t.batch_id "
        "LEFT JOIN central_districts d ON d.district_code = t.district_code "
    )


@router.get("")
def list_pl(
    request: Request,
    enrollment_id: Optional[int] = None,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    enrollment_type: Optional[str] = None,
    name: Optional[str] = None,
    sort_by: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
):
    page = max(page, 1); limit = max(limit, 1); offset = (page - 1) * limit
    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        # ---- LEGACY FALLBACK: www_permanent_licenses absent -> read www_pl ----
        if not _legacy.table_exists(cur, "www_permanent_licenses"):
            lwhere, lparams = _legacy_filters(
                state_code, centre_code, batch_id, enrollment_type, name, district_code=district_code)
            if enrollment_id:
                lwhere += " AND p.enrollment_id = %s"; lparams.append(enrollment_id)
            _df = request.query_params.get("date_from"); _dt = request.query_params.get("date_to")
            if _df: lwhere += " AND p.date_of_pl >= %s"; lparams.append(_df)
            if _dt: lwhere += " AND p.date_of_pl <= %s"; lparams.append(_dt)
            cur.execute(
                "SELECT COUNT(*) AS total FROM mis_azad.www_pl p "
                + _legacy.geo_joins("p") + _legacy.trainee_join("p") + lwhere,
                lparams,
            )
            total = cur.fetchone()["total"]
            cur.execute(
                _legacy_row_select() + lwhere +
                " ORDER BY " + www_list_order(sort_by, "p.name", "p.created_at", "p.created_at DESC NULLS LAST, p.id DESC", date_col="p.date_of_pl") + " LIMIT %s OFFSET %s",
                lparams + [limit, offset],
            )
            rows = cur.fetchall()
            return {"total": total, "page": page, "limit": limit, "data": rows}

        conds = ["p.deleted_at IS NULL"]; params = []
        if state_code:      conds.append("t.state_code = %s");      params.append(state_code)
        if district_code:   conds.append("t.district_code = %s");   params.append(district_code)
        if centre_code:     conds.append("t.centre_code = %s");     params.append(centre_code)
        if batch_id:        conds.append("t.batch_id = %s");        params.append(batch_id)
        if enrollment_type: conds.append("t.enrollment_type = %s"); params.append(enrollment_type)
        if name:            conds.append(_legacy.name_match("t.name"));        params.append(_legacy.name_pattern(name))
        where = "WHERE " + " AND ".join(conds)
        cur.execute(
            "SELECT COUNT(*) AS total FROM www_permanent_licenses p "
            "JOIN www_enrollment t ON t.id = p.trainee_id " + where,
            params,
        )
        total = cur.fetchone()["total"]
        sql = _row_select() + where + " ORDER BY " + www_list_order(sort_by, "p.name", "p.created_at", "p.created_at DESC NULLS LAST, p.id DESC", date_col="p.date_of_pl") + " LIMIT %s OFFSET %s"
        cur.execute(sql, params + [limit, offset])
        rows = cur.fetchall()
        return {"total": total, "page": page, "limit": limit, "data": rows}


@router.get("/{pl_id}")
def get_pl(request: Request, pl_id: int):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_permanent_licenses"):
            cur.execute(_legacy_row_select() + "WHERE p.id = %s", (pl_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Permanent License not found.")
            _scope.guard_detail(request, row)
            return row

        cur.execute(_row_select() + "WHERE p.id = %s AND p.deleted_at IS NULL", (pl_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Permanent License not found.")
    _scope.guard_detail(request, row)
    return row

@router.post("")
def create_pl(body: PLCreate):
    with get_cursor() as cur:
        # 2026-08-18 (Ashish): flow guard -- picker ki rok server par bhi.
        _legacy.assert_flow(cur, body.trainee_id, requires="ll", stage="Permanent Licence")
        if not _legacy.table_exists(cur, "www_permanent_licenses"):
            cur.execute(
                "INSERT INTO mis_azad.www_pl "
                "    (enrollment_id, name, type_of_enrollment, "
                "     state, district, centre, batch_number, date_of_birth, "
                "     date_of_pl, pl_number, duration_in_days, "
                "     attempts_taken_to_clear_pl, reason_for_delay) "
                "SELECT e.id, e.name, e.type_of_enrollment, "
                "       e.state, e.district, e.centre, e.batch, e.date_of_birth, "
                "       %s, %s, %s, %s, %s "
                "FROM mis_azad.www_enrollment e WHERE e.id = %s "
                "RETURNING id",
                (body.date_of_pl, body.pl_number, body.duration_days,
                 body.attempts_taken, body.reason_for_delay,
                 body.trainee_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Trainee not found.")
            return {"id": row["id"], "ok": True}

        cur.execute("SELECT 1 FROM www_enrollment WHERE id=%s", (body.trainee_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Trainee not found.")
        cur.execute(
            "INSERT INTO www_permanent_licenses (trainee_id, date_of_pl, pl_number, duration_days, attempts_taken, reason_for_delay) "
            "VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
            (body.trainee_id, body.date_of_pl, body.pl_number, body.duration_days,
             body.attempts_taken, body.reason_for_delay),
        )
        new_id = cur.fetchone()["id"]
    return {"id": new_id, "ok": True}


@router.put("/{pl_id}")
def update_pl(pl_id: int, body: PLUpdate):
    payload = body.model_dump(exclude_unset=True)
    if not payload:
        return {"ok": True}
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_permanent_licenses"):
            lfields, lparams = [], []
            for k, v in payload.items():
                col = _LEGACY_UPDATE_MAP.get(k)
                if col:
                    lfields.append(f"{col} = %s"); lparams.append(v)
            if not lfields:
                return {"ok": True}
            lparams.append(pl_id)
            cur.execute(
                "UPDATE mis_azad.www_pl SET " + ",".join(lfields) + " WHERE id = %s",
                lparams,
            )
            if cur.rowcount == 0:
                raise HTTPException(404, "Permanent License not found.")
            return {"ok": True}

        fields = []; params = []
        for k, v in payload.items():
            fields.append(f"{k} = %s"); params.append(v)
        params.append(pl_id)
        cur.execute("UPDATE www_permanent_licenses SET " + ",".join(fields) +
                    " WHERE id = %s AND deleted_at IS NULL", params)
        if cur.rowcount == 0:
            raise HTTPException(404, "Permanent License not found.")
    return {"ok": True}


@router.delete("/{pl_id}")
def delete_pl(pl_id: int):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_permanent_licenses"):
            # 2026-08-19 (Ashish): pehle ye row ko HAMESHA ke liye mita deta tha.
            # Ab deleted_at bhar dete hain -- row DB me bachi rehti hai, bas har
            # list se hat jati hai. Wapas laani ho to deleted_at = NULL.
            cur.execute("UPDATE mis_azad.www_pl SET deleted_at = NOW() "
                        "WHERE id = %s AND deleted_at IS NULL", (pl_id,))
        else:
            cur.execute("UPDATE www_permanent_licenses SET deleted_at = now() WHERE id=%s AND deleted_at IS NULL", (pl_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "Permanent License not found.")
    return {"ok": True}


@router.get("/{pl_id}/renewals")
def list_renewals(pl_id: int):
    with get_cursor() as cur:
        # No www_pl_renewals here, but www_pl carries one renewal inline.
        if not _legacy.table_exists(cur, "www_pl_renewals"):
            cur.execute(
                "SELECT id, date_of_renewal AS renewal_date, "
                "       NULLIF(TRIM(new_pl_number), '') AS new_pl_number, "
                "       number_of_attempts_to_clear_the_pl AS attempts_taken, "
                "       NULL::timestamptz AS created_at "
                "FROM mis_azad.www_pl WHERE id = %s "
                "  AND (date_of_renewal IS NOT NULL "
                "       OR NULLIF(TRIM(new_pl_number), '') IS NOT NULL)",
                (pl_id,),
            )
            rows = cur.fetchall()
            return {"data": rows, "count": len(rows)}
        cur.execute("SELECT id, renewal_date, new_pl_number, attempts_taken, created_at FROM www_pl_renewals "
                    "WHERE pl_id = %s AND deleted_at IS NULL ORDER BY renewal_date DESC, id DESC", (pl_id,))
        rows = cur.fetchall()
    return {"data": rows, "count": len(rows)}

@router.post("/{pl_id}/renewals")
def create_renewal(pl_id: int, body: RenewalCreate):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_pl_renewals"):
            # Only one renewal fits on a www_pl row; writing a second would
            # silently overwrite the first, so refuse instead.
            cur.execute(
                "SELECT date_of_renewal, NULLIF(TRIM(new_pl_number), '') AS new_pl_number "
                "FROM mis_azad.www_pl WHERE id = %s",
                (pl_id,),
            )
            existing = cur.fetchone()
            if not existing:
                raise HTTPException(404, "Permanent License not found.")
            if existing["date_of_renewal"] or existing["new_pl_number"]:
                raise HTTPException(
                    409,
                    "This deployment stores a single PL renewal per licence and "
                    "one is already recorded. Edit the existing renewal instead.",
                )
            cur.execute(
                "UPDATE mis_azad.www_pl "
                "   SET date_of_renewal = %s, new_pl_number = %s, "
                "       number_of_attempts_to_clear_the_pl = %s "
                " WHERE id = %s",
                (body.renewal_date, body.new_pl_number, body.attempts_taken, pl_id),
            )
            return {"id": pl_id, "ok": True}

        cur.execute("SELECT 1 FROM www_permanent_licenses WHERE id=%s AND deleted_at IS NULL", (pl_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Permanent License not found.")
        cur.execute("INSERT INTO www_pl_renewals (pl_id, renewal_date, new_pl_number, attempts_taken) "
                    "VALUES (%s,%s,%s,%s) RETURNING id",
                    (pl_id, body.renewal_date, body.new_pl_number, body.attempts_taken))
        new_id = cur.fetchone()["id"]
    return {"id": new_id, "ok": True}


# =============================================================================
# EXPORT (Excel) — 2026-08-08
# Section-wise xlsx: Trainee Details + PL Details + PL Renewed Details
# (inline, floor at 3) + System. Mirrors the LL export pattern.
# =============================================================================
@router.get("/export/excel")
def export_permanent_licenses_excel(
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
        has_table = _legacy.table_exists(cur, "www_permanent_licenses")

        if not has_table:
            # ---- Legacy fallback: www_pl, with its one inline renewal ----
            where, lparams = _legacy_filters(
                state_code, centre_code, batch_id, enrollment_type,
                name, date_from, date_to, district_code=district_code)
            cur.execute(
                # 2026-08-13: the list query already reads the mobile off
                # the enrollment join (_te); the export still hardcoded
                # NULL, so the Mobile column was blank on every row.
                "SELECT p.id, " + _legacy.enroll_no() + ", p.name, _te.mobile, "
                "       COALESCE(NULLIF(TRIM(_te.type_of_enrollment), ''), NULLIF(TRIM(p.type_of_enrollment), '')) AS enrollment_type, "
                "       p.state AS state_name, p.district AS district_name, "
                "       " + _legacy.centre_expr("p.centre") + " AS centre_name, "
                "       NULL::text AS area_name, "
                "       COALESCE(NULLIF(TRIM(_te.batch), ''), NULLIF(TRIM(p.batch_number), '')) AS batch_name, "
                # 2026-08-12: www_pl also carries the trainee's status, DOB,
                # joining date and the whole LL block.  None of it was
                # selected, so the export showed the PL columns only.
                "       NULLIF(TRIM(p.status), '') AS trainee_status, "
                "       p.date_of_birth, p.date_of_joining, "
                "       p.date_of_ll, p.ll_number, "
                "       p.attempts_taken_to_clear_ll AS ll_attempts, "
                "       p.date_of_pl, p.pl_number, "
                "       p.duration_in_days AS duration_days, "
                "       p.attempts_taken_to_clear_pl AS attempts_taken, "
                "       p.reason_for_delay, "
                "       p.date_of_renewal AS renewal_date, "
                "       NULLIF(TRIM(p.new_pl_number), '') AS new_pl_number, "
                "       p.number_of_attempts_to_clear_the_pl AS renewal_attempts, "
                "       NULL::timestamptz AS created_at "
                "FROM mis_azad.www_pl p " + _legacy.geo_joins("p") +
                _legacy.trainee_join("p") + where +
                " ORDER BY p.date_of_pl DESC NULLS LAST, p.id DESC",
                lparams,
            )
            rows = cur.fetchall()
            renewal_map = {}
            for r in rows:
                if r.get("renewal_date") or r.get("new_pl_number"):
                    renewal_map[r["id"]] = [{
                        "renewal_date": r.get("renewal_date"),
                        "new_pl_number": r.get("new_pl_number"),
                        "attempts_taken": r.get("renewal_attempts"),
                    }]
        else:
            conds = ["p.deleted_at IS NULL"]
            params = []
            if state_code:      conds.append("t.state_code = %s");      params.append(state_code)
            if centre_code:     conds.append("t.centre_code = %s");     params.append(centre_code)
            if batch_id:        conds.append("t.batch_id = %s");        params.append(batch_id)
            if enrollment_type: conds.append("t.enrollment_type = %s"); params.append(enrollment_type)
            if name:            conds.append(_legacy.name_match("t.name"));        params.append(_legacy.name_pattern(name))
            if date_from:       conds.append("p.date_of_pl >= %s");     params.append(date_from)
            if date_to:         conds.append("p.date_of_pl <= %s");     params.append(date_to)
            where = "WHERE " + " AND ".join(conds)
            cur.execute(
                "SELECT p.id, p.date_of_pl, p.pl_number, p.duration_days, "
                "       p.attempts_taken, p.reason_for_delay, p.created_at, "
                "       t.enrollment_no, t.name, t.mobile, t.enrollment_type, "
                "       t.state_code, t.district_code, t.centre_code, t.area_code, "
                "       s.state_name, d.district_name, c.centre_name, a.area_name, "
                "       b.name AS batch_name "
                "FROM www_permanent_licenses p "
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

            renewal_map = {}
            cur.execute("SELECT to_regclass('mis_azad.www_pl_renewals') AS t")
            if cur.fetchone()["t"] and rows:
                ids = [r["id"] for r in rows]
                ph = ",".join(["%s"] * len(ids))
                cur.execute(
                    f"SELECT pl_id, renewal_date, new_pl_number, attempts_taken "
                    f"FROM www_pl_renewals WHERE pl_id IN ({ph}) AND deleted_at IS NULL "
                    f"ORDER BY pl_id, renewal_date, id",
                    ids,
                )
                for rn in cur.fetchall():
                    renewal_map.setdefault(rn["pl_id"], []).append(rn)

    def _g(r, k):
        v = r.get(k)
        return "" if v is None else v

    trainee_headers = [
        "Enrollment No.", "Name", "Mobile", "Enrollment Type",
        "State", "District", "Centre", "Area", "Batch",
        "Status", "Date of Birth", "Date of Joining",
    ]
    pl_headers = [
        "Date of LL", "LL Number", "LL Attempts",
        "Date of PL", "PL Number", "Duration (Days)", "Attempts Taken",
    ]
    max_renewals = max([len(v) for v in renewal_map.values()] + [3])
    renewal_headers = []
    for i in range(1, max_renewals + 1):
        renewal_headers.extend([
            f"Renewal {i} Date",
            f"Renewal {i} New PL Number",
            f"Renewal {i} Attempts",
        ])
    system_headers = ["Created At"]
    all_headers = trainee_headers + pl_headers + renewal_headers + system_headers
    n_t, n_pl, n_ren, n_sy = (
        len(trainee_headers), len(pl_headers), len(renewal_headers), len(system_headers)
    )
    group_headers = [
        (1, n_t, "Trainee Details"),
        (n_t + 1, n_t + n_pl, "Permanent License Details"),
    ]
    if n_ren > 0:
        group_headers.append((
            n_t + n_pl + 1,
            n_t + n_pl + n_ren,
            "PL Renewed Details",
        ))
    group_headers.append((
        n_t + n_pl + n_ren + 1,
        n_t + n_pl + n_ren + n_sy,
        "System",
    ))

    data_rows = []
    for r in rows:
        renewals = renewal_map.get(r.get("id"), [])
        row = [
            _g(r, "enrollment_no"), _g(r, "name"), _g(r, "mobile"), _g(r, "enrollment_type"),
            _g(r, "state_name") or _g(r, "state_code"),
            _g(r, "district_name") or _g(r, "district_code"),
            _g(r, "centre_name") or _g(r, "centre_code"),
            _g(r, "area_name") or _g(r, "area_code"),
            _g(r, "batch_name"),
            _g(r, "trainee_status"), _g(r, "date_of_birth"),
            _g(r, "date_of_joining"),
            _g(r, "date_of_ll"), _g(r, "ll_number"), _g(r, "ll_attempts"),
            _g(r, "date_of_pl"), _g(r, "pl_number"),
            _g(r, "duration_days"), _g(r, "attempts_taken"),
        ]
        for i in range(max_renewals):
            if i < len(renewals):
                rn = renewals[i]
                row.extend([
                    _g(rn, "renewal_date"),
                    _g(rn, "new_pl_number"),
                    _g(rn, "attempts_taken"),
                ])
            else:
                row.extend(["", ""])
        row.append(_g(r, "created_at"))
        data_rows.append(row)

    # 2026-08-26: WWW tracking columns (Created By / Updated By / Updated At)
    from routes._www_export_tracking import WWW_TRACK_HEADERS as _WT_H, www_tracking_cells as _wt_cells
    all_headers = list(all_headers) + _WT_H
    # 2026-09-19: Record Info banner over Created By + Updated By.
    group_headers = list(group_headers) + [(len(all_headers) - len(_WT_H) + 1, len(all_headers), "Record Info")]
    _wt_rows = _wt_cells(rows, "mis_azad.www_pl", "id")
    for _wi in range(len(data_rows)):
        data_rows[_wi] = list(data_rows[_wi]) + (_wt_rows[_wi] if _wi < len(_wt_rows) else ["", ""])
    sheets = [{
        "name": "Permanent Licenses",
        "group_headers": group_headers,
        "headers": all_headers,
        "rows": data_rows,
    }]
    return multi_sheet_xlsx_response_v2(
        sheets,
        f"WWW_Permanent_Licenses_{_d.today().isoformat()}.xlsx",
    )
