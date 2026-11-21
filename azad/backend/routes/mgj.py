"""MGJ (Men with Gender Justice) module routes."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from jose import jwt, JWTError
from config import JWT_SECRET, JWT_ALGORITHM
from fastapi.responses import StreamingResponse
from typing import Optional, Any, Dict
from pydantic import BaseModel
from psycopg2.extras import Json
import sys, os, io, csv, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from config import UPLOAD_DIR

router = APIRouter(prefix="/api/mgj", tags=["MGJ"])


class MGJCreate(BaseModel):
    name: str
    surname: Optional[str] = None
    # Basic Profile
    date_of_birth: Optional[str] = None
    age_at_enrollment: Optional[int] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    permanent_address: Optional[str] = None
    state_code: Optional[str] = None
    district_code: Optional[str] = None
    centre_code: Optional[str] = None
    area_code: Optional[str] = None
    group_number: Optional[str] = None
    batch_id: Optional[int] = None
    mobiliser_name: Optional[str] = None
    caste_category: Optional[str] = None
    community_religion: Optional[str] = None
    gender: Optional[str] = None
    social_media_account: Optional[str] = None
    social_media_details: Optional[str] = None
    marital_status: Optional[str] = None
    age_at_marriage: Optional[int] = None
    number_of_children: Optional[int] = None
    # Family
    family_members_count: Optional[int] = None
    earning_members: Optional[int] = None
    monthly_family_income: Optional[float] = None
    per_capita_income: Optional[float] = None
    women_below_18: Optional[int] = None
    men_below_18: Optional[int] = None
    women_above_18: Optional[int] = None
    men_above_18: Optional[int] = None
    women_in_azad: Optional[str] = None
    women_in_azad_relation: Optional[str] = None
    men_in_azad: Optional[str] = None
    men_in_azad_relation: Optional[str] = None
    # Per-member breakdown — JSONB. Shape:
    #   { "women_below_18": [{member_no, edu}, …],
    #     "men_below_18":   [{member_no, edu}, …],
    #     "women_above_18": [{member_no, act, mar}, …],
    #     "men_above_18":   [{member_no, act, mar}, …] }
    family_member_details: Optional[Dict[str, Any]] = None
    # Education
    education: Optional[str] = None
    education_other: Optional[str] = None
    education_year: Optional[int] = None   # 2026-05-27 — year of attainment
    still_studying: Optional[str] = None
    studying_what: Optional[str] = None    # legacy — UI removed 2026-05-27, column kept for old data
    # Work
    career_status: Optional[str] = None    # legacy — UI replaced by `is_working` on 2026-05-27
    is_working: Optional[str] = None       # 'Yes' / 'No' — gates the work-detail fields
    work_type: Optional[str] = None        # 'Full Time' / 'Part Time' (only when is_working = Yes)
    work_nature: Optional[str] = None
    work_place: Optional[str] = None
    monthly_income: Optional[float] = None
    future_goal: Optional[str] = None
    occupation: Optional[str] = None
    how_know_azad: Optional[str] = None
    why_join_mgj: Optional[str] = None
    challenges: Optional[str] = None
    status: Optional[str] = 'Active'


class MGJRemarksUpdate(BaseModel):
    remarks: Optional[str] = None


def _ensure_mgj_extension_columns(cur):
    """Keep MGJ list usable when code is deployed before migration 070.

    These are additive, nullable columns only; existing member rows and values
    are not changed. The migration remains the canonical deployment path, while
    this guard prevents the list query from failing with UndefinedColumn.
    """
    expected = {"mobiliser_name", "remarks", "remarks_date"}
    cur.execute("""
        SELECT attname
          FROM pg_attribute
         WHERE attrelid = 'mgj_members'::regclass
           AND attname = ANY(%s)
           AND NOT attisdropped
    """, (list(expected),))
    if expected.issubset({row["attname"] for row in cur.fetchall()}):
        return
    cur.execute("""
        ALTER TABLE mgj_members
          ADD COLUMN IF NOT EXISTS mobiliser_name VARCHAR(200),
          ADD COLUMN IF NOT EXISTS remarks TEXT,
          ADD COLUMN IF NOT EXISTS remarks_date DATE
    """)


def _generate_enrollment(cur, state_code, district_code):
    """Generate MGJ enrollment number: AF/MGJ-StateAbbr/Session/Serial"""
    import datetime
    year = datetime.date.today().year
    month = datetime.date.today().month
    # Financial year: Apr-Mar
    if month >= 4:
        year_str = f"{year}-{str(year+1)[-2:]}"
    else:
        year_str = f"{year-1}-{str(year)[-2:]}"

    # Get state abbreviation from central_states (the MGJ-side master, kept in
    # sync with FLP geo via the canonical-cleanup migration).
    state_abbr = 'XX'
    if state_code:
        cur.execute(
            "SELECT state_name FROM central_states WHERE state_code = %s AND deleted_at IS NULL",
            (state_code,),
        )
        row = cur.fetchone()
        if row:
            # Use first 3 chars of state name
            state_abbr = row['state_name'][:3].capitalize()

    prefix = f"AF/MGJ-{state_abbr}/{year_str}"

    # 2026-05-28 bugfix: derive next serial from the MAX existing serial
    # under this prefix, NOT from COUNT(*) of non-deleted rows. The old
    # COUNT+1 approach collided whenever any member was soft-deleted —
    # e.g. with rows 001/002/003 and 002 soft-deleted, COUNT(non-deleted)+1
    # = 3, so the generator tried to re-insert "003" and the unique
    # constraint mgj_members_enrollment_number_key fired.
    #
    # We scan ALL rows (including soft-deleted) matching the prefix so
    # the next serial is always strictly above the highest serial ever
    # used for this state/year, even if those rows are gone.
    cur.execute(
        "SELECT enrollment_number FROM mgj_members WHERE enrollment_number LIKE %s",
        (f"{prefix}/%",),
    )
    max_serial = 0
    for row in cur.fetchall():
        try:
            n = int((row['enrollment_number'] or '').rsplit('/', 1)[-1])
            if n > max_serial:
                max_serial = n
        except (ValueError, AttributeError):
            pass
    serial = max_serial + 1

    return f"{prefix}/{serial:03d}"




# 2026-08-04 — MGJ List mobiliser scoping.
# When a Mobiliser is logged in, the MGJ list / export endpoints must
# only surface members owned by THAT mobiliser (i.e. members whose
# ``mgj_members.mobiliser_name`` matches the caller's ``users.name``).
# Historically the list handler took an optional ``mobiliser_name``
# query param that was purely client-side, so a mobiliser could see —
# and open — any other mobiliser's records simply by not sending it.
# The helper below re-resolves the JWT caller and returns their role /
# name; the two list endpoints then SERVER-SIDE OVERRIDE any client
# value when the caller is a Mobiliser. Admins / SL / DL / PI etc. are
# unaffected. Deliberately does NOT modify _role_scope.enforce_role_scope
# (that helper is shared with many endpoints and only pins geo codes;
# mobiliser ownership is orthogonal to geo scope).
def _caller_user_id(request):
    """Return the JWT-authenticated caller's user id (int) or None.
    2026-08-13: added so create_mgj can stamp mgj_members.created_by
    with the operator's user id (the export's 'Created By' column
    reads users.name via this fk)."""
    try:
        auth = request.headers.get("authorization", "")
    except Exception:
        return None
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None
    try:
        uid = int(payload.get("sub", 0))
    except (TypeError, ValueError):
        return None
    return uid if uid > 0 else None


def _caller_role_and_name(request):
    """Return (role_lower, user_name) for the JWT-authenticated caller
    or (None, None). Never raises — fail-open matches _role_scope."""
    try:
        auth = request.headers.get("authorization", "")
    except Exception:
        return (None, None)
    if not auth.startswith("Bearer "):
        return (None, None)
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return (None, None)
    try:
        user_id = int(payload.get("sub", 0))
    except (TypeError, ValueError):
        return (None, None)
    if user_id <= 0:
        return (None, None)
    with get_cursor() as cur:
        cur.execute(
            "SELECT u.name, LOWER(r.name) AS role_name "
            "  FROM mis_user u JOIN roles r ON r.id = u.role_id "
            " WHERE u.id = %s AND u.deleted_at IS NULL",
            (user_id,),
        )
        row = cur.fetchone()
    if not row:
        return (None, None)
    return (row["role_name"], row["name"])

@router.get("")
def list_mgj(request: Request,
             state_code: Optional[str] = None, district_code: Optional[str] = None,
             centre_code: Optional[str] = None,
             area_code: Optional[str] = None,
             group_number: Optional[str] = None,
             batch_id: Optional[int] = None,
             mobiliser_name: Optional[str] = None,
             name: Optional[str] = None, status: Optional[str] = None,
             date_from: Optional[str] = None, date_to: Optional[str] = None,
             include_dropout: bool = False,
             sort_by: Optional[str] = None,
             page: int = 1, limit: int = 10):
    """
    2026-05-30: Default behaviour now EXCLUDES members whose status is
    Walkout/Dropout, so any dropdown / selection picker that reads from
    this endpoint stops leaking dropped-out members. The MGJ Members
    list page passes ``include_dropout=true`` to opt back in.
    """
    offset = (page - 1) * limit
    with get_cursor() as cur:
        _ensure_mgj_extension_columns(cur)
        conditions = ["m.deleted_at IS NULL"]
        params = []
        # 2026-08-04 — Server-side override: when the caller is a
        # Mobiliser, IGNORE any client-supplied mobiliser_name and
        # force the filter to the caller's own users.name so a
        # mobiliser cannot see (or open) another mobiliser's
        # members. Other roles fall through to the client value if
        # any (unchanged behaviour for admins / SL / DL / PI).
        _caller_role, _caller_name = _caller_role_and_name(request)
        if _caller_role == "mobiliser":
            mobiliser_name = _caller_name or ""
        if mobiliser_name:
            conditions.append("TRIM(m.mobiliser_name) ILIKE TRIM(%s)")
            params.append(mobiliser_name)
        if state_code:
            conditions.append("m.state_code = %s"); params.append(state_code)
        if district_code:
            conditions.append("m.district_code = %s"); params.append(district_code)
        if centre_code:
            conditions.append("m.centre_code = %s"); params.append(centre_code)
        # 2026-08-06: Area + Group Name filters. mgj_members.area_code is
        # populated by the Add MGJ form; group_number stores the group NAME
        # string (matches mgj_master_groups.name — see cascade comment at
        # the render site around line 19735 in app.js).
        if area_code:
            conditions.append("m.area_code = %s"); params.append(area_code)
        if group_number:
            conditions.append("m.group_number = %s"); params.append(group_number)
        if batch_id:
            conditions.append("m.batch_id = %s"); params.append(batch_id)
        if name:
            conditions.append("m.name ILIKE %s"); params.append(f"%{name}%")
        if status == 'Dropout':
            # 2026-07-24: MGJ List Status filter picks 'Dropout' but the
            # DB stores dropouts as status='Walkout'. Alias so the filter
            # returns those rows (parallels the mgj_dashboard alias).
            conditions.append("m.status IN ('Walkout', 'Dropout')")
        elif status:
            conditions.append("m.status = %s"); params.append(status)
        elif not include_dropout:
            conditions.append("COALESCE(m.status,'Active') NOT IN ('Walkout','Dropout')")
        if date_from:
            conditions.append("m.created_at >= %s::date"); params.append(date_from)
        if date_to:
            conditions.append("m.created_at <= (%s::date + interval '1 day')"); params.append(date_to)

        where = " AND ".join(conditions)

        # 2026-08-25: Sort By — whitelist mapping. Default (unknown
        # or missing) preserves insertion order (m.id ASC).
        # updated_* uses GREATEST(updated_at, created_at) so rows
        # sort by most-recent activity (add OR update).
        _sort_map = {
            "name_asc":     "LOWER(TRIM(m.name)) ASC  NULLS LAST, m.id ASC",
            "name_desc":    "LOWER(TRIM(m.name)) DESC NULLS LAST, m.id DESC",
            "updated_desc": "GREATEST(m.updated_at, m.created_at) DESC NULLS LAST, m.id DESC",
            "updated_asc":  "GREATEST(m.updated_at, m.created_at) ASC  NULLS LAST, m.id ASC",
        }
        order_by = _sort_map.get(sort_by or "", "m.id ASC")

        cur.execute(f"SELECT COUNT(*) as total FROM mgj_members m WHERE {where}", params)
        total = cur.fetchone()["total"]

        # 2026-06-08: Expose batch_id + batch_name on the list payload
        # so the new "Batch" column on the MGJ List page can render
        # without a per-row lookup. Joined LEFT so members without an
        # assigned batch still appear (batch_name comes back as '').
        cur.execute(f"""
            SELECT m.id, m.enrollment_number, m.name, m.mobiliser_name, m.mobile, m.status,
                   m.group_number, m.state_code, m.centre_code, m.area_code,
                   m.batch_id,
                   -- 2026-08-13: expose date_of_birth so the list can render
                   -- it in place of Enrollment No. (per user request).
                   m.date_of_birth,
                   COALESCE(b.name, '') as batch_name,
                   COALESCE(nc.centre_name, '') as centre_name,
                   COALESCE(ns.state_name, '') as state_name,
                   COALESCE(na.area_name, '') as area_name,
                   m.created_at,
                   EXISTS (
                     SELECT 1 FROM mgj_leaders l
                     WHERE l.member_id = m.id
                       AND l.deleted_at IS NULL
                       AND l.status = 'Active'
                   ) AS is_leader
            FROM mgj_members m
            LEFT JOIN central_centres nc ON m.centre_code = nc.centre_code AND nc.deleted_at IS NULL
            LEFT JOIN central_states  ns ON m.state_code  = ns.state_code  AND ns.deleted_at IS NULL
            LEFT JOIN central_areas   na ON m.area_code   = na.area_code   AND na.deleted_at IS NULL
            LEFT JOIN mgj_master_batches b ON m.batch_id = b.id        AND b.deleted_at  IS NULL
            WHERE {where}
            -- 2026-08-25: dynamic sort — driven by sort_by query param.
            -- Whitelist-mapped above; safe to interpolate directly.
            ORDER BY {order_by}
            LIMIT %s OFFSET %s
        """.replace("{order_by}", order_by), params + [limit, offset])
        rows = cur.fetchall()

        # 2026-07-24: Batch-fetch Pakhwada attendance summary for every
        # member on this page in one query, then merge onto each row.
        # Keeps the per-row payload cheap (single object with two nested
        # objects) and avoids N+1 lookups from the frontend. Counts only
        # rows from Submitted sessions per session_type INPUT / SPORTS.
        _DEFAULT_PAKH = lambda: {
            'input':  {'present': 0, 'absent': 0, 'one_on_one': 0, 'late': 0, 'total': 0},
            'sports': {'present': 0, 'absent': 0, 'one_on_one': 0, 'late': 0, 'total': 0},
        }
        _pakh_by_id = {}
        _member_ids = [r['id'] for r in rows]
        if _member_ids:
            cur.execute("""
                SELECT a.member_id, s.session_type, a.status, COUNT(*) AS c
                FROM mgj_pakhwada_attendance a
                JOIN mgj_pakhwada_sessions   s ON s.id = a.session_id
                WHERE a.member_id = ANY(%s)
                  AND s.deleted_at IS NULL
                  AND s.attendance_status = 'Submitted'
                GROUP BY a.member_id, s.session_type, a.status
            """, (_member_ids,))
            _STATUS_KEY = {'Present': 'present', 'Absent': 'absent',
                           'Late': 'late', '1:1 Session': 'one_on_one'}
            for pr in cur.fetchall():
                stype = 'input' if pr['session_type'] == 'INPUT' else \
                        'sports' if pr['session_type'] == 'SPORTS' else None
                key   = _STATUS_KEY.get(pr['status'])
                if not stype or not key:
                    continue
                summary = _pakh_by_id.setdefault(pr['member_id'], _DEFAULT_PAKH())
                summary[stype][key]   += int(pr['c'])
                summary[stype]['total'] += int(pr['c'])
        data_out = []
        for r in rows:
            row = dict(r)
            row['pakhwada_summary'] = _pakh_by_id.get(row['id'], _DEFAULT_PAKH())
            data_out.append(row)

    return {"total": total, "page": page, "limit": limit, "data": data_out}


@router.get("/export/excel")
def export_mgj(request: Request,
               state_code: Optional[str] = None, district_code: Optional[str] = None,
               centre_code: Optional[str] = None,
               area_code: Optional[str] = None, group_number: Optional[str] = None,
               batch_id: Optional[int] = None,
               mobiliser_name: Optional[str] = None,
               name: Optional[str] = None, status: Optional[str] = None):
    # 2026-07-06: Export rewritten — two reported problems:
    #   1) "State" came out blank/misplaced. The old query resolved state
    #      through the district chain (m.district_code → central_districts →
    #      central_states), but the registration form doesn't capture a
    #      district at all (State → Centre → Area cascade only), so
    #      district_code is NULL for every member and the state join
    #      never matched. Fixed by joining central_states DIRECTLY on
    #      m.state_code — the same pattern get_mgj / list_mgj use.
    #   2) The old export had only 13 columns (including the legacy
    #      "Occupation" field the form no longer collects). Now exports
    #      the full registration field set in the same order as the
    #      Add-MGJ form / member View page, plus Centre/Area/Batch names
    #      and an aggregated Education History column.
    with get_cursor() as cur:
        conditions = ["m.deleted_at IS NULL"]
        params = []
        # 2026-08-04 — Mirror of list_mgj mobiliser-scope override:
        # a Mobiliser calling the Excel export must only get their
        # own members. Force mobiliser_name to the caller's name.
        _caller_role, _caller_name = _caller_role_and_name(request)
        if _caller_role == "mobiliser":
            mobiliser_name = _caller_name or ""
        if mobiliser_name:
            conditions.append("TRIM(m.mobiliser_name) ILIKE TRIM(%s)")
            params.append(mobiliser_name)
        if state_code: conditions.append("m.state_code = %s"); params.append(state_code)
        if district_code: conditions.append("m.district_code = %s"); params.append(district_code)
        if centre_code: conditions.append("m.centre_code = %s"); params.append(centre_code)
        if area_code: conditions.append("m.area_code = %s"); params.append(area_code)
        if group_number: conditions.append("m.group_number = %s"); params.append(group_number)
        if batch_id: conditions.append("m.batch_id = %s"); params.append(batch_id)
        if name: conditions.append("m.name ILIKE %s"); params.append(f"%{name}%")
        if status: conditions.append("m.status = %s"); params.append(status)
        where = " AND ".join(conditions)

        cur.execute(f"""
            SELECT m.*,
                   COALESCE(ns.state_name,  '') as state_name,
                   COALESCE(nc.centre_name, '') as centre_name,
                   COALESCE(na.area_name,   '') as area_name,
                   COALESCE(b.name,         '') as batch_name,
                   -- 2026-08-13: resolve created_by (user id) to user name so
                   -- the export can show a "Created By" column in the last
                   -- position (per user request). Fallback chain for legacy
                   -- rows: users.name -> mobiliser_name -> group's mobiliser.
                   COALESCE(cu.name,
                            NULLIF(TRIM(m.mobiliser_name), ''),
                            NULLIF(TRIM(mg.mobiliser_name), ''),
                            '') as created_by_name,
                   (SELECT string_agg(eh.year || ' - ' ||
                                      COALESCE(NULLIF(eh.qualification_other, ''), eh.qualification),
                                      '; ' ORDER BY eh.year)
                      FROM mgj_member_education_history eh
                     WHERE eh.member_id = m.id AND eh.deleted_at IS NULL) as education_history
            FROM mgj_members m
            LEFT JOIN central_states         ns ON m.state_code  = ns.state_code  AND ns.deleted_at IS NULL
            LEFT JOIN central_centres        nc ON m.centre_code = nc.centre_code AND nc.deleted_at IS NULL
            LEFT JOIN central_areas          na ON m.area_code   = na.area_code   AND na.deleted_at IS NULL
            LEFT JOIN mgj_master_batches b  ON m.batch_id    = b.id           AND b.deleted_at  IS NULL
            LEFT JOIN mis_user                 cu ON m.created_by  = cu.id
            -- 2026-08-13: legacy rows lack created_by and mobiliser_name;
            -- fall back to the group's assigned mobiliser via group_number.
            LEFT JOIN mgj_master_groups     mg ON mg.name       = m.group_number AND mg.deleted_at IS NULL
            WHERE {where} ORDER BY LOWER(TRIM(m.name)) ASC NULLS LAST, m.id ASC  -- 2026-08-21: alphabetical
        """, params)
        rows = cur.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Enrollment No.', 'Status', 'State', 'Centre', 'Area', 'Cohort', 'Group Name', 'Mobiliser Name',
        'Name', 'Date of Birth', 'Age at Enrollment', 'Current Age', 'Address', 'Mobile Number',
        'Caste Category', 'Community (Religion)', 'Gender',
        'Social Media Account', 'Social Media Details',
        'Marital Status', 'Age at Marriage', 'Number of Children',
        'Family Members Count', 'Earning Members', 'Monthly Family Income', 'Per Capita Income',
        'Women Below 18', 'Men Below 18', 'Women Above 18', 'Men Above 18',
        'Women Associated with Azad', 'Women Member Relation',
        'Men Associated with Azad', 'Men Member Relation',
        'Education Qualification', 'Education (Other)',
        'Still Studying', 'Education History',
        'Are You Working', 'Work Nature', 'Work Place', 'Monthly Income (Self)',
        'Future Goal / Aspiration',
        'Walkout Date', 'Walkout Reason', 'Created',
        # 2026-08-13: expose the user who created each MGJ member as the
        # last column so exports can be audited per data-entry operator.
        'Created By'
    ])
    from datetime import date as _date
    def _compute_age(dob, ref=None):
        if not dob:
            return ''
        try:
            d = _date.fromisoformat(str(dob)[:10]) if not isinstance(dob, _date) else dob
            t = ref if ref else _date.today()
            if not isinstance(t, _date):
                t = _date.fromisoformat(str(t)[:10])
            return str(t.year - d.year - ((t.month, t.day) < (d.month, d.day)))
        except Exception:
            return ''
    def _present_age(dob, age_at_enroll):
        if age_at_enroll not in (None, ''):
            return str(age_at_enroll)
        return _compute_age(dob)
    for r in rows:
        def _g(key):
            v = r.get(key)
            return '' if v is None else str(v)
        writer.writerow([
            _g('enrollment_number'), _g('status'),
            r['state_name'], r['centre_name'], r['area_name'], r['batch_name'], _g('group_number'), _g('mobiliser_name'),
            _g('name'), _g('date_of_birth'),
            (_g('age_at_enrollment') if r.get('age_at_enrollment') not in (None, '') else _compute_age(r.get('date_of_birth'), r.get('created_at'))),
            _compute_age(r.get('date_of_birth')),
            _g('address'), _g('mobile'),
            _g('caste_category'), _g('community_religion'), _g('gender'),
            _g('social_media_account'), _g('social_media_details'),
            _g('marital_status'), _g('age_at_marriage'), _g('number_of_children'),
            _g('family_members_count'), _g('earning_members'),
            _g('monthly_family_income'), _g('per_capita_income'),
            _g('women_below_18'), _g('men_below_18'), _g('women_above_18'), _g('men_above_18'),
            _g('women_in_azad'), _g('women_in_azad_relation'),
            _g('men_in_azad'), _g('men_in_azad_relation'),
            _g('education'), _g('education_other'),
            _g('still_studying'), _g('education_history'),
            _g('is_working'), _g('work_nature'), _g('work_place'), _g('monthly_income'),
            _g('future_goal'),
            _g('walkout_date'), _g('walkout_reason'), str(r['created_at'])[:10],
            # 2026-08-13: created_by_name comes from the LEFT JOIN on users
            # (aliased 'cu'). Empty string when the member has no owner id.
            r.get('created_by_name') or ''
        ])
    from datetime import date
    from export_helper import csv_string_to_xlsx_response
    return csv_string_to_xlsx_response(output.getvalue(), f"MGJ_List_Export_{date.today().isoformat()}.xlsx")


@router.get("/{mgj_id}")
def get_mgj(mgj_id: int):
    with get_cursor() as cur:
        _ensure_mgj_extension_columns(cur)
        cur.execute("""
            SELECT m.*, COALESCE(ns.state_name, '') as state_name,
                   COALESCE(nc.centre_name, '') as centre_name,
                   COALESCE(na.area_name, '') as area_name,
                   COALESCE(nd.district_name, '') as district_name,
                   COALESCE(b.name, '') as batch_name
            FROM mgj_members m
            LEFT JOIN central_states       ns ON m.state_code    = ns.state_code    AND ns.deleted_at IS NULL
            LEFT JOIN central_centres      nc ON m.centre_code   = nc.centre_code   AND nc.deleted_at IS NULL
            LEFT JOIN central_areas        na ON m.area_code     = na.area_code     AND na.deleted_at IS NULL
            LEFT JOIN central_districts    nd ON m.district_code = nd.district_code AND nd.deleted_at IS NULL
            LEFT JOIN mgj_master_batches b ON m.batch_id     = b.id             AND b.deleted_at  IS NULL
            WHERE m.id = %s AND m.deleted_at IS NULL
        """, (mgj_id,))
        member = cur.fetchone()
    if not member:
        raise HTTPException(status_code=404, detail="MGJ member not found")
    return dict(member)


def _validate_mgj_payload(mgj: "MGJCreate"):
    """Server-side sanity checks that complement the frontend gauntlet.
    2026-06-03 — added Monthly Family Income > 0 check at the request
    layer so a crafted curl / replayed payload can't slip a negative or
    zero income past the UI. Frontend already enforces this, but the
    spec is explicit that validation must work at API level too."""
    if mgj.monthly_family_income is not None and mgj.monthly_family_income <= 0:
        raise HTTPException(status_code=400,
            detail="Monthly Family Income must be greater than 0. "
                   "Zero or negative amounts are not allowed.")
    if mgj.family_members_count is not None and mgj.family_members_count <= 0:
        raise HTTPException(status_code=400,
            detail="Number of Family Members must be greater than 0.")
    if (mgj.earning_members is not None and mgj.family_members_count is not None
            and mgj.earning_members > mgj.family_members_count):
        raise HTTPException(status_code=400,
            detail="Earning Members cannot exceed Number of Family Members.")
    if (mgj.education_year is not None and mgj.date_of_birth):
        try:
            dob_year = int(str(mgj.date_of_birth)[:4])
            if mgj.education_year < dob_year:
                raise HTTPException(status_code=400,
                    detail=f"Year of qualification ({mgj.education_year}) cannot be "
                           f"earlier than the year of birth ({dob_year}).")
        except (ValueError, TypeError):
            pass


@router.post("")
def create_mgj(mgj: MGJCreate, request: Request):
    _validate_mgj_payload(mgj)
    # 2026-08-13: capture the authenticated user's id so mgj_members
    # .created_by is stamped on insert. The export's "Created By" column
    # LEFT JOINs users on this fk - before this fix every new row's
    # created_by was NULL and the export column came out blank.
    _uid = _caller_user_id(request)
    with get_cursor() as cur:
        _ensure_mgj_extension_columns(cur)
        enrollment = _generate_enrollment(cur, mgj.state_code, mgj.district_code)

        cur.execute("""
            INSERT INTO mgj_members (
                enrollment_number, name, surname, date_of_birth, age_at_enrollment,
                mobile, email, address, permanent_address,
                state_code, district_code, centre_code, area_code,
                group_number, batch_id, mobiliser_name,
                caste_category, community_religion, gender,
                social_media_account, social_media_details,
                marital_status, age_at_marriage, number_of_children,
                family_members_count, earning_members, monthly_family_income, per_capita_income,
                women_below_18, men_below_18, women_above_18, men_above_18,
                women_in_azad, women_in_azad_relation, men_in_azad, men_in_azad_relation,
                family_member_details,
                education, education_other, education_year, still_studying, studying_what,
                career_status, is_working, work_type, work_nature, work_place, monthly_income, future_goal,
                occupation, how_know_azad, why_join_mgj, challenges, status,
                created_by
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (enrollment, mgj.name, mgj.surname, mgj.date_of_birth, mgj.age_at_enrollment,
              mgj.mobile, mgj.email, mgj.address, mgj.permanent_address,
              mgj.state_code, mgj.district_code, mgj.centre_code, mgj.area_code,
              mgj.group_number, mgj.batch_id, mgj.mobiliser_name,
              mgj.caste_category, mgj.community_religion, mgj.gender,
              mgj.social_media_account, mgj.social_media_details,
              mgj.marital_status, mgj.age_at_marriage, mgj.number_of_children,
              mgj.family_members_count, mgj.earning_members, mgj.monthly_family_income, mgj.per_capita_income,
              mgj.women_below_18, mgj.men_below_18, mgj.women_above_18, mgj.men_above_18,
              mgj.women_in_azad, mgj.women_in_azad_relation, mgj.men_in_azad, mgj.men_in_azad_relation,
              Json(mgj.family_member_details) if mgj.family_member_details is not None else None,
              mgj.education, mgj.education_other, mgj.education_year, mgj.still_studying, mgj.studying_what,
              mgj.career_status, mgj.is_working, mgj.work_type, mgj.work_nature, mgj.work_place, mgj.monthly_income, mgj.future_goal,
              mgj.occupation, mgj.how_know_azad, mgj.why_join_mgj, mgj.challenges, mgj.status or 'Active',
              _uid))
        new_id = cur.fetchone()["id"]

        # Mirror the primary education into the per-member history so the
        # View page renders a uniform timeline. Only insert when the user
        # actually picked a qualification (not a Draft save with blank).
        if mgj.education and (mgj.education_year or mgj.education_year == 0):
            cur.execute(
                "INSERT INTO mgj_member_education_history (member_id, year, qualification, qualification_other) "
                "VALUES (%s, %s, %s, %s)",
                (new_id, mgj.education_year, mgj.education, mgj.education_other),
            )

    return {"id": new_id, "enrollment_number": enrollment, "message": "MGJ member created"}


@router.put("/{mgj_id}")
def update_mgj(mgj_id: int, mgj: MGJCreate):
    _validate_mgj_payload(mgj)
    with get_cursor() as cur:
        _ensure_mgj_extension_columns(cur)
        cur.execute("SELECT id FROM mgj_members WHERE id = %s AND deleted_at IS NULL", (mgj_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="MGJ member not found")

        cur.execute("""
            UPDATE mgj_members SET
                name=%s, surname=%s, date_of_birth=%s, age_at_enrollment=%s,
                mobile=%s, email=%s, address=%s, permanent_address=%s,
                state_code=%s, district_code=%s, centre_code=%s, area_code=%s,
                group_number=%s, batch_id=%s, mobiliser_name=%s,
                caste_category=%s, community_religion=%s, gender=%s,
                social_media_account=%s, social_media_details=%s,
                marital_status=%s, age_at_marriage=%s, number_of_children=%s,
                family_members_count=%s, earning_members=%s, monthly_family_income=%s, per_capita_income=%s,
                women_below_18=%s, men_below_18=%s, women_above_18=%s, men_above_18=%s,
                women_in_azad=%s, women_in_azad_relation=%s, men_in_azad=%s, men_in_azad_relation=%s,
                family_member_details=%s,
                education=%s, education_other=%s, education_year=%s, still_studying=%s, studying_what=%s,
                career_status=%s, is_working=%s, work_type=%s, work_nature=%s, work_place=%s, monthly_income=%s, future_goal=%s,
                occupation=%s, how_know_azad=%s, why_join_mgj=%s, challenges=%s, status=%s,
                updated_at=NOW()
            WHERE id=%s
        """, (mgj.name, mgj.surname, mgj.date_of_birth, mgj.age_at_enrollment,
              mgj.mobile, mgj.email, mgj.address, mgj.permanent_address,
              mgj.state_code, mgj.district_code, mgj.centre_code, mgj.area_code,
              mgj.group_number, mgj.batch_id, mgj.mobiliser_name,
              mgj.caste_category, mgj.community_religion, mgj.gender,
              mgj.social_media_account, mgj.social_media_details,
              mgj.marital_status, mgj.age_at_marriage, mgj.number_of_children,
              mgj.family_members_count, mgj.earning_members, mgj.monthly_family_income, mgj.per_capita_income,
              mgj.women_below_18, mgj.men_below_18, mgj.women_above_18, mgj.men_above_18,
              mgj.women_in_azad, mgj.women_in_azad_relation, mgj.men_in_azad, mgj.men_in_azad_relation,
              Json(mgj.family_member_details) if mgj.family_member_details is not None else None,
              mgj.education, mgj.education_other, mgj.education_year, mgj.still_studying, mgj.studying_what,
              mgj.career_status, mgj.is_working, mgj.work_type, mgj.work_nature, mgj.work_place, mgj.monthly_income, mgj.future_goal,
              mgj.occupation, mgj.how_know_azad, mgj.why_join_mgj, mgj.challenges, mgj.status,
              mgj_id))

    return {"message": "MGJ member updated"}


@router.put("/{mgj_id}/remarks")
def update_mgj_remarks(mgj_id: int, body: MGJRemarksUpdate):
    remarks = (body.remarks or "").strip() or None
    with get_cursor() as cur:
        _ensure_mgj_extension_columns(cur)
        cur.execute("""
            UPDATE mgj_members
               SET remarks = %s,
                   remarks_date = CASE WHEN %s IS NULL THEN NULL ELSE CURRENT_DATE END,
                   updated_at = NOW()
             WHERE id = %s AND deleted_at IS NULL
         RETURNING id, remarks, remarks_date
        """, (remarks, remarks, mgj_id))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="MGJ member not found")
    return dict(row)


@router.delete("/{mgj_id}")
def delete_mgj(mgj_id: int):
    with get_cursor() as cur:
        cur.execute("UPDATE mgj_members SET deleted_at = NOW() WHERE id = %s", (mgj_id,))
    return {"message": "MGJ member deleted"}


# ── Dropout / Walkout ────────────────────────────────────────────────────
# Mirrors flp_records and ak_leaders. Sets status='Walkout' (rendered as
# "Dropout" in the UI via statusBadge) and captures the date + reason.
# Migration 044_mgj_members_dropout adds the two columns.

class MGJWalkoutRequest(BaseModel):
    walkout_date: str
    walkout_reason: Optional[str] = None


@router.post("/{mgj_id}/walkout")
def walkout_mgj(mgj_id: int, data: MGJWalkoutRequest):
    with get_cursor() as cur:
        cur.execute("""
            UPDATE mgj_members
               SET status='Walkout', walkout_date=%s, walkout_reason=%s, updated_at=NOW()
             WHERE id = %s AND deleted_at IS NULL
         RETURNING id
        """, (data.walkout_date, data.walkout_reason, mgj_id))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="MGJ member not found")
    return {"message": "MGJ member marked as dropout"}


# ── Photo Upload ─────────────────────────────────────────────────────────
# 2026-07-06: The MGJ member photo feature was half-built — the
# mgj_members.photo_url column existed and the edit form let the user pick
# a file (previewed locally via FileReader), but NOTHING ever uploaded or
# persisted it, so photo_url stayed NULL in the DB. This endpoint mirrors
# the working FLP (routes/flps.py upload_photo) and AK (routes/ak.py)
# patterns exactly: save under UPLOAD_DIR, persist the URL-RELATIVE
# /uploads/... path (never the filesystem path — see the flp_documents
# comment in flps.py for the 404 that caused).

@router.post("/{mgj_id}/photo")
async def upload_photo(mgj_id: int, file: UploadFile = File(...)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    saved_name = f"mgj_photo_{mgj_id}_{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, saved_name)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    photo_url = f"/uploads/{saved_name}"
    with get_cursor() as cur:
        cur.execute("""
            UPDATE mgj_members SET photo_url = %s, updated_at = NOW()
             WHERE id = %s AND deleted_at IS NULL RETURNING id
        """, (photo_url, mgj_id))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="MGJ member not found")
    return {"photo_url": photo_url}
