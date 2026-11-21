"""WWW Mobilisation module — activity-log entries per centre / date.

Mounted under /api/www-mobilisation. Isolated from FLP.

Endpoints:
  GET  /                         list with filters (centre / month / from / to / name / status page/limit)
  GET  /export/excel             filter-honoring CSV→XLSX export
  GET  /{id}                     single record
  POST /                         create
  PUT  /{id}                     full update
  DELETE /{id}                   soft-delete
"""
from fastapi import APIRouter, HTTPException, Request
from routes import _www_scope as _scope
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import date as _date
import sys, os, io, csv, json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from routes._www_list_sort import www_list_order

router = APIRouter(prefix="/api/www-mobilisation", tags=["WWW Mobilisation"])


# ---------- Pydantic ----------

class OtherActivity(BaseModel):
    name: Optional[str] = None
    detail: Optional[str] = None


class MobilisationBody(BaseModel):
    # Basic Details
    centre_code: str
    activity_date: str
    month: str
    quarter: str

    # Geographical Coverage
    districts_covered_count: Optional[int] = 0
    districts_covered_names: Optional[str] = None
    wards_covered_count: Optional[int] = 0
    old_bastis_count: Optional[int] = 0
    old_bastis_names: Optional[str] = None
    new_bastis_count: Optional[int] = 0
    new_bastis_names: Optional[str] = None
    total_bastis_count: Optional[int] = 0

    # Activities
    canopy_count: Optional[int] = 0
    community_meeting_count: Optional[int] = 0
    street_play_count: Optional[int] = 0
    mike_prachar_count: Optional[int] = 0
    rally_count: Optional[int] = 0
    other_activities_count: Optional[int] = 0
    other_activities: Optional[List[OtherActivity]] = None
    www_survey_count: Optional[int] = 0

    # Direct Outreach
    dir_www_survey: Optional[int] = 0
    dir_canopy: Optional[int] = 0
    dir_community_meeting: Optional[int] = 0
    dir_street_play: Optional[int] = 0
    dir_mike_prachar: Optional[int] = 0
    dir_rally: Optional[int] = 0
    dir_other_activities: Optional[int] = 0
    total_direct_outreach: Optional[int] = 0

    # Indirect Outreach
    ind_canopy: Optional[int] = 0
    ind_community_meeting: Optional[int] = 0
    ind_street_play: Optional[int] = 0
    ind_mike_prachar: Optional[int] = 0
    ind_rally: Optional[int] = 0
    ind_other_activities: Optional[int] = 0
    total_indirect_outreach: Optional[int] = 0
    pamphlet_distributed: Optional[int] = 0

    # Follow Ups
    enrol_home_visit: Optional[int] = 0
    enrol_phone_calls: Optional[int] = 0
    enrol_total_follow_up: Optional[int] = 0
    walkout_home_visit: Optional[int] = 0
    walkout_phone_calls: Optional[int] = 0
    walkout_total_follow_up: Optional[int] = 0
    walkouts_prevented: Optional[int] = 0

    # Registration & Enrollment
    interested_eligible_count: Optional[int] = 0
    eligible_count: Optional[int] = 0
    registrations_count: Optional[int] = 0
    enrollments_count: Optional[int] = 0
    registered_no_documents: Optional[int] = 0
    interested_not_eligible_no_docs: Optional[int] = 0

    # Women & GBV Support
    women_counselled_documents: Optional[int] = 0
    documents_made_count: Optional[int] = 0
    documents_made_types: Optional[str] = None
    women_reported_gbv: Optional[int] = 0
    women_counselled_gbv: Optional[int] = 0
    violence_support_options: Optional[List[str]] = None
    violence_support_other_specify: Optional[str] = None
    cbo_collaborations: Optional[int] = 0

    # 2026-11-04: Save-as-Draft support
    is_draft: Optional[bool] = False


ALL_COLS = [
    "centre_code","activity_date","month","quarter",
    "districts_covered_count","districts_covered_names","wards_covered_count",
    "old_bastis_count","old_bastis_names","new_bastis_count","new_bastis_names","total_bastis_count",
    "canopy_count","community_meeting_count","street_play_count","mike_prachar_count","rally_count",
    "other_activities_count","other_activities","www_survey_count",
    "dir_www_survey","dir_canopy","dir_community_meeting","dir_street_play",
    "dir_mike_prachar","dir_rally","dir_other_activities","total_direct_outreach",
    "ind_canopy","ind_community_meeting","ind_street_play","ind_mike_prachar",
    "ind_rally","ind_other_activities","total_indirect_outreach","pamphlet_distributed",
    "enrol_home_visit","enrol_phone_calls","enrol_total_follow_up",
    "walkout_home_visit","walkout_phone_calls","walkout_total_follow_up","walkouts_prevented",
    "interested_eligible_count","eligible_count","registrations_count","enrollments_count",
    "registered_no_documents","interested_not_eligible_no_docs",
    "women_counselled_documents","documents_made_count","documents_made_types",
    "women_reported_gbv","women_counselled_gbv","violence_support_options",
    "violence_support_other_specify","cbo_collaborations",
    "is_draft",
]

JSON_COLS = {"other_activities", "violence_support_options"}


def _row_to_body_values(body: MobilisationBody):
    d = body.dict()
    # dicts / lists → JSON strings for JSONB
    if d.get("other_activities") is not None:
        d["other_activities"] = json.dumps([oa if isinstance(oa, dict) else oa for oa in d["other_activities"]])
    if d.get("violence_support_options") is not None:
        d["violence_support_options"] = json.dumps(d["violence_support_options"])
    return [d.get(c) for c in ALL_COLS]


# ---------- CRUD ----------

# 2026-09-28: name -> month number. Used by list + export month filter
# to also match EXTRACT(MONTH FROM activity_date) so a typo in the free
# text `month` column (e.g. 'Feburary') no longer hides the row.
_MOB_MONTH_NUM = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
    'july': 7,   'august':   8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
}

def _mob_month_predicate(month_val):
    key = (month_val or '').strip().lower()
    n = _MOB_MONTH_NUM.get(key)
    if n is None:
        try: n = int(key)
        except Exception: n = None
    if n and 1 <= n <= 12:
        return "(m.month = %s OR EXTRACT(MONTH FROM m.activity_date) = %s)", [month_val, n]
    return "m.month = %s", [month_val]



@router.get("")
def list_mobilisations(request: Request,
                       state_code: Optional[str] = None,
                       centre_code: Optional[str] = None,
                       month: Optional[str] = None,
                       date_from: Optional[str] = None,
                       date_to: Optional[str] = None,
                       name: Optional[str] = None,  # accepted, but currently unused (no name column)
                       sort_by: Optional[str] = None,
                       page: int = 1, limit: int = 10):
    offset = max(0, (page - 1) * limit)
    _cc = _scope.scoped_centre_codes(request)
    # 2026-09-25: the scope helper returns WWW-mapped centre NAMES
    # (e.g. "North Delhi") because most WWW modules key by name.
    # Mobilisation rows key by the central CODE (e.g. "S07091B2"), so we
    # expand `_cc` to include BOTH forms -- otherwise a PI/DL/SL sees an
    # empty list even though rows exist for their centre.
    if _cc:
        with get_cursor() as _mcc:
            _mcc.execute(
                "SELECT centre_code FROM mis_azad.central_centres "
                "WHERE centre_name = ANY(%s) OR centre_code = ANY(%s)",
                (_cc, _cc),
            )
            _extra = [r["centre_code"] for r in _mcc.fetchall()]
        _cc = list(set(list(_cc) + _extra))
    conds: List[str] = ["m.deleted_at IS NULL"]
    params: List = []
    if _cc is not None:
        conds.append("m.centre_code = ANY(%s)"); params.append(_cc)
    if state_code:
        # 2026-09-25: match by code OR by name (name-as-code rows) OR by
        # LEFT(3) prefix (orphan codes like S19348B1). Belt-and-braces so
        # the state filter never silently drops a row.
        conds.append("(m.centre_code IN (SELECT centre_code FROM mis_azad.central_centres WHERE state_code = %s) OR m.centre_code IN (SELECT centre_name FROM mis_azad.central_centres WHERE state_code = %s) OR LEFT(m.centre_code, 3) = %s)")
        params.append(state_code); params.append(state_code); params.append(state_code)
    if centre_code:
        # 2026-09-25: the shared /www-master/dropdown/centres feeds the Mob
        # Centre filter with `www_centres.centre_code` -- but that table
        # stores the NAME as its code for most rows, so the filter used to
        # send "North Delhi" while mob rows store "S07091B2". Accept BOTH
        # forms: match by code, or translate the picked name to a code via
        # central_centres.
        # 2026-09-28: WB mob rows use orphan codes 'S19348B1' (South Kolkata)
        # and 'S19348B2' (North Kolkata) that aren't in central_centres. The
        # SELECT above has a hardcoded CASE for display; replicate it here so
        # a picker value of 'South Kolkata' / 'North Kolkata' / their canonical
        # www_centres codes (S19347B3 / S19347B4) also match the orphan rows.
        # 2026-09-28: resolve the picker's value via BOTH central_centres AND
        # www_centres so live picks like 'S19347B3' (South Kolkata in
        # www_centres but NOT in central_centres) match the WB orphan rows.
        conds.append(
            "("
            "m.centre_code = %s "
            "OR m.centre_code IN (SELECT centre_code FROM mis_azad.central_centres WHERE centre_name = %s) "
            "OR m.centre_code IN (SELECT centre_code FROM mis_azad.central_centres     WHERE centre_name = %s AND deleted_at IS NULL) "
            "OR CASE m.centre_code WHEN 'S19348B1' THEN 'South Kolkata' WHEN 'S19348B2' THEN 'North Kolkata' END = %s "
            "OR CASE m.centre_code WHEN 'S19348B1' THEN 'South Kolkata' WHEN 'S19348B2' THEN 'North Kolkata' END IN ("
            "     SELECT centre_name FROM mis_azad.central_centres WHERE centre_code = %s "
            "     UNION "
            "     SELECT centre_name FROM mis_azad.central_centres     WHERE centre_code = %s AND deleted_at IS NULL"
            ") "
            ")"
        )
        params.extend([centre_code] * 6)
    if month:
        _mp, _mparams = _mob_month_predicate(month)
        conds.append(_mp); params.extend(_mparams)
    if date_from:
        # 2026-09-28: match reporting-month-start OR raw activity_date so
        # a report filed on the 1st (e.g. May report filed Jun 1) still
        # shows up when filtering from the start of its reporting month.
        conds.append("(m.activity_date >= %s OR date_trunc('month', m.activity_date - INTERVAL '1 day')::date >= %s)")
        params.append(date_from); params.append(date_from)
    if date_to:
        # 2026-09-28: mirror the date_from widening for the upper bound.
        conds.append("(m.activity_date <= %s OR date_trunc('month', m.activity_date - INTERVAL '1 day')::date <= %s)")
        params.append(date_to); params.append(date_to)
    if name and name.strip():
        # Free-text search across the "names" columns since there is no
        # explicit person column on this record.
        conds.append("(COALESCE(m.districts_covered_names,'') ILIKE %s"
                     " OR COALESCE(m.old_bastis_names,'') ILIKE %s"
                     " OR COALESCE(m.new_bastis_names,'') ILIKE %s)")
        like = f"%{name.strip()}%"
        params.extend([like, like, like])
    where = " AND ".join(conds)

    with get_cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS total FROM www_mobilisation_form m WHERE {where}", params)
        total = cur.fetchone()["total"]
        # 2026-08-31: resolve state via the WWW masters (mobilisation stores the
        # centre as its NAME, so JOIN central_centres by name -> www_states) so the
        # list can show "Centre, State". Sort By applies here too.
        _mob_order = www_list_order(
            sort_by, "centre_name", "m.id",
            "m.id DESC", enroll_col="m.id")
        cur.execute(
            f"""
            SELECT m.id, m.centre_code, m.activity_date, m.month, m.quarter,
                   m.canopy_count, m.rally_count,
                   m.total_direct_outreach, m.total_indirect_outreach,
                   m.is_draft,
                   COALESCE(
                       CASE m.centre_code
                           WHEN 'S19348B1' THEN 'South Kolkata'
                           WHEN 'S19348B2' THEN 'North Kolkata'
                       END,
                       c.centre_name, cn.centre_name, m.centre_code
                   ) AS centre_name,
                   COALESCE(cs.state_name, cns.state_name, csp.state_name, '') AS state_name,
                   m.created_at, m.updated_at
            FROM www_mobilisation_form m
            LEFT JOIN mis_azad.central_centres c   ON m.centre_code = c.centre_code
            LEFT JOIN mis_azad.central_states  cs  ON cs.state_code = c.state_code
            -- 2026-09-25 fallbacks for the 52 rows whose centre_code isn't a real code:
            --   * cn:  matches when centre_code holds a NAME instead (e.g. "North Delhi").
            --   * csp: derives state from the first 3 chars of the code (S19348B1 -> S19).
            LEFT JOIN mis_azad.central_centres cn  ON cn.centre_name = m.centre_code
            LEFT JOIN mis_azad.central_states  cns ON cns.state_code = cn.state_code
            LEFT JOIN mis_azad.central_states  csp ON csp.state_code = LEFT(m.centre_code, 3)
            WHERE {where}
            ORDER BY {_mob_order}
            LIMIT %s OFFSET %s
            """,
            params + [limit, offset],
        )
        rows = cur.fetchall()
    return {"total": total, "page": page, "limit": limit, "data": rows}


@router.get("/export/excel")
def export_mobilisations(request: Request,
                         state_code: Optional[str] = None,
                         centre_code: Optional[str] = None,
                         month: Optional[str] = None,
                         date_from: Optional[str] = None,
                         date_to: Optional[str] = None,
                         name: Optional[str] = None):
    _cc = _scope.scoped_centre_codes(request)
    if _cc:
        with get_cursor() as _mcc:
            _mcc.execute(
                "SELECT centre_code FROM mis_azad.central_centres "
                "WHERE centre_name = ANY(%s) OR centre_code = ANY(%s)",
                (_cc, _cc),
            )
            _extra = [r["centre_code"] for r in _mcc.fetchall()]
        _cc = list(set(list(_cc) + _extra))
    conds: List[str] = ["m.deleted_at IS NULL"]
    params: List = []
    if _cc is not None: conds.append("m.centre_code = ANY(%s)"); params.append(_cc)
    # 2026-09-25: mirror list_mobilisations state/centre filter fixes.
    if state_code:
        conds.append("(m.centre_code IN (SELECT centre_code FROM mis_azad.central_centres WHERE state_code = %s) OR m.centre_code IN (SELECT centre_name FROM mis_azad.central_centres WHERE state_code = %s) OR LEFT(m.centre_code, 3) = %s)")
        params.append(state_code); params.append(state_code); params.append(state_code)
    if centre_code:
        # 2026-09-28: WB mob rows use orphan codes 'S19348B1' (South Kolkata)
        # and 'S19348B2' (North Kolkata) that aren't in central_centres. The
        # SELECT above has a hardcoded CASE for display; replicate it here so
        # a picker value of 'South Kolkata' / 'North Kolkata' / their canonical
        # www_centres codes (S19347B3 / S19347B4) also match the orphan rows.
        # 2026-09-28: resolve the picker's value via BOTH central_centres AND
        # www_centres so live picks like 'S19347B3' (South Kolkata in
        # www_centres but NOT in central_centres) match the WB orphan rows.
        conds.append(
            "("
            "m.centre_code = %s "
            "OR m.centre_code IN (SELECT centre_code FROM mis_azad.central_centres WHERE centre_name = %s) "
            "OR m.centre_code IN (SELECT centre_code FROM mis_azad.central_centres     WHERE centre_name = %s AND deleted_at IS NULL) "
            "OR CASE m.centre_code WHEN 'S19348B1' THEN 'South Kolkata' WHEN 'S19348B2' THEN 'North Kolkata' END = %s "
            "OR CASE m.centre_code WHEN 'S19348B1' THEN 'South Kolkata' WHEN 'S19348B2' THEN 'North Kolkata' END IN ("
            "     SELECT centre_name FROM mis_azad.central_centres WHERE centre_code = %s "
            "     UNION "
            "     SELECT centre_name FROM mis_azad.central_centres     WHERE centre_code = %s AND deleted_at IS NULL"
            ") "
            ")"
        )
        params.extend([centre_code] * 6)
    if month:
        _mp, _mparams = _mob_month_predicate(month)
        conds.append(_mp); params.extend(_mparams)
    if date_from:
        # 2026-09-28: mirror the list's date_from widening (reporting-
        # month-start OR raw activity_date).
        conds.append("(m.activity_date >= %s OR date_trunc('month', m.activity_date - INTERVAL '1 day')::date >= %s)")
        params.append(date_from); params.append(date_from)
    if date_to:
        # 2026-09-28: mirror the list's date_to widening.
        conds.append("(m.activity_date <= %s OR date_trunc('month', m.activity_date - INTERVAL '1 day')::date <= %s)")
        params.append(date_to); params.append(date_to)
    if name and name.strip():
        conds.append("(COALESCE(m.districts_covered_names,'') ILIKE %s"
                     " OR COALESCE(m.old_bastis_names,'') ILIKE %s"
                     " OR COALESCE(m.new_bastis_names,'') ILIKE %s)")
        like = f"%{name.strip()}%"; params.extend([like, like, like])
    where = " AND ".join(conds)

    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT m.id, COALESCE(
                       CASE m.centre_code
                           WHEN 'S19348B1' THEN 'South Kolkata'
                           WHEN 'S19348B2' THEN 'North Kolkata'
                       END,
                       c.centre_name, cn.centre_name, m.centre_code
                   ) AS centre_name,
                   COALESCE(cs.state_name, cns.state_name, csp.state_name, '') AS state_name,
                   m.activity_date, m.month, m.quarter,
                   m.districts_covered_count, m.districts_covered_names,
                   m.wards_covered_count,
                   m.old_bastis_count, m.old_bastis_names,
                   m.new_bastis_count, m.new_bastis_names,
                   m.total_bastis_count,
                   m.canopy_count, m.community_meeting_count, m.street_play_count,
                   m.mike_prachar_count, m.rally_count, m.other_activities_count,
                   m.other_activities, m.www_survey_count,
                   m.dir_www_survey, m.dir_canopy, m.dir_community_meeting, m.dir_street_play,
                   m.dir_mike_prachar, m.dir_rally, m.dir_other_activities, m.total_direct_outreach,
                   m.ind_canopy, m.ind_community_meeting, m.ind_street_play,
                   m.ind_mike_prachar, m.ind_rally, m.ind_other_activities, m.total_indirect_outreach,
                   m.pamphlet_distributed,
                   m.enrol_home_visit, m.enrol_phone_calls, m.enrol_total_follow_up,
                   m.walkout_home_visit, m.walkout_phone_calls, m.walkout_total_follow_up,
                   m.walkouts_prevented,
                   m.interested_eligible_count, m.eligible_count,
                   m.registrations_count, m.enrollments_count,
                   m.registered_no_documents, m.interested_not_eligible_no_docs,
                   m.women_counselled_documents, m.documents_made_count, m.documents_made_types,
                   m.women_reported_gbv, m.women_counselled_gbv,
                   m.violence_support_options, m.violence_support_other_specify,
                   m.cbo_collaborations
            FROM www_mobilisation_form m
            LEFT JOIN mis_azad.central_centres c   ON m.centre_code = c.centre_code
            LEFT JOIN mis_azad.central_states  cs  ON cs.state_code = c.state_code
            LEFT JOIN mis_azad.central_centres cn  ON cn.centre_name = m.centre_code
            LEFT JOIN mis_azad.central_states  cns ON cns.state_code = cn.state_code
            LEFT JOIN mis_azad.central_states  csp ON csp.state_code = LEFT(m.centre_code, 3)
            WHERE {where}
            ORDER BY m.activity_date DESC NULLS LAST, m.id DESC
            """,
            params,
        )
        rows = cur.fetchall()

    from routes._www_export_tracking import www_tracking_cells as _wt_cells
    _wt = _wt_cells(rows, "mis_azad.www_mobilisation_form", "id", "id")
    output = io.StringIO()
    w = csv.writer(output)
    def _flatten_json(val):
        """Best-effort flatten of JSONB (list/dict/str) into a semicolon-joined string."""
        if val is None:
            return ''
        if isinstance(val, str):
            try:
                val = json.loads(val)
            except Exception:
                return val
        if isinstance(val, list):
            out = []
            for it in val:
                if isinstance(it, dict):
                    parts = [str(it.get('name','')).strip(), str(it.get('detail','')).strip()]
                    parts = [p for p in parts if p]
                    if parts:
                        out.append(': '.join(parts))
                elif it is not None and str(it).strip():
                    out.append(str(it))
            return '; '.join(out)
        return str(val)
    w.writerow([
        'S.No', 'Centre', 'State', 'Date', 'Month', 'Quarter',
        'Districts Covered', 'Districts Names',
        'Wards Covered',
        'Old Bastis', 'Old Bastis Names',
        'New Bastis', 'New Bastis Names',
        'Total Bastis',
        'Canopy', 'Community Meeting', 'Street Play',
        'Mike Prachar', 'Rally', 'Other Activities Count', 'Other Activities',
        'WWW Survey',
        'Dir WWW Survey', 'Dir Canopy', 'Dir Community Meeting', 'Dir Street Play',
        'Dir Mike Prachar', 'Dir Rally', 'Dir Other', 'Total Direct Outreach',
        'Ind Canopy', 'Ind Community Meeting', 'Ind Street Play',
        'Ind Mike Prachar', 'Ind Rally', 'Ind Other', 'Total Indirect Outreach',
        'Pamphlets Distributed',
        'Enrol Home Visit', 'Enrol Phone Calls', 'Enrol Total Follow-Up',
        'Walkout Home Visit', 'Walkout Phone Calls', 'Walkout Total Follow-Up',
        'Walkouts Prevented',
        'Interested+Eligible', 'Eligible', 'Registrations', 'Enrollments',
        'Registered w/o Docs', 'Interested Not Eligible (no docs)',
        'Women Counselled (docs)', 'Docs Made', 'Docs Made Types',
        'Women Reported GBV', 'Women Counselled GBV',
        'Violence Support Options', 'Violence Support Other',
        'CBO Collaborations', 'Created By', 'Updated By', 'Updated At',
    ])
    for i, r in enumerate(rows, 1):
        w.writerow([
            i, r.get('centre_name') or '', r.get('state_name') or '',
            r['activity_date'].isoformat() if r.get('activity_date') else '',
            r.get('month') or '', r.get('quarter') or '',
            r.get('districts_covered_count') or 0, r.get('districts_covered_names') or '',
            r.get('wards_covered_count') or 0,
            r.get('old_bastis_count') or 0, r.get('old_bastis_names') or '',
            r.get('new_bastis_count') or 0, r.get('new_bastis_names') or '',
            r.get('total_bastis_count') or 0,
            r.get('canopy_count') or 0, r.get('community_meeting_count') or 0,
            r.get('street_play_count') or 0, r.get('mike_prachar_count') or 0,
            r.get('rally_count') or 0, r.get('other_activities_count') or 0,
            _flatten_json(r.get('other_activities')),
            r.get('www_survey_count') or 0,
            r.get('dir_www_survey') or 0, r.get('dir_canopy') or 0,
            r.get('dir_community_meeting') or 0, r.get('dir_street_play') or 0,
            r.get('dir_mike_prachar') or 0, r.get('dir_rally') or 0,
            r.get('dir_other_activities') or 0, r.get('total_direct_outreach') or 0,
            r.get('ind_canopy') or 0, r.get('ind_community_meeting') or 0,
            r.get('ind_street_play') or 0, r.get('ind_mike_prachar') or 0,
            r.get('ind_rally') or 0, r.get('ind_other_activities') or 0,
            r.get('total_indirect_outreach') or 0,
            r.get('pamphlet_distributed') or 0,
            r.get('enrol_home_visit') or 0, r.get('enrol_phone_calls') or 0,
            r.get('enrol_total_follow_up') or 0,
            r.get('walkout_home_visit') or 0, r.get('walkout_phone_calls') or 0,
            r.get('walkout_total_follow_up') or 0,
            r.get('walkouts_prevented') or 0,
            r.get('interested_eligible_count') or 0, r.get('eligible_count') or 0,
            r.get('registrations_count') or 0, r.get('enrollments_count') or 0,
            r.get('registered_no_documents') or 0, r.get('interested_not_eligible_no_docs') or 0,
            r.get('women_counselled_documents') or 0, r.get('documents_made_count') or 0,
            r.get('documents_made_types') or '',
            r.get('women_reported_gbv') or 0, r.get('women_counselled_gbv') or 0,
            _flatten_json(r.get('violence_support_options')),
            r.get('violence_support_other_specify') or '',
            r.get('cbo_collaborations') or 0,
        ] + _wt[i-1])
    from export_helper import csv_string_to_xlsx_response
    return csv_string_to_xlsx_response(
        output.getvalue(),
        f"WWW_Mobilisation_{_date.today().isoformat()}.xlsx",
    )


@router.get("/{mob_id}")
def get_mobilisation(request: Request, mob_id: int):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT m.*, COALESCE(c.centre_name, m.centre_code) AS centre_name
            FROM www_mobilisation_form m
            LEFT JOIN mis_azad.central_centres c ON m.centre_code = c.centre_code
            WHERE m.id = %s AND m.deleted_at IS NULL
            """,
            (mob_id,),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Mobilisation record not found")
    # 2026-09-25: expand the caller's scope to include BOTH the WWW-name form
    # AND the central code form before checking membership. Same reason as the
    # list endpoint fix -- guard_detail_by_centre would otherwise 404 a PI/DL/SL
    # every time they open a row (their scope is ['North Delhi'] but the row
    # stores 'S07091B2', so the raw guard sees a mismatch).
    _cc = _scope.scoped_centre_codes(request)
    if _cc is not None:
        if _cc:
            with get_cursor() as _mcc:
                _mcc.execute(
                    "SELECT centre_code FROM mis_azad.central_centres "
                    "WHERE centre_name = ANY(%s) OR centre_code = ANY(%s)",
                    (_cc, _cc),
                )
                _extra = [r["centre_code"] for r in _mcc.fetchall()]
            _cc = list(set(list(_cc) + _extra))
        rc = (row.get("centre_code") or "")
        if rc not in _cc:
            raise HTTPException(status_code=404, detail="Not found.")
    return row


@router.post("")
def create_mobilisation(body: MobilisationBody):
    values = _row_to_body_values(body)
    placeholders = ", ".join(["%s"] * len(ALL_COLS))
    cols_sql = ", ".join(ALL_COLS)
    with get_cursor() as cur:
        cur.execute(
            f"INSERT INTO www_mobilisation_form ({cols_sql}) VALUES ({placeholders}) RETURNING id",
            values,
        )
        new_id = cur.fetchone()["id"]
    return {"id": new_id, "message": "Mobilisation record created"}


@router.put("/{mob_id}")
def update_mobilisation(mob_id: int, body: MobilisationBody):
    with get_cursor() as cur:
        cur.execute("SELECT id FROM www_mobilisation_form WHERE id = %s AND deleted_at IS NULL", (mob_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Mobilisation record not found")
        values = _row_to_body_values(body)
        set_sql = ", ".join(f"{c} = %s" for c in ALL_COLS)
        cur.execute(
            f"UPDATE www_mobilisation_form SET {set_sql}, updated_at = NOW() WHERE id = %s",
            values + [mob_id],
        )
    return {"message": "Mobilisation record updated"}


@router.delete("/{mob_id}")
def delete_mobilisation(mob_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT id FROM www_mobilisation_form WHERE id = %s AND deleted_at IS NULL", (mob_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Mobilisation record not found")
        cur.execute("UPDATE www_mobilisation_form SET deleted_at = NOW() WHERE id = %s", (mob_id,))
    return {"message": "Mobilisation record deleted"}
