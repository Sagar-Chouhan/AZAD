"""WWW External Sakha.

Without the normalized www_external_sakha table the routes read
mis_azad.www_sakha_external, the spreadsheet import.  That is a
dedicated external-sakha table, so unlike the older fallback — which
scraped pass dates off the 4-wheeler employment sheet — every field
including the fail reasons and transfer date has a real home.
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

router = APIRouter(prefix="/api/www-external-sakha", tags=["WWW External Sakha"])


def _legacy_row_select():
    """SELECT list mapping a www_sakha_external row onto API field names."""
    return (
        "SELECT s.id, s.enrollment_id AS trainee_id, "
        # 2026-08-17: wahi TEXT 'Yes'/'No' wala mamla jo internal me tha.
        "       CASE LOWER(TRIM(COALESCE(s.have_the_trainee_passed_the_external_test, ''))) WHEN 'yes' THEN TRUE WHEN 'true' THEN TRUE WHEN '1' THEN TRUE WHEN 'no' THEN FALSE WHEN 'false' THEN FALSE WHEN '0' THEN FALSE ELSE NULL END "
        "           AS passed_external, "
        "       s.if_yes_date_of_external_sakha_pass AS external_pass_date, "
        "       s.no_of_attempts_to_clear_external_sakha_test AS external_attempts, "
        "       NULLIF(TRIM(s.if_no_reason), '') AS fail_reason, "
        "       NULLIF(TRIM(s.specify_if_any_other), '') AS fail_reason_other, "
        "       s.duration_in_months AS duration_months, "
        "       s.date_of_transfer_to_sakha, "
        "       COALESCE(s.is_draft, false) AS is_draft, "
        "       s.created_at, "
        "       " + _legacy.enroll_no() + ", s.name, "
        # 2026-08-18: mobile placeholder tha, isliye View par hamesha
        # "--" dikhta tha. _te = www_enrollment (trainee_join).
        "       NULLIF(TRIM(_te.mobile), '') AS mobile, "
        "       " + _legacy.geo_cols() + ", "
        "       s.date_of_joining, COALESCE(NULLIF(TRIM(_te.type_of_enrollment), ''), NULLIF(TRIM(s.type_of_enrollment), '')) AS enrollment_type, "
        # batch module ka apna, khali ho to enrollment wala.
        "       COALESCE(NULLIF(TRIM(_te.batch), ''), NULLIF(TRIM(s.batch_number), '')) AS batch_name, NULL::int AS batch_id, "
        + _legacy.trainee_status("s") +
        "FROM mis_azad.www_sakha_external s " + _legacy.geo_joins("s")
        + _legacy.trainee_join("s")
    )


def _legacy_filters(passed, name, batch_id, date_from, date_to):
    """WHERE clause + params shared by the legacy list and export paths."""
    conds = ["NULLIF(TRIM(s.name), '') IS NOT NULL", "s.deleted_at IS NULL"]
    params = []
    if passed == "yes":
        conds.append("LOWER(TRIM(s.have_the_trainee_passed_the_external_test)) = 'yes'")
    if passed == "no":
        conds.append("LOWER(TRIM(s.have_the_trainee_passed_the_external_test)) = 'no'")
    if name:      conds.append("(" + _legacy.name_match("s.name") + " OR _te.enrollment_no ILIKE %s)");                          params.append(_legacy.name_pattern(name)); params.append(_legacy.name_pattern(name))
    if date_from: conds.append("s.if_yes_date_of_external_sakha_pass >= %s"); params.append(date_from)
    if date_to:   conds.append("s.if_yes_date_of_external_sakha_pass <= %s"); params.append(date_to)
    if batch_id:
        conds.append("NULLIF(TRIM(s.batch_number), '') = "
                     "(SELECT name FROM mis_azad.www_master_batches WHERE id = %s)")
        params.append(batch_id)
    return "WHERE " + " AND ".join(conds), params


# API field -> www_sakha_external column, for the legacy write path.
# is_draft has no home on the import table and is dropped.
_LEGACY_UPDATE_MAP = {
    "passed_external":           "have_the_trainee_passed_the_external_test",
    "external_pass_date":        "if_yes_date_of_external_sakha_pass",
    "external_attempts":         "no_of_attempts_to_clear_external_sakha_test",
    "fail_reason":               "if_no_reason",
    "fail_reason_other":         "specify_if_any_other",
    "duration_months":           "duration_in_months",
    "date_of_transfer_to_sakha": "date_of_transfer_to_sakha",
    "is_draft":                  "is_draft",
}


class ESCreate(BaseModel):
    trainee_id: int
    passed_external: Optional[bool] = None
    external_pass_date: Optional[date] = None
    external_attempts: Optional[int] = None
    fail_reason: Optional[str] = None
    fail_reason_other: Optional[str] = None
    duration_months: Optional[int] = None
    date_of_transfer_to_sakha: Optional[date] = None
    is_draft: Optional[bool] = False


class ESUpdate(BaseModel):
    passed_external: Optional[bool] = None
    external_pass_date: Optional[date] = None
    external_attempts: Optional[int] = None
    fail_reason: Optional[str] = None
    fail_reason_other: Optional[str] = None
    duration_months: Optional[int] = None
    date_of_transfer_to_sakha: Optional[date] = None
    is_draft: Optional[bool] = None


def _row_select():
    return (
        "SELECT s.*, "
        "       t.enrollment_no, t.name, t.mobile, t.state_code, t.district_code, t.centre_code, "
        "       t.enrollment_date AS date_of_joining, t.enrollment_type, "
        "       COALESCE(b.name, NULL) AS batch_name, b.id AS batch_id "
        "FROM www_external_sakha s "
        "JOIN www_enrollment t ON t.id = s.trainee_id "
        "LEFT JOIN www_master_batches b ON b.id = t.batch_id "
    )


@router.get("")
def list_es(
    request: Request,
    enrollment_id: Optional[int] = None,
    passed: Optional[str] = None,
    name: Optional[str] = None,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort_by: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
):
    page = max(page, 1); limit = max(limit, 1); offset = (page - 1) * limit
    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        # ---- LEGACY FALLBACK: www_external_sakha absent -> www_sakha_external ----
        if not _legacy.table_exists(cur, "www_external_sakha"):
            lwhere, lparams = _legacy_filters(passed, name, batch_id, date_from, date_to)
            # 2026-08-12: same gap as the internal-sakha list — the export
            # honoured state/centre, the list silently ignored them.
            if centre_code:
                lwhere += " AND " + _legacy.centre_filter("s"); lparams.append(centre_code)
            if state_code:
                lwhere += " AND " + _legacy.state_filter(); lparams.append(state_code)
            if district_code:
                lwhere += " AND " + _legacy.district_filter(); lparams.append(district_code)
            if enrollment_id:
                lwhere += " AND s.enrollment_id = %s"; lparams.append(enrollment_id)
            cur.execute(
                "SELECT COUNT(*) AS total FROM mis_azad.www_sakha_external s "
                + _legacy.geo_joins("s") + _legacy.trainee_join("s") + lwhere,
                lparams,
            )
            total = cur.fetchone()["total"]
            cur.execute(
                _legacy_row_select() + lwhere +
                " ORDER BY " + www_list_order(sort_by, "s.name", "s.created_at", "s.created_at DESC NULLS LAST, s.id DESC", date_col="s.if_yes_date_of_external_sakha_pass") +
                " LIMIT %s OFFSET %s",
                lparams + [limit, offset],
            )
            rows = cur.fetchall()
            return {"total": total, "page": page, "limit": limit, "data": rows}

        conds = ["s.deleted_at IS NULL"]; params = []
        if passed == "yes": conds.append("s.passed_external = TRUE")
        if passed == "no":  conds.append("s.passed_external = FALSE")
        if name:            conds.append(_legacy.name_match("t.name"));           params.append(_legacy.name_pattern(name))
        if state_code:      conds.append("t.state_code = %s");         params.append(state_code)
        if district_code:   conds.append("t.district_code = %s");      params.append(district_code)
        if centre_code:     conds.append("t.centre_code = %s");        params.append(centre_code)
        if batch_id:        conds.append("t.batch_id = %s");           params.append(batch_id)
        if date_from:       conds.append("s.external_pass_date >= %s"); params.append(date_from)
        if date_to:         conds.append("s.external_pass_date <= %s"); params.append(date_to)
        where = "WHERE " + " AND ".join(conds)
        cur.execute(
            "SELECT COUNT(*) AS total FROM www_external_sakha s "
            "JOIN www_enrollment t ON t.id = s.trainee_id " + where,
            params,
        )
        total = cur.fetchone()["total"]
        sql = _row_select() + where + " ORDER BY " + www_list_order(sort_by, "s.name", "s.created_at", "s.created_at DESC NULLS LAST, s.id DESC", date_col="s.if_yes_date_of_external_sakha_pass") + " LIMIT %s OFFSET %s"
        cur.execute(sql, params + [limit, offset])
        rows = cur.fetchall()
        return {"total": total, "page": page, "limit": limit, "data": rows}


@router.get("/{es_id}")
def get_es(request: Request, es_id: int):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_external_sakha"):
            cur.execute(_legacy_row_select() + "WHERE s.id = %s", (es_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "External Sakha record not found.")
            _scope.guard_detail(request, row)
            return row

        cur.execute(_row_select() + "WHERE s.id = %s AND s.deleted_at IS NULL", (es_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "External Sakha record not found.")
    _scope.guard_detail(request, row)
    return row


@router.post("")
def create_es(body: ESCreate):
    with get_cursor() as cur:
        # 2026-08-18 (Ashish): flow guard -- picker ki rok server par bhi.
        _legacy.assert_flow(cur, body.trainee_id, stage="External Sakha")
        if not _legacy.table_exists(cur, "www_external_sakha"):
            cur.execute(
                "INSERT INTO mis_azad.www_sakha_external "
                "    (enrollment_id, name, type_of_enrollment, "
                "     state, district, centre, batch_number, date_of_joining, "
                "     have_the_trainee_passed_the_external_test, "
                "     if_yes_date_of_external_sakha_pass, "
                "     no_of_attempts_to_clear_external_sakha_test, "
                "     if_no_reason, specify_if_any_other, duration_in_months, "
                "     date_of_transfer_to_sakha, is_draft) "
                "SELECT e.id, e.name, e.type_of_enrollment, "
                "       e.state, e.district, e.centre, e.batch, e.enrollment_date, "
                "       %s, %s, %s, %s, %s, %s, %s, %s "
                "FROM mis_azad.www_enrollment e WHERE e.id = %s "
                "RETURNING id",
                (None if body.passed_external is None else ("Yes" if body.passed_external else "No"),
                 body.external_pass_date, body.external_attempts,
                 body.fail_reason, body.fail_reason_other, body.duration_months,
                 body.date_of_transfer_to_sakha, bool(body.is_draft), body.trainee_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Trainee not found.")
            return {"id": row["id"], "ok": True}

        cur.execute("SELECT 1 FROM www_enrollment WHERE id=%s", (body.trainee_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Trainee not found.")
        cur.execute(
            "INSERT INTO www_external_sakha (trainee_id, passed_external, external_pass_date, "
            "external_attempts, fail_reason, fail_reason_other, duration_months, "
            "date_of_transfer_to_sakha, is_draft) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (body.trainee_id, body.passed_external, body.external_pass_date,
             body.external_attempts, body.fail_reason, body.fail_reason_other,
             body.duration_months, body.date_of_transfer_to_sakha, bool(body.is_draft)),
        )
        new_id = cur.fetchone()["id"]
    return {"id": new_id, "ok": True}


@router.put("/{es_id}")
def update_es(es_id: int, body: ESUpdate):
    payload = body.model_dump(exclude_unset=True)
    if not payload: return {"ok": True}
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_external_sakha"):
            lfields, lparams = [], []
            for k, v in payload.items():
                col = _LEGACY_UPDATE_MAP.get(k)
                if not col:
                    continue
                if k == "passed_external" and v is not None:
                    v = "Yes" if v else "No"
                lfields.append(f"{col} = %s"); lparams.append(v)
            if not lfields:
                return {"ok": True}
            lparams.append(es_id)
            cur.execute("UPDATE mis_azad.www_sakha_external SET " + ",".join(lfields) +
                        " WHERE id = %s", lparams)
            if cur.rowcount == 0:
                raise HTTPException(404, "External Sakha record not found.")
            return {"ok": True}

        fields = []; params = []
        for k, v in payload.items():
            fields.append(f"{k} = %s"); params.append(v)
        params.append(es_id)
        cur.execute("UPDATE www_external_sakha SET " + ",".join(fields) +
                    " WHERE id = %s AND deleted_at IS NULL", params)
        if cur.rowcount == 0:
            raise HTTPException(404, "External Sakha record not found.")
    return {"ok": True}


@router.delete("/{es_id}")
def delete_es(es_id: int):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_external_sakha"):
            # 2026-08-19 (Ashish): pehle ye row ko HAMESHA ke liye mita deta tha.
            # Ab deleted_at bhar dete hain -- row DB me bachi rehti hai, bas har
            # list se hat jati hai. Wapas laani ho to deleted_at = NULL.
            cur.execute("UPDATE mis_azad.www_sakha_external SET deleted_at = NOW() "
                        "WHERE id = %s AND deleted_at IS NULL", (es_id,))
        else:
            cur.execute("UPDATE www_external_sakha SET deleted_at = now() WHERE id=%s AND deleted_at IS NULL", (es_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "External Sakha record not found.")
    return {"ok": True}


# =============================================================================
# EXPORT (Excel) — 2026-08-08
# Section-wise xlsx: Trainee Details + External Sakha Details + System.
# Date filter uses external_pass_date.
# =============================================================================
@router.get("/export/excel")
def export_es_excel(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    enrollment_type: Optional[str] = None,
    passed: Optional[str] = None,
    name: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    from datetime import date as _d
    from export_helper import multi_sheet_xlsx_response_v2

    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        has_table = _legacy.table_exists(cur, "www_external_sakha")

        if not has_table:
            lwhere, lparams = _legacy_filters(passed, name, batch_id, date_from, date_to)
            if centre_code:
                lwhere += " AND " + _legacy.centre_filter("s"); lparams.append(centre_code)
            if state_code:
                lwhere += " AND " + _legacy.state_filter(); lparams.append(state_code)
            if district_code:
                lwhere += " AND " + _legacy.district_filter(); lparams.append(district_code)
            if enrollment_type:
                lwhere += " AND s.type_of_enrollment = %s"; lparams.append(enrollment_type)
            cur.execute(
                "SELECT " + _legacy.enroll_no() + ", s.id AS id, s.name, "
                "       NULLIF(TRIM(_te.mobile), '') AS mobile, "
                "       COALESCE(NULLIF(TRIM(_te.type_of_enrollment), ''), NULLIF(TRIM(s.type_of_enrollment), '')) AS enrollment_type, "
                "       s.state AS state_name, s.district AS district_name, "
                "       " + _legacy.centre_expr("s.centre") + " AS centre_name, "
                "       NULL::text AS area_name, "
                "       COALESCE(NULLIF(TRIM(_te.batch), ''), NULLIF(TRIM(s.batch_number), '')) AS batch_name, "
                # 2026-08-12: the joining date, the LL/PL block and the
                # internal-test result all sit on www_sakha_external and were
                # never selected, so the export started at the external test.
                "       s.date_of_joining, "
                "       NULLIF(TRIM(s.date_of_ll), '') AS date_of_ll, "
                "       NULLIF(TRIM(s.ll_number), '') AS ll_number, "
                "       s.attempts_taken_to_clear_ll AS ll_attempts, "
                "       s.date_of_pl, "
                "       NULLIF(TRIM(s.pl_number), '') AS pl_number, "
                "       s.attempts_taken_to_clear_pl AS pl_attempts, "
                "       s.if_yes_date_of_internal_sakha_pass AS internal_pass_date, "
                "       s.no_of_attempts_to_clear_internal_sakha_test AS internal_attempts, "
                "       NULLIF(TRIM(s.have_the_trainee_passed_the_external_test), '') "
                "           AS passed_external, "
                "       s.if_yes_date_of_external_sakha_pass AS external_pass_date, "
                "       s.no_of_attempts_to_clear_external_sakha_test AS external_attempts, "
                "       NULLIF(TRIM(s.if_no_reason), '') AS fail_reason, "
                "       NULLIF(TRIM(s.specify_if_any_other), '') AS fail_reason_other, "
                "       s.duration_in_months AS duration_months, "
                "       s.date_of_transfer_to_sakha, "
                "       NULL::timestamptz AS created_at "
                "FROM mis_azad.www_sakha_external s " + _legacy.geo_joins("s") +
                _legacy.trainee_join("s") + lwhere +
                " ORDER BY s.if_yes_date_of_external_sakha_pass DESC NULLS LAST, s.id DESC",
                lparams,
            )
            rows = cur.fetchall()
        else:
            conds = ["s.deleted_at IS NULL"]; params = []
            if state_code:      conds.append("t.state_code = %s");      params.append(state_code)
            if centre_code:     conds.append("t.centre_code = %s");     params.append(centre_code)
            if batch_id:        conds.append("t.batch_id = %s");        params.append(batch_id)
            if enrollment_type: conds.append("t.enrollment_type = %s"); params.append(enrollment_type)
            if passed == "yes": conds.append("s.passed_external = TRUE")
            if passed == "no":  conds.append("s.passed_external = FALSE")
            if name:            conds.append(_legacy.name_match("t.name"));        params.append(_legacy.name_pattern(name))
            if date_from:       conds.append("s.external_pass_date >= %s"); params.append(date_from)
            if date_to:         conds.append("s.external_pass_date <= %s"); params.append(date_to)
            where = "WHERE " + " AND ".join(conds)
            cur.execute(
                "SELECT s.id AS id, s.passed_external, s.external_pass_date, s.external_attempts, "
                "       s.fail_reason, s.fail_reason_other, s.duration_months, "
                "       s.date_of_transfer_to_sakha, s.created_at, "
                "       t.enrollment_no, t.name, t.mobile, t.enrollment_type, "
                "       t.state_code, t.district_code, t.centre_code, t.area_code, "
                "       st.state_name, di.district_name, ce.centre_name, ar.area_name, "
                "       b.name AS batch_name "
                "FROM www_external_sakha s "
                "JOIN www_enrollment t ON t.id = s.trainee_id "
                "LEFT JOIN central_states    st ON st.state_code    = t.state_code "
                "LEFT JOIN central_districts di ON di.district_code = t.district_code "
                "LEFT JOIN central_centres   ce ON ce.centre_code   = t.centre_code "
                "LEFT JOIN www_areas     ar ON ar.area_code     = t.area_code "
                "LEFT JOIN www_master_batches b ON b.id = t.batch_id " +
                where + " ORDER BY s.created_at DESC",
                params,
            )
            rows = cur.fetchall()

    def _g(r, k):
        v = r.get(k)
        return "" if v is None else v

    def _yn(v):
        if v is None or v == "":
            return ""
        if isinstance(v, bool):
            return "Yes" if v else "No"
        return str(v)

    trainee_headers = [
        "Enrollment No.", "Name", "Mobile", "Enrollment Type",
        "State", "District", "Centre", "Area", "Batch",
        "Date of Joining",
    ]
    licence_headers = [
        "Date of LL", "LL Number", "LL Attempts",
        "Date of PL", "PL Number", "PL Attempts",
        "Internal Sakha Pass Date", "Internal Sakha Attempts",
    ]
    es_headers = [
        "Passed External", "External Pass Date", "External Attempts",
        "Fail Reason", "Fail Reason Other", "Duration (Months)",
        "Date of Transfer to Sakha",
    ]
    system_headers = ["Created At"]
    all_headers = trainee_headers + licence_headers + es_headers + system_headers
    n_t, n_l, n_e, n_s = (len(trainee_headers), len(licence_headers),
                          len(es_headers), len(system_headers))
    group_headers = [
        (1, n_t, "Trainee Details"),
        (n_t + 1, n_t + n_l, "License & Internal Test"),
        (n_t + n_l + 1, n_t + n_l + n_e, "External Sakha Details"),
        (n_t + n_l + n_e + 1, n_t + n_l + n_e + n_s, "System"),
    ]

    data_rows = []
    for r in rows:
        data_rows.append([
            _g(r, "enrollment_no"), _g(r, "name"), _g(r, "mobile"), _g(r, "enrollment_type"),
            _g(r, "state_name") or _g(r, "state_code"),
            _g(r, "district_name") or _g(r, "district_code"),
            _g(r, "centre_name") or _g(r, "centre_code"),
            _g(r, "area_name") or _g(r, "area_code"),
            _g(r, "batch_name"), _g(r, "date_of_joining"),
            _g(r, "date_of_ll"), _g(r, "ll_number"), _g(r, "ll_attempts"),
            _g(r, "date_of_pl"), _g(r, "pl_number"), _g(r, "pl_attempts"),
            _g(r, "internal_pass_date"), _g(r, "internal_attempts"),
            _yn(r.get("passed_external")), _g(r, "external_pass_date"),
            _g(r, "external_attempts"),
            _g(r, "fail_reason"), _g(r, "fail_reason_other"),
            _g(r, "duration_months"), _g(r, "date_of_transfer_to_sakha"),
            _g(r, "created_at"),
        ])

    # 2026-08-26: WWW tracking columns (Created By / Updated By / Updated At)
    from routes._www_export_tracking import WWW_TRACK_HEADERS as _WT_H, www_tracking_cells as _wt_cells
    all_headers = list(all_headers) + _WT_H
    # 2026-09-19: Record Info banner over Created By + Updated By.
    group_headers = list(group_headers) + [(len(all_headers) - len(_WT_H) + 1, len(all_headers), "Record Info")]
    _wt_rows = _wt_cells(rows, "mis_azad.www_sakha_external", "id")
    for _wi in range(len(data_rows)):
        data_rows[_wi] = list(data_rows[_wi]) + (_wt_rows[_wi] if _wi < len(_wt_rows) else ["", ""])
    sheets = [{
        "name": "External Sakha",
        "group_headers": group_headers,
        "headers": all_headers,
        "rows": data_rows,
    }]
    return multi_sheet_xlsx_response_v2(
        sheets,
        f"WWW_External_Sakha_{_d.today().isoformat()}.xlsx",
    )
