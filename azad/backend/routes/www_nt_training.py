"""WWW Non-Technical Training + Attendance.

Without the normalized www_nt_trainings / www_nt_attendance tables the
routes read mis_azad.www_ntt_training, which already stores one row per
trainee per training type along with that row's event dates and a
pre-rendered attendance summary.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from routes import _www_legacy as _legacy
from routes._www_list_sort import www_list_order
from routes import _www_scope as _scope

router = APIRouter(prefix="/api/www-nt-trainings", tags=["WWW NT Training"])

# API field -> www_ntt_training column, for the legacy write path.  The
# import already has a column per field, so this is a plain rename table.
# 2026-10-09: schema migration dropped individual_counselling_*,
# family_faculty_meeting_date, assembly_date from www_ntt_training
# (those live on www_institutional_events now) and renamed
# attendance_target -> attendance. Map stripped accordingly; API
# fields pointing at dropped columns silently no-op in UPDATE.
_LEGACY_UPDATE_MAP = {
    "quarter":                           "quarter",
    "training_type":                     "training_type",
    "centre_code":                       "centre",
    "facilitator_name":                  "facilitator_name",
    "start_date":                        "start_date",
    "end_date":                          "end_date",
    "status":                            "status",
    "attendance_target":                 "attendance",
}


class NTCreate(BaseModel):
    quarter: Optional[str] = None
    training_type: Optional[str] = None
    centre_code: Optional[str] = None
    facilitator_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = "Planned"
    attendance_target: Optional[int] = None


class NTUpdate(BaseModel):
    quarter: Optional[str] = None
    training_type: Optional[str] = None
    centre_code: Optional[str] = None
    facilitator_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    attendance_target: Optional[int] = None
    # 2026-07-31: Training-event dates stored per legacy source row.
    individual_counselling_start_date: Optional[date] = None
    individual_counselling_end_date: Optional[date] = None
    family_faculty_meeting_date: Optional[date] = None
    assembly_date: Optional[date] = None


class AttendanceItem(BaseModel):
    trainee_id: int
    status: Optional[str] = None  # 'present' | 'absent' | None


class AttendanceBulkUpdate(BaseModel):
    items: List[AttendanceItem]


class NTEventCreate(BaseModel):
    assembly_date: Optional[date] = None
    family_faculty_date: Optional[date] = None
    individual_start_date: Optional[date] = None
    individual_end_date: Optional[date] = None


def _row_select():
    return (
        "SELECT t.id, t.quarter, t.training_type, t.centre_code, t.facilitator_name, "
        "       t.start_date, t.end_date, t.status, t.attendance_target, t.created_at, "
        "       c.centre_name, c.state_code, "
        "       (SELECT count(*) FROM www_nt_attendance a WHERE a.training_id = t.id AND LOWER(a.attendance) = 'present') AS present_count, "
        "       (SELECT count(*) FROM www_nt_attendance a WHERE a.training_id = t.id AND LOWER(a.attendance) = 'absent')  AS absent_count, "
        "       (SELECT count(*) FROM www_nt_attendance a WHERE a.training_id = t.id) AS marked_count "
        "FROM www_nt_trainings t "
        "LEFT JOIN central_centres c ON c.centre_code = t.centre_code "
    )


def _legacy_end_date_filter(alias: str) -> str:
    """"Ends on or before" predicate for the import's text end_date column.

    2026-08-12: www_ntt_training.start_date is a real date but end_date is
    text, and seven rows hold something a cast chokes on ("29-02-2025",
    "12-09-2025 |").  COALESCE(end_date, start_date) therefore failed with
    "types text and date cannot be matched" and every list or export call
    carrying a To-date filter returned 500.  safe_date() nulls the junk out
    so those rows fall back to their start_date instead of killing the query.
    """
    return "COALESCE(%s, %s.start_date) <= %%s" % (
        _legacy.safe_date(f"{alias}.end_date"), alias)


# The CTE exposes the import's columns unrenamed, so the same predicate works
# against the "legacy" alias the list and export paths select from.
_LEGACY_END_DATE_FILTER = _legacy_end_date_filter("l")


# 2026-10-09: IDs returned for institutional events are OFFSET by this
# constant so they never collide with training ids on write. Trainings
# use their raw bigint id; events use (ie.id + _IE_ID_OFFSET).
_IE_ID_OFFSET = 1_000_000_000


def _resolve_tid(cur, training_id):
    """Return (actual_id, is_event). None/None if neither table has it."""
    if training_id >= _IE_ID_OFFSET:
        _real = training_id - _IE_ID_OFFSET
        cur.execute("SELECT 1 FROM mis_azad.www_institutional_events "
                    "WHERE id = %s AND deleted_at IS NULL", (_real,))
        return (_real, True) if cur.fetchone() else (None, None)
    # Legacy caller (no offset) -- probe both tables, prefer the training
    # table if alive there (keeps old pages working), else fall through
    # to institutional events.
    cur.execute("SELECT 1 FROM mis_azad.www_ntt_training "
                "WHERE id = %s AND deleted_at IS NULL", (training_id,))
    if cur.fetchone():
        return training_id, False
    cur.execute("SELECT 1 FROM mis_azad.www_institutional_events "
                "WHERE id = %s AND deleted_at IS NULL", (training_id,))
    return (training_id, True) if cur.fetchone() else (None, None)


def _legacy_list_cte():
    """Expose www_ntt_training under the output names the list/export code
    expects, after the 2026-10-08 schema migration dropped the per-trainee
    compat columns (enrollment_id/name/mobile/batch_id/date_of_joining/
    ll_number/attendance_target/individual_counselling_*/family_faculty_*/
    assembly_date). Trainee data for a training now lives in
    www_nt_attendance -> www_enrollment; the LIST stays one row per training
    with those trainee cells NULL. The EXPORT does its own LEFT JOIN of
    www_nt_attendance to expand per-attendee.
    """
    return (
        " WITH legacy AS ("
        "   SELECT n.id, NULL::bigint AS enrollment_id, NULL::bigint AS trainee_id, n.training_type, "
        # 2026-09-15: 54 recently re-imported training rows have a blank centre
        # column but a valid enrollment_id; fall back to the trainee's enrollment
        # centre so the Location (Centre, State) column is not blank for them (and
        # they stay filterable by Centre). Trainee-less rows have no source -> blank.
        # 2026-09-26: prefer www_centres-resolved code/name (via _gc join from
        # geo_joins) so a row whose n.centre stores 'South Kolkata' returns
        # centre_code='S19347B3' + centre_name='South Kolkata'. Falls back to
        # the raw centre_expr when the row's centre is unknown to www_centres.
        "          COALESCE(_gc.centre_code, " + _legacy.centre_expr("n.centre") + ", " + _legacy.centre_expr("_te.centre") + ") AS centre_code, "
        "          COALESCE(_gc.centre_name, " + _legacy.centre_expr("n.centre") + ", " + _legacy.centre_expr("_te.centre") + ") AS centre_name, "
        "          _gs.state_code, "
        "          _gd.district_code AS trainee_district_code, "
        # Plain names too — the export prints these, and a code is unreadable.
        # 2026-09-26: fallback state derived from centre when both n.state
        # and trainee's state are blank -- so a row still shows "South
        # Kolkata, West Bengal" instead of just "South Kolkata".
        "          COALESCE(NULLIF(TRIM(n.state), ''), NULLIF(TRIM(_te.state), ''), (SELECT s.state_name FROM mis_azad.central_states s WHERE s.state_code = _gc.state_code)) AS state_name, "
        "          COALESCE(NULLIF(TRIM(n.district), ''), NULLIF(TRIM(_te.district), '')) AS district_name, "
        "          n.facilitator_name, "
        "          NULL::text AS trainee_name, NULL::text AS enrollment_no, "
        "          NULL::date AS trainee_date_of_joining, "
        "          NULL::text AS trainee_ll_number, "
        # 2026-10-08: event-date columns removed from www_ntt_training
        # (they live on www_institutional_events now).
        "          n.start_date AS start_date, "
        "          " + _legacy.safe_date("n.end_date") + " AS end_date, "
        "          NULL::date AS individual_counselling_start_date, "
        "          NULL::date AS individual_counselling_end_date, "
        "          NULL::date AS family_faculty_meeting_date, "
        "          NULL::date AS assembly_date, "
        "          NULL::integer AS batch_id, "
        "          NULL::text AS batch_name, "
        # 2026-09-15: derive Quarter (FY: Q1 Apr-Jun / Q2 Jul-Sep / Q3 Oct-Dec /
        # Q4 Jan-Mar) from start_date, falling back to end_date (text); stored
        # n.quarter is blank on every row. Output Q1..Q4 to match the Quarter filter.
        "          CASE "
        "               WHEN COALESCE(n.start_date, " + _legacy.safe_date("n.end_date") + ") IS NULL THEN NULLIF(TRIM(n.quarter), '') "
        "               WHEN EXTRACT(MONTH FROM COALESCE(n.start_date, " + _legacy.safe_date("n.end_date") + ")) BETWEEN 4 AND 6 THEN 'Q1' "
        "               WHEN EXTRACT(MONTH FROM COALESCE(n.start_date, " + _legacy.safe_date("n.end_date") + ")) BETWEEN 7 AND 9 THEN 'Q2' "
        "               WHEN EXTRACT(MONTH FROM COALESCE(n.start_date, " + _legacy.safe_date("n.end_date") + ")) BETWEEN 10 AND 12 THEN 'Q3' "
        "               ELSE 'Q4' END AS quarter, "
        "          n.status, n.attendance AS attendance_target, "
        # attendance_count is a pre-rendered summary, e.g. "P:1 / A:0 / Marked:1".
        "          COALESCE(substring(n.attendance_count from 'P:[ ]*([0-9]+)')::int, 0) "
        "              AS present_count, "
        "          COALESCE(substring(n.attendance_count from 'A:[ ]*([0-9]+)')::int, 0) "
        "              AS absent_count, "
        "          COALESCE(substring(n.attendance_count from 'Marked:[ ]*([0-9]+)')::int, 0) "
        "              AS marked_count "
        # 2026-10-08: list = ONE ROW PER TRAINING. No trainee_join
        # (n.enrollment_id dropped); per-attendee data lives on
        # www_nt_attendance and is exposed only in the EXPORT path.
        # Keep a never-matching _te join so residual _te.* references
        # in the SELECT list resolve as NULL instead of UndefinedTable.
        "   FROM mis_azad.www_ntt_training n " + _legacy.geo_joins("n") +
        "   LEFT JOIN mis_azad.www_enrollment _te ON FALSE "
        "   WHERE NULLIF(TRIM(n.training_type), '') IS NOT NULL "
        # 2026-08-19: soft-delete ki hui training list me na aaye.
        "     AND n.deleted_at IS NULL"
        " ) "
    )


def _institutional_events_as_legacy_rows():
    """Shape mis_azad.www_institutional_events rows to the `legacy` CTE's
    29-column output so they can UNION ALL straight into it.

    2026-08-25: the historical dump's event data (assembly/family-faculty/
    individual-counselling dates) was moved out of www_ntt_training into
    www_institutional_events, keyed by enrollment_id rather than a specific
    training row. `id` here is any still-existing www_ntt_training row for
    that same trainee (the row the event was originally extracted from, if
    it's still there) so downstream code that expects a real training id
    (the events modal, row grouping) keeps working; 0 if none is found.
    """
    return (
        " SELECT "
        "   (ie.id + 1000000000) AS id, "
        "   NULL::bigint AS enrollment_id, NULL::bigint AS trainee_id, ie.type_of_event AS training_type, "
        # 2026-09-26: resolve centre via www_centres (see _gc3 join below)
        # so the events branch returns canonical centre_code (S19347B3)
        # + centre_name ("South Kolkata"), matching the main CTE and the
        # frontend Centre filter dropdown values.
        "   COALESCE(_gc3.centre_code, " + _legacy.centre_expr("ie.centre") + ") AS centre_code, "
        "   COALESCE(_gc3.centre_name, " + _legacy.centre_expr("ie.centre") + ") AS centre_name, "
        "   _gs3.state_code, _gd3.district_code AS trainee_district_code, "
        # 2026-09-26: fallback state derived from centre via _gc3.state_code.
        "   COALESCE(NULLIF(TRIM(_te3.state), ''), (SELECT s.state_name FROM mis_azad.central_states s WHERE s.state_code = _gc3.state_code)) AS state_name, _te3.district AS district_name, "
        "   NULL::text AS facilitator_name, "
        "   NULLIF(TRIM(_te3.name), '') AS trainee_name, "
        "   _te3.enrollment_no AS enrollment_no, "
        "   _te3.enrollment_date AS trainee_date_of_joining, "
        "   NULL::text AS trainee_ll_number, "
        # 2026-09-29: legacy branch's end_date is now DATE (after the
        # 2026-09-28 COALESCE widening) so this UNION partner must also
        # be DATE to keep Postgres happy.
        "   NULL::date AS start_date, NULL::date AS end_date, "
        "   ie.individual_counselling_start AS individual_counselling_start_date, "
        "   ie.individual_counselling_end   AS individual_counselling_end_date, "
        "   ie.family_faculty_meeting_date, ie.assembly_date, "
        "   NULL::integer AS batch_id, " + _legacy.batch_name("_te3.batch", "_te3.id") + " AS batch_name, "
        "   NULL::text AS quarter, NULL::text AS status, NULL::integer AS attendance_target, "
        # 2026-10-09 (user ask): live Present/Absent/Marked counts for event rows -- the Trainee Process list and View page need to show the real tally after attendance is saved (same table as training attendance, keyed by ie.id).
        "   (SELECT COUNT(*) FROM mis_azad.www_event_attendance a WHERE a.event_id = ie.id AND LOWER(a.attendance) = 'present' AND a.deleted_at IS NULL)::integer AS present_count, "
        "   (SELECT COUNT(*) FROM mis_azad.www_event_attendance a WHERE a.event_id = ie.id AND LOWER(a.attendance) = 'absent'  AND a.deleted_at IS NULL)::integer AS absent_count, "
        "   (SELECT COUNT(*) FROM mis_azad.www_event_attendance a WHERE a.event_id = ie.id AND LOWER(a.attendance) IN ('present','absent') AND a.deleted_at IS NULL)::integer AS marked_count "
        " FROM mis_azad.www_institutional_events ie "
        # 2026-10-09: www_ntt_training.enrollment_id was dropped,
        # so this subquery can no longer link an institutional event
        # back to a training by trainee. Keep the _im alias so the
        # SELECT list still resolves; COALESCE(_im.id, 0::bigint)
        # then always picks 0 as the training id placeholder.
        " LEFT JOIN (SELECT NULL::bigint AS enrollment_id, NULL::bigint AS id "
        "              WHERE FALSE) _im "
        "        ON FALSE "
        " LEFT JOIN mis_azad.www_enrollment _te3 ON FALSE "
        # 2026-09-26: centre resolution join for the SELECT above.
        " LEFT JOIN mis_azad.central_centres _gc3 "
        "        ON (_gc3.centre_code = " + _legacy.centre_expr("ie.centre") + " "
        "            OR _gc3.centre_name = " + _legacy.centre_expr("ie.centre") + ") "
        " LEFT JOIN mis_azad.central_states _gs3 ON _gs3.state_name = NULLIF(TRIM(_te3.state), '') "
        " LEFT JOIN mis_azad.central_districts _gd3 ON _gd3.district_name = NULLIF(TRIM(_te3.district), '') "
        "        AND (_gs3.state_code IS NULL OR _gd3.state_code = _gs3.state_code) "
        " WHERE ie.deleted_at IS NULL "
    )


def _legacy_training(cur, training_id: int):
    # 2026-10-09: the id can be bare (training) or offset by _IE_ID_OFFSET
    # (institutional event). The helper's SELECT emits ie.id + offset for
    # events, so the WHERE l.id = %s match naturally works on either
    # shape without touching the id here.
    cur.execute(
        _legacy_list_cte()
        + " SELECT l.* FROM ("
        + "   SELECT l.* FROM legacy l UNION ALL "
        + _institutional_events_as_legacy_rows()
        + " ) l WHERE l.id = %s",
        (training_id,),
    )
    return cur.fetchone()


def _legacy_identity(cur, training_id: int):
    """Confirm the training row exists; ids here are real www_ntt_training ids."""
    cur.execute("SELECT id FROM mis_azad.www_ntt_training WHERE id = %s", (training_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Training not found.")
    return row["id"]


@router.get("")
def list_trainings(
    request: Request,
    enrollment_id: Optional[int] = None,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    quarter: Optional[str] = None,
    training_type: Optional[str] = None,
    centre_code: Optional[str] = None,
    facilitator_name: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    # 2026-08-19: events_only restricts to rows created via the
    # Add Event flow (batch_id set OR any event date populated).
    events_only: bool = False,
    # 2026-09-30: exclude_events drops training_type IN (Assembly,
    # Family Faculty Meeting, Individual Counselling) so the Training
    # list shows only trainings (Trainee Process list uses events_only).
    exclude_events: bool = False,
    name: Optional[str] = None,
    batch_id: Optional[int] = None,
    sort_by: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
):
    page = max(page, 1); limit = max(limit, 1); offset = (page - 1) * limit
    _cc = _scope.scoped_centre_codes(request)
    with get_cursor() as cur:
        # Legacy DB stores one wide form per trainee. Expand its nine training
        # sections into list rows so existing data remains visible and pageable.
        cur.execute("SELECT to_regclass('mis_azad.www_nt_trainings') AS t")
        if not cur.fetchone()["t"]:
            conds = ["1=1"]; params = []
            if _cc is not None:  conds.append("l.centre_code = ANY(%s)");           params.append(_cc)
            if quarter:          conds.append("l.quarter = %s");                    params.append(quarter)
            if training_type:    conds.append("l.training_type = %s");              params.append(training_type)
            if centre_code:      conds.append("l.centre_code = %s");                params.append(centre_code)
            if facilitator_name: conds.append(_legacy.name_match("l.facilitator_name"));        params.append(_legacy.name_pattern(facilitator_name))
            if status:           conds.append("l.status = %s");                     params.append(status)
            if date_from:        conds.append("l.start_date >= %s");                 params.append(date_from)
            if date_to:          conds.append(_LEGACY_END_DATE_FILTER);              params.append(date_to)
            if state_code:       conds.append("l.state_code = %s");                  params.append(state_code)
            # 2026-08-19 additions:
            if name:             conds.append(_legacy.name_match("l.trainee_name")); params.append(_legacy.name_pattern(name))
            if batch_id:         conds.append("l.batch_id = %s");                    params.append(batch_id)
            if events_only:
                conds.append("(l.batch_id IS NOT NULL OR l.assembly_date IS NOT NULL "
                              "OR l.family_faculty_meeting_date IS NOT NULL "
                              "OR l.individual_counselling_start_date IS NOT NULL "
                              "OR l.individual_counselling_end_date IS NOT NULL)")
            elif exclude_events:
                # 2026-09-30: Training list -- drop event rows so only real
                # trainings (Map Reading / Self Defence / BKS / ...) show.
                conds.append("COALESCE(NULLIF(TRIM(l.training_type), ''), '') "
                              "NOT IN ('Assembly', 'Family Faculty Meeting', 'Individual Counselling')")
            where = "WHERE " + " AND ".join(conds)
            if enrollment_id:
                # 2026-09-02: sirf trainee ki APNI NT rows dikhao. Pehle ek
                # attendance-based OR bhi tha (jis session me trainee 'present'
                # ho wo bhi dikhta tha) -- lekin wo session-row DUSRE trainee
                # ke naam se labelled hoti thi, jisse View me "Amala M" jaise
                # dusre naam aur inflated count aa jaate the. User ne 2026-09-02
                # ko decide kiya: keval l.enrollment_id match hi dikhao.
                where += " AND l.enrollment_id = %s"
                params.append(enrollment_id)
            cte = _legacy_list_cte()
            # 2026-08-25: events_only also needs to surface the historical
            # events migrated into www_institutional_events (they no longer
            # live on any www_ntt_training row), so pull from a union of
            # both sources instead of `legacy` alone. Non-events listing is
            # untouched.
            from_clause = (
                "(SELECT l.* FROM legacy l UNION ALL " +
                _institutional_events_as_legacy_rows() + ") l"
                if events_only else
                "legacy l"
            )
            cur.execute(cte + " SELECT COUNT(*) AS total FROM " + from_clause + " " + where, params)
            total = cur.fetchone()["total"]
            # 2026-08-19: events_only rows don't have start_date, so
            # NULLS LAST pushes them to the very bottom of the list.
            # For that branch, sort by id DESC (newest first).
            # 2026-08-31: Sort By filter. events_only -> name is the trainee;
            # training list -> name is the facilitator.
            _nt_name = "l.trainee_name" if events_only else "l.facilitator_name"
            _nt_def  = "l.id DESC" if events_only else "l.id DESC"
            _order = " ORDER BY " + www_list_order(
                sort_by, _nt_name, "l.id", _nt_def, enroll_col="l.enrollment_no") + " "
            cur.execute(
                cte + " SELECT l.* FROM " + from_clause + " " + where +
                _order + " LIMIT %s OFFSET %s",
                params + [limit, offset],
            )
            return {"total": total, "page": page, "limit": limit, "data": cur.fetchall()}

        conds = ["t.deleted_at IS NULL"]; params = []
        if _cc is not None:  conds.append("t.centre_code = ANY(%s)");                   params.append(_cc)
        if quarter:          conds.append("t.quarter = %s");                            params.append(quarter)
        if training_type:    conds.append("t.training_type = %s");                      params.append(training_type)
        if centre_code:      conds.append("t.centre_code = %s");                        params.append(centre_code)
        if facilitator_name: conds.append(_legacy.name_match("t.facilitator_name"));               params.append(_legacy.name_pattern(facilitator_name))
        if status:           conds.append("t.status = %s");                             params.append(status)
        if date_from:        conds.append("t.start_date >= %s");                        params.append(date_from)
        if date_to:          conds.append("t.end_date <= %s");                          params.append(date_to)
        where = "WHERE " + " AND ".join(conds)
        cur.execute("SELECT COUNT(*) AS total FROM www_nt_trainings t " + where, params)
        total = cur.fetchone()["total"]
        sql = (_row_select() + where +
               " ORDER BY t.start_date DESC NULLS LAST, t.id DESC LIMIT %s OFFSET %s")
        cur.execute(sql, params + [limit, offset])
        rows = cur.fetchall()
        return {"total": total, "page": page, "limit": limit, "data": rows}


@router.get("/{training_id}")
def get_training(request: Request, training_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT to_regclass('mis_azad.www_nt_trainings') AS t")
        if not cur.fetchone()["t"]:
            row = _legacy_training(cur, training_id)
            if not row:
                raise HTTPException(404, "Training not found.")
            _scope.guard_detail_by_centre(request, row)
            # 2026-09-30: overlay live attendance counts from www_nt_attendance.
            # The CTE regex-scrapes the pre-rendered attendance_count text on
            # www_ntt_training which is empty for app-created + many historical
            # trainings, so the View page always showed 0/0/0. Prefer live counts.
            try:
                # 2026-10-09: try www_event_attendance first (new IE events).
                # If empty, fall through to www_nt_attendance (legacy trainings).
                _ev_id = training_id - _IE_ID_OFFSET if training_id >= _IE_ID_OFFSET else training_id
                cur.execute(
                    "SELECT "
                    "  COUNT(*) FILTER (WHERE LOWER(attendance) = 'present') AS present_count, "
                    "  COUNT(*) FILTER (WHERE LOWER(attendance) = 'absent')  AS absent_count, "
                    "  COUNT(*) FILTER (WHERE LOWER(attendance) IN ('present','absent')) AS marked_count "
                    "FROM mis_azad.www_event_attendance "
                    "WHERE event_id = %s AND deleted_at IS NULL",
                    (_ev_id,),
                )
                _att_evt = cur.fetchone() or {}
                if int(_att_evt.get("marked_count") or 0) > 0:
                    row["present_count"] = int(_att_evt.get("present_count") or 0)
                    row["absent_count"]  = int(_att_evt.get("absent_count")  or 0)
                    row["marked_count"]  = int(_att_evt.get("marked_count")  or 0)
                    return row
                cur.execute(
                    "SELECT "
                    "  COUNT(*) FILTER (WHERE LOWER(attendance) = 'present') AS present_count, "
                    "  COUNT(*) FILTER (WHERE LOWER(attendance) = 'absent')  AS absent_count, "
                    "  COUNT(*) FILTER (WHERE LOWER(attendance) IN ('present','absent')) AS marked_count "
                    "FROM mis_azad.www_nt_attendance "
                    "WHERE training_id = %s AND deleted_at IS NULL",
                    (training_id,),
                )
                _att = cur.fetchone()
                if _att:
                    _live_marked = int(_att.get("marked_count") or 0)
                    # Only overlay when live data has rows -- keeps the CTE's
                    # historical parse alive for pure legacy imports whose
                    # attendance was never persisted per-trainee.
                    if _live_marked > 0:
                        try: row["present_count"] = int(_att.get("present_count") or 0)
                        except Exception: pass
                        try: row["absent_count"]  = int(_att.get("absent_count")  or 0)
                        except Exception: pass
                        try: row["marked_count"] = _live_marked
                        except Exception: pass
            except Exception:
                pass
            return row
        cur.execute(_row_select() + "WHERE t.id = %s AND t.deleted_at IS NULL", (training_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Training not found.")
    _scope.guard_detail_by_centre(request, row)
    return row


@router.post("")
def create_training(body: NTCreate):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_nt_trainings"):
            # www_ntt_training rows are per trainee; a training created here
            # has no trainee attached yet, so only the session fields are set.
            cur.execute(
                "INSERT INTO mis_azad.www_ntt_training "
                "    (quarter, training_type, centre, facilitator_name, "
                "     start_date, end_date, status, attendance, "
                "     state, district) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s, "
                "        (SELECT state_name FROM mis_azad.central_states s "
                "          JOIN mis_azad.central_centres c ON c.state_code = s.state_code "
                "         WHERE c.centre_code = %s), "
                "        (SELECT district_name FROM mis_azad.central_districts d "
                "          JOIN mis_azad.central_centres c ON c.district_code = d.district_code "
                "         WHERE c.centre_code = %s)) "
                "RETURNING id",
                (body.quarter, body.training_type, body.centre_code, body.facilitator_name,
                 body.start_date, body.end_date, body.status or "Planned",
                 body.attendance_target, body.centre_code, body.centre_code),
            )
            return {"id": cur.fetchone()["id"], "ok": True}

        cur.execute(
            "INSERT INTO www_nt_trainings (quarter, training_type, centre_code, facilitator_name, "
            "start_date, end_date, status, attendance_target) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (body.quarter, body.training_type, body.centre_code, body.facilitator_name,
             body.start_date, body.end_date, body.status or "Planned", body.attendance_target),
        )
        new_id = cur.fetchone()["id"]
    return {"id": new_id, "ok": True}


@router.put("/{training_id}")
def update_training(training_id: int, body: NTUpdate):
    payload = body.model_dump(exclude_unset=True)
    if not payload:
        return {"ok": True}
    fields = []; params = []
    for k, v in payload.items():
        fields.append(f"{k} = %s"); params.append(v)
    params.append(training_id)
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_nt_trainings"):
            _legacy_identity(cur, training_id)
            updates, values = [], []
            for api_col, legacy_col in _LEGACY_UPDATE_MAP.items():
                val = payload.get(api_col)
                if api_col in payload and val is not None:
                    updates.append(f"{legacy_col} = %s"); values.append(val)
            if not updates:
                return {"ok": True}
            values.append(training_id)
            cur.execute(
                "UPDATE mis_azad.www_ntt_training SET " + ", ".join(updates) +
                " WHERE id = %s",
                values,
            )
            if cur.rowcount == 0:
                raise HTTPException(404, "Training not found.")
            return {"ok": True}
        cur.execute(
            "UPDATE www_nt_trainings SET " + ", ".join(fields) +
            " WHERE id = %s AND deleted_at IS NULL", params)
        if cur.rowcount == 0:
            raise HTTPException(404, "Training not found.")
    return {"ok": True}


@router.delete("/{training_id}")
def delete_training(training_id: int):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_nt_trainings"):
            # 2026-08-19 (Ashish): pehle ye row ko HAMESHA ke liye mita deta tha.
            # Ab deleted_at bhar dete hain -- row DB me bachi rehti hai, bas har
            # list se hat jati hai. Wapas laani ho to deleted_at = NULL.
            cur.execute("UPDATE mis_azad.www_ntt_training SET deleted_at = NOW() "
                        "WHERE id = %s AND deleted_at IS NULL", (training_id,))
        else:
            cur.execute("UPDATE www_nt_trainings SET deleted_at = now() WHERE id = %s AND deleted_at IS NULL",
                        (training_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "Training not found.")
    return {"ok": True}


@router.get("/{training_id}/events")
def get_training_events(training_id: int):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_nt_trainings"):
            # Legacy path — events used to live on the training row itself,
            # but 2026-08-25's migration moved that data (plus everything
            # imported from the historical dump) into
            # mis_azad.www_institutional_events, keyed by enrollment_id.
            # Resolve this training's trainee, then pull every event
            # recorded for them from there.
            # 2026-10-09: www_ntt_training.enrollment_id was dropped and
            # www_institutional_events no longer carries enrollment_id either,
            # so there is no reliable trainee->events linkage from a single
            # training id anymore. Return an empty list so the training view
            # loads without 500ing; the Institutional Events screen is the
            # authoritative source now.
            cur.execute(
                "SELECT id FROM mis_azad.www_ntt_training WHERE id = %s",
                (training_id,),
            )
            if not cur.fetchone():
                raise HTTPException(404, "Training not found.")
            return {"data": [], "count": 0}
        cur.execute("SELECT 1 FROM www_nt_trainings WHERE id=%s AND deleted_at IS NULL", (training_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Training not found.")
        cur.execute(
            "SELECT id, assembly_date, family_faculty_date, individual_start_date, individual_end_date, created_at "
            "FROM www_nt_training_events WHERE training_id=%s ORDER BY created_at DESC, id DESC",
            (training_id,),
        )
        rows = cur.fetchall()
    return {"data": rows, "count": len(rows)}


@router.post("/{training_id}/events", status_code=201)
def create_training_event(training_id: int, body: NTEventCreate):
    if not any((body.assembly_date, body.family_faculty_date,
                body.individual_start_date, body.individual_end_date)):
        raise HTTPException(400, "At least one event date is required.")
    if (body.individual_start_date and body.individual_end_date and
            body.individual_end_date < body.individual_start_date):
        raise HTTPException(400, "Individual counselling end date cannot be before start date.")
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_nt_trainings"):
            # 2026-10-09: event-date columns (assembly_date,
            # family_faculty_meeting_date, individual_counselling_*) were
            # dropped from www_ntt_training. Institutional events live on
            # www_institutional_events now and are managed through the
            # Trainee Process screen, not from the training row.
            raise HTTPException(
                400,
                "Institutional events are no longer stored on the training "
                "row. Please add them via the Trainee Process (Institutional "
                "Events) screen.",
            )
        cur.execute("SELECT 1 FROM www_nt_trainings WHERE id=%s AND deleted_at IS NULL", (training_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Training not found.")
        cur.execute(
            "INSERT INTO www_nt_training_events "
            "(training_id, assembly_date, family_faculty_date, individual_start_date, individual_end_date) "
            "VALUES (%s,%s,%s,%s,%s) RETURNING id",
            (training_id, body.assembly_date, body.family_faculty_date,
             body.individual_start_date, body.individual_end_date),
        )
        event_id = cur.fetchone()["id"]
    return {"ok": True, "id": event_id}


@router.get("/{training_id}/attendance")
def get_attendance(training_id: int):
    """Return the merged roster (all trainees of the training's centre) + attendance status."""
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_nt_trainings"):
            # 2026-10-09: the id can be either a www_ntt_training id (older
            # training rows) OR a www_institutional_events id (new events
            # created via /event). Try the training table first; fall back
            # to the institutional-events table so the roster is scoped to
            # the event's own centre.
            # 2026-10-09: resolve via _resolve_tid so offset-encoded
            # event ids (>= _IE_ID_OFFSET) go to institutional_events and
            # bare training ids stay with www_ntt_training.
            _actual_id, _is_event = _resolve_tid(cur, training_id)
            if _actual_id is None:
                raise HTTPException(404, "Training not found.")
            training_id = _actual_id
            if _is_event:
                cur.execute(
                    "SELECT " + _legacy.centre_expr("centre") + " AS centre_clean "
                    "FROM mis_azad.www_institutional_events "
                    "WHERE id = %s AND deleted_at IS NULL",
                    (training_id,),
                )
            else:
                cur.execute(
                    "SELECT " + _legacy.centre_expr("centre") + " AS centre_clean "
                    "FROM mis_azad.www_ntt_training "
                    "WHERE id = %s AND deleted_at IS NULL",
                    (training_id,),
                )
            trow = cur.fetchone()
            if not trow:
                raise HTTPException(404, "Training not found.")
            # 2026-09-30: the training's `centre` column may hold either the
            # CODE (e.g. 'S19347B3' for South Kolkata) or the display NAME
            # (e.g. 'North Kolkata'). Resolve to central_centres so we can
            # match enrollments whose own `centre` column uses either form.
            _ccl = (trow["centre_clean"] or "").strip()
            _ccode = _cname = _ccl
            cur.execute(
                "SELECT centre_code, centre_name FROM mis_azad.central_centres "
                "WHERE centre_code = %s OR centre_name = %s LIMIT 1",
                (_ccl, _ccl),
            )
            _cr = cur.fetchone()
            if _cr:
                _ccode = _cr["centre_code"] or _ccl
                _cname = _cr["centre_name"] or _ccl
            # 2026-09-10: the roster is ALWAYS the full non-Draft, named enrollment
            # list of the training's CENTRE -- for both app-created sessions and the
            # legacy per-trainee import rows -- so every NT session shows all
            # trainees of its centre. Marks come from www_nt_attendance; batch /
            # centre / state are the enrollment's own values (the old import branch
            # leaked the centre into batch_name -- fixed here).
            cur.execute(
                "SELECT e.id AS trainee_id, e.enrollment_no, e.name, "
                "       NULLIF(TRIM(e.mobile), '') AS mobile, "
                "       " + _legacy.batch_name("e.batch", "e.id") + " AS batch_name, "
                "       NULLIF(TRIM(e.centre), '') AS centre_name, "
                "       NULLIF(TRIM(e.state), '') AS state_name, "
                "       LOWER(COALESCE(a.attendance, '')) AS attendance_status "
                "FROM mis_azad.www_enrollment e "
                # 2026-10-09: IE events read from www_event_attendance (keyed
                # by event_id); trainings keep reading from www_nt_attendance.
                + (
                    "LEFT JOIN mis_azad.www_event_attendance a "
                    "       ON a.enrollment_id = e.id AND a.event_id = %s AND a.deleted_at IS NULL "
                    if _is_event else
                    "LEFT JOIN mis_azad.www_nt_attendance a "
                    "       ON a.enrollment_id = e.id AND a.training_id = %s AND a.deleted_at IS NULL "
                ) +
                "WHERE NULLIF(TRIM(e.name), '') IS NOT NULL "
                "  AND COALESCE(NULLIF(TRIM(e.status), ''), 'Active') <> 'Draft' "
                "  AND " + _legacy.centre_expr("e.centre") + " IN (%s, %s) "
                "ORDER BY e.name",
                (training_id, _ccode, _cname),
            )
            rows = cur.fetchall()
            return {"data": rows, "count": len(rows)}
        cur.execute("SELECT centre_code FROM www_nt_trainings WHERE id=%s AND deleted_at IS NULL",
                    (training_id,))
        t = cur.fetchone()
        if not t:
            raise HTTPException(404, "Training not found.")
        cur.execute(
            "SELECT tr.id AS trainee_id, tr.enrollment_no, tr.name, tr.mobile, "
            "       COALESCE(b.name, NULL) AS batch_name, "
            "       LOWER(COALESCE(a.attendance, '')) AS attendance_status "
            "FROM www_enrollment tr "
            "LEFT JOIN www_master_batches b ON b.id = tr.batch_id "
            "LEFT JOIN www_nt_attendance a ON a.enrollment_id = tr.id AND a.training_id = %s AND a.deleted_at IS NULL "
            "WHERE tr.centre_code = %s "
            "ORDER BY tr.name",
            (training_id, t["centre_code"]),
        )
        rows = cur.fetchall()
    return {"data": rows, "count": len(rows)}


@router.put("/{training_id}/attendance")
def update_attendance(training_id: int, body: AttendanceBulkUpdate):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_nt_trainings"):
            # 2026-10-08: all alive trainings are event-level now
            # (enrollment_id column dropped from www_ntt_training).
            # Each mark goes into www_nt_attendance via enrollment_id
            # + attendance (Present/Absent). The "import single-
            # trainee row" branch that used to update the training
            # row's status/attendance_count directly is gone -- there
            # are no such rows anymore.
            # 2026-10-09: resolve the id so an offset-encoded event id
            # (>= _IE_ID_OFFSET) deterministically routes to the IE table,
            # avoiding the id-collision case where the same bare id was
            # alive in both tables.
            _actual_id, _is_event = _resolve_tid(cur, training_id)
            if _actual_id is None:
                raise HTTPException(404, "Training not found.")
            training_id = _actual_id
            _is_training = not _is_event
            p = a = 0
            for it in body.items:
                if it.trainee_id is None:
                    continue
                raw = (it.status or "").strip().lower()
                if raw == "present":
                    norm, p = "Present", p + 1
                elif raw == "absent":
                    norm, a = "Absent",  a + 1
                else:
                    norm = it.status
                # 2026-10-09: IE events write to www_event_attendance; a
                # BEFORE trigger on that table recomputes the parent event's
                # 'P: X, A: Y' summary string on www_institutional_events.
                if _is_training:
                    cur.execute(
                        "INSERT INTO mis_azad.www_nt_attendance "
                        "    (training_id, enrollment_id, attendance, updated_at) "
                        "VALUES (%s, %s, %s, now()) "
                        "ON CONFLICT (training_id, enrollment_id) WHERE deleted_at IS NULL "
                        "DO UPDATE SET attendance = EXCLUDED.attendance, updated_at = now()",
                        (training_id, it.trainee_id, norm),
                    )
                else:
                    # 2026-10-09 (user ask): www_event_attendance stores only
                    # rows where attendance was explicitly marked Present or
                    # Absent. If the trainee is unmarked here (anything else),
                    # soft-delete any existing row for that (event, trainee).
                    if norm in ("Present", "Absent"):
                        cur.execute(
                            "INSERT INTO mis_azad.www_event_attendance "
                            "    (event_id, enrollment_id, attendance, updated_at) "
                            "VALUES (%s, %s, %s, now()) "
                            "ON CONFLICT (event_id, enrollment_id) WHERE deleted_at IS NULL "
                            "DO UPDATE SET attendance = EXCLUDED.attendance, updated_at = now()",
                            (training_id, it.trainee_id, norm),
                        )
                    else:
                        # 2026-10-09 (user ask v2): un-marked trainees are
                        # removed from the table entirely (hard DELETE), not
                        # soft-deleted. The recount trigger fires AFTER
                        # DELETE and refreshes the parent IE summary.
                        cur.execute(
                            "DELETE FROM mis_azad.www_event_attendance "
                            " WHERE event_id = %s AND enrollment_id = %s",
                            (training_id, it.trainee_id),
                        )
            if _is_training:
                # Only trainings carry the pre-rendered attendance_count
                # summary string; institutional events don't need it (the
                # Trainee Process view computes counts live).
                cur.execute(
                    "UPDATE mis_azad.www_ntt_training SET attendance_count = %s "
                    "WHERE id = %s",
                    ("P:%d / A:%d / Marked:%d" % (p, a, p + a), training_id),
                )
            return {"ok": True, "updated": len(body.items)}
        cur.execute("SELECT 1 FROM www_nt_trainings WHERE id=%s AND deleted_at IS NULL", (training_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Training not found.")
        for it in body.items:
            cur.execute(
                "INSERT INTO www_nt_attendance (training_id, enrollment_id, attendance, updated_at) "
                "VALUES (%s, %s, %s, now()) "
                "ON CONFLICT (training_id, enrollment_id) WHERE deleted_at IS NULL "
                "DO UPDATE SET attendance=EXCLUDED.attendance, updated_at=now()",
                (training_id, it.trainee_id, (it.status or "").capitalize()),
            )
    return {"ok": True, "updated": len(body.items)}


# =============================================================================
# EXPORT (Excel) — 2026-08-08
# Two endpoints:
#   1. /api/www-nt-trainings/export/excel         — training-centric list
#   2. /api/www-nt-trainings/attendance/export/excel — trainee attendance
# Reuses list filters. Legacy fallback via _legacy_list_cte for endpoint #1.
# =============================================================================
@router.get("/export/excel")
def export_nt_trainings_excel(
    request: Request,
    state_code: Optional[str] = None,
    quarter: Optional[str] = None,
    training_type: Optional[str] = None,
    centre_code: Optional[str] = None,
    facilitator_name: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """Per-list-entry NT trainings export (2026-09-18).

    Matches the on-screen list row-for-row. Columns:
      S. No. | Training Type | Enrollment No. | Name | Mobile | Batch | Centre | State | Present | Absent
    Legacy branch: n.status = 'Conducted' -> X in Present, otherwise X in Absent.
    Normalized branch: joins the training's own centre roster and uses the
    app-marked status (present / absent). Filters and geo scope unchanged.
    """
    from datetime import date as _d
    from export_helper import multi_sheet_xlsx_response_v2

    with get_cursor() as cur:
        has_table = _legacy.table_exists(cur, "www_nt_trainings")
        _cc = _scope.scoped_centre_codes(request)

        data_rows = []
        if not has_table:
            conds = ["1=1"]; params = []
            if _cc is not None:  conds.append("l.centre_code = ANY(%s)");                   params.append(_cc)
            if quarter:          conds.append("l.quarter = %s");                            params.append(quarter)
            if training_type:    conds.append("l.training_type = %s");                      params.append(training_type)
            if centre_code:      conds.append("l.centre_code = %s");                        params.append(centre_code)
            if facilitator_name: conds.append(_legacy.name_match("l.facilitator_name"));    params.append(_legacy.name_pattern(facilitator_name))
            if status:           conds.append("l.status = %s");                             params.append(status)
            if date_from:        conds.append("l.start_date >= %s");                        params.append(date_from)
            if date_to:          conds.append(_LEGACY_END_DATE_FILTER);                     params.append(date_to)
            if state_code:       conds.append("l.state_code = %s");                         params.append(state_code)
            where = "WHERE " + " AND ".join(conds)
            cte = _legacy_list_cte()
            # 2026-10-05: pull every training-level field the list UI
            # exposes so the Excel export carries Quarter, Start Date,
            # End Date, Centre, State, Facilitator and Status, not just
            # Training Type.
            # 2026-10-08 (user ask): training-event rows (legacy l rows
            # whose enrollment_id IS NULL) carry no trainee linkage on
            # www_ntt_training itself; the attendees live on
            # www_nt_attendance (keyed by training_id -> trainee_id ->
            # www_enrollment.id). LEFT JOIN that here so each attendee
            # of a training-event row becomes its own Excel row with
            # Enrollment No./Name/Mobile/Batch filled, and the
            # attendance's own status drives Present/Absent. For
            # trainee-level rows (enrollment_id SET) the attendance
            # JOIN is gated off, so they still emit one row each
            # (unchanged). Mobile is pulled from the trainee's
            # www_enrollment row (te_main for trainee-level rows,
            # te_att for the attendance-expanded rows), filling the
            # Mobile column that used to always be blank in the
            # legacy branch.
            cur.execute(cte +
                        " SELECT l.id AS training_id, l.training_type, l.quarter, "
                        "        l.start_date, l.end_date, "
                        "        l.facilitator_name, l.status AS training_status, "
                        "        COALESCE(l.enrollment_no, te_att.enrollment_no) AS enrollment_no, "
                        "        COALESCE(l.trainee_name,  te_att.name)          AS trainee_name, "
                        "        COALESCE(te_main.mobile,  te_att.mobile)        AS trainee_mobile, "
                        "        COALESCE(l.batch_name,    NULLIF(TRIM(te_att.batch), ''))        AS batch_name, "
                        "        l.centre_name, l.state_name, l.status, "
                        "        LOWER(COALESCE(att.attendance, '')) AS attendee_status, "
                        # 2026-10-09 (user ask): per-training totals used by the
                        # new "Attendance Count" column. Fresh counts from
                        # www_nt_attendance so the number isn't stale text.
                        "        (SELECT COUNT(*) FROM mis_azad.www_nt_attendance a2 "
                        "          WHERE a2.training_id = l.id "
                        "            AND a2.attendance = 'Present' "
                        "            AND a2.deleted_at IS NULL) AS tr_present_cnt, "
                        "        (SELECT COUNT(*) FROM mis_azad.www_nt_attendance a2 "
                        "          WHERE a2.training_id = l.id "
                        "            AND a2.attendance = 'Absent' "
                        "            AND a2.deleted_at IS NULL) AS tr_absent_cnt, "
                        "        l.attendance_target                     AS tr_target "
                        "   FROM legacy l "
                        "   LEFT JOIN mis_azad.www_enrollment te_main "
                        "          ON te_main.id = l.enrollment_id "
                        "   LEFT JOIN mis_azad.www_nt_attendance att "
                        "          ON att.training_id = l.id "
                        "         AND att.deleted_at IS NULL "
                        "   LEFT JOIN mis_azad.www_enrollment te_att "
                        "          ON te_att.id = att.enrollment_id "
                        " " + where +
                        " ORDER BY l.start_date DESC NULLS LAST, l.id DESC",
                        params)
            def _fmt_date(v):
                try:
                    return v.isoformat() if v and hasattr(v, 'isoformat') else (v or "")
                except Exception:
                    return ""

            # 2026-10-10 FIX: materialize the main query's results into a
            # Python list IMMEDIATELY, so the subsequent _bak_ preload
            # (which issues its own cur.execute) does not overwrite the
            # cursor and lose the main training rows. (Previous version
            # left the main results in the cursor until after the preload,
            # which produced a blank Excel sheet.)
            _main_rows = cur.fetchall()

            # 2026-10-10 (user ask #2): pre-load historical roster
            # from the pre-migration backup table so old trainings (with
            # no marked attendance after the Oct-10 NULL cleanup) can
            # still emit per-trainee rows with Name/Enrollment filled.
            _bak_roster_by_tid = {}
            try:
                cur.execute("""
                    SELECT bak.enrollment_id,
                           bak.name AS orig_name,
                           e.enrollment_no, e.name AS enroll_name,
                           NULLIF(TRIM(e.mobile), '') AS mobile, e.batch,
                           MIN(bak.id) OVER (PARTITION BY
                               COALESCE(bak.state,''), COALESCE(bak.centre,''),
                               COALESCE(bak.training_type,''),
                               bak.start_date, COALESCE(bak.end_date,''),
                               COALESCE(bak.facilitator_name,''),
                               COALESCE(bak.quarter,''), COALESCE(bak.status,''),
                               COALESCE(bak.batch_id,-1)
                           ) AS kept_id
                      FROM mis_azad._bak_www_ntt_training_20261010_100430 bak
                      LEFT JOIN mis_azad.www_enrollment e ON e.id = bak.enrollment_id
                     WHERE bak.deleted_at IS NULL
                       AND bak.enrollment_id IS NOT NULL
                """)
                for _br in cur.fetchall():
                    _kept = _br.get("kept_id")
                    if _kept is None:
                        continue
                    _bak_roster_by_tid.setdefault(_kept, []).append(_br)
            except Exception:
                # _bak_ table may not exist on stage or future environments;
                # fall through so the export still works (header-only rows).
                _bak_roster_by_tid = {}

            # 2026-10-10 (user ask): group the main-query output by training_id,
            # then
            #   * trainings with >=1 Present/Absent -> expand per attendee
            #   * trainings with 0 marked attendees -> hydrate roster from
            #     _bak_, or emit a header-only row if backup has nothing.
            from collections import OrderedDict
            _by_tid = OrderedDict()
            for r in _main_rows:
                tid = r.get("training_id")
                if tid not in _by_tid:
                    _by_tid[tid] = []
                _by_tid[tid].append(r)

            for tid, rows in _by_tid.items():
                marked = [rr for rr in rows
                          if (rr.get("attendee_status") or "").strip().lower() in ("present","absent")]
                any_r = rows[0]
                _roster = _bak_roster_by_tid.get(tid, [])
                _tgt_raw = any_r.get("tr_target")
                _tgt_num = int(_tgt_raw) if (_tgt_raw is not None and str(_tgt_raw).strip() != "") else None

                # 2026-10-10 (user ask): if a training has no live attendance
                # rows but the pre-migration backup has an enrolled roster,
                # treat each roster entry as Present (historical semantics:
                # per-trainee rows that existed = trainees who attended).
                if marked:
                    _p = int(any_r.get("tr_present_cnt") or 0)
                    _a = int(any_r.get("tr_absent_cnt") or 0)
                    _t = _tgt_num if _tgt_num is not None else (_p + _a)
                elif _roster:
                    _p = len(_roster)
                    _a = 0
                    _t = _tgt_num if _tgt_num is not None else _p
                else:
                    _p = 0
                    _a = 0
                    _t = _tgt_num if _tgt_num is not None else 0
                _att_str = "P: %d, Absent: %d, Target: %d" % (_p, _a, _t)

                if marked:
                    for r in marked:
                        att_st = (r.get("attendee_status") or "").strip().lower()
                        data_rows.append([
                            len(data_rows) + 1,
                            r.get("training_type") or "",
                            r.get("quarter") or "",
                            _fmt_date(r.get("start_date")),
                            _fmt_date(r.get("end_date")),
                            r.get("centre_name") or "",
                            r.get("state_name") or "",
                            r.get("facilitator_name") or "",
                            r.get("training_status") or "",
                            r.get("enrollment_no") or "",
                            r.get("trainee_name") or "",
                            r.get("trainee_mobile") or "",
                            r.get("batch_name") or "",
                            r.get("centre_name") or "",
                            r.get("state_name") or "",
                            "Present" if att_st == "present" else "Absent",
                            _att_str,
                        ])
                else:
                    # 2026-10-10 (user ask): hydrate trainee roster from the
                    # pre-migration backup _bak_www_ntt_training_20261010_100430
                    # for old trainings that have no marked attendance (otherwise
                    # Name/Enrollment show blank in Excel). Backup table has
                    # every original per-trainee row with its enrollment_id.
                    # 2026-10-10 (user ask): _roster was already computed
                    # above when deciding counts; use the same list here.
                    if _roster:
                        for br in _roster:
                            data_rows.append([
                                len(data_rows) + 1,
                                any_r.get("training_type") or "",
                                any_r.get("quarter") or "",
                                _fmt_date(any_r.get("start_date")),
                                _fmt_date(any_r.get("end_date")),
                                any_r.get("centre_name") or "",
                                any_r.get("state_name") or "",
                                any_r.get("facilitator_name") or "",
                                any_r.get("training_status") or "",
                                br.get("enrollment_no") or "",
                                br.get("enroll_name") or br.get("orig_name") or "",
                                br.get("mobile") or "",
                                br.get("batch") or "",
                                any_r.get("centre_name") or "",
                                any_r.get("state_name") or "",
                                "Present",          # Status: historical rows = Present
                                _att_str,
                            ])
                    else:
                        # Fallback: no backup roster either -> emit header-only.
                        data_rows.append([
                            len(data_rows) + 1,
                            any_r.get("training_type") or "",
                            any_r.get("quarter") or "",
                            _fmt_date(any_r.get("start_date")),
                            _fmt_date(any_r.get("end_date")),
                            any_r.get("centre_name") or "",
                            any_r.get("state_name") or "",
                            any_r.get("facilitator_name") or "",
                            any_r.get("training_status") or "",
                            "", "", "", "",
                            any_r.get("centre_name") or "",
                            any_r.get("state_name") or "",
                            "",
                            _att_str,
                        ])
        else:
            conds = ["t.deleted_at IS NULL"]; params = []
            if _cc is not None:  conds.append("t.centre_code = ANY(%s)");                   params.append(_cc)
            if quarter:          conds.append("t.quarter = %s");                            params.append(quarter)
            if training_type:    conds.append("t.training_type = %s");                      params.append(training_type)
            if centre_code:      conds.append("t.centre_code = %s");                        params.append(centre_code)
            if facilitator_name: conds.append(_legacy.name_match("t.facilitator_name"));    params.append(_legacy.name_pattern(facilitator_name))
            if status:           conds.append("t.status = %s");                             params.append(status)
            if date_from:        conds.append("t.start_date >= %s");                        params.append(date_from)
            if date_to:          conds.append("t.end_date <= %s");                          params.append(date_to)
            where = "WHERE " + " AND ".join(conds)
            # 2026-10-05: fetch every training-level field the list UI
            # exposes so the Excel export carries Quarter / Start / End
            # Date / Centre / State / Facilitator / Status alongside
            # Training Type. Resolve training.centre_code to the display
            # name via www_centres / www_states so the export reads the
            # same as the list.
            cur.execute(
                "SELECT t.id AS training_id, t.training_type, t.quarter, "
                "       t.start_date, t.end_date, t.facilitator_name, "
                "       t.status AS training_status, t.centre_code, "
                "       tc.centre_name AS training_centre, "
                "       ts.state_name  AS training_state "
                "FROM www_nt_trainings t "
                "LEFT JOIN central_centres tc ON tc.centre_code = t.centre_code "
                "LEFT JOIN central_states  ts ON ts.state_code  = t.state_code "
                + where +
                " ORDER BY t.start_date DESC NULLS LAST, t.id DESC",
                params,
            )
            trainings = cur.fetchall()
            def _fmt_date_n(v):
                try:
                    return v.isoformat() if v and hasattr(v, 'isoformat') else (v or "")
                except Exception:
                    return ""
            for tr in trainings:
                cur.execute(
                    "SELECT tr.enrollment_no, tr.name AS trainee_name, tr.mobile, "
                    "       b.name AS batch_name, c.centre_name, s.state_name, "
                    "       LOWER(COALESCE(a.attendance, \'\')) AS attendance_status "
                    "FROM www_enrollment tr "
                    "LEFT JOIN www_master_batches b ON b.id = tr.batch_id "
                    "LEFT JOIN central_centres c ON c.centre_code = tr.centre_code "
                    "LEFT JOIN central_states  s ON s.state_code  = tr.state_code "
                    "LEFT JOIN www_nt_attendance a ON a.enrollment_id = tr.id AND a.training_id = %s "
                    "WHERE tr.centre_code = %s "
                    "ORDER BY tr.name",
                    (tr["training_id"], tr["centre_code"]),
                )
                for r in cur.fetchall():
                    st = (r.get("attendance_status") or "").strip().lower()
                    if st != "present":
                        continue
                    data_rows.append([
                        len(data_rows) + 1,
                        tr.get("training_type") or "",
                        tr.get("quarter") or "",
                        _fmt_date_n(tr.get("start_date")),
                        _fmt_date_n(tr.get("end_date")),
                        tr.get("training_centre") or "",
                        tr.get("training_state") or "",
                        tr.get("facilitator_name") or "",
                        tr.get("training_status") or "",
                        r.get("enrollment_no") or "",
                        r.get("trainee_name") or "",
                        r.get("mobile") or "",
                        r.get("batch_name") or "",
                        r.get("centre_name") or "",
                        r.get("state_name") or "",
                        "Present" if st == "present" else "Absent",
                        "",
                    ])

    # 2026-10-05: Training section expanded with Quarter / Start Date /
    # End Date / Centre / State / Facilitator / Status so the Excel
    # export carries every training-level detail from the list UI.
    training_headers = ["Training Type", "Quarter", "Start Date", "End Date",
                        "Centre", "State", "Facilitator", "Status"]
    trainee_headers  = ["Enrollment No.", "Name", "Mobile", "Batch", "Centre", "State", "Status"]
    # 2026-10-09 (user ask): single Attendance Count col replacing
    # Present + Absent, formatted "P: 2, Absent: 3, Target: 5".
    attend_headers   = ["Attendance Count"]
    all_headers = ["S. No."] + training_headers + trainee_headers + attend_headers
    n_tr, n_te, n_at = len(training_headers), len(trainee_headers), len(attend_headers)
    group_headers = [
        (2,               1 + n_tr,                     "Training"),
        (2 + n_tr,        1 + n_tr + n_te,              "Trainee Details"),
        (2 + n_tr + n_te, 1 + n_tr + n_te + n_at,       "Attendance"),
    ]
    sheets = [{
        "name": "NT Trainings",
        "group_headers": group_headers,
        "headers": all_headers,
        "rows": data_rows,
    }]
    return multi_sheet_xlsx_response_v2(
        sheets,
        f"WWW_NT_Trainings_{_d.today().isoformat()}.xlsx",
    )


# 2026-10-09: Trainee Process (institutional events) export. Mirrors the
# Training List export: 2 header bands + Attendance Count column. One
# row per attendee marked Present or Absent on www_event_attendance.
@router.get("/events/export/excel")
def export_nt_events_excel(
    request: Request,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    type_of_event: Optional[str] = None,
):
    from datetime import date as _d
    from export_helper import multi_sheet_xlsx_response_v2

    conds = ["ie.deleted_at IS NULL"]
    params: List = []
    if centre_code:
        conds.append(
            "COALESCE("
            "  (SELECT centre_code FROM mis_azad.central_centres "
            "    WHERE centre_code = ie.centre OR centre_name = ie.centre LIMIT 1),"
            "  ie.centre) = "
            "COALESCE("
            "  (SELECT centre_code FROM mis_azad.central_centres "
            "    WHERE centre_code = %s OR centre_name = %s LIMIT 1),"
            "  %s)"
        )
        params.extend([centre_code, centre_code, centre_code])
    if type_of_event:
        conds.append("ie.type_of_event = %s"); params.append(type_of_event)
    where = "WHERE " + " AND ".join(conds)

    data_rows = []
    with get_cursor() as cur:
        cur.execute(
            "SELECT ie.id, ie.centre, ie.type_of_event, "
            "       ie.assembly_date, ie.family_faculty_meeting_date, "
            "       ie.individual_counselling_start, ie.individual_counselling_end, "
            "       ie.attendance AS summary, "
            "       COALESCE(nc.centre_name, ie.centre) AS centre_name, "
            "       ns.state_name "
            "  FROM mis_azad.www_institutional_events ie "
            "  LEFT JOIN mis_azad.central_centres nc ON nc.centre_code = ie.centre "
            "                                       OR nc.centre_name = ie.centre "
            "  LEFT JOIN mis_azad.central_states ns ON ns.state_code = nc.state_code "
            + where +
            " ORDER BY ie.created_at DESC NULLS LAST, ie.id DESC",
            params,
        )
        events = cur.fetchall()

        def _fmt(d):
            # 2026-10-10 (user ask): return DD/MM/YYYY like the UI list so
            # Excel can't auto-interpret the cell as a date (which was
            # hiding the "to end" half of IC ranges when the column
            # happened to be narrow).
            try:
                if d is None or d == "":
                    return ""
                if hasattr(d, "strftime"):
                    return d.strftime("%d/%m/%Y")
                s = str(d)
                # already a text date? If it's ISO (YYYY-MM-DD), reformat; else leave.
                if len(s) >= 10 and s[4] == "-" and s[7] == "-":
                    return s[8:10] + "/" + s[5:7] + "/" + s[0:4]
                return s
            except Exception:
                return ""

        for ev in events:
            cur.execute(
                "SELECT ea.enrollment_id, ea.attendance, "
                "       e.enrollment_no, e.name AS trainee_name, e.mobile, "
                "       NULLIF(TRIM(e.batch), '') AS batch_name, "
                "       NULLIF(TRIM(e.centre), '') AS trainee_centre, "
                "       NULLIF(TRIM(e.state), '') AS trainee_state "
                "  FROM mis_azad.www_event_attendance ea "
                "  JOIN mis_azad.www_enrollment e ON e.id = ea.enrollment_id "
                " WHERE ea.event_id = %s "
                "   AND ea.deleted_at IS NULL "
                "   AND LOWER(TRIM(COALESCE(ea.attendance,''))) IN ('present','absent') "
                " ORDER BY e.name",
                (ev["id"],),
            )
            for r in cur.fetchall():
                st = (r.get("attendance") or "").strip().lower()
                data_rows.append([
                    len(data_rows) + 1,
                    ev.get("type_of_event") or "",
                    ev.get("centre_name") or "",
                    ev.get("state_name") or "",
                    # 2026-10-10 (user ask): single "Event Date" column.
                    # Assembly / FFM -> their single date; Individual
                    # Counselling -> "start to end" range (or whichever
                    # one is set).
                    # 2026-10-10 v2 (user ask): always show IC as a "start to end"
                    # range, even if only one of the two dates is populated.
                    (
                        _fmt(ev.get("assembly_date")) if (ev.get("type_of_event") or "") == "Assembly"
                        else _fmt(ev.get("family_faculty_meeting_date")) if (ev.get("type_of_event") or "") == "Family Faculty Meeting"
                        else (
                            (
                                (_fmt(ev.get("individual_counselling_start")) or _fmt(ev.get("individual_counselling_end")))
                                + " to "
                                + (_fmt(ev.get("individual_counselling_end")) or _fmt(ev.get("individual_counselling_start")))
                            )
                            if (ev.get("individual_counselling_start") or ev.get("individual_counselling_end"))
                            else ""
                        ) if (ev.get("type_of_event") or "") == "Individual Counselling"
                        else ""
                    ),
                    r.get("enrollment_no") or "",
                    r.get("trainee_name") or "",
                    r.get("mobile") or "",
                    r.get("batch_name") or "",
                    r.get("trainee_centre") or "",
                    r.get("trainee_state") or "",
                    "Present" if st == "present" else "Absent",
                    ev.get("summary") or "",
                ])

    # 2026-10-10 (user ask): single Event Date column replaces the
    # four separate date columns.
    event_headers   = ["Type of Event", "Centre", "State", "Event Date"]
    trainee_headers = ["Enrollment No.", "Name", "Mobile", "Batch", "Centre", "State", "Status"]
    attend_headers  = ["Attendance Count"]
    all_headers = ["S. No."] + event_headers + trainee_headers + attend_headers
    n_ev, n_te, n_at = len(event_headers), len(trainee_headers), len(attend_headers)
    group_headers = [
        (2,                1 + n_ev,                 "Event"),
        (2 + n_ev,         1 + n_ev + n_te,          "Trainee Details"),
        (2 + n_ev + n_te,  1 + n_ev + n_te + n_at,   "Attendance"),
    ]
    sheets = [{
        "name": "Trainee Process",
        "group_headers": group_headers,
        "headers": all_headers,
        "rows": data_rows,
    }]
    return multi_sheet_xlsx_response_v2(
        sheets,
        f"WWW_Trainee_Process_{_d.today().isoformat()}.xlsx",
    )


@router.get("/attendance/export/excel")
def export_nt_attendance_excel(
    request: Request,
    training_id: Optional[int] = None,
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
        # 2026-08-17: gate www_nt_attendance par tha; wo storage-table ab is
        # deployment par ban gaya hai, par www_nt_trainings / www_trainees
        # aaj bhi nahi hain -- us branch me jate hi export 500 deta. Asli
        # normalized marker wahi hai jo baaki sab jagah hai.
        has_table = _legacy.table_exists(cur, "www_nt_trainings")

        rows = []
        if not has_table:
            # 2026-09-17 -- roster-scoped legacy export (2026-09-17): the on-screen
            # Attendance page builds its roster from www_enrollment at the training's
            # centre; the export must match. Reading www_ntt_training filtered by n.id
            # (as before) returned a single imported-mark row per training, so the file
            # showed 1 trainee for a 300+ centre roster.
            if training_id is None:
                rows = []
            else:
                cur.execute(
                    "SELECT " + _legacy.centre_expr("centre") + " AS centre_clean, "
                    "       quarter, training_type, facilitator_name, start_date, end_date, "
                    "       status AS training_status, attendance AS attendance_target, attendance_count "
                    "FROM mis_azad.www_ntt_training WHERE id = %s",
                    (training_id,),
                )
                trow = cur.fetchone()
                if not trow:
                    rows = []
                else:
                    cur.execute(
                        "SELECT %s AS training_id, e.id AS trainee_id, "
                        "       LOWER(COALESCE(a.attendance, '')) AS attendance_status, "
                        "       a.updated_at, NULL::integer AS created_by, NULL::integer AS updated_by, "
                        "       %s AS quarter, %s AS training_type, %s AS facilitator_name, "
                        "       %s AS start_date, %s AS end_date, "
                        "       %s AS training_status, %s AS attendance_target, %s AS attendance_count, "
                        "       e.enrollment_date AS date_of_joining, NULL::text AS ll_number, "
                        "       e.enrollment_no, e.name, NULLIF(TRIM(e.mobile), '') AS mobile, "
                        "       e.type_of_enrollment AS enrollment_type, "
                        "       NULL::text AS state_code, NULL::text AS district_code, "
                        "       NULL::text AS centre_code, "
                        "       e.state AS state_name, e.district AS district_name, "
                        "       " + _legacy.centre_expr("e.centre") + " AS centre_name, "
                        "       NULL::text AS area_name, "
                        "       " + _legacy.batch_name("e.batch", "e.id") + " AS batch_name "
                        "FROM mis_azad.www_enrollment e "
                        "LEFT JOIN mis_azad.www_nt_attendance a "
                        "       ON a.enrollment_id = e.id AND a.training_id = %s AND a.deleted_at IS NULL "
                        "WHERE NULLIF(TRIM(e.name), '') IS NOT NULL "
                        "  AND COALESCE(NULLIF(TRIM(e.status), ''), 'Active') <> 'Draft' "
                        "  AND " + _legacy.centre_expr("e.centre") + " = %s "
                        "ORDER BY e.name",
                        (training_id, trow['quarter'], trow['training_type'], trow['facilitator_name'],
                         trow['start_date'], trow['end_date'], trow['training_status'],
                         trow['attendance_target'], trow['attendance_count'],
                         training_id, trow['centre_clean']),
                    )
                    rows = cur.fetchall()
        if has_table:
            conds = ["1=1"]; params = []
            if training_id:     conds.append("a.training_id = %s");        params.append(training_id)
            if state_code:      conds.append("tr.state_code = %s");        params.append(state_code)
            if centre_code:     conds.append("tr.centre_code = %s");       params.append(centre_code)
            if batch_id:        conds.append("tr.batch_id = %s");          params.append(batch_id)
            if enrollment_type: conds.append("tr.enrollment_type = %s");   params.append(enrollment_type)
            if name:            conds.append(_legacy.name_match("tr.name"));          params.append(_legacy.name_pattern(name))
            if date_from:       conds.append("t.start_date >= %s");        params.append(date_from)
            if date_to:         conds.append("t.end_date <= %s");          params.append(date_to)
            where = "WHERE " + " AND ".join(conds)
            cur.execute(
                "SELECT a.id AS id, a.training_id, a.enrollment_id AS trainee_id, LOWER(COALESCE(a.attendance,'')) AS attendance_status, a.updated_at, "
                "       t.quarter, t.training_type, t.facilitator_name, "
                "       t.start_date, t.end_date, "
                "       tr.enrollment_no, tr.name, tr.mobile, tr.enrollment_type, "
                "       tr.state_code, tr.district_code, tr.centre_code, tr.area_code, "
                "       s.state_name, d.district_name, c.centre_name, ar.area_name, "
                "       b.name AS batch_name "
                "FROM www_nt_attendance a "
                "JOIN www_nt_trainings t ON t.id = a.training_id AND t.deleted_at IS NULL "
                "JOIN www_enrollment tr ON tr.id = a.enrollment_id "
                "LEFT JOIN central_states    s  ON s.state_code    = tr.state_code "
                "LEFT JOIN central_districts d  ON d.district_code = tr.district_code "
                "LEFT JOIN central_centres   c  ON c.centre_code   = tr.centre_code "
                "LEFT JOIN www_areas     ar ON ar.area_code    = tr.area_code "
                "LEFT JOIN www_master_batches b ON b.id = tr.batch_id " +
                where + " ORDER BY a.updated_at DESC NULLS LAST",
                params,
            )
            rows = cur.fetchall()

    def _g(r, k):
        v = r.get(k)
        return "" if v is None else v

    trainee_headers = [
        "Enrollment No.", "Name", "Mobile", "Enrollment Type",
        "State", "District", "Centre", "Area", "Batch",
        "Date of Joining", "LL Number",
    ]
    nt_headers = [
        "Training Quarter", "Training Type", "Facilitator",
        "Start Date", "End Date", "Training Status",
        "Attendance Target", "Attendance Count", "Attendance Status",
    ]
    system_headers = ["Updated At"]
    all_headers = trainee_headers + nt_headers + system_headers
    n_t, n_n, n_s = len(trainee_headers), len(nt_headers), len(system_headers)
    group_headers = [
        (1, n_t, "Trainee Details"),
        (n_t + 1, n_t + n_n, "NT Attendance"),
        (n_t + n_n + 1, n_t + n_n + n_s, "System"),
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
            _g(r, "date_of_joining"), _g(r, "ll_number"),
            _g(r, "quarter"), _g(r, "training_type"), _g(r, "facilitator_name"),
            _g(r, "start_date"), _g(r, "end_date"),
            _g(r, "training_status"), _g(r, "attendance_target"),
            _g(r, "attendance_count"),
            _g(r, "attendance_status"),
            _g(r, "updated_at"),
        ])

    # 2026-08-26: WWW tracking columns (Created By / Updated By / Updated At)
    from routes._www_export_tracking import WWW_TRACK_HEADERS as _WT_H, www_tracking_cells_inline as _wt_inline
    all_headers = list(all_headers) + _WT_H
    # 2026-09-19: Record Info banner over Created By + Updated By.
    group_headers = list(group_headers) + [(len(all_headers) - len(_WT_H) + 1, len(all_headers), "Record Info")]
    _wt_rows = _wt_inline(rows)
    for _wi in range(len(data_rows)):
        data_rows[_wi] = list(data_rows[_wi]) + (_wt_rows[_wi] if _wi < len(_wt_rows) else ["", ""])
    sheets = [{
        "name": "NT Attendance",
        "group_headers": group_headers,
        "headers": all_headers,
        "rows": data_rows,
    }]
    return multi_sheet_xlsx_response_v2(
        sheets,
        f"WWW_NT_Attendance_{_d.today().isoformat()}.xlsx",
    )



# 2026-08-18: Add Event flow — single-shot insert of a Centre + Batch +
# Training Type + 4 event dates row (enrollment_id NULL). Frontend hits
# this from the new #page-wwwAddNTEvent screen wired next to ADD Training.
class NTEventCreate(BaseModel):
    centre: Optional[str] = None
    batch_id: Optional[int] = None
    # 2026-08-19: trainee FK (matches existing
    # www_ntt_training.enrollment_id -> www_enrollment.id).
    enrollment_id: Optional[int] = None
    training_type: Optional[str] = None
    assembly_date: Optional[date] = None
    family_faculty_meeting_date: Optional[date] = None
    individual_counselling_start: Optional[date] = None
    individual_counselling_end: Optional[date] = None


@router.post("/event")
def create_nt_event(body: NTEventCreate):
    # 2026-10-09: Add Event now writes to www_institutional_events
    # (new schema). The per-event columns -- assembly_date, family_
    # faculty_meeting_date, individual_counselling_start/_end -- were
    # dropped from www_ntt_training and moved to this table. The
    # Trainee Process list surfaces these rows via
    # _institutional_events_as_legacy_rows(), so they still appear in
    # the merged event list.
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO mis_azad.www_institutional_events
                (centre, type_of_event,
                 assembly_date, family_faculty_meeting_date,
                 individual_counselling_start, individual_counselling_end,
                 created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id""",
            (body.centre, body.training_type,
             body.assembly_date, body.family_faculty_meeting_date,
             body.individual_counselling_start, body.individual_counselling_end),
        )
        r = cur.fetchone()
    new_id = r.get("id") if hasattr(r, "get") else r[0]
    return {"id": new_id, "ok": True}


# 2026-08-19: Edit for an Event row — mirrors POST /event.
@router.put("/event/{training_id}")
def update_nt_event(training_id: int, body: NTEventCreate):
    # 2026-10-09: id can be offset-encoded (>= _IE_ID_OFFSET). Strip
    # it so the UPDATE hits the real IE row.
    with get_cursor() as cur:
        if training_id >= _IE_ID_OFFSET:
            training_id = training_id - _IE_ID_OFFSET
        cur.execute(
            """UPDATE mis_azad.www_institutional_events
                  SET centre        = %s,
                      type_of_event = %s,
                      assembly_date = %s,
                      family_faculty_meeting_date  = %s,
                      individual_counselling_start = %s,
                      individual_counselling_end   = %s,
                      updated_at    = NOW()
                WHERE id = %s AND deleted_at IS NULL
                RETURNING id""",
            (body.centre, body.training_type,
             body.assembly_date, body.family_faculty_meeting_date,
             body.individual_counselling_start, body.individual_counselling_end,
             training_id),
        )
        r = cur.fetchone()
    if not r:
        raise HTTPException(404, "Event not found.")
    return {"id": training_id, "ok": True}
