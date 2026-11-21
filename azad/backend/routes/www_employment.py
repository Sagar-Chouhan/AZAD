"""WWW Employment routes — CRUD + list with filters."""
from typing import Optional, List
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Request
from pydantic import BaseModel
import sys as _sys, os as _os, uuid
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(__file__)))
from database import get_cursor
from routes import _www_legacy as _legacy
from routes import _www_scope as _scope
from routes._www_list_sort import www_list_order
try:
    from config import UPLOAD_DIR, MAX_FILE_SIZE
except Exception:
    UPLOAD_DIR = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "uploads")
    MAX_FILE_SIZE = 5 * 1024 * 1024

router = APIRouter(prefix="/api/www-employment", tags=["www-employment"])


class EmploymentCreate(BaseModel):
    trainee_id: int
    financial_year: Optional[str] = None
    type_of_enrollment: Optional[str] = None
    current_status: Optional[str] = None
    current_status_other: Optional[str] = None
    type_of_job: Optional[str] = None
    where_location: Optional[str] = None
    outside_location: Optional[str] = None
    date_of_job: Optional[date] = None
    salary: Optional[Decimal] = None
    is_active: Optional[bool] = True
    is_draft: Optional[bool] = False


class EmploymentUpdate(BaseModel):
    financial_year: Optional[str] = None
    type_of_enrollment: Optional[str] = None
    current_status: Optional[str] = None
    current_status_other: Optional[str] = None
    type_of_job: Optional[str] = None
    where_location: Optional[str] = None
    outside_location: Optional[str] = None
    date_of_job: Optional[date] = None
    salary: Optional[Decimal] = None
    is_active: Optional[bool] = None


# Helper: rows -> dict list (handles RealDictCursor or tuple cursors)
def _rows_to_dicts(cur):
    rows = cur.fetchall()
    if not rows: return []
    if hasattr(rows[0], 'get'):
        return [dict(r) for r in rows]
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]


def _row_to_dict(cur):
    r = cur.fetchone()
    if r is None: return None
    if hasattr(r, 'get'): return dict(r)
    cols = [d[0] for d in cur.description]
    return dict(zip(cols, r))


def _enriched_select():
    return """
        SELECT e.*,
               t.name, t.enrollment_no, t.state_code, t.district_code,
               t.centre_code, t.batch_id, t.enrollment_date AS date_of_joining,
               t.enrollment_type AS trainee_enrollment_type,
               t.status AS trainee_status,
               t.mobile AS trainee_mobile,
               t.ll_date, t.ll_number, t.ll_attempts,
               t.pl_date, t.pl_number, t.pl_attempts,
               b.name AS batch_name,
               s.state_name,
               d.district_name,
               ct.centre_name
        FROM mis_azad.www_employment e
        JOIN mis_azad.www_enrollment t  ON e.trainee_id = t.id
        LEFT JOIN mis_azad.www_master_batches b ON t.batch_id = b.id
        LEFT JOIN mis_azad.central_states    s  ON t.state_code   = s.state_code
        LEFT JOIN mis_azad.central_districts d  ON t.district_code= d.district_code
        LEFT JOIN mis_azad.central_centres   ct ON t.centre_code  = ct.centre_code
    """


# Legacy fallback.  Name collision: this deployment has a www_employment
# table, but it is the spreadsheet import rather than the normalized one,
# so the routes switch on the presence of the trainee_id FK.  Earlier
# deployments split employment across a 2-wheeler and a 4-wheeler sheet
# and had to union them; here both live in one table and
# type_of_enrollment carries the distinction.
# ("where" is quoted because it is a SQL keyword.)
def _legacy_emp_select():
    return (
        "SELECT e.id, e.enrollment_id AS trainee_id, e.financial_year, e.type_of_enrollment, "
        "       NULLIF(TRIM(e.what_is_your_current_status), '') AS current_status, "
        "       NULLIF(TRIM(e.specify_if_any_other), '') AS current_status_other, "
        "       NULLIF(TRIM(e.type_of_job), '') AS type_of_job, "
        '       NULLIF(TRIM(e."where"), \'\') AS where_location, '
        "       NULLIF(TRIM(e.if_working_outside_where), '') AS outside_location, "
        "       e.date_of_job, e.salary, "
        "       NULL::boolean AS is_active, NULL::boolean AS is_draft, "
        "       e.created_at, "
        "       e.name, " + _legacy.enroll_no() + ", "
        "       " + _legacy.geo_cols() + ", "
        "       NULL::int AS batch_id, e.date_of_joining, "
        "       COALESCE(NULLIF(TRIM(_te.type_of_enrollment), ''), NULLIF(TRIM(e.type_of_enrollment), '')) AS trainee_enrollment_type, "
        "       NULL::text AS trainee_status, NULL::text AS trainee_mobile, "
        "       e.date_of_ll AS ll_date, e.ll_number, "
        "       e.attempts_taken_to_clear_ll AS ll_attempts, "
        "       NULLIF(TRIM(e.do_you_have_a_pl), '') AS has_pl, "
        "       e.date_of_pl AS pl_date, e.pl_number, "
        "       e.attempts_taken_to_clear_pl AS pl_attempts, "
        # 2026-08-12: the two Sakha test results and the working-outside
        # document proof are on the import; the export never showed them.
        "       e.if_yes_date_of_internal_sakha_pass AS internal_pass_date, "
        "       e.no_of_attempts_to_clear_internal_sakha_test AS internal_attempts, "
        "       e.if_yes_date_of_external_sakha_pass AS external_pass_date, "
        "       e.no_of_attempts_to_clear_external_sakha_test AS external_attempts, "
        "       NULLIF(TRIM(e.documents_to_be_uploaded_document_proof_for_working_out), '') "
        "           AS work_proof_documents, "
        "       COALESCE(NULLIF(TRIM(_te.batch), ''), NULLIF(TRIM(e.batch_number), '')) AS batch_name, "
        "       e.state AS state_name, e.district AS district_name, "
        "       " + _legacy.centre_expr("e.centre") + " AS centre_name, "
        "       COALESCE(NULLIF(TRIM(_te.type_of_enrollment), ''), NULLIF(TRIM(e.type_of_enrollment), '')) AS vehicle_source "
        "FROM mis_azad.www_employment e " + _legacy.geo_joins("e")
        + _legacy.trainee_join("e")
    )


# API field -> imported www_employment column.  is_active / is_draft have
# no home on the import and are dropped.  "where" needs the quotes.
_LEGACY_EMP_UPDATE_MAP = {
    "financial_year":       "financial_year",
    "type_of_enrollment":   "type_of_enrollment",
    "current_status":       "what_is_your_current_status",
    "current_status_other": "specify_if_any_other",
    "type_of_job":          "type_of_job",
    "where_location":       '"where"',
    "outside_location":     "if_working_outside_where",
    "date_of_job":          "date_of_job",
    "salary":               "salary",
}


def _legacy_emp_filters(state_code, centre_code, type_of_enrollment,
                        type_of_job, name, min_salary, max_salary,
                        batch_id=None, district_code=None):
    conds = ["NULLIF(TRIM(e.name), '') IS NOT NULL", "e.deleted_at IS NULL"]
    params = []
    if state_code:         conds.append(_legacy.state_filter());     params.append(state_code)
    if district_code:      conds.append(_legacy.district_filter());  params.append(district_code)
    if centre_code:        conds.append(_legacy.centre_filter("e")); params.append(centre_code)
    if type_of_enrollment: conds.append("e.type_of_enrollment = %s"); params.append(type_of_enrollment)
    # 2026-08-17: ILIKE %...% substring match tha -- "Driver" chunne par
    # 'Working Outside as driver/rider' bhi aa jata tha. Exact (case/space
    # ke bina) match hi sahi hai.
    if type_of_job:
        conds.append("LOWER(TRIM(e.type_of_job)) = LOWER(TRIM(%s))")
        params.append(type_of_job)
    # 2026-08-17: batch_id yahan tak pahunchta hi nahi tha (list endpoint
    # legacy branch me use gira deta tha). Import ki apni batch_number cell
    # ya trainee ke enrollment ki batch -- dono master batch ke naam se milte
    # hain, jaise trainee list me hota hai.
    if batch_id:
        conds.append(
            "(NULLIF(TRIM(e.batch_number), '') = "
            "   (SELECT name FROM mis_azad.www_master_batches WHERE id = %s) "
            " OR EXISTS (SELECT 1 FROM mis_azad.www_enrollment _be "
            "            WHERE _be.id = e.enrollment_id "
            "              AND NULLIF(TRIM(_be.batch), '') = "
            "                  (SELECT name FROM mis_azad.www_master_batches WHERE id = %s)))")
        params.append(batch_id); params.append(batch_id)
    if name:               conds.append("(" + _legacy.name_match("e.name") + " OR _te.enrollment_no ILIKE %s)");           params.append(_legacy.name_pattern(name)); params.append(_legacy.name_pattern(name))
    if min_salary is not None: conds.append("e.salary >= %s");        params.append(min_salary)
    if max_salary is not None: conds.append("e.salary <= %s");        params.append(max_salary)
    return " WHERE " + " AND ".join(conds), params

@router.get("")
def list_employment(
    request: Request,
    enrollment_id: Optional[int] = None,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    type_of_enrollment: Optional[str] = None,
    type_of_job: Optional[str] = None,
    name: Optional[str] = None,
    min_salary: Optional[float] = None,
    max_salary: Optional[float] = None,
    sort_by: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=200),
):
    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        # ---- LEGACY FALLBACK: www_employment is the import, not the normalized table ----
        if not _legacy.is_normalized(cur, "www_employment"):
            lwhere, lparams = _legacy_emp_filters(
                state_code, centre_code, type_of_enrollment, type_of_job,
                name, min_salary, max_salary, batch_id=batch_id, district_code=district_code)
            if enrollment_id:
                lwhere += " AND e.enrollment_id = %s"; lparams.append(enrollment_id)
            _df = request.query_params.get("date_from"); _dt = request.query_params.get("date_to")
            if _df: lwhere += " AND e.date_of_job >= %s"; lparams.append(_df)
            if _dt: lwhere += " AND e.date_of_job <= %s"; lparams.append(_dt)
            cur.execute(
                "SELECT COUNT(*) AS n FROM mis_azad.www_employment e "
                + _legacy.geo_joins("e") + _legacy.trainee_join("e") + lwhere,
                lparams,
            )
            r = cur.fetchone()
            total = r.get('n') if hasattr(r, 'get') else r[0]
            cur.execute(
                _legacy_emp_select() + lwhere +
                " ORDER BY " + www_list_order(sort_by, "e.name", "e.created_at", "e.created_at DESC NULLS LAST, e.id DESC", date_col="e.date_of_joining") + " LIMIT %s OFFSET %s",
                lparams + [limit, (page - 1) * limit])
            rows = _rows_to_dicts(cur)
            return {"total": total, "page": page, "limit": limit, "data": rows}

        where, params = ["1=1"], []
        if state_code:           where.append("t.state_code = %s");        params.append(state_code)
        if district_code:        where.append("t.district_code = %s");     params.append(district_code)
        if centre_code:          where.append("t.centre_code = %s");       params.append(centre_code)
        if batch_id:             where.append("t.batch_id = %s");          params.append(batch_id)
        if type_of_enrollment:   where.append("(e.type_of_enrollment = %s OR t.enrollment_type = %s)"); params.extend([type_of_enrollment, type_of_enrollment])
        if type_of_job:          where.append("e.type_of_job ILIKE %s");   params.append(f"%{type_of_job}%")
        if name:                 where.append(_legacy.name_match("t.name"));          params.append(_legacy.name_pattern(name))
        if min_salary is not None: where.append("e.salary >= %s");         params.append(min_salary)
        if max_salary is not None: where.append("e.salary <= %s");         params.append(max_salary)
        sql_where = " WHERE " + " AND ".join(where)
        offset = (page - 1) * limit
        cur.execute(f"SELECT COUNT(*) AS n FROM mis_azad.www_employment e JOIN mis_azad.www_enrollment t ON e.trainee_id = t.id {sql_where}", params)
        r = cur.fetchone()
        total = r.get('n') if hasattr(r, 'get') else r[0]
        cur.execute(_enriched_select() + sql_where + " ORDER BY " + www_list_order(sort_by, "e.name", "e.created_at", "e.created_at DESC NULLS LAST, e.id DESC", date_col="e.date_of_joining") + " LIMIT %s OFFSET %s", params + [limit, offset])
        rows = _rows_to_dicts(cur)
        return {"total": total, "page": page, "limit": limit, "data": rows}

@router.get("/eligible-trainees")
def eligible_trainees(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    financial_year: Optional[str] = None,
    type_of_enrollment: Optional[str] = None,
    name: Optional[str] = None,
    # 2026-09-21: was Query(200, ge=1, le=500) -- too small (same reason as
    # www_walkout). The picker fetches ONCE per state+centre and filters
    # client-side, so 200 is the whole searchable universe; several centres
    # have more than 200 eligible trainees.
    limit: int = Query(2000, ge=1, le=5000),
):
    """Trainees eligible to add an employment record — currently NOT in www_employment with active status."""
    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_trainees"):
            # www_enrollment is the trainee master here; exclude anyone who
            # already has an employment row.
            where = [
                "NULLIF(TRIM(en.name), '') IS NOT NULL",
                "COALESCE(NULLIF(TRIM(en.status), ''), 'Active') <> 'Draft'",
                "NOT EXISTS (SELECT 1 FROM mis_azad.www_employment e "
                "            WHERE e.enrollment_id = en.id)",
            ]
            params = []
            if state_code:         where.append(_legacy.state_filter());      params.append(state_code)
            if district_code:      where.append(_legacy.district_filter());   params.append(district_code)
            if centre_code:        where.append(_legacy.centre_filter("en")); params.append(centre_code)
            if financial_year:     where.append("en.financial_year = %s");    params.append(financial_year)
            if type_of_enrollment: where.append("en.type_of_enrollment = %s"); params.append(type_of_enrollment)
            if name:               where.append(_legacy.name_match("en.name"));          params.append(_legacy.name_pattern(name))
            cur.execute(
                "SELECT en.id, en.name, en.enrollment_no, "
                "       " + _legacy.geo_cols() + ", "
                "       NULL::int AS batch_id, "
                "       en.type_of_enrollment AS enrollment_type, en.status, "
                "       en.financial_year, en.enrollment_date, "
                "       NULLIF(TRIM(en.batch), '') AS batch_name, "
                "       en.state AS state_name, "
                "       " + _legacy.centre_expr("en.centre") + " AS centre_name "
                "FROM mis_azad.www_enrollment en " + _legacy.geo_joins("en") +
                "WHERE " + " AND ".join(where) + " ORDER BY en.name LIMIT %s",
                params + [limit],
            )
            return _rows_to_dicts(cur)
        where, params = [
            "t.id NOT IN (SELECT trainee_id FROM mis_azad.www_employment WHERE is_active = TRUE)",
            # 2026-08-19: Draft trainees are ineligible for downstream tabs.
            "COALESCE(NULLIF(TRIM(t.status), ''), 'Active') <> 'Draft'",
        ], []
        if state_code:         where.append("t.state_code = %s");  params.append(state_code)
        if district_code:      where.append("t.district_code = %s"); params.append(district_code)
        if centre_code:        where.append("t.centre_code = %s"); params.append(centre_code)
        if financial_year:     where.append("t.financial_year = %s"); params.append(financial_year)
        if type_of_enrollment: where.append("t.enrollment_type = %s"); params.append(type_of_enrollment)
        if name:               where.append(_legacy.name_match("t.name"));    params.append(_legacy.name_pattern(name))
        sql = f"""
            SELECT t.id, t.name, t.enrollment_no, t.state_code, t.centre_code, t.batch_id,
                   t.enrollment_type, t.status, t.financial_year,
                   b.name AS batch_name, s.state_name, ct.centre_name
            FROM mis_azad.www_enrollment t
            LEFT JOIN mis_azad.www_master_batches b ON t.batch_id = b.id
            LEFT JOIN mis_azad.central_states  s  ON t.state_code  = s.state_code
            LEFT JOIN mis_azad.central_centres ct ON t.centre_code = ct.centre_code
            WHERE {" AND ".join(where)}
            ORDER BY t.name LIMIT %s
        """
        params.append(limit)
        cur.execute(sql, params)
        return _rows_to_dicts(cur)

@router.get("/{emp_id}")
def get_employment(request: Request, emp_id: int):
    with get_cursor() as cur:
        if not _legacy.is_normalized(cur, "www_employment"):
            cur.execute(_legacy_emp_select() + " WHERE e.id = %s", (emp_id,))
            rec = _row_to_dict(cur)
            if not rec:
                raise HTTPException(404, "Employment not found")
            _scope.guard_detail(request, rec)
            # The import keeps the proof-of-employment file as free text on
            # the row and carries the sakha pass dates itself.
            cur.execute(
                "SELECT NULLIF(TRIM(documents_to_be_uploaded_document_proof_for_working_out), '') "
                "           AS file_name, "
                "       if_yes_date_of_internal_sakha_pass AS internal_pass_date, "
                "       no_of_attempts_to_clear_internal_sakha_test AS internal_attempts, "
                "       if_yes_date_of_external_sakha_pass AS external_pass_date, "
                "       no_of_attempts_to_clear_external_sakha_test AS external_attempts "
                "FROM mis_azad.www_employment WHERE id = %s",
                (emp_id,),
            )
            extra = _row_to_dict(cur) or {}
            # 2026-09-11: prefer the real documents table (document_type, created_at
            # = Upload Date, file_path = View link). Fall back to the import's single
            # free-text proof when the table is absent or has no rows for this row.
            if _legacy.table_exists(cur, "www_employment_documents"):
                cur.execute(
                    "SELECT id, employment_id, document_type, file_name, file_path, created_at "
                    "FROM mis_azad.www_employment_documents WHERE employment_id = %s ORDER BY id",
                    (emp_id,),
                )
                rec["documents"] = _rows_to_dicts(cur)
                if not rec["documents"] and extra.get("file_name"):
                    rec["documents"] = [{"id": None, "employment_id": emp_id, "document_type": None,
                                         "file_name": extra["file_name"], "file_path": "", "created_at": None}]
            else:
                rec["documents"] = (
                    [{"id": None, "employment_id": emp_id, "document_type": None,
                      "file_name": extra["file_name"], "file_path": ""}]
                    if extra.get("file_name") else []
                )
            for k in ("internal_pass_date", "internal_attempts",
                      "external_pass_date", "external_attempts"):
                rec[k] = extra.get(k)
            # 2026-08-30: LL/PL come from the employment import row, but some rows
            # lack them though the trainee has an LL/PL record. Backfill from
            # www_ll / www_pl (by enrollment_id) so the view sections are not blank.
            _enr = rec.get("trainee_id")
            if _enr:
                if not str(rec.get("ll_number") or "").strip():
                    cur.execute(
                        "SELECT date_of_ll, ll_number, attempts_taken_to_clear_ll "
                        "FROM mis_azad.www_ll WHERE enrollment_id = %s "
                        "AND NULLIF(TRIM(ll_number), '') IS NOT NULL "
                        "ORDER BY id DESC LIMIT 1", (_enr,))
                    _ll = _row_to_dict(cur)
                    if _ll:
                        rec["ll_date"] = rec.get("ll_date") or _ll.get("date_of_ll")
                        rec["ll_number"] = _ll.get("ll_number")
                        rec["ll_attempts"] = rec.get("ll_attempts") or _ll.get("attempts_taken_to_clear_ll")
                if not str(rec.get("pl_number") or "").strip():
                    cur.execute(
                        "SELECT date_of_pl, pl_number, attempts_taken_to_clear_pl "
                        "FROM mis_azad.www_pl WHERE enrollment_id = %s "
                        "AND NULLIF(TRIM(pl_number), '') IS NOT NULL "
                        "ORDER BY id DESC LIMIT 1", (_enr,))
                    _pl = _row_to_dict(cur)
                    if _pl:
                        rec["pl_date"] = rec.get("pl_date") or _pl.get("date_of_pl")
                        rec["pl_number"] = _pl.get("pl_number")
                        rec["pl_attempts"] = rec.get("pl_attempts") or _pl.get("attempts_taken_to_clear_pl")
                # 2026-09-11: Sakha backfill. The employment import row's own sakha
                # columns are blank for app-added trainees; pull the latest PASSED
                # internal/external sakha from the module tables (by enrollment_id),
                # mirroring the LL/PL backfill above.
                if rec.get("internal_pass_date") is None and rec.get("internal_attempts") is None:
                    cur.execute(
                        "SELECT if_yes_date_of_internal_sakha_pass AS d, "
                        "       no_of_attempts_to_clear_internal_sakha_test AS a "
                        "FROM mis_azad.www_sakha_internal "
                        "WHERE enrollment_id = %s AND deleted_at IS NULL "
                        "  AND if_yes_date_of_internal_sakha_pass IS NOT NULL "
                        "ORDER BY id DESC LIMIT 1", (_enr,))
                    _si = _row_to_dict(cur)
                    if _si:
                        rec["internal_pass_date"] = _si.get("d")
                        rec["internal_attempts"]  = _si.get("a")
                if rec.get("external_pass_date") is None and rec.get("external_attempts") is None:
                    cur.execute(
                        "SELECT if_yes_date_of_external_sakha_pass AS d, "
                        "       no_of_attempts_to_clear_external_sakha_test AS a "
                        "FROM mis_azad.www_sakha_external "
                        "WHERE enrollment_id = %s AND deleted_at IS NULL "
                        "  AND if_yes_date_of_external_sakha_pass IS NOT NULL "
                        "ORDER BY id DESC LIMIT 1", (_enr,))
                    _se = _row_to_dict(cur)
                    if _se:
                        rec["external_pass_date"] = _se.get("d")
                        rec["external_attempts"]  = _se.get("a")
            return rec
            rec["documents"] = []
            return rec

        cur.execute(_enriched_select() + " WHERE e.id = %s", (emp_id,))
        rec = _row_to_dict(cur)
        if not rec: raise HTTPException(404, "Employment not found")
        _scope.guard_detail(request, rec)
        cur.execute("SELECT * FROM mis_azad.www_employment_documents WHERE employment_id = %s ORDER BY id", (emp_id,))
        rec["documents"] = _rows_to_dicts(cur)
        try:
            cur.execute("SELECT internal_pass_date, internal_attempts FROM mis_azad.www_internal_sakha WHERE trainee_id = %s ORDER BY id DESC LIMIT 1", (rec["trainee_id"],))
            sk = _row_to_dict(cur)
            if sk:
                rec["internal_pass_date"]  = sk.get("internal_pass_date")
                rec["internal_attempts"]   = sk.get("internal_attempts")
        except Exception: pass
        try:
            cur.execute("SELECT external_pass_date, external_attempts FROM mis_azad.www_external_sakha WHERE trainee_id = %s ORDER BY id DESC LIMIT 1", (rec["trainee_id"],))
            sk = _row_to_dict(cur)
            if sk:
                rec["external_pass_date"]  = sk.get("external_pass_date")
                rec["external_attempts"]   = sk.get("external_attempts")
        except Exception: pass
    return rec

@router.post("")
def create_employment(payload: EmploymentCreate):
    with get_cursor() as cur:
        # 2026-08-18 (Ashish): flow guard -- picker ki rok server par bhi.
        _legacy.assert_flow(cur, payload.trainee_id, stage="Employment")
        if not _legacy.is_normalized(cur, "www_employment"):
            cur.execute("""
                INSERT INTO mis_azad.www_employment
                  (enrollment_id, name, state, district, centre, batch_number,
                   date_of_joining, financial_year, type_of_enrollment,
                   what_is_your_current_status, specify_if_any_other,
                   type_of_job, "where", if_working_outside_where,
                   date_of_job, salary)
                SELECT en.id, en.name, en.state, en.district, en.centre,
                       en.batch, en.enrollment_date,
                       %s, COALESCE(%s, en.type_of_enrollment), %s, %s, %s, %s, %s, %s, %s
                FROM mis_azad.www_enrollment en WHERE en.id = %s
                RETURNING id
            """, (payload.financial_year, payload.type_of_enrollment,
                  payload.current_status, payload.current_status_other,
                  payload.type_of_job, payload.where_location,
                  payload.outside_location, payload.date_of_job, payload.salary,
                  payload.trainee_id))
            r = cur.fetchone()
            if not r: raise HTTPException(400, "Trainee not found")
            return {"id": r.get('id') if hasattr(r, 'get') else r[0]}

        cur.execute("SELECT id FROM mis_azad.www_enrollment WHERE id = %s", (payload.trainee_id,))
        if not cur.fetchone(): raise HTTPException(400, "Trainee not found")
        cur.execute("""
            INSERT INTO mis_azad.www_employment
              (trainee_id, financial_year, type_of_enrollment, current_status, current_status_other,
               type_of_job, where_location, outside_location, date_of_job, salary, is_active, is_draft)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (payload.trainee_id, payload.financial_year, payload.type_of_enrollment,
              payload.current_status, payload.current_status_other, payload.type_of_job,
              payload.where_location, payload.outside_location, payload.date_of_job,
              payload.salary, payload.is_active, payload.is_draft))
        r = cur.fetchone()
        new_id = r.get('id') if hasattr(r,'get') else r[0]
    return {"id": new_id}


@router.put("/{emp_id}")
def update_employment(emp_id: int, payload: EmploymentUpdate):
    updates = {k: v for k, v in payload.dict(exclude_unset=True).items()}
    if not updates: return {"id": emp_id, "updated": 0}
    with get_cursor() as cur:
        if not _legacy.is_normalized(cur, "www_employment"):
            lupdates = {}
            for k, v in updates.items():
                col = _LEGACY_EMP_UPDATE_MAP.get(k)
                if col:
                    lupdates[col] = v
            if not lupdates:
                return {"id": emp_id, "updated": 0}
            set_parts = ", ".join(f'{c} = %s' for c in lupdates)
            cur.execute(
                f"UPDATE mis_azad.www_employment SET {set_parts} WHERE id = %s RETURNING id",
                list(lupdates.values()) + [emp_id])
            if not cur.fetchone(): raise HTTPException(404, "Employment not found")
            return {"id": emp_id, "updated": len(lupdates)}

        set_parts = ", ".join(f"{k} = %s" for k in updates) + ", updated_at = CURRENT_TIMESTAMP"
        params = list(updates.values()) + [emp_id]
        cur.execute(f"UPDATE mis_azad.www_employment SET {set_parts} WHERE id = %s RETURNING id", params)
        if not cur.fetchone(): raise HTTPException(404, "Employment not found")
    return {"id": emp_id, "updated": len(updates)}


@router.delete("/{emp_id}")
def delete_employment(emp_id: int):
    with get_cursor() as cur:
        # 2026-08-19 (Ashish): mitane ke bajaye deleted_at bhar do.
        cur.execute("UPDATE mis_azad.www_employment SET deleted_at = NOW() "
                    "WHERE id = %s AND deleted_at IS NULL RETURNING id", (emp_id,))
        if not cur.fetchone(): raise HTTPException(404, "Employment not found")
    return {"deleted": emp_id}


@router.post("/{emp_id}/documents")
def add_document(emp_id: int, payload: dict):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_employment_documents"):
            # The import has a single proof-of-employment text column, so
            # there is only ever one document and it lives on the row.
            cur.execute(
                "UPDATE mis_azad.www_employment "
                "   SET documents_to_be_uploaded_document_proof_for_working_out = %s "
                " WHERE id = %s RETURNING id",
                (payload.get("file_name") or payload.get("file_path"), emp_id))
            if not cur.fetchone():
                raise HTTPException(404, "Employment not found")
            return {"id": emp_id}

        cur.execute("""
            INSERT INTO mis_azad.www_employment_documents (employment_id, document_type, file_name, file_path)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (emp_id, payload.get("document_type"), payload.get("file_name"), payload.get("file_path", "")))
        r = cur.fetchone()
        doc_id = r.get('id') if hasattr(r,'get') else r[0]
    return {"id": doc_id}


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_employment_documents"):
            # doc_id is the employment row id in this schema.
            cur.execute(
                "UPDATE mis_azad.www_employment "
                "   SET documents_to_be_uploaded_document_proof_for_working_out = NULL "
                " WHERE id = %s", (doc_id,))
            return {"deleted": doc_id}
        cur.execute("DELETE FROM mis_azad.www_employment_documents WHERE id = %s", (doc_id,))
    return {"deleted": doc_id}


# =============================================================================
# Document upload (multipart) for Employment
# =============================================================================
@router.post("/upload-doc")
async def upload_emp_doc(file: UploadFile = File(...)):
    """Store an employment document file. Returns its public URL."""
    allowed_ct = {"image/jpeg", "image/png", "image/webp", "image/avif", "image/gif",
                  "application/pdf",
                  "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                  "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
    allowed_ext = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif",
                   ".pdf", ".doc", ".docx", ".xls", ".xlsx"}
    ext = _os.path.splitext(file.filename or "")[1].lower()
    if (file.content_type or "") not in allowed_ct or ext not in allowed_ext:
        raise HTTPException(400, "File must be JPG, PNG, WebP, AVIF, GIF, PDF, DOC/DOCX or XLS/XLSX.")
    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "File exceeds the 25 MB size limit.")
    _os.makedirs(UPLOAD_DIR, exist_ok=True)
    saved_name = f"www_emp_doc_{uuid.uuid4().hex}{ext}"
    disk_path = _os.path.join(UPLOAD_DIR, saved_name)
    try:
        with open(disk_path, "wb") as dst:
            dst.write(content)
    except Exception:
        if _os.path.isfile(disk_path):
            _os.remove(disk_path)
        raise
    url = f"/uploads/{saved_name}"
    return {"ok": True, "url": url}


# =============================================================================
# EXPORT (Excel) — 2026-08-08
# Section-wise xlsx: Trainee Details + Employment Details + System.
# NB: www_employment has no deleted_at column — no soft-delete filter.
# =============================================================================
@router.get("/export/excel")
def export_employment_excel(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    type_of_enrollment: Optional[str] = None,
    type_of_job: Optional[str] = None,
    name: Optional[str] = None,
    min_salary: Optional[float] = None,
    max_salary: Optional[float] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    from datetime import date as _d
    from export_helper import multi_sheet_xlsx_response_v2

    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        has_table = _legacy.is_normalized(cur, "www_employment")

        if not has_table:
            lwhere, lparams = _legacy_emp_filters(
                state_code, centre_code, type_of_enrollment, type_of_job,
                name, min_salary, max_salary, batch_id=batch_id, district_code=district_code)
            if date_from: lwhere += " AND e.date_of_job >= %s"; lparams.append(date_from)
            if date_to:   lwhere += " AND e.date_of_job <= %s"; lparams.append(date_to)
            cur.execute(
                _legacy_emp_select() + lwhere +
                " ORDER BY e.date_of_job DESC NULLS LAST, e.id DESC",
                lparams)
            rows = _rows_to_dicts(cur)
            docs_map = {}
        else:
            where, params = ["1=1"], []
            if state_code:           where.append("t.state_code = %s");        params.append(state_code)
            if centre_code:          where.append("t.centre_code = %s");       params.append(centre_code)
            if batch_id:             where.append("t.batch_id = %s");          params.append(batch_id)
            if type_of_enrollment:   where.append("(e.type_of_enrollment = %s OR t.enrollment_type = %s)"); params.extend([type_of_enrollment, type_of_enrollment])
            if type_of_job:          where.append("e.type_of_job ILIKE %s");   params.append(f"%{type_of_job}%")
            if name:                 where.append(_legacy.name_match("t.name"));          params.append(_legacy.name_pattern(name))
            if min_salary is not None: where.append("e.salary >= %s");         params.append(min_salary)
            if max_salary is not None: where.append("e.salary <= %s");         params.append(max_salary)
            if date_from:            where.append("e.date_of_job >= %s");      params.append(date_from)
            if date_to:              where.append("e.date_of_job <= %s");      params.append(date_to)
            sql_where = " WHERE " + " AND ".join(where)
            cur.execute(
                "SELECT e.id, e.financial_year, e.type_of_enrollment, e.current_status, "
                "       e.current_status_other, e.type_of_job, e.where_location, "
                "       e.outside_location, e.date_of_job, e.salary, e.is_active, e.created_at, "
                "       t.enrollment_no, t.name, t.mobile, t.enrollment_type, "
                "       t.state_code, t.district_code, t.centre_code, t.area_code, "
                "       s.state_name, d.district_name, c.centre_name, a.area_name, "
                "       b.name AS batch_name, "
                "       (SELECT count(*) FROM mis_azad.www_employment_documents ed WHERE ed.employment_id = e.id) AS documents_count "
                "FROM mis_azad.www_employment e "
                "JOIN mis_azad.www_enrollment t ON t.id = e.trainee_id "
                "LEFT JOIN mis_azad.central_states    s ON s.state_code    = t.state_code "
                "LEFT JOIN mis_azad.central_districts d ON d.district_code = t.district_code "
                "LEFT JOIN mis_azad.central_centres   c ON c.centre_code   = t.centre_code "
                "LEFT JOIN mis_azad.www_areas     a ON a.area_code     = t.area_code "
                "LEFT JOIN mis_azad.www_master_batches b ON b.id = t.batch_id " +
                sql_where + " ORDER BY e.created_at DESC",
                params,
            )
            rows = _rows_to_dicts(cur)

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
        "Has PL", "Date of PL", "PL Number", "PL Attempts",
        "Internal Sakha Pass Date", "Internal Sakha Attempts",
        "External Sakha Pass Date", "External Sakha Attempts",
    ]
    emp_headers = [
        "Financial Year", "Type of Enrollment", "Current Status",
        "Current Status Other", "Type of Job", "Where Location",
        "Outside Location", "Date of Job", "Salary", "Is Active",
        "Work Proof Documents", "Documents Count",
    ]
    system_headers = ["Created At"]
    all_headers = (trainee_headers + licence_headers + emp_headers
                   + system_headers)
    n_t, n_l, n_e, n_s = (len(trainee_headers), len(licence_headers),
                          len(emp_headers), len(system_headers))
    group_headers = [
        (1, n_t, "Trainee Details"),
        (n_t + 1, n_t + n_l, "License & Sakha Tests"),
        (n_t + n_l + 1, n_t + n_l + n_e, "Employment Details"),
        (n_t + n_l + n_e + 1, n_t + n_l + n_e + n_s, "System"),
    ]

    data_rows = []
    for r in rows:
        data_rows.append([
            _g(r, "enrollment_no"), _g(r, "name"), _g(r, "mobile"),
            _g(r, "enrollment_type") or _g(r, "trainee_enrollment_type"),
            _g(r, "state_name") or _g(r, "state_code"),
            _g(r, "district_name") or _g(r, "district_code"),
            _g(r, "centre_name") or _g(r, "centre_code"),
            _g(r, "area_name") or _g(r, "area_code"),
            _g(r, "batch_name"), _g(r, "date_of_joining"),
            _g(r, "ll_date"), _g(r, "ll_number"), _g(r, "ll_attempts"),
            _g(r, "has_pl"), _g(r, "pl_date"), _g(r, "pl_number"),
            _g(r, "pl_attempts"),
            _g(r, "internal_pass_date"), _g(r, "internal_attempts"),
            _g(r, "external_pass_date"), _g(r, "external_attempts"),
            _g(r, "financial_year"), _g(r, "type_of_enrollment"),
            _g(r, "current_status"), _g(r, "current_status_other"),
            _g(r, "type_of_job"), _g(r, "where_location"),
            _g(r, "outside_location"), _g(r, "date_of_job"),
            _g(r, "salary"), _yn(r.get("is_active")),
            _g(r, "work_proof_documents"), _g(r, "documents_count"),
            _g(r, "created_at"),
        ])

    # 2026-08-26: WWW tracking columns (Created By / Updated By / Updated At)
    from routes._www_export_tracking import WWW_TRACK_HEADERS as _WT_H, www_tracking_cells as _wt_cells
    all_headers = list(all_headers) + _WT_H
    # 2026-09-19: Record Info banner over Created By + Updated By.
    group_headers = list(group_headers) + [(len(all_headers) - len(_WT_H) + 1, len(all_headers), "Record Info")]
    _wt_rows = _wt_cells(rows, "mis_azad.www_employment", "id")
    for _wi in range(len(data_rows)):
        data_rows[_wi] = list(data_rows[_wi]) + (_wt_rows[_wi] if _wi < len(_wt_rows) else ["", ""])
    sheets = [{
        "name": "Employment",
        "group_headers": group_headers,
        "headers": all_headers,
        "rows": data_rows,
    }]
    return multi_sheet_xlsx_response_v2(
        sheets,
        f"WWW_Employment_{_d.today().isoformat()}.xlsx",
    )
