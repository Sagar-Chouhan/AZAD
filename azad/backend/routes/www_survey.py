"""WWW Survey — read-only list + view over the www_survey_form table.

Table is populated by the mobile app; the web UI is display-only. Endpoints:
  GET  /api/www-surveys                     list with filters
  GET  /api/www-surveys/export/excel        filter-honoring XLSX export
  GET  /api/www-surveys/{pk}                full record
"""
from fastapi import APIRouter, HTTPException, Request
from routes import _www_scope as _scope
from typing import Optional, List
import sys, os, io, csv
from datetime import date as _date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor

router = APIRouter(prefix="/api/www-surveys", tags=["WWW Surveys"])


def _list_where(state_code, district_code, centre, surveyor_name, respondent_name, date_from, date_to):
    conds: List[str] = ["(s.deleted_at IS NULL)"]
    params: list = []
    if state_code:
        conds.append("s.state_code = %s"); params.append(state_code)
    if district_code:
        conds.append("s.district_code = %s"); params.append(district_code)
    if centre and centre.strip():
        conds.append("s.centre_census ILIKE %s"); params.append(f"%{centre.strip()}%")
    if surveyor_name and surveyor_name.strip():
        conds.append("s.name_of_surveyer ILIKE %s"); params.append(f"%{surveyor_name.strip()}%")
    if respondent_name and respondent_name.strip():
        conds.append("s.name_with_whom_the_survey_is_done ILIKE %s"); params.append(f"%{respondent_name.strip()}%")
    if date_from:
        conds.append("s.date_of_survey >= %s"); params.append(date_from)
    if date_to:
        conds.append("s.date_of_survey <= %s"); params.append(date_to)
    return " AND ".join(conds), params


@router.get("")
def list_surveys(request: Request,
                 state_code: Optional[str] = None,
                 district_code: Optional[str] = None,
                 centre: Optional[str] = None,
                 surveyor_name: Optional[str] = None,
                 respondent_name: Optional[str] = None,
                 date_from: Optional[str] = None,
                 date_to: Optional[str] = None,
                 page: int = 1, limit: int = 10):
    state_code, district_code, _sc = _scope.scope_geo(request, state_code, district_code, None)
    offset = max(0, (page - 1) * limit)
    where, params = _list_where(state_code, district_code, centre, surveyor_name, respondent_name, date_from, date_to)

    with get_cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS total FROM www_survey_form s WHERE {where}", params)
        total = cur.fetchone()["total"]
        cur.execute(
            f"""
            SELECT s._pk AS id,
                   s.response_id,
                   s.date_of_survey,
                   s.name_of_surveyer      AS surveyor_name,
                   s.name_with_whom_the_survey_is_done AS respondent_name,
                   s.contact_number,
                   s.state,
                   s.state_code,
                   s.district,
                   s.district_code,
                   s.centre_census         AS centre_name,
                   s.name_of_area_census   AS area_name,
                   s.server_synced_at,
                   s.mobile_createdat
            FROM www_survey_form s
            WHERE {where}
            ORDER BY s.server_synced_at DESC NULLS LAST, s._pk DESC
            LIMIT %s OFFSET %s
            """,
            params + [limit, offset],
        )
        rows = cur.fetchall()
    return {"total": total, "page": page, "limit": limit, "data": rows}


@router.get("/export/excel")
def export_surveys(request: Request,
                   state_code: Optional[str] = None,
                   district_code: Optional[str] = None,
                   centre: Optional[str] = None,
                   surveyor_name: Optional[str] = None,
                   respondent_name: Optional[str] = None,
                   date_from: Optional[str] = None,
                   date_to: Optional[str] = None):
    # 2026-09-24: expanded export to cover every Survey View field. Adds
    # Family Profile (decision maker, native place, male/female count, boys/
    # girls preference + count), Women & WWW Eligibility (name, contact,
    # age, marital, education, living, working, work type, income), and
    # WWW Status (interested, challenges, training pref, eligible,
    # eligible & interested, surveyor comments). Created At/By and
    # Updated At/By resolved from www_survey_form.users_id + timestamps
    # (the shared tracking helper does not apply -- www_survey_form has
    # no created_by/updated_by/updated_at columns of its own; it stores
    # mobile_createdat/mobile_updatedat/server_synced_at/server_modified_at
    # and one users_id).
    state_code, district_code, _sc = _scope.scope_geo(request, state_code, district_code, None)
    where, params = _list_where(state_code, district_code, centre, surveyor_name, respondent_name, date_from, date_to)
    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT
                s._pk                                                                        AS id,
                s.response_id,
                s.date_of_survey,
                s.quarter_of_survey,
                s.name_of_surveyer,
                s.designation,
                s.state,
                s.district,
                s.block,
                s.grampanchayat,
                s.centre_census                                                              AS centre_name,
                s.name_of_area_census                                                        AS area_name,
                s.name_of_basti,
                s.name_with_whom_the_survey_is_done                                          AS respondent_name,
                s.contact_number,
                s.address,
                s.caste_category,
                s.religion,
                s.total_family_members,
                s.how_many_earning_members_are_there_in_the_family                           AS earning_members,
                s.total_monthly_income,
                s.per_capita_income,
                s.who_is_the_primary_decision_maker_in_the_family                            AS decision_maker,
                s.name_of_the_primary_decision_maker_in_the_family                           AS decision_maker_name,
                s.what_is_the_occupation_of_primary_decision_maker_of_the_family             AS decision_maker_occupation,
                s.decision_maker_education,
                s.family_s_native_place                                                      AS native_place,
                s.total_male_members_in_the_family                                           AS male_members,
                s.total_female_members_in_the_family                                         AS female_members,
                s.if_there_is_a_boy_in_the_age_group_of_13_18_in_the_house_will_y            AS prefer_educate_boys,
                s.how_many_boys_in_this_age_group                                            AS boys_count,
                s.if_there_are_13_15_year_old_girls_in_the_family_will_you_prefer            AS prefer_educate_girls,
                s.how_many_girls_in_the_family_in_this_age_group                             AS girls_count,
                s.how_many_women_in_the_family_who_are_18                                    AS women_18_count,
                s.name_of_the_women_family_members_who_are_18                                AS woman_name,
                s.contact_number_1                                                           AS woman_contact,
                s.age                                                                        AS woman_age,
                s.marital_status                                                             AS woman_marital,
                s.education                                                                  AS woman_education,
                s.living_with_whom                                                           AS woman_living,
                s.is_she_working                                                             AS working_status,
                s.what_kind_of_work_is_she_doing                                             AS work_type,
                s.what_is_the_monthly_income                                                 AS woman_monthly_income,
                s.are_you_intrested_joining_www_program_at_azad                              AS interested_www,
                s.if_yes_what_challenges_you_might_face                                      AS challenges,
                s.which_type_of_training_do_you_want_to_do_post_joining_azad_www_            AS training_pref,
                s.is_she_eligible_to_join_the_www_program                                    AS eligible,
                s.is_she_eligible_and_intrested                                              AS eligible_interested,
                s.comments_of_the_surveyer_on_the_readiness_of_the_women_with_who            AS surveyor_comments,
                s.mobile_createdat,
                s.mobile_updatedat,
                s.server_synced_at,
                s.server_modified_at,
                s.users_id,
                s.user_name                                                                  AS mobile_user_name,
                s.eligible_women_json                                                        AS eligible_women_json
            FROM www_survey_form s
            WHERE {where}
            ORDER BY s.date_of_survey DESC NULLS LAST, s._pk DESC
            """,
            params,
        )
        rows = cur.fetchall()

        # Resolve users_id -> users.name in one batch (populates Created By / Updated By).
        # www_survey_form only carries ONE user id per row (the mobile capture user), so
        # Created By == Updated By for these legacy rows. The helper below still runs;
        # if a future edit path writes created_by/updated_by directly, we'll pick it up.
        uid_set = {r.get("users_id") for r in rows if r.get("users_id")}
        uname = {}
        if uid_set:
            cur.execute("SELECT id, name FROM mis_user WHERE id = ANY(%s)", (sorted(uid_set),))
            for u in cur.fetchall():
                uname[u["id"]] = u.get("name") or ""

    # 2026-09-24: recent mobile-app surveys keep training/eligibility/
    # eligible_interested/surveyor_comment inside eligible_women_json
    # (first entry). Flat columns are only populated for legacy Kobo
    # imports. Parse the JSON up front so the row loop can fall back.
    import json as _json
    def _ewj_first(raw):
        if not raw: return {}
        try:
            v = _json.loads(raw)
        except Exception:
            return {}
        if isinstance(v, list) and v and isinstance(v[0], dict):
            return v[0]
        if isinstance(v, dict):
            return v
        return {}
    def _pick(flat, first, key):
        f = (flat or "").strip() if isinstance(flat, str) else flat
        if f: return f
        v = first.get(key) if isinstance(first, dict) else None
        return "" if v is None else str(v)

    def _fmt_dt(v):
        if not v: return ""
        try:
            return v.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return str(v)

    def _fmt_date(v):
        if not v: return ""
        try:
            return v.isoformat()
        except Exception:
            return str(v)

    output = io.StringIO()
    w = csv.writer(output)
    w.writerow([
        # Basic
        "S.No", "Survey ID", "Date of Survey", "Synced Time", "Quarter",
        # 2026-11-07 wwwDashSplit: user-requested 'Synced Time' column
        "Surveyor Name", "Surveyor Designation",
        # Location
        "State", "District", "Block", "Gram Panchayat",
        "Centre", "Area", "Basti",
        # Respondent
        "Respondent Name", "Contact Number", "Address",
        "Caste", "Religion",
        # Family Profile
        "Total Family Members", "Earning Members",
        "Total Monthly Income", "Per Capita Income",
        "Primary Decision Maker", "Decision Maker Name",
        "Decision Maker Occupation", "Decision Maker Education",
        "Native Place",
        "Total Male Members", "Total Female Members",
        "Prefer Educating Boys (13-18)", "Number of Boys (13-18)",
        "Prefer Educating Girls (13-15)", "Number of Girls (13-15)",
        # Women & WWW Eligibility
        "Women 18+ Count", "Woman Name", "Woman Contact",
        "Age", "Marital Status", "Education",
        "Living With", "Working Status", "Work Type", "Monthly Income",
        # WWW Status
        "Interested in WWW", "Challenges", "Training Preference",
        "Eligible", "Eligible & Interested", "Surveyor Comments",
        # Tracking
        "Mobile Created At", "Server Synced At",
        "Created At", "Created By", "Updated At", "Updated By",
    ])
    for i, r in enumerate(rows, 1):
        created_at = r.get("server_synced_at") or r.get("mobile_createdat")
        updated_at = r.get("server_modified_at") or r.get("mobile_updatedat") or created_at
        uid = r.get("users_id")
        cb = uname.get(uid, "") if uid else ""
        # 2026-09-24: legacy Kobo rows have users_id NULL. Fall back to
        # the mobile-side user_name text field so Created By is never
        # blank on real data.
        if not cb:
            cb = (r.get("mobile_user_name") or "").strip()
        ub = cb  # www_survey_form only carries one user id/name per row
        w.writerow([
            i, r.get("response_id") or "",
            _fmt_date(r.get("date_of_survey")),
            # 2026-11-07 wwwDashRevert: show TIME only (HH:MM:SS) not date;
            # Excel was parsing full datetimes as date cells and hiding the time.
            (r.get("server_synced_at").strftime("%H:%M:%S") if r.get("server_synced_at") else ""),
            r.get("quarter_of_survey") or "",
            r.get("name_of_surveyer") or "", r.get("designation") or "",
            r.get("state") or "", r.get("district") or "",
            r.get("block") or "", r.get("grampanchayat") or "",
            r.get("centre_name") or "", r.get("area_name") or "",
            r.get("name_of_basti") or "",
            r.get("respondent_name") or "", r.get("contact_number") or "",
            r.get("address") or "",
            r.get("caste_category") or "", r.get("religion") or "",
            r.get("total_family_members") or "", r.get("earning_members") or "",
            r.get("total_monthly_income") or "", r.get("per_capita_income") if r.get("per_capita_income") is not None else "",
            r.get("decision_maker") or "", r.get("decision_maker_name") or "",
            r.get("decision_maker_occupation") or "", r.get("decision_maker_education") or "",
            r.get("native_place") or "",
            r.get("male_members") or "", r.get("female_members") or "",
            r.get("prefer_educate_boys") or "", r.get("boys_count") if r.get("boys_count") is not None else "",
            r.get("prefer_educate_girls") or "", r.get("girls_count") if r.get("girls_count") is not None else "",
            r.get("women_18_count") or "",
            r.get("woman_name") or "", r.get("woman_contact") or "",
            r.get("woman_age") or "", r.get("woman_marital") or "", r.get("woman_education") or "",
            r.get("woman_living") or "", r.get("working_status") or "",
            r.get("work_type") or "", r.get("woman_monthly_income") or "",
            # 2026-09-24: fall back to eligible_women_json[0].<key> when the
            # flat legacy column is empty (mobile-app surveys write here).
            r.get("interested_www") or "", r.get("challenges") or "",
            _pick(r.get("training_pref"), _ewj_first(r.get("eligible_women_json")), "training_pref"),
            _pick(r.get("eligible"), _ewj_first(r.get("eligible_women_json")), "is_eligible"),
            _pick(r.get("eligible_interested"), _ewj_first(r.get("eligible_women_json")), "eligible_interested"),
            _pick(r.get("surveyor_comments"), _ewj_first(r.get("eligible_women_json")), "surveyor_comment"),
            _fmt_dt(r.get("mobile_createdat")),
            _fmt_dt(r.get("server_synced_at")),
            _fmt_dt(created_at), cb,
            _fmt_dt(updated_at), ub,
        ])
    from export_helper import csv_string_to_xlsx_response
    return csv_string_to_xlsx_response(
        output.getvalue(),
        f"WWW_Survey_{_date.today().isoformat()}.xlsx",
    )


@router.get("/download/mobiliser/{mobiliser_id}")
def download_surveys_by_mobiliser(mobiliser_id: str):
    """Download all WWW surveys submitted by one mobiliser as .xlsx.

    `mobiliser_id` may be the numeric www_mobilisers.id or the mobiliser
    login string. www_survey_form stamps user_id = str(mobiliser.id) and
    user_name = login, so we match either."""
    # Resolve the mobiliser to its numeric id (for the user_id match).
    real_id = None
    with get_cursor() as cur:
        if str(mobiliser_id).isdigit():
            cur.execute("SELECT id FROM mis_azad.www_mobilisers WHERE id = %s", (int(mobiliser_id),))
            r = cur.fetchone()
            if r: real_id = r["id"]
        if real_id is None:
            cur.execute("SELECT id FROM mis_azad.www_mobilisers WHERE LOWER(mobiliser_id) = LOWER(%s) AND deleted_at IS NULL", (mobiliser_id,))
            r = cur.fetchone()
            if r: real_id = r["id"]
    uid = str(real_id) if real_id is not None else str(mobiliser_id)
    where = "(s.deleted_at IS NULL) AND (s.user_id = %s OR s.user_name = %s)"
    params = [uid, mobiliser_id]
    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT s._pk AS id, s.response_id, s.date_of_survey,
                   s.quarter_of_survey, s.name_of_surveyer, s.designation,
                   s.name_with_whom_the_survey_is_done AS respondent_name,
                   s.contact_number, s.age, s.marital_status, s.education,
                   s.caste_category, s.religion,
                   s.state, s.district, s.block, s.grampanchayat,
                   s.centre_census AS centre_name, s.name_of_area_census AS area_name,
                   s.name_of_basti,
                   s.total_family_members, s.how_many_earning_members_are_there_in_the_family AS earning_members,
                   s.total_monthly_income, s.per_capita_income,
                   s.is_she_working, s.what_kind_of_work_is_she_doing,
                   s.what_is_the_monthly_income,
                   s.are_you_intrested_joining_www_program_at_azad AS interested_in_www,
                   s.is_she_eligible_to_join_the_www_program AS eligible,
                   s.is_she_eligible_and_intrested AS eligible_and_interested,
                   s.server_synced_at, s.mobile_createdat
            FROM www_survey_form s
            WHERE {where}
            ORDER BY s.date_of_survey DESC NULLS LAST, s._pk DESC
            """,
            params,
        )
        rows = cur.fetchall()
    from routes._www_export_tracking import www_tracking_cells as _wt_cells
    _wt = _wt_cells(rows, "mis_azad.www_survey_form", "id", "_pk")
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow([
        'S.No', 'Survey ID', 'Date', 'Quarter',
        'Surveyor', 'Designation', 'Respondent', 'Contact',
        'Age', 'Marital Status', 'Education', 'Caste', 'Religion',
        'State', 'District', 'Block', 'Gram Panchayat',
        'Centre', 'Area', 'Basti',
        'Family Members', 'Earning Members', 'Monthly Income', 'Per Capita Income',
        'Is Working', 'Kind of Work', 'Her Monthly Income',
        'Interested in WWW', 'Eligible', 'Eligible & Interested',
        'Server Synced At', 'Mobile Created At', 'Created By', 'Updated By', 'Updated At',
    ])
    for i, r in enumerate(rows, 1):
        w.writerow([
            i, r.get('response_id') or '',
            r['date_of_survey'].isoformat() if r.get('date_of_survey') else '',
            r.get('quarter_of_survey') or '',
            r.get('name_of_surveyer') or '', r.get('designation') or '',
            r.get('respondent_name') or '', r.get('contact_number') or '',
            r.get('age') or '', r.get('marital_status') or '',
            r.get('education') or '', r.get('caste_category') or '', r.get('religion') or '',
            r.get('state') or '', r.get('district') or '', r.get('block') or '', r.get('grampanchayat') or '',
            r.get('centre_name') or '', r.get('area_name') or '', r.get('name_of_basti') or '',
            r.get('total_family_members') or '', r.get('earning_members') or '',
            r.get('total_monthly_income') or '', r.get('per_capita_income') or '',
            r.get('is_she_working') or '', r.get('what_kind_of_work_is_she_doing') or '',
            r.get('what_is_the_monthly_income') or '',
            r.get('interested_in_www') or '',
            r.get('eligible') or '', r.get('eligible_and_interested') or '',
            r.get('server_synced_at').isoformat() if r.get('server_synced_at') else '',
            r.get('mobile_createdat').isoformat() if r.get('mobile_createdat') else '',
        ] + _wt[i-1])
    from export_helper import csv_string_to_xlsx_response
    return csv_string_to_xlsx_response(
        output.getvalue(),
        f"WWW_Survey_mobiliser_{mobiliser_id}_{_date.today().isoformat()}.xlsx",
    )


@router.get("/{pk}")
def get_survey(request: Request, pk: int):
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM www_survey_form WHERE _pk = %s AND deleted_at IS NULL",
            (pk,),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Survey record not found")
    # 2026-09-24: www_survey_form has centre_census (a name) instead of the
    # centre_code column _scope.guard_detail expects, and it also has no
    # per-row centre_code at all. Using guard_detail 404s every survey a PI
    # opens (centre check fails) and every survey opened by any restricted
    # role that lacks a district/centre pin (fail-closed). Instead mirror
    # list_surveys's scoping: run scope_geo with centre=None and check the
    # row against state + district only -- exactly the way the LIST already
    # decides what this caller may see. Consistent with what the caller sees
    # on the Survey List page.
    state_code_s, district_code_s, _ = _scope.scope_geo(request, None, None, None)
    if state_code_s == _scope.DENY:
        raise HTTPException(status_code=404, detail="Survey record not found")
    if state_code_s and row.get("state_code") != state_code_s:
        raise HTTPException(status_code=404, detail="Survey record not found")
    if district_code_s and row.get("district_code") != district_code_s:
        raise HTTPException(status_code=404, detail="Survey record not found")
    return row


@router.delete("/{pk}")
def delete_survey(pk: int):
    with get_cursor() as cur:
        cur.execute("SELECT _pk FROM www_survey_form WHERE _pk = %s AND deleted_at IS NULL", (pk,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Survey record not found")
        cur.execute("UPDATE www_survey_form SET deleted_at = NOW() WHERE _pk = %s", (pk,))
    return {"message": "Survey record deleted"}
