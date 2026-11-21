"""WWW GBV — list + CRUD.

Note the name collision: this deployment has a www_gbv table, but it is
the spreadsheet import rather than the normalized one, so the routes
switch on the presence of the trainee_id FK instead of on the table
existing at all.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from routes import _www_legacy as _legacy
from routes import _www_scope as _scope
from routes._www_list_sort import www_list_order

router = APIRouter(prefix="/api/www-gbv", tags=["WWW GBV"])


def _legacy_row_select():
    """SELECT list mapping an imported www_gbv row onto API field names."""
    return (
        "SELECT g.id, g.enrollment_id AS trainee_id, "
        # 2026-08-18: raw text par View "--" dikhata tha aur Edit form
        # "No" ko "Yes" par set kar deta tha. Asli boolean bhejo.
        "       CASE LOWER(TRIM(COALESCE(g.is_the_trainee_a_survivor_of_violence_y_n, '')))   WHEN 'yes' THEN TRUE  WHEN 'y' THEN TRUE   WHEN 'true' THEN TRUE WHEN '1' THEN TRUE   WHEN 'no' THEN FALSE  WHEN 'n' THEN FALSE   WHEN 'false' THEN FALSE WHEN '0' THEN FALSE   ELSE NULL END "
        "           AS is_survivor, "
        "       CASE LOWER(TRIM(COALESCE(g.has_she_mentioned_it_in_the_enrollment_form, '')))   WHEN 'yes' THEN TRUE  WHEN 'y' THEN TRUE   WHEN 'true' THEN TRUE WHEN '1' THEN TRUE   WHEN 'no' THEN FALSE  WHEN 'n' THEN FALSE   WHEN 'false' THEN FALSE WHEN '0' THEN FALSE   ELSE NULL END "
        "           AS mentioned_in_enrollment, "
        "       NULLIF(TRIM(g.are_you_facing_or_have_faced_violence_during_the_traini), '') "
        "           AS facing_during_training, "
        "       NULLIF(TRIM(g.if_yes_where_did_the_violence_take_place), '') "
        "           AS violence_location, "
        "       NULLIF(TRIM(g.if_inside_by_known_or_unknown), '') AS inside_known_unknown, "
        "       NULLIF(TRIM(g.if_known_state_relation_with_person), '') AS known_relation, "
        "       NULL::text AS outside_by_whom, "
        "       " + _legacy.multi_select_array("g.what_form_of_violence") + " AS form_of_violence, "
        "       CASE LOWER(TRIM(COALESCE(g.do_you_want_support, '')))   WHEN 'yes' THEN TRUE  WHEN 'y' THEN TRUE   WHEN 'true' THEN TRUE WHEN '1' THEN TRUE   WHEN 'no' THEN FALSE  WHEN 'n' THEN FALSE   WHEN 'false' THEN FALSE WHEN '0' THEN FALSE   ELSE NULL END "
        "           AS do_you_want_support, "
        "       " + _legacy.multi_select_array("g.if_yes_what_kind_of_support_has_azad_provided") +
        "           AS support_kinds, "
        "       NULLIF(TRIM(g.if_any_other_what), '') AS any_other_what, "
        "       NULLIF(TRIM(g.if_before_training_what_is_the_time_period), '') "
        "           AS before_training_period, "
        # 2026-08-17: "Time of the Incident" ka asli jawab -- Before Training /
        # During Training / Both. Ye SELECT me tha hi nahi, isliye List ne
        # galti se facing_during_training (Yes/No) dikhana shuru kar diya tha.
        "       NULLIF(TRIM(g.if_yes_when_did_the_violence_happen), '') "
        "           AS violence_when, "
        "       NULL::boolean AS is_draft, "
        "       g.created_at, "
        # 2026-09-25: display-only fix for corrupted rows -- see _te_fb join below.
        "       COALESCE(" + _legacy.enroll_no().replace(' AS enrollment_no', '') + ", _te_fb.enrollment_no) AS enrollment_no, "
        "       COALESCE("
        "          CASE WHEN LOWER(TRIM(COALESCE(g.name,''))) IN ('2 wheeler','4 wheeler','either 2 wheeler or 4 wheeler') "
        "               THEN NULLIF(TRIM(g.date_of_ll), '') "
        "               ELSE g.name END, "
        "          NULLIF(TRIM(_te.name), ''), NULLIF(TRIM(_te_fb.name), ''), g.name) AS name, "
        # 2026-08-18: mobile/batch placeholder the, isliye View par
        # hamesha "--" dikhta tha. _te = www_enrollment (trainee_join).
        "       NULLIF(TRIM(_te.mobile), '') AS mobile, "
        "       " + _legacy.geo_cols() + ", "
        "       NULLIF(TRIM(COALESCE(_te.batch, _te_fb.batch)), '') AS batch_name, NULL::int AS batch_id, "
        "       g.date_of_joining "
        "FROM mis_azad.www_gbv g " + _legacy.geo_joins("g") + _legacy.trainee_join("g") + 
        # 2026-09-25: fallback join for the 194 corrupted rows where the FK is
        # NULL. Uses the real name (which lives in date_of_ll on those rows)
        # + centre. LATERAL LIMIT 1 so each GBV row matches at most one
        # enrollment (there can be many trainees with the same name at a
        # centre; the pick is deterministic -- highest enrollment id).
        " LEFT JOIN LATERAL ("
        "   SELECT id, name, enrollment_no, batch "
        "     FROM mis_azad.www_enrollment "
        "    WHERE deleted_at IS NULL "
        "      AND LOWER(TRIM(name)) = LOWER(TRIM(COALESCE(NULLIF(TRIM(g.date_of_ll), ''), g.name))) "
        "      AND LOWER(TRIM(COALESCE(centre, ''))) = LOWER(TRIM(COALESCE(g.centre, ''))) "
        "    ORDER BY id DESC LIMIT 1 "
        " ) _te_fb ON _te.id IS NULL "
    )


def _legacy_filters(facing_during_training, violence_when, form_of_violence, support_kind,
                    batch_id, name):
    """WHERE clause + params shared by the legacy list and export paths."""
    conds = ["NULLIF(TRIM(g.name), '') IS NOT NULL", "g.deleted_at IS NULL"]
    params = []
    if name:
        conds.append("(" + _legacy.name_match("g.name") + " OR _te.enrollment_no ILIKE %s)"); params.append(_legacy.name_pattern(name)); params.append(_legacy.name_pattern(name))
    if facing_during_training:
        conds.append("g.are_you_facing_or_have_faced_violence_during_the_traini = %s")
        params.append(facing_during_training)
    # 2026-08-19: Incident Time filter — Before / During / Both.
    if violence_when:
        conds.append("g.if_yes_when_did_the_violence_happen = %s")
        params.append(violence_when)
    # `= ANY((SELECT ...))` reads as ANY's *subquery* form, so Postgres
    # compared the filter value against the returned array itself and failed
    # with "malformed array literal". Containment takes the array form.
    if form_of_violence:
        conds.append(_legacy.multi_select_array("g.what_form_of_violence")
                     + " @> ARRAY[%s]::text[]")
        params.append(form_of_violence)
    if support_kind:
        conds.append(_legacy.multi_select_array("g.if_yes_what_kind_of_support_has_azad_provided")
                     + " @> ARRAY[%s]::text[]")
        params.append(support_kind)
    # 2026-11-03: Batch filter did nothing on the legacy branch because
    # batch_id was in the signature but never added to the WHERE. First
    # pass referenced _te_fb.batch directly, but _te_fb only exists on the
    # row SELECT's LATERAL join - the COUNT query errored "missing
    # FROM-clause entry for _te_fb". Hotfix: match _te.batch, else an
    # EXISTS subquery that resolves the fallback trainee by name+centre.
    if batch_id:
        conds.append(
            "(NULLIF(TRIM(_te.batch), '') = "
            "   (SELECT name FROM mis_azad.www_master_batches WHERE id = %s) "
            " OR EXISTS ("
            "   SELECT 1 FROM mis_azad.www_enrollment _bg "
            "    WHERE _bg.deleted_at IS NULL "
            "      AND LOWER(TRIM(_bg.name)) = LOWER(TRIM(COALESCE(NULLIF(TRIM(g.date_of_ll), ''), g.name))) "
            "      AND LOWER(TRIM(COALESCE(_bg.centre, ''))) = LOWER(TRIM(COALESCE(g.centre, ''))) "
            "      AND NULLIF(TRIM(_bg.batch), '') = "
            "          (SELECT name FROM mis_azad.www_master_batches WHERE id = %s)))")
        params.append(batch_id); params.append(batch_id)
    return "WHERE " + " AND ".join(conds), params


def _yn(v):
    """The import stores the yes/no answers as text, not booleans."""
    return None if v is None else ("Yes" if v else "No")


# API field -> imported www_gbv column, for the legacy write path.
# outside_by_whom and is_draft have no home on the import and are dropped.
_LEGACY_UPDATE_MAP = {
    "is_survivor":            "is_the_trainee_a_survivor_of_violence_y_n",
    "mentioned_in_enrollment": "has_she_mentioned_it_in_the_enrollment_form",
    "facing_during_training": "are_you_facing_or_have_faced_violence_during_the_traini",
    "violence_when":          "if_yes_when_did_the_violence_happen",
    "before_training_period": "if_before_training_what_is_the_time_period",
    "violence_location":      "if_yes_where_did_the_violence_take_place",
    "inside_known_unknown":   "if_inside_by_known_or_unknown",
    "known_relation":         "if_known_state_relation_with_person",
    "form_of_violence":       "what_form_of_violence",
    "do_you_want_support":    "do_you_want_support",
    "support_kinds":          "if_yes_what_kind_of_support_has_azad_provided",
    "any_other_what":         "if_any_other_what",
}


class GBVCreate(BaseModel):
    trainee_id: int
    is_survivor: Optional[bool] = None
    mentioned_in_enrollment: Optional[bool] = None
    facing_during_training: Optional[str] = None
    violence_when: Optional[str] = None
    before_training_period: Optional[str] = None
    violence_location: Optional[str] = None
    inside_known_unknown: Optional[str] = None
    known_relation: Optional[str] = None
    outside_by_whom: Optional[str] = None
    form_of_violence: Optional[List[str]] = None
    do_you_want_support: Optional[bool] = None
    support_kinds: Optional[List[str]] = None
    any_other_what: Optional[str] = None
    is_draft: Optional[bool] = False


class GBVUpdate(BaseModel):
    is_survivor: Optional[bool] = None
    mentioned_in_enrollment: Optional[bool] = None
    facing_during_training: Optional[str] = None
    violence_when: Optional[str] = None
    before_training_period: Optional[str] = None
    violence_location: Optional[str] = None
    inside_known_unknown: Optional[str] = None
    known_relation: Optional[str] = None
    outside_by_whom: Optional[str] = None
    form_of_violence: Optional[List[str]] = None
    do_you_want_support: Optional[bool] = None
    support_kinds: Optional[List[str]] = None
    any_other_what: Optional[str] = None
    is_draft: Optional[bool] = None


def _row_select():
    return (
        "SELECT g.*, "
        "       t.enrollment_no, t.name, t.mobile, t.state_code, t.district_code, t.centre_code, "
        "       COALESCE(b.name, NULL) AS batch_name, b.id AS batch_id, "
        "       t.enrollment_date AS date_of_joining "
        "FROM www_gbv g "
        "JOIN www_enrollment t ON t.id = g.trainee_id "
        "LEFT JOIN www_master_batches b ON b.id = t.batch_id "
    )


@router.get("")
def list_gbv(
    request: Request,
    enrollment_id: Optional[int] = None,
    facing_during_training: Optional[str] = None,
    violence_when: Optional[str] = None,
    form_of_violence: Optional[str] = None,
    support_kind: Optional[str] = None,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    name: Optional[str] = None,
    sort_by: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
):
    page = max(page, 1); limit = max(limit, 1); offset = (page - 1) * limit
    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        # ---- LEGACY FALLBACK: www_gbv is the import, not the normalized table ----
        if not _legacy.is_normalized(cur, "www_gbv"):
            lwhere, lparams = _legacy_filters(
                facing_during_training, violence_when, form_of_violence, support_kind, batch_id, name)
            # 2026-08-12: the export honoured state/centre, the list did not
            # accept them at all, so filtering the page changed nothing.
            if centre_code:
                lwhere += " AND " + _legacy.centre_filter("g"); lparams.append(centre_code)
            if state_code:
                lwhere += " AND " + _legacy.state_filter(); lparams.append(state_code)
            if district_code:
                lwhere += " AND " + _legacy.district_filter(); lparams.append(district_code)
            if enrollment_id:
                lwhere += " AND g.enrollment_id = %s"; lparams.append(enrollment_id)
            _df = request.query_params.get("date_from"); _dt = request.query_params.get("date_to")
            if _df: lwhere += " AND g.created_at >= %s"; lparams.append(_df)
            if _dt: lwhere += " AND g.created_at <= %s"; lparams.append(_dt)
            cur.execute(
                "SELECT COUNT(*) AS total FROM mis_azad.www_gbv g "
                + _legacy.geo_joins("g") + _legacy.trainee_join("g") + lwhere,
                lparams,
            )
            total = cur.fetchone()["total"]
            cur.execute(
                _legacy_row_select() + lwhere + " ORDER BY " + www_list_order(sort_by, "g.name", "g.id", "g.id DESC") + " LIMIT %s OFFSET %s",
                lparams + [limit, offset],
            )
            rows = cur.fetchall()
            return {"total": total, "page": page, "limit": limit, "data": rows}

        conds = ["g.deleted_at IS NULL"]; params = []
        if facing_during_training: conds.append("g.facing_during_training = %s"); params.append(facing_during_training)
        if violence_when:          conds.append("g.violence_when = %s");          params.append(violence_when)
        if form_of_violence:       conds.append("%s = ANY(g.form_of_violence)");  params.append(form_of_violence)
        if support_kind:           conds.append("%s = ANY(g.support_kinds)");     params.append(support_kind)
        if state_code:            conds.append("t.state_code = %s");              params.append(state_code)
        if district_code:         conds.append("t.district_code = %s");           params.append(district_code)
        if centre_code:           conds.append("t.centre_code = %s");             params.append(centre_code)
        if batch_id:               conds.append("t.batch_id = %s");               params.append(batch_id)
        if name:                   conds.append(_legacy.name_match("t.name"));               params.append(_legacy.name_pattern(name))
        where = "WHERE " + " AND ".join(conds)
        cur.execute(
            "SELECT COUNT(*) AS total FROM www_gbv g "
            "JOIN www_enrollment t ON t.id = g.trainee_id " + where,
            params,
        )
        total = cur.fetchone()["total"]
        sql = _row_select() + where + " ORDER BY " + www_list_order(sort_by, "g.name", "g.created_at", "g.created_at DESC NULLS LAST, g.id DESC") + " LIMIT %s OFFSET %s"
        cur.execute(sql, params + [limit, offset])
        rows = cur.fetchall()
        return {"total": total, "page": page, "limit": limit, "data": rows}

@router.get("/{gbv_id}")
def get_gbv(request: Request, gbv_id: int):
    with get_cursor() as cur:
        if not _legacy.is_normalized(cur, "www_gbv"):
            cur.execute(_legacy_row_select() + "WHERE g.id = %s", (gbv_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "GBV record not found.")
            _scope.guard_detail(request, row)
            return row

        cur.execute(_row_select() + "WHERE g.id = %s AND g.deleted_at IS NULL", (gbv_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "GBV record not found.")
    _scope.guard_detail(request, row)
    return row

@router.post("")
def create_gbv(body: GBVCreate):
    with get_cursor() as cur:
        # 2026-08-18 (Ashish): flow guard -- picker ki rok server par bhi.
        _legacy.assert_flow(cur, body.trainee_id, requires="ll", stage="GBV record")
        if not _legacy.is_normalized(cur, "www_gbv"):
            cur.execute(
                "INSERT INTO mis_azad.www_gbv "
                "    (enrollment_id, name, state, district, centre, date_of_joining, "
                "     is_the_trainee_a_survivor_of_violence_y_n, "
                "     has_she_mentioned_it_in_the_enrollment_form, "
                "     are_you_facing_or_have_faced_violence_during_the_traini, "
                "     if_yes_when_did_the_violence_happen, "
                "     if_before_training_what_is_the_time_period, "
                "     if_yes_where_did_the_violence_take_place, "
                "     if_inside_by_known_or_unknown, if_known_state_relation_with_person, "
                "     what_form_of_violence, do_you_want_support, "
                "     if_yes_what_kind_of_support_has_azad_provided, if_any_other_what) "
                "SELECT e.id, e.name, e.state, e.district, e.centre, "
                "       e.enrollment_date, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s "
                "FROM mis_azad.www_enrollment e WHERE e.id = %s "
                "RETURNING id",
                (_yn(body.is_survivor), _yn(body.mentioned_in_enrollment),
                 body.facing_during_training,
                 body.violence_when, body.before_training_period,
                 body.violence_location,
                 body.inside_known_unknown, body.known_relation,
                 # 2026-09-02: join multi-selects with "|" (the delimiter the
                 # READ side splits on via multi_select_array). ", " ke saath
                 # join karne se do+ values ek hi comma-joined string ban ke
                 # aati thi list me (e.g. ["Financial Help, Legal Help"]).
                 "|".join(body.form_of_violence or []) or None,
                 _yn(body.do_you_want_support),
                 "|".join(body.support_kinds or []) or None,
                 body.any_other_what, body.trainee_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Trainee not found.")
            return {"id": row["id"], "ok": True}

        cur.execute("SELECT 1 FROM www_enrollment WHERE id=%s", (body.trainee_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Trainee not found.")
        cur.execute(
            "INSERT INTO www_gbv (trainee_id, is_survivor, mentioned_in_enrollment, "
            "facing_during_training, violence_location, inside_known_unknown, known_relation, "
            "outside_by_whom, form_of_violence, do_you_want_support, support_kinds, any_other_what, is_draft) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (body.trainee_id, body.is_survivor, body.mentioned_in_enrollment,
             body.facing_during_training, body.violence_location, body.inside_known_unknown,
             body.known_relation, body.outside_by_whom, body.form_of_violence or [],
             body.do_you_want_support, body.support_kinds or [], body.any_other_what,
             bool(body.is_draft)),
        )
        new_id = cur.fetchone()["id"]
    return {"id": new_id, "ok": True}


@router.put("/{gbv_id}")
def update_gbv(gbv_id: int, body: GBVUpdate):
    payload = body.model_dump(exclude_unset=True)
    if not payload: return {"ok": True}
    with get_cursor() as cur:
        if not _legacy.is_normalized(cur, "www_gbv"):
            lfields, lparams = [], []
            for k, v in payload.items():
                col = _LEGACY_UPDATE_MAP.get(k)
                if not col:
                    continue
                if k in ("is_survivor", "mentioned_in_enrollment", "do_you_want_support"):
                    v = _yn(v)
                elif k in ("form_of_violence", "support_kinds"):
                    # 2026-09-02: "|" delimiter to match the READ split.
                    v = "|".join(v or []) or None
                lfields.append(f"{col} = %s"); lparams.append(v)
            if not lfields:
                return {"ok": True}
            lparams.append(gbv_id)
            cur.execute("UPDATE mis_azad.www_gbv SET " + ", ".join(lfields) +
                        " WHERE id = %s", lparams)
            if cur.rowcount == 0:
                raise HTTPException(404, "GBV record not found.")
            return {"ok": True}

        fields = []; params = []
        for k, v in payload.items():
            fields.append(f"{k} = %s"); params.append(v)
        params.append(gbv_id)
        cur.execute("UPDATE www_gbv SET " + ", ".join(fields) +
                    " WHERE id = %s AND deleted_at IS NULL", params)
        if cur.rowcount == 0:
            raise HTTPException(404, "GBV record not found.")
    return {"ok": True}


@router.delete("/{gbv_id}")
def delete_gbv(gbv_id: int):
    with get_cursor() as cur:
        if not _legacy.is_normalized(cur, "www_gbv"):
            # 2026-08-19 (Ashish): pehle ye row ko HAMESHA ke liye mita deta tha.
            # Ab deleted_at bhar dete hain -- row DB me bachi rehti hai, bas har
            # list se hat jati hai. Wapas laani ho to deleted_at = NULL.
            cur.execute("UPDATE mis_azad.www_gbv SET deleted_at = NOW() "
                        "WHERE id = %s AND deleted_at IS NULL", (gbv_id,))
        else:
            cur.execute("UPDATE www_gbv SET deleted_at = now() WHERE id=%s AND deleted_at IS NULL", (gbv_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "GBV record not found.")
    return {"ok": True}


# =============================================================================
# EXPORT (Excel) — 2026-08-08
# Section-wise xlsx: Trainee Details + GBV Details + System.
# =============================================================================
@router.get("/export/excel")
def export_gbv_excel(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    enrollment_type: Optional[str] = None,
    facing_during_training: Optional[str] = None,
    violence_when: Optional[str] = None,
    form_of_violence: Optional[str] = None,
    support_kind: Optional[str] = None,
    name: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    from datetime import date as _d
    from export_helper import multi_sheet_xlsx_response_v2

    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        has_table = _legacy.is_normalized(cur, "www_gbv")

        if not has_table:
            lwhere, lparams = _legacy_filters(
                facing_during_training, violence_when, form_of_violence, support_kind, batch_id, name)
            if centre_code:
                lwhere += " AND " + _legacy.centre_filter("g"); lparams.append(centre_code)
            if state_code:
                lwhere += " AND " + _legacy.state_filter(); lparams.append(state_code)
            if district_code:
                lwhere += " AND " + _legacy.district_filter(); lparams.append(district_code)
            if date_from: lwhere += " AND g.created_at >= %s"; lparams.append(date_from)
            if date_to:   lwhere += " AND g.created_at <= %s"; lparams.append(date_to)
            cur.execute(
                "SELECT " + _legacy.enroll_no() + ", g.id AS id, g.name, "
                "       NULLIF(TRIM(_te.mobile), '') AS mobile, "
                "       NULLIF(TRIM(_te.type_of_enrollment), '') AS enrollment_type, "
                "       g.state AS state_name, g.district AS district_name, "
                "       " + _legacy.centre_expr("g.centre") + " AS centre_name, "
                "       NULL::text AS area_name, "
                "       NULLIF(TRIM(_te.batch), '') AS batch_name, "
                # 2026-08-12: four www_gbv columns were never selected, so the
                # export lost the joining/LL dates and both "when did it
                # happen" answers.
                "       g.date_of_joining, "
                "       NULLIF(TRIM(g.date_of_ll), '') AS date_of_ll, "
                "       NULLIF(TRIM(g.if_yes_when_did_the_violence_happen), '') "
                "           AS violence_when, "
                "       NULLIF(TRIM(g.if_before_training_what_is_the_time_period), '') "
                "           AS before_training_period, "
                "       NULLIF(TRIM(g.is_the_trainee_a_survivor_of_violence_y_n), '') "
                "           AS is_survivor, "
                "       NULLIF(TRIM(g.has_she_mentioned_it_in_the_enrollment_form), '') "
                "           AS mentioned_in_enrollment, "
                "       NULLIF(TRIM(g.are_you_facing_or_have_faced_violence_during_the_traini), '') "
                "           AS facing_during_training, "
                "       NULLIF(TRIM(g.if_yes_where_did_the_violence_take_place), '') "
                "           AS violence_location, "
                "       NULLIF(TRIM(g.if_inside_by_known_or_unknown), '') AS inside_known_unknown, "
                "       NULLIF(TRIM(g.if_known_state_relation_with_person), '') AS known_relation, "
                "       NULL::text AS outside_by_whom, "
                "       " + _legacy.multi_select_array("g.what_form_of_violence") + " AS form_of_violence, "
                "       NULLIF(TRIM(g.do_you_want_support), '') AS do_you_want_support, "
                "       " + _legacy.multi_select_array("g.if_yes_what_kind_of_support_has_azad_provided") +
                "           AS support_kinds, "
                "       NULLIF(TRIM(g.if_any_other_what), '') AS any_other_what, "
                "       NULL::timestamptz AS created_at "
                "FROM mis_azad.www_gbv g " + _legacy.geo_joins("g") +
                _legacy.trainee_join("g") + lwhere +
                " ORDER BY g.id DESC",
                lparams,
            )
            rows = cur.fetchall()
        else:
            conds = ["g.deleted_at IS NULL"]; params = []
            if state_code:             conds.append("t.state_code = %s");             params.append(state_code)
            if centre_code:            conds.append("t.centre_code = %s");            params.append(centre_code)
            if batch_id:               conds.append("t.batch_id = %s");               params.append(batch_id)
            if enrollment_type:        conds.append("t.enrollment_type = %s");        params.append(enrollment_type)
            if facing_during_training: conds.append("g.facing_during_training = %s"); params.append(facing_during_training)
            if violence_when:          conds.append("g.violence_when = %s");          params.append(violence_when)
            if form_of_violence:       conds.append("%s = ANY(g.form_of_violence)");  params.append(form_of_violence)
            if support_kind:           conds.append("%s = ANY(g.support_kinds)");     params.append(support_kind)
            if name:                   conds.append(_legacy.name_match("t.name"));               params.append(_legacy.name_pattern(name))
            if date_from:              conds.append("g.created_at >= %s");            params.append(date_from)
            if date_to:                conds.append("g.created_at <= %s");            params.append(date_to)
            where = "WHERE " + " AND ".join(conds)
            cur.execute(
                "SELECT g.id AS id, g.is_survivor, g.mentioned_in_enrollment, g.facing_during_training, "
                "       g.violence_location, g.inside_known_unknown, g.known_relation, "
                "       g.outside_by_whom, g.form_of_violence, g.do_you_want_support, "
                "       g.support_kinds, g.any_other_what, g.created_at, "
                "       t.enrollment_no, t.name, t.mobile, t.enrollment_type, "
                "       t.state_code, t.district_code, t.centre_code, t.area_code, "
                "       s.state_name, d.district_name, c.centre_name, a.area_name, "
                "       b.name AS batch_name "
                "FROM www_gbv g "
                "JOIN www_enrollment t ON t.id = g.trainee_id "
                "LEFT JOIN central_states    s ON s.state_code    = t.state_code "
                "LEFT JOIN central_districts d ON d.district_code = t.district_code "
                "LEFT JOIN central_centres   c ON c.centre_code   = t.centre_code "
                "LEFT JOIN www_areas     a ON a.area_code     = t.area_code "
                "LEFT JOIN www_master_batches b ON b.id = t.batch_id " +
                where + " ORDER BY g.created_at DESC",
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

    def _arr(v):
        if not v:
            return ""
        if isinstance(v, (list, tuple)):
            return ", ".join(str(x) for x in v if x is not None)
        return str(v)

    trainee_headers = [
        "Enrollment No.", "Name", "Mobile", "Enrollment Type",
        "State", "District", "Centre", "Area", "Batch",
        "Date of Joining", "Date of LL",
    ]
    gbv_headers = [
        "Is Survivor", "Mentioned in Enrollment", "When Did the Violence Happen",
        "If Before Training, Time Period", "Facing During Training",
        "Violence Location", "Inside Known/Unknown", "Known Relation",
        "Outside By Whom", "Form of Violence",
        "Do You Want Support", "Support Kinds", "Any Other What",
    ]
    system_headers = ["Created At"]
    all_headers = trainee_headers + gbv_headers + system_headers
    n_t, n_g, n_s = len(trainee_headers), len(gbv_headers), len(system_headers)
    group_headers = [
        (1, n_t, "Trainee Details"),
        (n_t + 1, n_t + n_g, "GBV Details"),
        (n_t + n_g + 1, n_t + n_g + n_s, "System"),
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
            _g(r, "date_of_joining"), _g(r, "date_of_ll"),
            _yn(r.get("is_survivor")), _yn(r.get("mentioned_in_enrollment")),
            _g(r, "violence_when"), _g(r, "before_training_period"),
            _g(r, "facing_during_training"), _g(r, "violence_location"),
            _g(r, "inside_known_unknown"), _g(r, "known_relation"),
            _g(r, "outside_by_whom"), _arr(r.get("form_of_violence")),
            _yn(r.get("do_you_want_support")), _arr(r.get("support_kinds")),
            _g(r, "any_other_what"),
            _g(r, "created_at"),
        ])

    # 2026-08-26: WWW tracking columns (Created By / Updated By / Updated At)
    from routes._www_export_tracking import WWW_TRACK_HEADERS as _WT_H, www_tracking_cells as _wt_cells
    all_headers = list(all_headers) + _WT_H
    # 2026-09-19: Record Info banner over Created By + Updated By.
    group_headers = list(group_headers) + [(len(all_headers) - len(_WT_H) + 1, len(all_headers), "Record Info")]
    _wt_rows = _wt_cells(rows, "mis_azad.www_gbv", "id")
    for _wi in range(len(data_rows)):
        data_rows[_wi] = list(data_rows[_wi]) + (_wt_rows[_wi] if _wi < len(_wt_rows) else ["", ""])
    sheets = [{
        "name": "GBV",
        "group_headers": group_headers,
        "headers": all_headers,
        "rows": data_rows,
    }]
    return multi_sheet_xlsx_response_v2(
        sheets,
        f"WWW_GBV_{_d.today().isoformat()}.xlsx",
    )
