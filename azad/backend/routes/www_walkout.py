"""WWW Walkout routes — CRUD + list with filters + walkin endpoint."""
from typing import Optional
from datetime import date
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(__file__)))
from database import get_cursor
from routes import _www_legacy as _legacy
from routes import _www_scope as _scope
from routes._www_list_sort import www_list_order

router = APIRouter(prefix="/api/www-walkout", tags=["www-walkout"])

# 2026-11-06 wwwWoListEmp: Employable status filter = walkout_stage in
# {After PL, Before IS, After IS, Before ES, After ES}. Used by the list,
# scoped list, and export branches below.
_WALKOUT_EMPLOYABLE_STAGES = [
    "After PL", "Before Internal Sakha", "After Internal Sakha",
    "Before External Sakha", "After External Sakha",
]


class WalkoutCreate(BaseModel):
    trainee_id: int
    walkout_date: Optional[date] = None
    walkout_stage: Optional[str] = None
    walkout_reason: Optional[str] = None
    walkout_reason_other: Optional[str] = None
    walkout_remark: Optional[str] = None  # 2026-08-21: free-text note
    status: Optional[str] = "Walkout"
    is_active: Optional[bool] = True


class WalkoutUpdate(BaseModel):
    walkout_date: Optional[date] = None
    walkout_stage: Optional[str] = None
    walkout_reason: Optional[str] = None
    walkout_reason_other: Optional[str] = None
    walkout_remark: Optional[str] = None  # 2026-08-21: free-text note
    is_active: Optional[bool] = None


class WalkinCreate(BaseModel):
    walkin_date: date
    walkin_stage: Optional[str] = None
    walkin_reason: Optional[str] = None
    walkin_reason_other: Optional[str] = None
    walkin_remark: Optional[str] = None  # 2026-08-21: free-text note


def _rows_to_dicts(cur):
    rows = cur.fetchall()
    if not rows: return []
    if hasattr(rows[0], "get"): return [dict(r) for r in rows]
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]


def _row_to_dict(cur):
    r = cur.fetchone()
    if r is None: return None
    if hasattr(r, "get"): return dict(r)
    cols = [d[0] for d in cur.description]
    return dict(zip(cols, r))


def _enriched_select():
    return """
        SELECT w.*,
               t.name, t.enrollment_no, t.state_code, t.district_code,
               t.centre_code, t.batch_id, t.mobile AS trainee_mobile,
               t.enrollment_date AS date_of_joining,
               t.enrollment_type AS trainee_enrollment_type,
               b.name AS batch_name,
               s.state_name,
               d.district_name,
               ct.centre_name
        FROM mis_azad.www_walkout w
        JOIN mis_azad.www_enrollment t  ON w.trainee_id = t.id
        LEFT JOIN mis_azad.www_master_batches b ON t.batch_id = b.id
        LEFT JOIN mis_azad.central_states    s  ON t.state_code   = s.state_code
        LEFT JOIN mis_azad.central_districts d  ON t.district_code= d.district_code
        LEFT JOIN mis_azad.central_centres   ct ON t.centre_code  = ct.centre_code
    """


# Legacy fallback.  Name collision: this deployment has a www_walkout
# table, but it is the spreadsheet import — one row per walkout, already
# carrying both the walkout and walk-in columns — rather than the
# normalized table that hangs off www_trainees.  Earlier deployments had
# to union walkout flags out of two unrelated Kobo forms; here a single
# straight read does it.
def _legacy_walkout_select():
    return (
        "SELECT w.id, w.enrollment_id AS trainee_id, "
        "       w.walkout_date, "
        "       NULLIF(TRIM(w.walkout_stage), '') AS walkout_stage, "
        "       NULLIF(TRIM(w.walkout_reason), '') AS walkout_reason, "
        "       NULLIF(TRIM(w.walkout_reason_other), '') AS walkout_reason_other, "
        "       NULLIF(TRIM(w.walkout_remark), '') AS walkout_remark, "
        "       COALESCE(NULLIF(TRIM(w.status), ''), 'Walkout') AS status, "
        "       NULL::boolean AS is_active, "
        "       NULLIF(TRIM(w.walkin_date), '') AS walkin_date, "
        "       NULLIF(TRIM(w.walkin_stage), '') AS walkin_stage, "
        "       NULLIF(TRIM(w.walkin_reason), '') AS walkin_reason, "
        "       NULLIF(TRIM(w.walkin_reason_other), '') AS walkin_reason_other, "
        "       NULLIF(TRIM(w.walkin_remark), '') AS walkin_remark, "
        "       w.created_at, "
        "       w.name, " + _legacy.enroll_no() + ", "
        "       " + _legacy.geo_cols() + ", "
        "       NULL::int AS batch_id, COALESCE(NULLIF(TRIM(_te.mobile), ''), NULLIF(TRIM(w.mobile), '')) AS trainee_mobile, "
        "       NULL::date AS date_of_joining, "
        "       COALESCE(NULLIF(TRIM(_te.type_of_enrollment), ''), NULLIF(TRIM(w.enrollment_type), '')) AS trainee_enrollment_type, "
        "       COALESCE(NULLIF(TRIM(_te.batch), ''), NULLIF(TRIM(w.batch), '')) AS batch_name, "
        "       w.state AS state_name, w.district AS district_name, "
        # 2026-08-12: www_walkout has an area column; without it the list and
        # the export both rendered the Area cell empty for every row.
        "       COALESCE(NULLIF(TRIM(_te.area), ''), NULLIF(TRIM(w.area), '')) AS area_name, "
        "       " + _legacy.centre_expr("w.centre") + " AS centre_name "
        "FROM mis_azad.www_walkout w " + _legacy.geo_joins("w") + _legacy.trainee_join("w")
    )


# Columns the imported www_walkout actually has, for the update path.
_LEGACY_WALKOUT_COLUMNS = {
    "walkout_date", "walkout_stage", "walkout_reason", "walkout_reason_other",
    "walkout_remark",  # 2026-08-21
    "status", "walkin_date", "walkin_stage", "walkin_reason",
    "walkin_reason_other", "walkin_remark",  # 2026-08-21
}


def _legacy_walkout_filters(state_code, centre_code, walkout_stage,
                            name, status, from_date, to_date, batch_id=None, district_code=None):
    conds = ["NULLIF(TRIM(w.name), '') IS NOT NULL", "w.deleted_at IS NULL"]
    params = []
    if state_code:    conds.append(_legacy.state_filter());     params.append(state_code)
    if district_code: conds.append(_legacy.district_filter());  params.append(district_code)
    if centre_code:   conds.append(_legacy.centre_filter("w")); params.append(centre_code)
    if walkout_stage: conds.append("w.walkout_stage = %s");     params.append(walkout_stage)
    # 2026-08-18: batch_id yahan tak pahunchta hi nahi tha (list aur export,
    # dono ka legacy branch use gira deta tha), isliye Batch chunne par list
    # badalti hi nahi thi. Dropdown master batch ka id bhejta hai aur import
    # batch ko text me rakhta hai -- to id ko naam me badal kar pehle walkout
    # ki apni cell, warna us trainee ke enrollment ki batch se milao. Wahi
    # tarika jo Employment list me lagaya tha.
    if batch_id:
        conds.append(
            "(NULLIF(TRIM(w.batch), '') = "
            "   (SELECT name FROM mis_azad.www_master_batches WHERE id = %s) "
            " OR EXISTS (SELECT 1 FROM mis_azad.www_enrollment _bw "
            "            WHERE _bw.id = w.enrollment_id "
            "              AND NULLIF(TRIM(_bw.batch), '') = "
            "                  (SELECT name FROM mis_azad.www_master_batches WHERE id = %s)))")
        params.append(batch_id); params.append(batch_id)
    if name:          conds.append("(" + _legacy.name_match("w.name") + " OR _te.enrollment_no ILIKE %s)");          params.append(_legacy.name_pattern(name)); params.append(_legacy.name_pattern(name))
    # 2026-11-06 wwwWoListEmp + 2026-11-07 wwwDashSplit:
    #   Employable = walkout_stage in employable set
    #   Walkout    = TRUE walkouts (walkout_stage NOT in employable set)
    if status == "Employable":
        conds.append("w.status = 'Walkout' AND w.walkout_stage = ANY(%s)")
        params.append(_WALKOUT_EMPLOYABLE_STAGES)
    elif status == "Walkout":
        conds.append("w.status = 'Walkout' AND (w.walkout_stage IS NULL OR TRIM(w.walkout_stage) = '' OR NOT (w.walkout_stage = ANY(%s)))")
        params.append(_WALKOUT_EMPLOYABLE_STAGES)
    elif status:     conds.append("w.status = %s");            params.append(status)
    if from_date:     conds.append("w.walkout_date >= %s");     params.append(from_date)
    if to_date:       conds.append("w.walkout_date <= %s");     params.append(to_date)
    return " WHERE " + " AND ".join(conds), params


@router.get("")
def list_walkout(
    request: Request,
    enrollment_id: Optional[int] = None,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    walkout_stage: Optional[str] = None,
    name: Optional[str] = None,
    status: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    sort_by: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=200),
):
    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        # ---- LEGACY FALLBACK: www_walkout is the import, not the normalized table ----
        if not _legacy.is_normalized(cur, "www_walkout"):
            lwhere, lparams = _legacy_walkout_filters(
                state_code, centre_code, walkout_stage, name, status, from_date, to_date,
                batch_id=batch_id, district_code=district_code)
            if enrollment_id:
                lwhere += " AND w.enrollment_id = %s"; lparams.append(enrollment_id)
            cur.execute(
                "SELECT COUNT(*) AS n FROM mis_azad.www_walkout w "
                + _legacy.geo_joins("w") + _legacy.trainee_join("w") + lwhere,
                lparams,
            )
            r = cur.fetchone(); total = r.get("n") if hasattr(r, "get") else r[0]
            cur.execute(
                _legacy_walkout_select() + lwhere +
                " ORDER BY " + www_list_order(sort_by, "w.name", "w.created_at", "w.created_at DESC NULLS LAST, w.id DESC", date_col="w.walkout_date") + " LIMIT %s OFFSET %s",
                lparams + [limit, (page - 1) * limit],
            )
            rows = _rows_to_dicts(cur)
            return {"total": total, "page": page, "limit": limit, "data": rows}

        where, params = ["1=1"], []
        if state_code:    where.append("t.state_code = %s");  params.append(state_code)
        if district_code: where.append("t.district_code = %s"); params.append(district_code)
        if centre_code:   where.append("t.centre_code = %s"); params.append(centre_code)
        if batch_id:      where.append("t.batch_id = %s");    params.append(batch_id)
        if walkout_stage: where.append("w.walkout_stage = %s"); params.append(walkout_stage)
        if name:          where.append(_legacy.name_match("t.name"));    params.append(_legacy.name_pattern(name))
        # 2026-11-06 wwwWoListEmp + 2026-11-07 wwwDashSplit
        if status == "Employable":
            where.append("w.status = 'Walkout' AND w.walkout_stage = ANY(%s)")
            params.append(_WALKOUT_EMPLOYABLE_STAGES)
        elif status == "Walkout":
            where.append("w.status = 'Walkout' AND (w.walkout_stage IS NULL OR TRIM(w.walkout_stage) = '' OR NOT (w.walkout_stage = ANY(%s)))")
            params.append(_WALKOUT_EMPLOYABLE_STAGES)
        elif status:     where.append("w.status = %s");      params.append(status)
        if from_date:     where.append("w.walkout_date >= %s"); params.append(from_date)
        if to_date:       where.append("w.walkout_date <= %s"); params.append(to_date)
        sql_where = " WHERE " + " AND ".join(where)
        offset = (page - 1) * limit
        cur.execute(f"SELECT COUNT(*) AS n FROM mis_azad.www_walkout w JOIN mis_azad.www_enrollment t ON w.trainee_id = t.id {sql_where}", params)
        r = cur.fetchone(); total = r.get("n") if hasattr(r, "get") else r[0]
        cur.execute(_enriched_select() + sql_where + " ORDER BY " + www_list_order(sort_by, "w.name", "w.created_at", "w.created_at DESC NULLS LAST, w.id DESC", date_col="w.walkout_date") + " LIMIT %s OFFSET %s", params + [limit, offset])
        rows = _rows_to_dicts(cur)
        return {"total": total, "page": page, "limit": limit, "data": rows}

@router.get("/eligible-trainees")
def eligible_trainees(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    name: Optional[str] = None,
    # 2026-09-21: was Query(200, ge=1, le=500) -- too small, and it silently
    # broke the Add-Walkout trainee search. The picker (loadWwwWoEligibleTrainees
    # in app.js) fetches this list ONCE per state+centre, passes no limit, and
    # then does its Name / Batch / Type filtering in the BROWSER. So the 200-row
    # cap was not "page one of many", it was the entire universe the search box
    # could ever see: with 279 eligible trainees at North Kolkata, everyone from
    # "Saloni Das" onwards was unreachable and the screen answered "No trainees
    # match the selected filters" for a trainee who was perfectly eligible
    # (reported for 'Shaista rafique', row 225 of 279). 5 of the 7 centres were
    # over the cap. The rows are small and one centre holds a few hundred
    # trainees, so serve the whole scope and let the picker filter it.
    limit: int = Query(2000, ge=1, le=5000),
):
    """Trainees who are NOT currently in an active Walkout (excludes those with Walkout-status entries)."""
    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_trainees"):
            # www_enrollment is the trainee master here; exclude anyone who
            # already appears as an open walkout.
            where = [
                "NULLIF(TRIM(e.name), '') IS NOT NULL",
                "NOT EXISTS (SELECT 1 FROM mis_azad.www_walkout w "
                "            WHERE w.enrollment_id = e.id "
                "              AND COALESCE(w.status, 'Walkout') = 'Walkout')",
                # 2026-09-10: once a trainee's Employment details are filled in
                # (non-draft), they are employed and can no longer walk out ->
                # exclude them from the Add-Walkout eligible list.
                "NOT EXISTS (SELECT 1 FROM mis_azad.www_employment emp "
                "            WHERE emp.enrollment_id = e.id "
                "              AND emp.deleted_at IS NULL "
                "              AND COALESCE(emp.is_draft, false) = false)",
            ]
            params = []
            if state_code:  where.append(_legacy.state_filter());     params.append(state_code)
            if district_code: where.append(_legacy.district_filter()); params.append(district_code)
            if centre_code: where.append(_legacy.centre_filter("e")); params.append(centre_code)
            if name:        where.append(_legacy.name_match("e.name"));          params.append(_legacy.name_pattern(name))
            cur.execute(
                "SELECT e.id, e.name, e.enrollment_no, e.mobile, "
                "       " + _legacy.geo_cols() + ", "
                "       NULL::int AS batch_id, "
                "       e.type_of_enrollment AS enrollment_type, e.status, e.enrollment_date, "
                "       NULLIF(TRIM(e.batch), '') AS batch_name, "
                "       e.state AS state_name, "
                "       " + _legacy.centre_expr("e.centre") + " AS centre_name "
                "FROM mis_azad.www_enrollment e " + _legacy.geo_joins("e") +
                "WHERE " + " AND ".join(where) + " ORDER BY e.name LIMIT %s",
                params + [limit],
            )
            return _rows_to_dicts(cur)
        where, params = ["t.id NOT IN (SELECT trainee_id FROM mis_azad.www_walkout WHERE status = 'Walkout' AND is_active = TRUE)"], []
        if state_code:  where.append("t.state_code = %s");  params.append(state_code)
        if district_code: where.append("t.district_code = %s"); params.append(district_code)
        if centre_code: where.append("t.centre_code = %s"); params.append(centre_code)
        if batch_id:    where.append("t.batch_id = %s");    params.append(batch_id)
        if name:        where.append(_legacy.name_match("t.name"));    params.append(_legacy.name_pattern(name))
        sql = f"""
            SELECT t.id, t.name, t.enrollment_no, t.mobile, t.state_code, t.centre_code, t.batch_id,
                   t.enrollment_type, t.status,
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

@router.get("/{wid}")
def get_walkout(request: Request, wid: int):
    with get_cursor() as cur:
        if not _legacy.is_normalized(cur, "www_walkout"):
            cur.execute(_legacy_walkout_select() + " WHERE w.id = %s", (wid,))
            rec = _row_to_dict(cur)
            if not rec:
                raise HTTPException(404, "Walkout not found")
            _scope.guard_detail(request, rec)
            return rec
        cur.execute(_enriched_select() + " WHERE w.id = %s", (wid,))
        rec = _row_to_dict(cur)
        if not rec: raise HTTPException(404, "Walkout not found")
        _scope.guard_detail(request, rec)
    return rec


@router.post("")
def create_walkout(payload: WalkoutCreate):
    with get_cursor() as cur:
        if not _legacy.is_normalized(cur, "www_walkout"):
            cur.execute("""
                INSERT INTO mis_azad.www_walkout
                  (enrollment_id, name, mobile, enrollment_type,
                   state, district, centre, area, batch,
                   walkout_date, walkout_stage, walkout_reason,
                   walkout_reason_other, walkout_remark, status)
                SELECT e.id, e.name, e.mobile, e.type_of_enrollment,
                       e.state, e.district, e.centre, e.area, e.batch,
                       %s, %s, %s, %s, %s, %s
                FROM mis_azad.www_enrollment e WHERE e.id = %s
                RETURNING id
            """, (payload.walkout_date, payload.walkout_stage,
                  payload.walkout_reason, payload.walkout_reason_other,
                  payload.walkout_remark,
                  payload.status or "Walkout", payload.trainee_id))
            r = cur.fetchone()
            if not r: raise HTTPException(400, "Trainee not found")
            return {"id": r.get("id") if hasattr(r, "get") else r[0]}

        cur.execute("SELECT id FROM mis_azad.www_enrollment WHERE id = %s", (payload.trainee_id,))
        if not cur.fetchone(): raise HTTPException(400, "Trainee not found")
        cur.execute("""
            INSERT INTO mis_azad.www_walkout
              (trainee_id, walkout_date, walkout_stage, walkout_reason, walkout_reason_other, walkout_remark, status, is_active)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
        """, (payload.trainee_id, payload.walkout_date, payload.walkout_stage,
              payload.walkout_reason, payload.walkout_reason_other, payload.walkout_remark,
              payload.status or "Walkout", payload.is_active))
        r = cur.fetchone()
        new_id = r.get("id") if hasattr(r,"get") else r[0]
    return {"id": new_id}


@router.put("/{wid}")
def update_walkout(wid: int, payload: WalkoutUpdate):
    updates = {k: v for k, v in payload.dict(exclude_unset=True).items()}
    if not updates: return {"id": wid, "updated": 0}
    with get_cursor() as cur:
        if not _legacy.is_normalized(cur, "www_walkout"):
            # The import has neither is_active nor updated_at.
            lupdates = {k: v for k, v in updates.items()
                        if k in _LEGACY_WALKOUT_COLUMNS}
            if not lupdates:
                return {"id": wid, "updated": 0}
            set_parts = ", ".join(f"{k} = %s" for k in lupdates)
            cur.execute(
                f"UPDATE mis_azad.www_walkout SET {set_parts} WHERE id = %s RETURNING id",
                list(lupdates.values()) + [wid])
            if not cur.fetchone(): raise HTTPException(404, "Walkout not found")
            return {"id": wid, "updated": len(lupdates)}

        set_parts = ", ".join(f"{k} = %s" for k in updates) + ", updated_at = CURRENT_TIMESTAMP"
        params = list(updates.values()) + [wid]
        cur.execute(f"UPDATE mis_azad.www_walkout SET {set_parts} WHERE id = %s RETURNING id", params)
        if not cur.fetchone(): raise HTTPException(404, "Walkout not found")
    return {"id": wid, "updated": len(updates)}


@router.post("/{wid}/walkin")
def add_walkin(wid: int, payload: WalkinCreate):
    """Record a Walk-in for an existing Walkout, flipping status to Walkin."""
    with get_cursor() as cur:
        # The import has no updated_at column; everything else lines up.
        stamp = "" if not _legacy.is_normalized(cur, "www_walkout") \
                else ", updated_at = CURRENT_TIMESTAMP"
        cur.execute(f"""
            UPDATE mis_azad.www_walkout
            SET walkin_date = %s,
                walkin_stage = %s,
                walkin_reason = %s,
                walkin_reason_other = %s,
                walkin_remark = %s,
                status = 'Walkin'{stamp}
            WHERE id = %s
            RETURNING id
        """, (payload.walkin_date, payload.walkin_stage, payload.walkin_reason,
              payload.walkin_reason_other, payload.walkin_remark, wid))
        if not cur.fetchone(): raise HTTPException(404, "Walkout not found")
    return {"id": wid, "status": "Walkin"}


@router.delete("/{wid}")
def delete_walkout(wid: int):
    with get_cursor() as cur:
        # 2026-08-19 (Ashish): mitane ke bajaye deleted_at bhar do.
        cur.execute("UPDATE mis_azad.www_walkout SET deleted_at = NOW() "
                    "WHERE id = %s AND deleted_at IS NULL RETURNING id", (wid,))
        if not cur.fetchone(): raise HTTPException(404, "Walkout not found")
    return {"deleted": wid}


# =============================================================================
# EXPORT (Excel) — 2026-08-08
# Section-wise xlsx: Trainee Details + Walkout Details + System.
# Simple: only exports v2 www_walkout rows. Legacy dual-source (union of
# www_ll_form + www_status_of_sakha_test_internal) is deferred — the v2 list
# is the modern source of truth for this feature.
# =============================================================================
@router.get("/export/excel")
def export_walkout_excel(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    enrollment_type: Optional[str] = None,
    walkout_stage: Optional[str] = None,
    name: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    from datetime import date as _d
    from export_helper import multi_sheet_xlsx_response_v2

    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        has_table = _legacy.is_normalized(cur, "www_walkout")

        if not has_table:
            lwhere, lparams = _legacy_walkout_filters(
                state_code, centre_code, walkout_stage, name, status,
                date_from, date_to, batch_id=batch_id, district_code=district_code)
            cur.execute(
                _legacy_walkout_select() + lwhere +
                " ORDER BY w.walkout_date DESC NULLS LAST, w.id DESC",
                lparams)
            rows = _rows_to_dicts(cur)
        else:
            where, params = ["1=1"], []
            if state_code:      where.append("t.state_code = %s");        params.append(state_code)
            if centre_code:     where.append("t.centre_code = %s");       params.append(centre_code)
            if batch_id:        where.append("t.batch_id = %s");          params.append(batch_id)
            if enrollment_type: where.append("t.enrollment_type = %s");   params.append(enrollment_type)
            if walkout_stage:   where.append("w.walkout_stage = %s");     params.append(walkout_stage)
            if name:            where.append(_legacy.name_match("t.name"));          params.append(_legacy.name_pattern(name))
            # 2026-11-06 wwwWoListEmp + 2026-11-07 wwwDashSplit
            if status == "Employable":
                where.append("w.status = 'Walkout' AND w.walkout_stage = ANY(%s)")
                params.append(_WALKOUT_EMPLOYABLE_STAGES)
            elif status == "Walkout":
                where.append("w.status = 'Walkout' AND (w.walkout_stage IS NULL OR TRIM(w.walkout_stage) = '' OR NOT (w.walkout_stage = ANY(%s)))")
                params.append(_WALKOUT_EMPLOYABLE_STAGES)
            elif status:   where.append("w.status = %s");            params.append(status)
            if date_from:       where.append("w.walkout_date >= %s");     params.append(date_from)
            if date_to:         where.append("w.walkout_date <= %s");     params.append(date_to)
            sql_where = " WHERE " + " AND ".join(where)
            cur.execute(
                "SELECT w.walkout_date, w.walkout_stage, w.walkout_reason, w.walkout_reason_other, "
                "       w.status, w.is_active, w.walkin_date, w.walkin_stage, "
                "       w.walkin_reason, w.walkin_reason_other, w.created_at, "
                "       t.enrollment_no, t.name, t.mobile, t.enrollment_type, "
                "       t.state_code, t.district_code, t.centre_code, t.area_code, "
                "       s.state_name, d.district_name, c.centre_name, a.area_name, "
                "       b.name AS batch_name "
                "FROM mis_azad.www_walkout w "
                "JOIN mis_azad.www_enrollment t ON t.id = w.trainee_id "
                "LEFT JOIN mis_azad.central_states    s ON s.state_code    = t.state_code "
                "LEFT JOIN mis_azad.central_districts d ON d.district_code = t.district_code "
                "LEFT JOIN mis_azad.central_centres   c ON c.centre_code   = t.centre_code "
                "LEFT JOIN mis_azad.www_areas     a ON a.area_code     = t.area_code "
                "LEFT JOIN mis_azad.www_master_batches b ON b.id = t.batch_id " +
                sql_where + " ORDER BY w.created_at DESC",
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
    ]
    wo_headers = [
        "Walkout Date", "Walkout Stage", "Walkout Reason",
        "Walkout Reason Other", "Status", "Is Active",
        "Walkin Date", "Walkin Stage", "Walkin Reason",
        "Walkin Reason Other",
    ]
    system_headers = ["Created At"]
    all_headers = trainee_headers + wo_headers + system_headers
    n_t, n_w, n_s = len(trainee_headers), len(wo_headers), len(system_headers)
    group_headers = [
        (1, n_t, "Trainee Details"),
        (n_t + 1, n_t + n_w, "Walkout Details"),
        (n_t + n_w + 1, n_t + n_w + n_s, "System"),
    ]

    data_rows = []
    for r in rows:
        data_rows.append([
            _g(r, "enrollment_no"), _g(r, "name"),
            _g(r, "mobile") or _g(r, "trainee_mobile"),
            _g(r, "enrollment_type") or _g(r, "trainee_enrollment_type"),
            _g(r, "state_name") or _g(r, "state_code"),
            _g(r, "district_name") or _g(r, "district_code"),
            _g(r, "centre_name") or _g(r, "centre_code"),
            _g(r, "area_name") or _g(r, "area_code"),
            _g(r, "batch_name"),
            _g(r, "walkout_date"), _g(r, "walkout_stage"),
            _g(r, "walkout_reason"), _g(r, "walkout_reason_other"),
            _g(r, "status"), _yn(r.get("is_active")),
            _g(r, "walkin_date"), _g(r, "walkin_stage"),
            _g(r, "walkin_reason"), _g(r, "walkin_reason_other"),
            _g(r, "created_at"),
        ])

    # 2026-08-26: WWW tracking columns (Created By / Updated By / Updated At)
    from routes._www_export_tracking import WWW_TRACK_HEADERS as _WT_H, www_tracking_cells as _wt_cells
    all_headers = list(all_headers) + _WT_H
    # 2026-09-19: Record Info banner over Created By + Updated By.
    group_headers = list(group_headers) + [(len(all_headers) - len(_WT_H) + 1, len(all_headers), "Record Info")]
    _wt_rows = _wt_cells(rows, "mis_azad.www_walkout", "id")
    for _wi in range(len(data_rows)):
        data_rows[_wi] = list(data_rows[_wi]) + (_wt_rows[_wi] if _wi < len(_wt_rows) else ["", ""])
    sheets = [{
        "name": "Walkout",
        "group_headers": group_headers,
        "headers": all_headers,
        "rows": data_rows,
    }]
    return multi_sheet_xlsx_response_v2(
        sheets,
        f"WWW_Walkout_{_d.today().isoformat()}.xlsx",
    )


# -----------------------------------------------------------------------------
# 2026-11-06 plwo AUTOSTAGE -- suggest a 'Stage of Walkout' for the Add-Walkout
# modal.  Priority = most-recent completed sub-module (ES > IS > PL > LL).
# Only looks at non-deleted rows.  Returns {suggested_stage: 'After LL'|...|None}.
# The frontend prefills the Stage select, user can still override.
# -----------------------------------------------------------------------------
@router.get("/trainee-stage/{trainee_id}")
def trainee_stage_suggestion(trainee_id: int):
    with get_cursor() as cur:
        def _has(tbl):
            try:
                cur.execute(
                    "SELECT 1 FROM mis_azad." + tbl +
                    " WHERE enrollment_id = %s"
                    "   AND COALESCE(deleted_at::text, '') = ''"
                    " LIMIT 1",
                    (trainee_id,),
                )
                return cur.fetchone() is not None
            except Exception:
                return False
        if _has("www_sakha_external"): return {"suggested_stage": "After External Sakha"}
        if _has("www_sakha_internal"): return {"suggested_stage": "After Internal Sakha"}
        if _has("www_pl"):             return {"suggested_stage": "After PL"}
        if _has("www_ll"):             return {"suggested_stage": "After LL"}
        # 2026-11-06 wwwDashFix: default to 'Before LL' so the dropdown
        # is never blank -- user can still override.
        return {"suggested_stage": "Before LL"}
