"""WWW Learning License — list + create + update + soft-delete.

Backed by mis_azad.www_learning_licenses, joined with www_trainees and
www_master_batches for display.

Without that schema the routes read mis_azad.www_ll, the spreadsheet
import.  www_ll keeps a single renewal inline (date_of_renewal_of_ll /
new_ll_number), so the renewals endpoint surfaces that one row rather
than reporting none."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from datetime import date
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from routes import _www_legacy as _legacy
from routes._www_list_sort import www_list_order
from routes import _www_scope as _scope

router = APIRouter(prefix="/api/www-learning-licenses", tags=["WWW Learning License"])

# www_ll stores these two as text, mixing real dates with notes like
# "Came with LL"; everything downstream wants a real date or NULL.
_LL_DATE = _legacy.safe_date("l.date_of_ll")
_LL_RENEWAL_DATE = _legacy.safe_date("l.date_of_renewal_of_ll")


def _legacy_row_select():
    """SELECT list mapping a www_ll row onto the API's field names."""
    return (
        "SELECT l.id, l.enrollment_id AS trainee_id, "
        "       " + _LL_DATE + " AS date_of_ll, "
        "       l.ll_number, "
        "       NULLIF(TRIM(l.duration_in_days), '') AS duration_days, "
        "       l.attempts_taken_to_clear_ll AS attempts_taken, "
        "       NULLIF(TRIM(l.module_done), '') AS module_done, "
        "       l.module_start_date, l.module_end_date, "
        "       l.reason_for_delay, "
        "       l.created_at, "
        "       " + _legacy.enroll_no() + ", l.name, "
        "       COALESCE(NULLIF(TRIM(_te.mobile), ''), NULLIF(TRIM(l.mobile_number), '')) AS mobile, "
        "       COALESCE(NULLIF(TRIM(_te.type_of_enrollment), ''), NULLIF(TRIM(l.type_of_enrollment), '')) AS enrollment_type, "
        "       " + _legacy.geo_cols() + ", "
        "       COALESCE(NULLIF(TRIM(_te.batch), ''), NULLIF(TRIM(l.batch_number), '')) AS batch_name, "
        "       NULL::int AS batch_id "
        "FROM mis_azad.www_ll l " + _legacy.geo_joins("l") + _legacy.trainee_join("l")
    )


def _legacy_filters(state_code, centre_code, batch_id, enrollment_type,
                    name, date_from, date_to, district_code=None):
    """WHERE clause + params shared by the legacy list and export paths."""
    conds = ["NULLIF(TRIM(l.name), '') IS NOT NULL", "l.deleted_at IS NULL"]
    params = []
    if state_code:      conds.append(_legacy.state_filter());     params.append(state_code)
    if district_code:   conds.append(_legacy.district_filter());  params.append(district_code)
    if centre_code:     conds.append(_legacy.centre_filter("l")); params.append(centre_code)
    if enrollment_type: conds.append("l.type_of_enrollment = %s"); params.append(enrollment_type)
    if name:            conds.append("(" + _legacy.name_match("l.name") + " OR _te.enrollment_no ILIKE %s)");           params.append(_legacy.name_pattern(name)); params.append(_legacy.name_pattern(name))
    if date_from:       conds.append(_LL_DATE + " >= %s");         params.append(date_from)
    if date_to:         conds.append(_LL_DATE + " <= %s");         params.append(date_to)
    if batch_id:
        conds.append("NULLIF(TRIM(l.batch_number), '') = "
                     "(SELECT name FROM mis_azad.www_master_batches WHERE id = %s)")
        params.append(batch_id)
    return "WHERE " + " AND ".join(conds), params


def _txt(v):
    return None if v is None else str(v)


def _same(v):
    return v


def _yes_no(v):
    return None if v is None else ("Yes" if v else "No")


# API field -> (www_ll column, converter).  www_ll holds several of these
# as text where the normalized table uses a typed column.
_LEGACY_UPDATE_MAP = {
    "date_of_ll":        ("date_of_ll", _txt),
    "ll_number":         ("ll_number", _same),
    "duration_days":     ("duration_in_days", _txt),
    "attempts_taken":    ("attempts_taken_to_clear_ll", _same),
    "module_done":       ("module_done", _yes_no),
    "module_start_date": ("module_start_date", _same),
    "module_end_date":   ("module_end_date", _same),
    "reason_for_delay":  ("reason_for_delay", _txt),
}


# 2026-11-04: reason_for_delay surfaces on both LLCreate and LLUpdate.
class LLCreate(BaseModel):
    trainee_id: int
    date_of_ll: date
    ll_number: str
    duration_days: Optional[int] = None
    attempts_taken: Optional[int] = None
    module_done: Optional[bool] = False
    module_start_date: Optional[date] = None
    module_end_date: Optional[date] = None
    reason_for_delay: Optional[str] = None


class LLUpdate(BaseModel):
    date_of_ll: Optional[date] = None
    ll_number: Optional[str] = None
    duration_days: Optional[int] = None
    attempts_taken: Optional[int] = None
    module_done: Optional[bool] = None
    module_start_date: Optional[date] = None
    module_end_date: Optional[date] = None
    reason_for_delay: Optional[str] = None


def _row_select():
    return (
        "SELECT l.id, l.trainee_id, l.date_of_ll, l.ll_number, l.duration_days, "
        "       l.attempts_taken, l.module_done, l.module_start_date, l.module_end_date, "
        "       l.created_at, "
        "       t.enrollment_no, t.name, t.mobile, t.enrollment_type, "
        "       t.state_code, t.centre_code, t.district_code, d.district_name, "
        "       COALESCE(b.name, NULL) AS batch_name, b.id AS batch_id "
        "FROM www_learning_licenses l "
        "JOIN www_enrollment t ON t.id = l.trainee_id "
        "LEFT JOIN www_master_batches b ON b.id = t.batch_id "
        "LEFT JOIN central_districts d ON d.district_code = t.district_code "
    )


@router.get("")
def list_licenses(
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
    page = max(page, 1); limit = max(limit, 1); offset = (page - 1) * limit
    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        # ---- LEGACY FALLBACK: www_learning_licenses absent -> read www_ll ----
        if not _legacy.table_exists(cur, "www_learning_licenses"):
            lwhere, lparams = _legacy_filters(
                state_code, centre_code, batch_id, enrollment_type,
                name, date_from, date_to, district_code)
            if enrollment_id:
                lwhere += " AND l.enrollment_id = %s"; lparams.append(enrollment_id)
            cur.execute(
                "SELECT COUNT(*) AS total FROM mis_azad.www_ll l "
                + _legacy.geo_joins("l") + _legacy.trainee_join("l") + lwhere,
                lparams,
            )
            total = cur.fetchone()["total"]
            cur.execute(
                _legacy_row_select() + lwhere +
                " ORDER BY " + www_list_order(sort_by, "l.name", "l.created_at", "l.created_at DESC NULLS LAST, l.id DESC", date_col="l.module_start_date") + " LIMIT %s OFFSET %s",
                lparams + [limit, offset],
            )
            rows = cur.fetchall()
            return {"total": total, "page": page, "limit": limit, "data": rows}

        # ---- Normalized path (unchanged) ----
        conds = ["l.deleted_at IS NULL"]
        params = []
        if state_code:      conds.append("t.state_code = %s");        params.append(state_code)
        if district_code:   conds.append("t.district_code = %s");     params.append(district_code)
        if centre_code:     conds.append("t.centre_code = %s");       params.append(centre_code)
        if batch_id:        conds.append("t.batch_id = %s");          params.append(batch_id)
        if enrollment_type: conds.append("t.enrollment_type = %s");   params.append(enrollment_type)
        if name:            conds.append(_legacy.name_match("t.name"));          params.append(_legacy.name_pattern(name))
        if date_from:       conds.append("l.date_of_ll >= %s");       params.append(date_from)
        if date_to:         conds.append("l.date_of_ll <= %s");       params.append(date_to)
        where = "WHERE " + " AND ".join(conds)
        cur.execute(
            "SELECT COUNT(*) AS total FROM www_learning_licenses l "
            "JOIN www_enrollment t ON t.id = l.trainee_id " + where,
            params,
        )
        total = cur.fetchone()["total"]
        sql = _row_select() + where + " ORDER BY " + www_list_order(sort_by, "l.name", "l.created_at", "l.created_at DESC NULLS LAST, l.id DESC", date_col="l.module_start_date") + " LIMIT %s OFFSET %s"
        cur.execute(sql, params + [limit, offset])
        rows = cur.fetchall()
        return {"total": total, "page": page, "limit": limit, "data": rows}


@router.get("/{license_id}")
def get_license(request: Request, license_id: int):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_learning_licenses"):
            cur.execute(
                _legacy_row_select() + "WHERE l.id = %s",
                (license_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Learning License not found.")
            _scope.guard_detail(request, row)
            return row

        cur.execute(_row_select() + "WHERE l.id = %s AND l.deleted_at IS NULL", (license_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Learning License not found.")
    _scope.guard_detail(request, row)
    return row


@router.post("")
def create_license(body: LLCreate):
    if body.module_end_date and body.module_start_date and body.module_end_date < body.module_start_date:
        raise HTTPException(400, "Module End Date must be on or after Start Date.")
    with get_cursor() as cur:
        # 2026-08-18 (Ashish): flow guard -- picker ki rok server par bhi.
        _legacy.assert_flow(cur, body.trainee_id, stage="Learning License")
        if not _legacy.table_exists(cur, "www_learning_licenses"):
            # Identity is copied off www_enrollment — www_ll carries its own.
            cur.execute(
                "INSERT INTO mis_azad.www_ll "
                "    (enrollment_id, name, mobile_number, "
                "     type_of_enrollment, state, district, centre, batch_number, "
                "     date_of_ll, ll_number, duration_in_days, "
                "     attempts_taken_to_clear_ll, module_done, "
                "     module_start_date, module_end_date, reason_for_delay) "
                "SELECT e.id, e.name, e.mobile, "
                "       e.type_of_enrollment, e.state, e.district, e.centre, e.batch, "
                "       %s, %s, %s, %s, %s, %s, %s, %s "
                "FROM mis_azad.www_enrollment e WHERE e.id = %s "
                "RETURNING id",
                (str(body.date_of_ll), body.ll_number,
                 None if body.duration_days is None else str(body.duration_days),
                 body.attempts_taken,
                 "Yes" if body.module_done else "No",
                 body.module_start_date, body.module_end_date,
                 body.reason_for_delay,
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
            "INSERT INTO www_learning_licenses "
            "(trainee_id, date_of_ll, ll_number, duration_days, attempts_taken, "
            " module_done, module_start_date, module_end_date, reason_for_delay) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (body.trainee_id, body.date_of_ll, body.ll_number, body.duration_days,
             body.attempts_taken, bool(body.module_done),
             body.module_start_date, body.module_end_date,
             body.reason_for_delay),
        )
        new_id = cur.fetchone()["id"]
    return {"id": new_id, "ok": True}


@router.put("/{license_id}")
def update_license(license_id: int, body: LLUpdate):
    fields, params = [], []
    payload = body.model_dump(exclude_unset=True)
    if "module_end_date" in payload and "module_start_date" in payload             and payload["module_end_date"] and payload["module_start_date"]             and payload["module_end_date"] < payload["module_start_date"]:
        raise HTTPException(400, "Module End Date must be on or after Start Date.")
    if not payload:
        return {"ok": True}
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_learning_licenses"):
            lfields, lparams = [], []
            for k, v in payload.items():
                col, val = _LEGACY_UPDATE_MAP.get(k, (None, None))
                if col is None:
                    continue
                lfields.append(f"{col} = %s"); lparams.append(val(v))
            if not lfields:
                return {"ok": True}
            lparams.append(license_id)
            cur.execute(
                "UPDATE mis_azad.www_ll SET " + ", ".join(lfields) + " WHERE id = %s",
                lparams,
            )
            if cur.rowcount == 0:
                raise HTTPException(404, "Learning License not found.")
            return {"ok": True}

        for k, v in payload.items():
            fields.append(f"{k} = %s"); params.append(v)
        params.append(license_id)
        cur.execute(
            "UPDATE www_learning_licenses SET " + ", ".join(fields) +
            " WHERE id = %s AND deleted_at IS NULL",
            params,
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "Learning License not found.")
    return {"ok": True}


@router.delete("/{license_id}")
def delete_license(license_id: int):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_learning_licenses"):
            # 2026-08-19 (Ashish): pehle ye row ko HAMESHA ke liye mita deta tha.
            # Ab deleted_at bhar dete hain -- row DB me bachi rehti hai, bas har
            # list se hat jati hai. Wapas laani ho to deleted_at = NULL.
            cur.execute("UPDATE mis_azad.www_ll SET deleted_at = NOW() "
                        "WHERE id = %s AND deleted_at IS NULL", (license_id,))
        else:
            cur.execute(
                "UPDATE www_learning_licenses SET deleted_at = now() "
                "WHERE id = %s AND deleted_at IS NULL",
                (license_id,),
            )
        if cur.rowcount == 0:
            raise HTTPException(404, "Learning License not found.")
    return {"ok": True}


class RenewalCreate(BaseModel):
    renewal_date: date
    new_ll_number: str
    attempts_taken: Optional[int] = None


@router.get("/{license_id}/renewals")
def list_renewals(license_id: int):
    with get_cursor() as cur:
        # No www_ll_renewals here, but www_ll carries one renewal inline.
        if not _legacy.table_exists(cur, "www_ll_renewals"):
            cur.execute(
                "SELECT l.id, " + _LL_RENEWAL_DATE + " AS renewal_date, "
                "       NULLIF(TRIM(l.new_ll_number), '') AS new_ll_number, "
                "       NULLIF(TRIM(l.number_of_attempts_to_clear_the_ll), '') AS attempts_taken, "
                "       NULL::timestamptz AS created_at "
                "FROM mis_azad.www_ll l WHERE l.id = %s "
                "  AND (" + _LL_RENEWAL_DATE + " IS NOT NULL "
                "       OR NULLIF(TRIM(l.new_ll_number), '') IS NOT NULL)",
                (license_id,),
            )
            rows = cur.fetchall()
            return {"data": rows, "count": len(rows)}
        cur.execute(
            "SELECT id, renewal_date, new_ll_number, attempts_taken, created_at "
            "FROM www_ll_renewals "
            "WHERE ll_id = %s AND deleted_at IS NULL "
            "ORDER BY renewal_date DESC, id DESC",
            (license_id,),
        )
        rows = cur.fetchall()
    return {"data": rows, "count": len(rows)}

@router.post("/{license_id}/renewals")
def create_renewal(license_id: int, body: RenewalCreate):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_ll_renewals"):
            # Only one renewal fits on a www_ll row; writing a second would
            # silently overwrite the first, so refuse instead.
            cur.execute(
                "SELECT " + _LL_RENEWAL_DATE + " AS renewal_date, "
                "       NULLIF(TRIM(new_ll_number), '') AS new_ll_number "
                "FROM mis_azad.www_ll l WHERE id = %s",
                (license_id,),
            )
            existing = cur.fetchone()
            if not existing:
                raise HTTPException(404, "Learning License not found.")
            if existing["renewal_date"] or existing["new_ll_number"]:
                raise HTTPException(
                    409,
                    "This deployment stores a single LL renewal per licence and "
                    "one is already recorded. Edit the existing renewal instead.",
                )
            cur.execute(
                "UPDATE mis_azad.www_ll "
                "   SET date_of_renewal_of_ll = %s, new_ll_number = %s, "
                "       number_of_attempts_to_clear_the_ll = %s "
                " WHERE id = %s",
                (str(body.renewal_date), body.new_ll_number,
                 None if body.attempts_taken is None else str(body.attempts_taken),
                 license_id),
            )
            return {"id": license_id, "ok": True}

        cur.execute("SELECT 1 FROM www_learning_licenses WHERE id=%s AND deleted_at IS NULL", (license_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Learning License not found.")
        cur.execute(
            "INSERT INTO www_ll_renewals (ll_id, renewal_date, new_ll_number, attempts_taken) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (license_id, body.renewal_date, body.new_ll_number, body.attempts_taken),
        )
        new_id = cur.fetchone()["id"]
    return {"id": new_id, "ok": True}


# =============================================================================
# EXPORT (Excel) — 2026-08-07
# Section-wise xlsx with:
#   1. Trainee Details        (Enrollment No, Name, Mobile, Type, State,
#                              District, Centre, Area, Batch)
#   2. Learning License Details (Date, LL Number, Duration, Attempts, Module
#                                Done, Module Start, Module End)
#   3. LL Renewed Details     (inline per LL — N * 3 columns, floor at 3)
#   4. System                 (Created At)
# Uses the same filters as list_licenses so the export matches what's on
# screen. Legacy www_ll fallback is preserved for schemas where the
# normalized table is absent; there the renewal columns come off the
# www_ll row itself, so at most one renewal group is filled.
# =============================================================================
@router.get("/export/excel")
def export_licenses_excel(
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
        has_table = _legacy.table_exists(cur, "www_learning_licenses")

        if not has_table:
            # ---- Legacy fallback: www_ll, with its one inline renewal ----
            where, lparams = _legacy_filters(
                state_code, centre_code, batch_id, enrollment_type,
                name, date_from, date_to, district_code)
            cur.execute(
                "SELECT l.id, " + _legacy.enroll_no() + ", l.name, "
                "       COALESCE(NULLIF(TRIM(_te.mobile), ''), NULLIF(TRIM(l.mobile_number), '')) AS mobile, "
                "       COALESCE(NULLIF(TRIM(_te.type_of_enrollment), ''), NULLIF(TRIM(l.type_of_enrollment), '')) AS enrollment_type, "
                "       l.state AS state_name, l.district AS district_name, "
                "       " + _legacy.centre_expr("l.centre") + " AS centre_name, "
                "       NULL::text AS area_name, "
                "       COALESCE(NULLIF(TRIM(_te.batch), ''), NULLIF(TRIM(l.batch_number), '')) AS batch_name, "
                # 2026-08-12: these four sit on www_ll but were never
                # selected, so the export dropped them.
                "       NULLIF(TRIM(l.status), '') AS trainee_status, "
                "       l.date_of_birth, l.current_address, l.date_of_joining, "
                "       " + _LL_DATE + " AS date_of_ll, l.ll_number, "
                "       NULLIF(TRIM(l.duration_in_days), '') AS duration_days, "
                "       l.attempts_taken_to_clear_ll AS attempts_taken, "
                "       NULLIF(TRIM(l.module_done), '') AS module_done, "
                "       l.module_start_date, l.module_end_date, "
                "       l.reason_for_delay, "
                "       " + _LL_RENEWAL_DATE + " AS renewal_date, "
                "       NULLIF(TRIM(l.new_ll_number), '') AS new_ll_number, "
                "       NULLIF(TRIM(l.number_of_attempts_to_clear_the_ll), '') "
                "           AS renewal_attempts, "
                "       NULL::timestamptz AS created_at "
                "FROM mis_azad.www_ll l " + _legacy.geo_joins("l") +
                _legacy.trainee_join("l") + where +
                " ORDER BY " + _LL_DATE + " DESC NULLS LAST, l.id DESC",
                lparams,
            )
            rows = cur.fetchall()
            renewal_map = {}
            for r in rows:
                if r.get("renewal_date") or r.get("new_ll_number"):
                    renewal_map[r["id"]] = [{
                        "renewal_date": r.get("renewal_date"),
                        "new_ll_number": r.get("new_ll_number"),
                        "attempts_taken": r.get("renewal_attempts"),
                    }]
        else:
            conds = ["l.deleted_at IS NULL"]
            params = []
            if state_code:      conds.append("t.state_code = %s");        params.append(state_code)
            if centre_code:     conds.append("t.centre_code = %s");       params.append(centre_code)
            if batch_id:        conds.append("t.batch_id = %s");          params.append(batch_id)
            if enrollment_type: conds.append("t.enrollment_type = %s");   params.append(enrollment_type)
            if name:            conds.append(_legacy.name_match("t.name"));          params.append(_legacy.name_pattern(name))
            if date_from:       conds.append("l.date_of_ll >= %s");       params.append(date_from)
            if date_to:         conds.append("l.date_of_ll <= %s");       params.append(date_to)
            where = "WHERE " + " AND ".join(conds)
            cur.execute(
                "SELECT l.id, l.date_of_ll, l.ll_number, l.duration_days, "
                "       l.attempts_taken, l.module_done, l.module_start_date, l.module_end_date, "
                "       l.reason_for_delay, "
                "       l.created_at, "
                "       t.enrollment_no, t.name, t.mobile, t.enrollment_type, "
                "       t.state_code, t.district_code, t.centre_code, t.area_code, "
                "       s.state_name, d.district_name, c.centre_name, a.area_name, "
                "       b.name AS batch_name "
                "FROM www_learning_licenses l "
                "JOIN www_enrollment t ON t.id = l.trainee_id "
                "LEFT JOIN central_states    s ON s.state_code    = t.state_code "
                "LEFT JOIN central_districts d ON d.district_code = t.district_code "
                "LEFT JOIN central_centres   c ON c.centre_code   = t.centre_code "
                "LEFT JOIN www_areas     a ON a.area_code     = t.area_code "
                "LEFT JOIN www_master_batches b ON b.id = t.batch_id " +
                where + " ORDER BY l.created_at DESC",
                params,
            )
            rows = cur.fetchall()

            # Renewals map (only if the renewal table exists in this schema).
            renewal_map = {}
            cur.execute("SELECT to_regclass('mis_azad.www_ll_renewals') AS t")
            if cur.fetchone()["t"] and rows:
                ids = [r["id"] for r in rows]
                ph = ",".join(["%s"] * len(ids))
                cur.execute(
                    f"SELECT ll_id, renewal_date, new_ll_number, attempts_taken "
                    f"FROM www_ll_renewals WHERE ll_id IN ({ph}) AND deleted_at IS NULL "
                    f"ORDER BY ll_id, renewal_date, id",
                    ids,
                )
                for rn in cur.fetchall():
                    renewal_map.setdefault(rn["ll_id"], []).append(rn)

    def _g(r, k):
        v = r.get(k)
        return "" if v is None else v

    def _yn(v):
        if v is None or v == "":
            return ""
        if isinstance(v, bool):
            return "Yes" if v else "No"
        return str(v)

    # Section 1: Trainee Details (13 cols)
    trainee_headers = [
        "Enrollment No.", "Name", "Mobile", "Enrollment Type",
        "State", "District", "Centre", "Area", "Batch",
        "Status", "Date of Birth", "Current Address", "Date of Joining",
    ]
    # Section 2: Learning License Details (7 cols)
    ll_headers = [
        "Date of LL", "LL Number", "Duration (Days)", "Attempts Taken",
        "Module Done", "Module Start Date", "Module End Date",
    ]
    # Section 3: Renewals (inline, floor at 3 → 9 cols)
    max_renewals = max([len(v) for v in renewal_map.values()] + [3])
    renewal_headers = []
    for i in range(1, max_renewals + 1):
        renewal_headers.extend([
            f"Renewal {i} Date",
            f"Renewal {i} New LL Number",
            f"Renewal {i} Attempts",
        ])
    # Section 4: System (1 col)
    system_headers = ["Created At"]

    all_headers = trainee_headers + ll_headers + renewal_headers + system_headers
    n_trainee = len(trainee_headers)
    n_ll = len(ll_headers)
    n_ren = len(renewal_headers)
    n_sys = len(system_headers)

    group_headers = [
        (1, n_trainee, "Trainee Details"),
        (n_trainee + 1, n_trainee + n_ll, "Learning License Details"),
    ]
    if n_ren > 0:
        group_headers.append((
            n_trainee + n_ll + 1,
            n_trainee + n_ll + n_ren,
            "LL Renewed Details",
        ))
    group_headers.append((
        n_trainee + n_ll + n_ren + 1,
        n_trainee + n_ll + n_ren + n_sys,
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
            _g(r, "current_address"), _g(r, "date_of_joining"),
            _g(r, "date_of_ll"), _g(r, "ll_number"), _g(r, "duration_days"),
            _g(r, "attempts_taken"), _yn(r.get("module_done")),
            _g(r, "module_start_date"), _g(r, "module_end_date"),
        ]
        for i in range(max_renewals):
            if i < len(renewals):
                rn = renewals[i]
                row.extend([
                    _g(rn, "renewal_date"),
                    _g(rn, "new_ll_number"),
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
    _wt_rows = _wt_cells(rows, "mis_azad.www_ll", "id")
    for _wi in range(len(data_rows)):
        data_rows[_wi] = list(data_rows[_wi]) + (_wt_rows[_wi] if _wi < len(_wt_rows) else ["", ""])
    sheets = [{
        "name": "Learning Licenses",
        "group_headers": group_headers,
        "headers": all_headers,
        "rows": data_rows,
    }]
    return multi_sheet_xlsx_response_v2(
        sheets,
        f"WWW_Learning_Licenses_{_d.today().isoformat()}.xlsx",
    )
