"""WWW Financial Assistance to Trainee."""
from fastapi import APIRouter, HTTPException, Request
from routes import _www_scope as _scope
from pydantic import BaseModel
from typing import Optional
from datetime import date
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from routes import _www_legacy as _legacy
from routes._www_list_sort import www_list_order

router = APIRouter(prefix="/api/www-fat", tags=["WWW Financial Assistance"])


class FATCreate(BaseModel):
    trainee_id: int
    social_security_taken: Optional[bool] = None
    social_security_date: Optional[date] = None
    social_security_amount: Optional[float] = None
    travel_subsidy_taken: Optional[bool] = None
    travel_subsidy_date: Optional[date] = None
    travel_subsidy_amount: Optional[float] = None
    ram_mohan_scholarship: Optional[bool] = None
    scholarship_months: Optional[int] = None
    scholarship_start_date: Optional[date] = None
    scholarship_total_amount: Optional[float] = None
    is_draft: Optional[bool] = False


class FATUpdate(BaseModel):
    social_security_taken: Optional[bool] = None
    social_security_date: Optional[date] = None
    social_security_amount: Optional[float] = None
    travel_subsidy_taken: Optional[bool] = None
    travel_subsidy_date: Optional[date] = None
    travel_subsidy_amount: Optional[float] = None
    ram_mohan_scholarship: Optional[bool] = None
    scholarship_months: Optional[int] = None
    scholarship_start_date: Optional[date] = None
    scholarship_total_amount: Optional[float] = None
    is_draft: Optional[bool] = None


def _row_select():
    return (
        "SELECT f.*, "
        "       t.enrollment_no, t.name, t.mobile, t.state_code, t.district_code, t.centre_code, "
        "       COALESCE(b.name, NULL) AS batch_name, b.id AS batch_id, "
        "       t.enrollment_date AS date_of_joining "
        "FROM www_fat f "
        "JOIN www_enrollment t ON t.id = f.trainee_id "
        "LEFT JOIN www_master_batches b ON b.id = t.batch_id "
    )


def _yn_bool(col: str) -> str:
    """The import stores these Yes/No answers as TEXT -- 'true' / 'false', and
    'Yes' / 'No' on older Kobo rows. Handing that straight to the API made the
    List read every record as Yes (in JavaScript the string 'false' is truthy)
    and the View screen show a blank (it compares with === true / === false).
    Cast to a real boolean; anything unrecognised stays NULL so the screens can
    say "not recorded" instead of guessing. 2026-08-17.
    """
    return (
        "CASE lower(trim(COALESCE(" + col + ", ''))) "
        "  WHEN 'true' THEN TRUE  WHEN 'yes' THEN TRUE  WHEN '1' THEN TRUE "
        "  WHEN 'false' THEN FALSE WHEN 'no' THEN FALSE WHEN '0' THEN FALSE "
        "  ELSE NULL END"
    )


@router.get("")
def list_fat(
    request: Request,
    enrollment_id: Optional[int] = None,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    type_of_fund: Optional[str] = None,
    scholarship: Optional[str] = None,
    name: Optional[str] = None,
    sort_by: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
):
    page = max(page, 1); limit = max(limit, 1); offset = (page - 1) * limit
    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        # ---- LEGACY FALLBACK: www_fat absent -> read www_financial_assistance_to_trainees ----
        cur.execute("SELECT to_regclass('mis_azad.www_fat') AS t")
        if not cur.fetchone()["t"]:
            lconds = ["NULLIF(TRIM(x.name), '') IS NOT NULL", "x.deleted_at IS NULL"]
            lparams = []
            if name: lconds.append("(" + _legacy.name_match("x.name") + " OR _te.enrollment_no ILIKE %s)"); lparams.append(_legacy.name_pattern(name)); lparams.append(_legacy.name_pattern(name))
            # 2026-08-17: the Fund and Scholarship filters were dropped here --
            # this branch only ever applied Name, so picking either one changed
            # nothing on screen.  Compare through _yn_bool() because the import
            # keeps these answers as text ('true' / 'false', older rows 'Yes' /
            # 'No'); "No" means explicitly false, not merely unanswered.
            if type_of_fund == "social_security":
                lconds.append(_yn_bool("x.any_social_security_fund_taken_support") + " IS TRUE")
            if type_of_fund == "travel_subsidy":
                lconds.append(_yn_bool("x.any_social_security_fund_taken_travel_subsidy") + " IS TRUE")
            if scholarship == "yes":
                lconds.append(_yn_bool("x.ram_mohan_scholarship_provided_yes_no") + " IS TRUE")
            if scholarship == "no":
                lconds.append(_yn_bool("x.ram_mohan_scholarship_provided_yes_no") + " IS FALSE")
            lwhere = "WHERE " + " AND ".join(lconds)
            if enrollment_id:
                lwhere += " AND x.enrollment_id = %s"; lparams.append(enrollment_id)
            _df = request.query_params.get("date_from"); _dt = request.query_params.get("date_to")
            if _df: lwhere += " AND x.created_at >= %s"; lparams.append(_df)
            if _dt: lwhere += " AND x.created_at <= %s"; lparams.append(_dt)
            if state_code:    lwhere += " AND " + _legacy.state_filter();       lparams.append(state_code)
            if district_code: lwhere += " AND " + _legacy.district_filter();    lparams.append(district_code)
            if centre_code:   lwhere += " AND " + _legacy.centre_filter("_te"); lparams.append(centre_code)
            cur.execute("SELECT COUNT(*) AS total FROM www_financial_assistance_to_trainees x " + _legacy.trainee_join("x") + _legacy.geo_joins("_te") + lwhere, lparams)
            total = cur.fetchone()["total"]
            cur.execute(
                "SELECT x._pk AS id, x.enrollment_id AS trainee_id, "
                "       " + _yn_bool("any_social_security_fund_taken_support") +
                "           AS social_security_taken, "
                "       date_of_issue_of_social_security_fund_support AS social_security_date, "
                "       amount_of_social_security_fund_taken_support AS social_security_amount, "
                "       " + _yn_bool("any_social_security_fund_taken_travel_subsidy") +
                "           AS travel_subsidy_taken, "
                "       date_of_issue_of_social_security_fund_travel_subsidy AS travel_subsidy_date, "
                "       amount_of_social_security_fund_taken_travel_subsidy AS travel_subsidy_amount, "
                "       " + _yn_bool("ram_mohan_scholarship_provided_yes_no") +
                "           AS ram_mohan_scholarship, "
                "       for_how_many_months AS scholarship_months, "
                "       date_when_scholarship_started_date_month_year AS scholarship_start_date, "
                "       total_amount_of_scholarship AS scholarship_total_amount, "
                "       COALESCE(is_draft, false) AS is_draft, "
                "       COALESCE(server_synced_at, mobile_createdat) AS created_at, "
                # 2026-08-17: mobile / batch / state / district came back NULL
                # (hard-coded, or read off the import row -- columns only the
                # Kobo capture fills), so the View screen showed blanks for
                # records added through this app. They all live on the
                # trainee's enrollment row, already joined below as _te. The
                # enrollment keeps geography as names, which is what the
                # View prints anyway.
                "       " + _legacy.enroll_no() + ", x.name, "
                "       NULLIF(TRIM(_te.mobile), '') AS mobile, "
                # 2026-09-02: geo ko enrollment (_te) se geo_cols/geo_joins ke
                # zariye resolve karo -- baaki 10 modules ki tarah proper
                # code + name dono keys aayein. Pehle sirf naam code-key me
                # aata tha (state_code="Tamil Nadu", state_name missing).
                "       " + _legacy.geo_cols() + ", "
                "       NULLIF(TRIM(_te.batch), '') AS batch_name, NULL::int AS batch_id, "
                # date_of_joining import me TEXT hai aur enrollment me DATE --
                # COALESCE dono ko mila nahi sakta, aur ye field pehle se
                # sahi aa raha tha, isliye jaisa tha waisa hi.
                "       x.date_of_joining "
                "FROM www_financial_assistance_to_trainees x "
                + _legacy.trainee_join("x") + _legacy.geo_joins("_te") + lwhere +
                " ORDER BY " + www_list_order(sort_by, "x.name", "x._pk", "_pk DESC") + " LIMIT %s OFFSET %s",
                lparams + [limit, offset],
            )
            rows = cur.fetchall()
            return {"total": total, "page": page, "limit": limit, "data": rows}

        conds = ["f.deleted_at IS NULL"]; params = []
        if state_code:    conds.append("t.state_code = %s");    params.append(state_code)
        if district_code: conds.append("t.district_code = %s"); params.append(district_code)
        if centre_code:   conds.append("t.centre_code = %s");   params.append(centre_code)
        if type_of_fund == "social_security": conds.append("f.social_security_taken = TRUE")
        if type_of_fund == "travel_subsidy":  conds.append("f.travel_subsidy_taken = TRUE")
        if scholarship == "yes":              conds.append("f.ram_mohan_scholarship = TRUE")
        if scholarship == "no":               conds.append("f.ram_mohan_scholarship = FALSE")
        if name:                              conds.append(_legacy.name_match("t.name")); params.append(_legacy.name_pattern(name))
        where = "WHERE " + " AND ".join(conds)
        cur.execute(
            "SELECT COUNT(*) AS total FROM www_fat f "
            "JOIN www_enrollment t ON t.id = f.trainee_id " + where,
            params,
        )
        total = cur.fetchone()["total"]
        sql = _row_select() + where + " ORDER BY " + www_list_order(sort_by, "f.name", "f.created_at", "f.created_at DESC NULLS LAST, f.id DESC") + " LIMIT %s OFFSET %s"
        cur.execute(sql, params + [limit, offset])
        rows = cur.fetchall()
        return {"total": total, "page": page, "limit": limit, "data": rows}


@router.get("/{fat_id}")
def get_fat(request: Request, fat_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT to_regclass('mis_azad.www_fat') AS t")
        if not cur.fetchone()["t"]:
            cur.execute(
                "SELECT x._pk AS id, x.enrollment_id AS trainee_id, "
                "       " + _yn_bool("any_social_security_fund_taken_support") +
                "           AS social_security_taken, "
                "       date_of_issue_of_social_security_fund_support AS social_security_date, "
                "       amount_of_social_security_fund_taken_support AS social_security_amount, "
                "       " + _yn_bool("any_social_security_fund_taken_travel_subsidy") +
                "           AS travel_subsidy_taken, "
                "       date_of_issue_of_social_security_fund_travel_subsidy AS travel_subsidy_date, "
                "       amount_of_social_security_fund_taken_travel_subsidy AS travel_subsidy_amount, "
                "       " + _yn_bool("ram_mohan_scholarship_provided_yes_no") +
                "           AS ram_mohan_scholarship, "
                "       for_how_many_months AS scholarship_months, "
                "       date_when_scholarship_started_date_month_year AS scholarship_start_date, "
                "       total_amount_of_scholarship AS scholarship_total_amount, "
                "       COALESCE(is_draft, false) AS is_draft, "
                "       COALESCE(server_synced_at, mobile_createdat) AS created_at, "
                # 2026-08-17: mobile / batch / state / district came back NULL
                # (hard-coded, or read off the import row -- columns only the
                # Kobo capture fills), so the View screen showed blanks for
                # records added through this app. They all live on the
                # trainee's enrollment row, already joined below as _te. The
                # enrollment keeps geography as names, which is what the
                # View prints anyway.
                "       " + _legacy.enroll_no() + ", x.name, "
                "       NULLIF(TRIM(_te.mobile), '') AS mobile, "
                # 2026-09-02: geo ko enrollment (_te) se geo_cols/geo_joins ke
                # zariye resolve karo -- baaki 10 modules ki tarah proper
                # code + name dono keys aayein. Pehle sirf naam code-key me
                # aata tha (state_code="Tamil Nadu", state_name missing).
                "       " + _legacy.geo_cols() + ", "
                "       NULLIF(TRIM(_te.batch), '') AS batch_name, NULL::int AS batch_id, "
                # date_of_joining import me TEXT hai aur enrollment me DATE --
                # COALESCE dono ko mila nahi sakta, aur ye field pehle se
                # sahi aa raha tha, isliye jaisa tha waisa hi.
                "       x.date_of_joining "
                "FROM www_financial_assistance_to_trainees x "
                + _legacy.trainee_join("x") + _legacy.geo_joins("_te") + " WHERE _pk = %s",
                (fat_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "FAT record not found.")
            _scope.guard_detail(request, row)
            return row

        cur.execute(_row_select() + "WHERE f.id = %s AND f.deleted_at IS NULL", (fat_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "FAT record not found.")
    _scope.guard_detail(request, row)
    return row


# API field -> www_financial_assistance_to_trainees column.
_LEGACY_UPDATE_MAP = {
    "social_security_taken":     "any_social_security_fund_taken_support",
    "social_security_date":      "date_of_issue_of_social_security_fund_support",
    "social_security_amount":    "amount_of_social_security_fund_taken_support",
    "travel_subsidy_taken":      "any_social_security_fund_taken_travel_subsidy",
    "travel_subsidy_date":       "date_of_issue_of_social_security_fund_travel_subsidy",
    "travel_subsidy_amount":     "amount_of_social_security_fund_taken_travel_subsidy",
    "ram_mohan_scholarship":     "ram_mohan_scholarship_provided_yes_no",
    "scholarship_months":        "for_how_many_months",
    "scholarship_start_date":    "date_when_scholarship_started_date_month_year",
    "scholarship_total_amount":  "total_amount_of_scholarship",
    "is_draft":                  "is_draft",
}


@router.post("")
def create_fat(body: FATCreate):
    with get_cursor() as cur:
        # 2026-08-18 (Ashish): flow guard -- picker ki rok server par bhi.
        _legacy.assert_flow(cur, body.trainee_id, requires="ll", stage="Financial Assistance")
        if not _legacy.table_exists(cur, "www_fat"):
            payload = {k: getattr(body, k, None) for k in _LEGACY_UPDATE_MAP}
            cols = list(_LEGACY_UPDATE_MAP.values())
            ph = ",".join(["%s"] * len(cols))
            cur.execute(
                "INSERT INTO mis_azad.www_financial_assistance_to_trainees "
                "    (enrollment_id, name, state, district, centre, "
                "     date_of_joining, " + ",".join(cols) + ") "
                "SELECT e.id, e.name, e.state, e.district, e.centre, "
                "       e.enrollment_date, " + ph + " "
                "FROM mis_azad.www_enrollment e WHERE e.id = %s "
                "RETURNING _pk AS id",
                [payload[k] for k in _LEGACY_UPDATE_MAP] + [body.trainee_id],
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Trainee not found.")
            return {"id": row["id"], "ok": True}

        cur.execute("SELECT 1 FROM www_enrollment WHERE id=%s", (body.trainee_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Trainee not found.")
        cur.execute(
            "INSERT INTO www_fat (trainee_id, social_security_taken, social_security_date, social_security_amount, "
            "travel_subsidy_taken, travel_subsidy_date, travel_subsidy_amount, "
            "ram_mohan_scholarship, scholarship_months, scholarship_start_date, scholarship_total_amount, is_draft) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (body.trainee_id, body.social_security_taken, body.social_security_date, body.social_security_amount,
             body.travel_subsidy_taken, body.travel_subsidy_date, body.travel_subsidy_amount,
             body.ram_mohan_scholarship, body.scholarship_months, body.scholarship_start_date,
             body.scholarship_total_amount, bool(body.is_draft)),
        )
        new_id = cur.fetchone()["id"]
    return {"id": new_id, "ok": True}


@router.put("/{fat_id}")
def update_fat(fat_id: int, body: FATUpdate):
    payload = body.model_dump(exclude_unset=True)
    if not payload: return {"ok": True}
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_fat"):
            lfields, lparams = [], []
            for k, v in payload.items():
                col = _LEGACY_UPDATE_MAP.get(k)
                if col:
                    lfields.append(f"{col} = %s"); lparams.append(v)
            if not lfields:
                return {"ok": True}
            lparams.append(fat_id)
            cur.execute(
                "UPDATE mis_azad.www_financial_assistance_to_trainees SET "
                + ", ".join(lfields) + " WHERE _pk = %s", lparams)
            if cur.rowcount == 0:
                raise HTTPException(404, "FAT record not found.")
            return {"ok": True}

        fields = []; params = []
        for k, v in payload.items():
            fields.append(f"{k} = %s"); params.append(v)
        params.append(fat_id)
        cur.execute("UPDATE www_fat SET " + ", ".join(fields) +
                    " WHERE id = %s AND deleted_at IS NULL", params)
        if cur.rowcount == 0:
            raise HTTPException(404, "FAT record not found.")
    return {"ok": True}


@router.delete("/{fat_id}")
def delete_fat(fat_id: int):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_fat"):
            # 2026-08-19 (Ashish): pehle ye row ko HAMESHA ke liye mita deta tha.
            # Ab deleted_at bhar dete hain -- row DB me bachi rehti hai, bas har
            # list se hat jati hai. Wapas laani ho to deleted_at = NULL.
            cur.execute("UPDATE mis_azad.www_financial_assistance_to_trainees "
                        "   SET deleted_at = NOW() "
                        " WHERE _pk = %s AND deleted_at IS NULL", (fat_id,))
        else:
            cur.execute("UPDATE www_fat SET deleted_at = now() WHERE id=%s AND deleted_at IS NULL", (fat_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "FAT record not found.")
    return {"ok": True}


# =============================================================================
# EXPORT (Excel) — 2026-08-08
# Section-wise xlsx: Trainee Details + FAT Details + System.
# =============================================================================
@router.get("/export/excel")
def export_fat_excel(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    enrollment_type: Optional[str] = None,
    type_of_fund: Optional[str] = None,
    scholarship: Optional[str] = None,
    name: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    from datetime import date as _d
    from export_helper import multi_sheet_xlsx_response_v2

    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        cur.execute("SELECT to_regclass('mis_azad.www_fat') AS t")
        has_table = bool(cur.fetchone()["t"])

        if not has_table:
            # 2026-08-12: this branch used to apply the Name filter only, so
            # an export taken with Fund or Scholarship set returned every
            # row.  The import stores both as free text ("Yes" / "No").
            lconds = ["NULLIF(TRIM(x.name), '') IS NOT NULL", "x.deleted_at IS NULL"]
            lparams = []
            if name: lconds.append("(" + _legacy.name_match("x.name") + " OR _te.enrollment_no ILIKE %s)"); lparams.append(_legacy.name_pattern(name)); lparams.append(_legacy.name_pattern(name))
            # 2026-08-17: these matched ILIKE 'yes%' / 'no%', which fit the
            # original Kobo wording.  Rows written by this app store 'true' /
            # 'false', so a filtered export came back empty.  _yn_bool() reads
            # both spellings.
            if type_of_fund == "social_security":
                lconds.append(_yn_bool("x.any_social_security_fund_taken_support") + " IS TRUE")
            if type_of_fund == "travel_subsidy":
                lconds.append(_yn_bool("x.any_social_security_fund_taken_travel_subsidy") + " IS TRUE")
            if scholarship == "yes":
                lconds.append(_yn_bool("x.ram_mohan_scholarship_provided_yes_no") + " IS TRUE")
            if scholarship == "no":
                lconds.append(_yn_bool("x.ram_mohan_scholarship_provided_yes_no") + " IS FALSE")
            if state_code:
                lconds.append("x.state_code = %s"); lparams.append(state_code)
            if district_code:
                lconds.append("x.district_code = %s"); lparams.append(district_code)
            if centre_code:
                lconds.append(_legacy.centre_filter("x")); lparams.append(centre_code)
            if date_from:
                lconds.append("x.date_of_issue_of_social_security_fund_travel_subsidy >= %s")
                lparams.append(date_from)
            if date_to:
                lconds.append("x.date_of_issue_of_social_security_fund_travel_subsidy <= %s")
                lparams.append(date_to)
            lwhere = "WHERE " + " AND ".join(lconds)
            cur.execute(
                "SELECT " + _legacy.enroll_no() + ", x._pk AS id, x.name, NULL::text AS mobile, "
                "       NULL::text AS enrollment_type, "
                "       x.state AS state_name, x.district AS district_name, "
                "       x.centre AS centre_name, NULL::text AS area_name, "
                "       NULL::text AS batch_name, "
                # 2026-08-12: the block, the two dates and the whole Kobo
                # capture block below are on the import but were never
                # selected, so the export showed 10 of its 41 columns.
                "       x.block, x.block_code, x.state_code, x.district_code, "
                "       x.date_of_joining, x.date_of_ll, "
                "       " + _yn_bool("any_social_security_fund_taken_support") +
                "           AS social_security_taken, "
                "       date_of_issue_of_social_security_fund_support AS social_security_date, "
                "       amount_of_social_security_fund_taken_support AS social_security_amount, "
                "       " + _yn_bool("any_social_security_fund_taken_travel_subsidy") +
                "           AS travel_subsidy_taken, "
                "       date_of_issue_of_social_security_fund_travel_subsidy AS travel_subsidy_date, "
                "       amount_of_social_security_fund_taken_travel_subsidy AS travel_subsidy_amount, "
                "       " + _yn_bool("ram_mohan_scholarship_provided_yes_no") +
                "           AS ram_mohan_scholarship, "
                "       for_how_many_months AS scholarship_months, "
                "       date_when_scholarship_started_date_month_year AS scholarship_start_date, "
                "       total_amount_of_scholarship AS scholarship_total_amount, "
                "       x.response_id, x.transaction_id, x.parent_response_id, "
                "       x.group_response_id, x.user_id, x.user_name, "
                "       x.app_version_during_data_fill, x.latitude_mobile, "
                "       x.longitude_mobile, x.accuracy_mobile, x.survey_started_at, "
                "       x.time_taken_in_minutes, x.mobile_createdat, "
                "       x.mobile_updatedat, x.server_modified_at, "
                "       COALESCE(server_synced_at, mobile_createdat) AS created_at "
                "FROM www_financial_assistance_to_trainees x "
                + _legacy.trainee_join("x") + lwhere + " ORDER BY _pk DESC",
                lparams,
            )
            rows = cur.fetchall()
        else:
            conds = ["f.deleted_at IS NULL"]; params = []
            if state_code:      conds.append("t.state_code = %s");        params.append(state_code)
            if centre_code:     conds.append("t.centre_code = %s");       params.append(centre_code)
            if batch_id:        conds.append("t.batch_id = %s");          params.append(batch_id)
            if enrollment_type: conds.append("t.enrollment_type = %s");   params.append(enrollment_type)
            if type_of_fund == "social_security": conds.append("f.social_security_taken = TRUE")
            if type_of_fund == "travel_subsidy":  conds.append("f.travel_subsidy_taken = TRUE")
            if scholarship == "yes":              conds.append("f.ram_mohan_scholarship = TRUE")
            if scholarship == "no":               conds.append("f.ram_mohan_scholarship = FALSE")
            if name:                              conds.append(_legacy.name_match("t.name")); params.append(_legacy.name_pattern(name))
            if date_from:                         conds.append("f.created_at >= %s"); params.append(date_from)
            if date_to:                           conds.append("f.created_at <= %s"); params.append(date_to)
            where = "WHERE " + " AND ".join(conds)
            cur.execute(
                "SELECT f.social_security_taken, f.social_security_date, f.social_security_amount, "
                "       f.travel_subsidy_taken, f.travel_subsidy_date, f.travel_subsidy_amount, "
                "       f.ram_mohan_scholarship, f.scholarship_months, f.scholarship_start_date, "
                "       f.scholarship_total_amount, f.created_at, "
                "       t.enrollment_no, t.name, t.mobile, t.enrollment_type, "
                "       t.state_code, t.district_code, t.centre_code, t.area_code, "
                "       s.state_name, d.district_name, c.centre_name, a.area_name, "
                "       b.name AS batch_name "
                "FROM www_fat f "
                "JOIN www_enrollment t ON t.id = f.trainee_id "
                "LEFT JOIN central_states    s ON s.state_code    = t.state_code "
                "LEFT JOIN central_districts d ON d.district_code = t.district_code "
                "LEFT JOIN central_centres   c ON c.centre_code   = t.centre_code "
                "LEFT JOIN www_areas     a ON a.area_code     = t.area_code "
                "LEFT JOIN www_master_batches b ON b.id = t.batch_id " +
                where + " ORDER BY f.created_at DESC",
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
        "State", "District", "Block", "Centre", "Area", "Batch",
        "Status", "Date of Joining", "Date of LL",
    ]
    fat_headers = [
        "Social Security Taken", "SS Date", "SS Amount",
        "Travel Subsidy Taken", "TS Date", "TS Amount",
        "Ram Mohan Scholarship", "Scholarship Months",
        "Scholarship Start Date", "Scholarship Total Amount",
    ]
    # The import is a Kobo capture, so each row carries the collection
    # metadata alongside the answers.  It travels with the export rather
    # than being thrown away.
    capture_headers = [
        "Response ID", "Transaction ID", "Parent Response ID",
        "Group Response ID", "Collected By (User ID)", "Collected By",
        "App Version", "Latitude", "Longitude", "Accuracy",
        "Survey Started At", "Time Taken (Minutes)",
        "Mobile Created At", "Mobile Updated At", "Server Modified At",
    ]
    system_headers = ["Created At"]
    all_headers = trainee_headers + fat_headers + capture_headers + system_headers
    n_t, n_f, n_c, n_s = (len(trainee_headers), len(fat_headers),
                          len(capture_headers), len(system_headers))
    group_headers = [
        (1, n_t, "Trainee Details"),
        (n_t + 1, n_t + n_f, "FAT Details"),
        (n_t + n_f + 1, n_t + n_f + n_c, "Data Capture"),
        (n_t + n_f + n_c + 1, n_t + n_f + n_c + n_s, "System"),
    ]

    data_rows = []
    for r in rows:
        data_rows.append([
            _g(r, "enrollment_no"), _g(r, "name"), _g(r, "mobile"), _g(r, "enrollment_type"),
            _g(r, "state_name") or _g(r, "state_code"),
            _g(r, "district_name") or _g(r, "district_code"),
            _g(r, "block"),
            _g(r, "centre_name") or _g(r, "centre_code"),
            _g(r, "area_name") or _g(r, "area_code"),
            _g(r, "batch_name"),
            _g(r, "date_of_joining"), _g(r, "date_of_ll"),
            _yn(r.get("social_security_taken")), _g(r, "social_security_date"), _g(r, "social_security_amount"),
            _yn(r.get("travel_subsidy_taken")), _g(r, "travel_subsidy_date"), _g(r, "travel_subsidy_amount"),
            _yn(r.get("ram_mohan_scholarship")), _g(r, "scholarship_months"),
            _g(r, "scholarship_start_date"), _g(r, "scholarship_total_amount"),
            _g(r, "response_id"), _g(r, "transaction_id"),
            _g(r, "parent_response_id"), _g(r, "group_response_id"),
            _g(r, "user_id"), _g(r, "user_name"),
            _g(r, "app_version_during_data_fill"),
            _g(r, "latitude_mobile"), _g(r, "longitude_mobile"),
            _g(r, "accuracy_mobile"), _g(r, "survey_started_at"),
            _g(r, "time_taken_in_minutes"), _g(r, "mobile_createdat"),
            _g(r, "mobile_updatedat"), _g(r, "server_modified_at"),
            _g(r, "created_at"),
        ])

    # 2026-08-26: WWW tracking columns (Created By / Updated By / Updated At)
    from routes._www_export_tracking import WWW_TRACK_HEADERS as _WT_H, www_tracking_cells as _wt_cells
    all_headers = list(all_headers) + _WT_H
    # 2026-09-19: Record Info banner over Created By + Updated By.
    group_headers = list(group_headers) + [(len(all_headers) - len(_WT_H) + 1, len(all_headers), "Record Info")]
    _wt_rows = _wt_cells(rows, "mis_azad.www_financial_assistance_to_trainees", "id", "_pk")
    for _wi in range(len(data_rows)):
        data_rows[_wi] = list(data_rows[_wi]) + (_wt_rows[_wi] if _wi < len(_wt_rows) else ["", ""])
    sheets = [{
        "name": "FAT",
        "group_headers": group_headers,
        "headers": all_headers,
        "rows": data_rows,
    }]
    return multi_sheet_xlsx_response_v2(
        sheets,
        f"WWW_FAT_{_d.today().isoformat()}.xlsx",
    )


# ============================================================================
# 2026-09-24 (LIVE): Ram Mohan Scholarship payments. Table:
# mis_azad.www_fat_scholarship_payment; fat_id references either the new
# mis_azad.www_fat.id or the legacy _pk of
# www_financial_assistance_to_trainees (whichever get_fat returns as `id`).
# The frontend computes any paid/remaining/status from SUM(payments).
# ============================================================================
from pydantic import BaseModel as _RMSBaseModel
from typing import Optional as _RMSOpt

class _RMSPaymentIn(_RMSBaseModel):
    amount_paid: float
    payment_month: _RMSOpt[str] = None
    payment_date:  _RMSOpt[str] = None

def _rms_fat_exists(cur, fat_id: int) -> bool:
    cur.execute("SELECT to_regclass('mis_azad.www_fat') AS t")
    has_new = bool(cur.fetchone()["t"])
    if has_new:
        cur.execute("SELECT 1 FROM mis_azad.www_fat WHERE id = %s AND deleted_at IS NULL", (fat_id,))
    else:
        cur.execute("SELECT 1 FROM mis_azad.www_financial_assistance_to_trainees "
                    " WHERE _pk = %s AND deleted_at IS NULL", (fat_id,))
    return bool(cur.fetchone())

@router.post("/{fat_id}/scholarship-payments")
def rms_add_payment(fat_id: int, body: _RMSPaymentIn):
    if body.amount_paid is None or float(body.amount_paid) <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be greater than 0.")
    if not (body.payment_date or "").strip():
        raise HTTPException(status_code=400, detail="Payment date is required.")
    if not (body.payment_month or "").strip():
        raise HTTPException(status_code=400, detail="Payment month is required.")
    with get_cursor() as cur:
        if not _rms_fat_exists(cur, fat_id):
            raise HTTPException(status_code=404, detail="FAT record not found.")
        cur.execute(
            "INSERT INTO mis_azad.www_fat_scholarship_payment "
            "  (fat_id, amount_paid, payment_month, payment_date) "
            "VALUES (%s, %s, %s, COALESCE(%s::date, CURRENT_DATE)) RETURNING id",
            (fat_id, float(body.amount_paid), body.payment_month.strip(), body.payment_date),
        )
        new_id = cur.fetchone()["id"]
    return {"id": new_id, "message": "Payment recorded."}

@router.get("/{fat_id}/scholarship-payments")
def rms_list_payments(fat_id: int):
    with get_cursor() as cur:
        if not _rms_fat_exists(cur, fat_id):
            raise HTTPException(status_code=404, detail="FAT record not found.")
        cur.execute(
            "SELECT id, fat_id, amount_paid, payment_month, payment_date, created_at "
            "  FROM mis_azad.www_fat_scholarship_payment "
            " WHERE fat_id = %s AND deleted_at IS NULL "
            " ORDER BY payment_date, id",
            (fat_id,),
        )
        rows = cur.fetchall()
    return {"data": rows}
