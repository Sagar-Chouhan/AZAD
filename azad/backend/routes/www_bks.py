"""WWW BKS (Badlaav Ka Safarnama).

Note the name collision: this deployment has a www_bks table, but it is
the spreadsheet import rather than the normalized one, so the routes
switch on the presence of the trainee_id FK.  The import's indicator
columns are the spreadsheet headings truncated to Postgres' 63-byte
identifier limit, which is why _LEGACY_INDICATOR_COLUMNS spells them
out rather than deriving them.

sql/072 renamed the import's text `enrollment_id` column to
`enrollment_no` (the name eight of the other WWW imports already used)
so that `enrollment_id` could become the BIGINT FK to www_enrollment(id).
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

router = APIRouter(prefix="/api/www-bks", tags=["WWW BKS"])

_INDICATORS = [
    "against_violence", "increased_mobility", "claiming_identity",
    "gaining_control", "joining_community", "engaging_government",
    "treating_equally", "putting_thoughts", "started_studying"
]

# 2026-10-05: BKS rows that share (trainee_id, date_of_bks) are merged
# into one logical record for the List / View / Export. Multiple
# import rows per trainee+date were common because each legacy row
# captured ONE indicator; consolidating keeps the Indicator column
# accurate without touching the raw table.
def _consolidate_bks_rows(rows, key_fields=("trainee_id", "date_of_bks")):
    groups = {}
    order = []
    for r in rows:
        if not isinstance(r, dict):
            try:
                r = dict(r)
            except Exception:
                continue
        key = tuple(r.get(k) for k in key_fields)
        if any(v is None for v in key):
            # ungroupable row: keep as its own entry so nothing is lost.
            key = ("__single__", r.get("id"))
        if key not in groups:
            groups[key] = dict(r)
            order.append(key)
            continue
        g = groups[key]
        for ind in _INDICATORS:
            sk, stk = "spoke_" + ind, "story_" + ind
            if r.get(sk) is True:
                g[sk] = True
            if not g.get(stk) and r.get(stk):
                g[stk] = r[stk]
        # spoke_other / story_other on the normalized export SELECT.
        if r.get("spoke_other") is True:
            g["spoke_other"] = True
        if not g.get("story_other") and r.get("story_other"):
            g["story_other"] = r["story_other"]
        for ck in ("other_indicator", "indicators_talked_upon",
                   "indicators_talked", "session_attended",
                   "story_indicator", "month_of_bks"):
            rv = r.get(ck)
            if rv is None:
                continue
            rv_s = str(rv).strip()
            if not rv_s:
                continue
            gv_s = (g.get(ck) or "").strip() if isinstance(g.get(ck), str) else str(g.get(ck) or "").strip()
            if not gv_s:
                g[ck] = rv
            elif rv_s not in gv_s:
                g[ck] = gv_s + ", " + rv_s
        if r.get("is_draft"):
            g["is_draft"] = True
        rca = r.get("created_at")
        if rca and (not g.get("created_at") or rca > g["created_at"]):
            g["created_at"] = rca
    return [groups[k] for k in order]

# indicator -> (spoke column, story column) on the imported www_bks.
_LEGACY_INDICATOR_COLUMNS = {
    "against_violence": (
        "spoke_out_against_violence",
        "if_yes_story"),
    "increased_mobility": (
        "spoke_about_increased_mobility",
        "increased_mobility"),
    "claiming_identity": (
        "spoke_about_claiming_identity_with_dignity",
        "claimed_my_identity_with_dignity"),
    "gaining_control": (
        "spoke_about_gaining_more_control_over_my_own_life",
        "gained_more_control_over_my_own_life"),
    "joining_community": (
        "spoke_about_joining_larger_community_through_campaign",
        "joined_in_the_larger_community_through_campaigns_and_ot"),
    "engaging_government": (
        "spoke_about_engaging_with_government_and_got_my_work_do",
        "engaged_with_government_and_other_offices_and_got_my_wo"),
    "treating_equally": (
        "spoke_about_treating_people_f_a_different_religion_cast",
        "treat_people_of_a_different_religion_caste_sexuality_an"),
    "putting_thoughts": (
        "spoke_about_putting_forward_my_own_thoughts_and_decisio",
        "was_able_to_put_forward_my_own_thoughts_and_decisions_i"),
    "started_studying": (
        "spoke_about_started_studying_again",
        "started_studying_again"),
}


def _legacy_indicator_cols():
    """SELECT fragments exposing both columns of each indicator pair."""
    parts = []
    for ind, (spoke, story) in _LEGACY_INDICATOR_COLUMNS.items():
        # 2026-08-18: raw text bhejne se JS me 'No' bhi truthy ho jata tha --
        # List har "No" indicator ko bhi gin leti thi aur Edit form use "Yes"
        # par set kar deta tha. Asli boolean bhejo; jo pehchana na jaye wo
        # NULL rahe (= "answered nahi").
        parts.append(
            "CASE LOWER(TRIM(COALESCE(b.%s, ''))) "
            "  WHEN 'yes' THEN TRUE  WHEN 'y' THEN TRUE "
            "  WHEN 'true' THEN TRUE WHEN '1' THEN TRUE "
            "  WHEN 'no' THEN FALSE  WHEN 'n' THEN FALSE "
            "  WHEN 'false' THEN FALSE WHEN '0' THEN FALSE "
            "  ELSE NULL END AS spoke_%s" % (spoke, ind))
        parts.append(f"NULLIF(TRIM(b.{story}), '') AS story_{ind}")
    return ", ".join(parts)


def _legacy_row_select():
    """SELECT list mapping an imported www_bks row onto API field names."""
    return (
        "SELECT b.id, b.enrollment_id AS trainee_id, "
        "       NULLIF(TRIM(b.month_of_bks_conducted), '') AS month_of_bks, "
        "       b.date_of_bks_conducted AS date_of_bks, "
        "       " + _legacy_indicator_cols() + ", "
        "       NULLIF(TRIM(b.others), '') AS other_indicator, "
        "       NULLIF(TRIM(b.indicators_she_talked_upon), '') AS indicators_talked_upon, "
        "       NULLIF(TRIM(b.bks_session_attended), '') AS session_attended, "
        "       COALESCE(b.is_draft, false) AS is_draft, "
        "       b.created_at, "
        "       " + _legacy.enroll_no() + ", b.name, "
        # 2026-08-18: mobile/batch placeholder the, isliye View par
        # hamesha "--" dikhta tha. _te = www_enrollment (trainee_join).
        "       NULLIF(TRIM(_te.mobile), '') AS mobile, "
        "       " + _legacy.geo_cols() + ", "
        "       b.date_of_joining, "
        "       NULLIF(TRIM(_te.batch), '') AS batch_name, NULL::int AS batch_id, "
        + _legacy.trainee_status("b") +
        "FROM mis_azad.www_bks b " + _legacy.geo_joins("b") + _legacy.trainee_join("b")
    )


def _legacy_filters(state_code, centre_code, indicator, date_from, date_to, name, district_code=None):
    """WHERE clause + params shared by the legacy list and export paths."""
    conds = ["NULLIF(TRIM(b.name), '') IS NOT NULL", "b.deleted_at IS NULL"]
    params = []
    if state_code:  conds.append(_legacy.state_filter());     params.append(state_code)
    if district_code: conds.append(_legacy.district_filter()); params.append(district_code)
    if centre_code: conds.append(_legacy.centre_filter("b")); params.append(centre_code)
    if name:        conds.append("(" + _legacy.name_match("b.name") + " OR _te.enrollment_no ILIKE %s)");          params.append(_legacy.name_pattern(name)); params.append(_legacy.name_pattern(name))
    if date_from:   conds.append("b.date_of_bks_conducted >= %s"); params.append(date_from)
    if date_to:     conds.append("b.date_of_bks_conducted <= %s"); params.append(date_to)
    if indicator and indicator in _LEGACY_INDICATOR_COLUMNS:
        spoke = _LEGACY_INDICATOR_COLUMNS[indicator][0]
        conds.append(f"LOWER(TRIM(COALESCE(b.{spoke}, ''))) IN ('yes','y','true','1')")
    return "WHERE " + " AND ".join(conds), params


def _yn(v):
    """The import stores the "did she speak about X" flags as text."""
    return None if v is None else ("Yes" if v else "No")


def _legacy_update_column(field: str):
    """Map an API field name onto its imported www_bks column, or None."""
    if field == "month_of_bks":
        return "month_of_bks_conducted"
    if field == "date_of_bks":
        return "date_of_bks_conducted"
    if field == "other_indicator":
        return "others"
    if field == "is_draft":
        return "is_draft"
    for ind, (spoke, story) in _LEGACY_INDICATOR_COLUMNS.items():
        if field == f"spoke_{ind}":
            return spoke
        if field == f"story_{ind}":
            return story
    return None


class BKSCreate(BaseModel):
    trainee_id: int
    month_of_bks: Optional[str] = None
    date_of_bks: Optional[date] = None
    spoke_against_violence: Optional[bool] = None
    story_against_violence: Optional[str] = None
    spoke_increased_mobility: Optional[bool] = None
    story_increased_mobility: Optional[str] = None
    spoke_claiming_identity: Optional[bool] = None
    story_claiming_identity: Optional[str] = None
    spoke_gaining_control: Optional[bool] = None
    story_gaining_control: Optional[str] = None
    spoke_joining_community: Optional[bool] = None
    story_joining_community: Optional[str] = None
    spoke_engaging_government: Optional[bool] = None
    story_engaging_government: Optional[str] = None
    spoke_treating_equally: Optional[bool] = None
    story_treating_equally: Optional[str] = None
    spoke_putting_thoughts: Optional[bool] = None
    story_putting_thoughts: Optional[str] = None
    spoke_started_studying: Optional[bool] = None
    story_started_studying: Optional[str] = None
    other_indicator: Optional[str] = None
    is_draft: Optional[bool] = False


class BKSUpdate(BaseModel):
    month_of_bks: Optional[str] = None
    date_of_bks: Optional[date] = None
    spoke_against_violence: Optional[bool] = None
    story_against_violence: Optional[str] = None
    spoke_increased_mobility: Optional[bool] = None
    story_increased_mobility: Optional[str] = None
    spoke_claiming_identity: Optional[bool] = None
    story_claiming_identity: Optional[str] = None
    spoke_gaining_control: Optional[bool] = None
    story_gaining_control: Optional[str] = None
    spoke_joining_community: Optional[bool] = None
    story_joining_community: Optional[str] = None
    spoke_engaging_government: Optional[bool] = None
    story_engaging_government: Optional[str] = None
    spoke_treating_equally: Optional[bool] = None
    story_treating_equally: Optional[str] = None
    spoke_putting_thoughts: Optional[bool] = None
    story_putting_thoughts: Optional[str] = None
    spoke_started_studying: Optional[bool] = None
    story_started_studying: Optional[str] = None
    other_indicator: Optional[str] = None
    is_draft: Optional[bool] = None


def _row_select():
    return (
        "SELECT b.*, t.enrollment_no, t.name, t.mobile, "
        "       t.state_code, t.district_code, t.centre_code, "
        "       t.enrollment_date AS date_of_joining, "
        "       COALESCE(ba.name, NULL) AS batch_name, ba.id AS batch_id "
        "FROM www_bks b "
        "JOIN www_enrollment t ON t.id = b.trainee_id "
        "LEFT JOIN www_master_batches ba ON ba.id = t.batch_id "
    )


@router.get("")
def list_bks(
    request: Request,
    enrollment_id: Optional[int] = None,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    indicator: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    name: Optional[str] = None,
    sort_by: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
):
    page = max(page, 1); limit = max(limit, 1); offset = (page - 1) * limit
    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        # ---- LEGACY FALLBACK: www_bks is the import, not the normalized table ----
        if not _legacy.is_normalized(cur, "www_bks"):
            lwhere, lparams = _legacy_filters(
                state_code, centre_code, indicator, date_from, date_to, name, district_code=district_code)
            if enrollment_id:
                lwhere += " AND b.enrollment_id = %s"; lparams.append(enrollment_id)
            # 2026-10-05: fetch ALL matching rows (no LIMIT) so we can
            # consolidate rows that share (trainee_id, date_of_bks) and
            # paginate on the consolidated list. Keeps the original SQL
            # sort order; group identity is defined by first appearance.
            cur.execute(
                _legacy_row_select() + lwhere +
                " ORDER BY " + www_list_order(sort_by, "b.name", "b.id", "b.id DESC"),
                lparams,
            )
            rows = _consolidate_bks_rows(cur.fetchall())
            total = len(rows)
            return {"total": total, "page": page, "limit": limit,
                    "data": rows[offset:offset + limit]}

        conds = ["b.deleted_at IS NULL"]
        params = []
        if state_code:  conds.append("t.state_code = %s");  params.append(state_code)
        if district_code: conds.append("t.district_code = %s"); params.append(district_code)
        if centre_code: conds.append("t.centre_code = %s"); params.append(centre_code)
        if name:        conds.append(_legacy.name_match("t.name"));    params.append(_legacy.name_pattern(name))
        if date_from:   conds.append("b.date_of_bks >= %s"); params.append(date_from)
        if date_to:     conds.append("b.date_of_bks <= %s"); params.append(date_to)
        if indicator and indicator in _INDICATORS:
            conds.append(f"b.spoke_{indicator} = TRUE")
        where = "WHERE " + " AND ".join(conds)
        # 2026-10-05: fetch ALL matching rows then consolidate on
        # (trainee_id, date_of_bks) before paginating. See the matching
        # change in the legacy branch above.
        sql = _row_select() + where + " ORDER BY " + www_list_order(sort_by, "b.name", "b.created_at", "b.created_at DESC NULLS LAST, b.id DESC")
        cur.execute(sql, params)
        rows = _consolidate_bks_rows(cur.fetchall())
        total = len(rows)
        return {"total": total, "page": page, "limit": limit,
                "data": rows[offset:offset + limit]}


@router.get("/{bks_id}")
def get_bks(request: Request, bks_id: int):
    with get_cursor() as cur:
        if not _legacy.is_normalized(cur, "www_bks"):
            cur.execute(_legacy_row_select() + "WHERE b.id = %s", (bks_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "BKS record not found.")
            _scope.guard_detail(request, row)
            # 2026-10-05: merge siblings sharing (trainee_id, date_of_bks)
            # so the View screen shows a single consolidated record.
            tid = row.get("trainee_id"); dob = row.get("date_of_bks")
            if tid is not None and dob is not None:
                cur.execute(
                    _legacy_row_select() +
                    "WHERE b.enrollment_id = %s AND b.date_of_bks_conducted = %s",
                    (tid, dob),
                )
                sibs = cur.fetchall()
                if sibs:
                    merged = _consolidate_bks_rows(sibs)
                    if merged:
                        # Keep the originally-requested id so the FE's
                        # Edit button still works on the record the user
                        # clicked, but surface the merged indicators.
                        _id = row.get("id")
                        row = merged[0]
                        row["id"] = _id
            return row

        cur.execute(_row_select() + "WHERE b.id = %s AND b.deleted_at IS NULL", (bks_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "BKS record not found.")
        _scope.guard_detail(request, row)
        # 2026-10-05: merge siblings on the normalized branch too.
        tid = row.get("trainee_id"); dob = row.get("date_of_bks")
        if tid is not None and dob is not None:
            cur.execute(
                _row_select() +
                "WHERE b.trainee_id = %s AND b.date_of_bks = %s AND b.deleted_at IS NULL",
                (tid, dob),
            )
            sibs = cur.fetchall()
            if sibs:
                merged = _consolidate_bks_rows(sibs)
                if merged:
                    _id = row.get("id")
                    row = merged[0]
                    row["id"] = _id
    return row


@router.post("")
def create_bks(body: BKSCreate):
    with get_cursor() as cur:
        # 2026-08-18 (Ashish): flow guard -- picker ki rok server par bhi.
        _legacy.assert_flow(cur, body.trainee_id, stage="BKS")
        if not _legacy.is_normalized(cur, "www_bks"):
            lcols = ["month_of_bks_conducted", "date_of_bks_conducted", "others",
                     "is_draft"]
            lvals = [body.month_of_bks, body.date_of_bks, body.other_indicator,
                     bool(body.is_draft)]
            for ind in _INDICATORS:
                spoke, story = _LEGACY_INDICATOR_COLUMNS[ind]
                lcols.append(spoke)
                lvals.append(_yn(getattr(body, f"spoke_{ind}", None)))
                lcols.append(story)
                lvals.append(getattr(body, f"story_{ind}", None))
            ph = ",".join(["%s"] * len(lvals))
            cur.execute(
                "INSERT INTO mis_azad.www_bks "
                "    (enrollment_id, name, type_of_enrollment, "
                "     state, district, centre, date_of_joining, "
                + ",".join(lcols) + ") "
                "SELECT e.id, e.name, e.type_of_enrollment, "
                "       e.state, e.district, e.centre, e.enrollment_date, " + ph + " "
                "FROM mis_azad.www_enrollment e WHERE e.id = %s "
                "RETURNING id",
                lvals + [body.trainee_id],
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Trainee not found.")
            return {"id": row["id"], "ok": True}

        cur.execute("SELECT 1 FROM www_enrollment WHERE id=%s", (body.trainee_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Trainee not found.")
        cols = ["trainee_id", "month_of_bks", "date_of_bks",
                "other_indicator", "is_draft"]
        vals = [body.trainee_id, body.month_of_bks, body.date_of_bks,
                body.other_indicator, bool(body.is_draft)]
        for ind in _INDICATORS:
            cols.append(f"spoke_{ind}"); vals.append(getattr(body, f"spoke_{ind}", None))
            cols.append(f"story_{ind}"); vals.append(getattr(body, f"story_{ind}", None))
        placeholders = ",".join(["%s"]*len(vals))
        cur.execute(
            f"INSERT INTO www_bks ({','.join(cols)}) VALUES ({placeholders}) RETURNING id",
            vals,
        )
        new_id = cur.fetchone()["id"]
    return {"id": new_id, "ok": True}


@router.put("/{bks_id}")
def update_bks(bks_id: int, body: BKSUpdate):
    payload = body.model_dump(exclude_unset=True)
    if not payload:
        return {"ok": True}
    with get_cursor() as cur:
        if not _legacy.is_normalized(cur, "www_bks"):
            lfields, lparams = [], []
            for k, v in payload.items():
                col = _legacy_update_column(k)
                if not col:
                    continue
                if k.startswith("spoke_"):
                    v = _yn(v)
                lfields.append(f"{col} = %s"); lparams.append(v)
            if not lfields:
                return {"ok": True}
            lparams.append(bks_id)
            cur.execute("UPDATE mis_azad.www_bks SET " + ",".join(lfields) +
                        " WHERE id = %s", lparams)
            if cur.rowcount == 0:
                raise HTTPException(404, "BKS record not found.")
            return {"ok": True}

        fields = []; params = []
        for k, v in payload.items():
            fields.append(f"{k} = %s"); params.append(v)
        params.append(bks_id)
        cur.execute("UPDATE www_bks SET " + ",".join(fields) +
                    " WHERE id = %s AND deleted_at IS NULL", params)
        if cur.rowcount == 0:
            raise HTTPException(404, "BKS record not found.")
    return {"ok": True}


@router.delete("/{bks_id}")
def delete_bks(bks_id: int):
    with get_cursor() as cur:
        if not _legacy.is_normalized(cur, "www_bks"):
            # 2026-08-19 (Ashish): pehle ye row ko HAMESHA ke liye mita deta tha.
            # Ab deleted_at bhar dete hain -- row DB me bachi rehti hai, bas har
            # list se hat jati hai. Wapas laani ho to deleted_at = NULL.
            cur.execute("UPDATE mis_azad.www_bks SET deleted_at = NOW() "
                        "WHERE id = %s AND deleted_at IS NULL", (bks_id,))
        else:
            cur.execute("UPDATE www_bks SET deleted_at = now() WHERE id=%s AND deleted_at IS NULL", (bks_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "BKS record not found.")
    return {"ok": True}


# =============================================================================
# EXPORT (Excel) — 2026-08-08
# Section-wise xlsx: Trainee Details + BKS Details (Month, Date, 10 topic
# pairs of Spoke/Story) + System.
# =============================================================================
@router.get("/export/excel")
def export_bks_excel(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    enrollment_type: Optional[str] = None,
    indicator: Optional[str] = None,
    name: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    from datetime import date as _d
    from export_helper import multi_sheet_xlsx_response_v2

    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        has_table = _legacy.is_normalized(cur, "www_bks")

        if not has_table:
            lwhere, lparams = _legacy_filters(
                state_code, centre_code, indicator, date_from, date_to, name, district_code=district_code)
            cur.execute(
                "SELECT " + _legacy.enroll_no() + ", b.id AS id, b.name, "
                "       NULLIF(TRIM(_te.mobile), '') AS mobile, "
                "       NULLIF(TRIM(b.type_of_enrollment), '') AS enrollment_type, "
                "       b.state AS state_name, b.district AS district_name, "
                "       " + _legacy.centre_expr("b.centre") + " AS centre_name, "
                "       NULL::text AS area_name, "
                "       NULLIF(TRIM(_te.batch), '') AS batch_name, "
                # 2026-08-12: six www_bks columns were never selected — the
                # year, the two dates, the session attended and both
                # indicator summaries the data-entry team fills in.
                "       b.year, b.date_of_joining, "
                "       NULLIF(TRIM(b.date_of_ll), '') AS date_of_ll, "
                "       NULLIF(TRIM(b.bks_session_attended), '') AS session_attended, "
                "       NULLIF(TRIM(b.indicators_she_talked_upon), '') AS indicators_talked, "
                "       NULLIF(TRIM(b.which_of_indicators_is_the_story_applicable_to), '') "
                "           AS story_indicator, "
                "       NULLIF(TRIM(b.month_of_bks_conducted), '') AS month_of_bks, "
                "       b.date_of_bks_conducted AS date_of_bks, "
                "       " + _legacy_indicator_cols() + ", "
                "       NULL::boolean AS spoke_other, "
                "       NULLIF(TRIM(b.others), '') AS story_other, "
                "       NULL::timestamptz AS created_at "
                "FROM mis_azad.www_bks b " + _legacy.geo_joins("b") +
                _legacy.trainee_join("b") + lwhere +
                " ORDER BY b.date_of_bks_conducted DESC NULLS LAST, b.id DESC",
                lparams,
            )
            # 2026-10-05: collapse rows sharing (enrollment_no, date_of_bks)
            # so the Excel export emits ONE row per trainee+date, matching
            # the consolidated List / View.
            rows = _consolidate_bks_rows(cur.fetchall(),
                                         key_fields=("enrollment_no", "date_of_bks"))
        else:
            conds = ["b.deleted_at IS NULL"]; params = []
            if state_code:      conds.append("t.state_code = %s");      params.append(state_code)
            if centre_code:     conds.append("t.centre_code = %s");     params.append(centre_code)
            if batch_id:        conds.append("t.batch_id = %s");        params.append(batch_id)
            if enrollment_type: conds.append("t.enrollment_type = %s"); params.append(enrollment_type)
            if name:            conds.append(_legacy.name_match("t.name"));        params.append(_legacy.name_pattern(name))
            if date_from:       conds.append("b.date_of_bks >= %s");    params.append(date_from)
            if date_to:         conds.append("b.date_of_bks <= %s");    params.append(date_to)
            if indicator and indicator in _INDICATORS:
                conds.append(f"b.spoke_{indicator} = TRUE")
            where = "WHERE " + " AND ".join(conds)
            cur.execute(
                "SELECT b.id AS id, b.month_of_bks, b.date_of_bks, "
                "       b.spoke_against_violence, b.story_against_violence, "
                "       b.spoke_increased_mobility, b.story_increased_mobility, "
                "       b.spoke_claiming_identity, b.story_claiming_identity, "
                "       b.spoke_gaining_control, b.story_gaining_control, "
                "       b.spoke_joining_community, b.story_joining_community, "
                "       b.spoke_engaging_government, b.story_engaging_government, "
                "       b.spoke_treating_equally, b.story_treating_equally, "
                "       b.spoke_putting_thoughts, b.story_putting_thoughts, "
                "       b.spoke_started_studying, b.story_started_studying, "
                "       NULL::boolean AS spoke_other, b.other_indicator AS story_other, "
                "       b.created_at, "
                "       t.enrollment_no, t.name, t.mobile, t.enrollment_type, "
                "       t.state_code, t.district_code, t.centre_code, t.area_code, "
                "       s.state_name, d.district_name, c.centre_name, a.area_name, "
                "       ba.name AS batch_name "
                "FROM www_bks b "
                "JOIN www_enrollment t ON t.id = b.trainee_id "
                "LEFT JOIN central_states    s ON s.state_code    = t.state_code "
                "LEFT JOIN central_districts d ON d.district_code = t.district_code "
                "LEFT JOIN central_centres   c ON c.centre_code   = t.centre_code "
                "LEFT JOIN www_areas     a ON a.area_code     = t.area_code "
                "LEFT JOIN www_master_batches ba ON ba.id = t.batch_id " +
                where + " ORDER BY b.created_at DESC",
                params,
            )
            # 2026-10-05: collapse rows sharing (enrollment_no, date_of_bks)
            # — see matching change on the legacy branch above.
            rows = _consolidate_bks_rows(cur.fetchall(),
                                         key_fields=("enrollment_no", "date_of_bks"))

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
        "Year", "Date of Joining", "Date of LL",
    ]
    # 10 topic pairs (indicator label -> spoke_xxx / story_xxx column suffix)
    _BKS_TOPICS = [
        ("Violence",            "against_violence"),
        ("Mobility",            "increased_mobility"),
        ("Identity",            "claiming_identity"),
        ("Control",             "gaining_control"),
        ("Community",           "joining_community"),
        ("Govt",                "engaging_government"),
        ("Equality",            "treating_equally"),
        ("Thoughts",            "putting_thoughts"),
        ("Studying",            "started_studying"),
        ("Other",               "other"),
    ]
    bks_headers = [
        "Month of BKS", "Date of BKS", "Session Attended",
        "Indicators She Talked Upon", "Story Applicable To Indicator",
    ]
    for label, _key in _BKS_TOPICS:
        bks_headers.append(f"Spoke About {label}")
        bks_headers.append(f"Story of {label}")
    system_headers = ["Created At"]
    all_headers = trainee_headers + bks_headers + system_headers
    n_t, n_b, n_s = len(trainee_headers), len(bks_headers), len(system_headers)
    group_headers = [
        (1, n_t, "Trainee Details"),
        (n_t + 1, n_t + n_b, "BKS Details"),
        (n_t + n_b + 1, n_t + n_b + n_s, "System"),
    ]

    data_rows = []
    for r in rows:
        row = [
            _g(r, "enrollment_no"), _g(r, "name"), _g(r, "mobile"), _g(r, "enrollment_type"),
            _g(r, "state_name") or _g(r, "state_code"),
            _g(r, "district_name") or _g(r, "district_code"),
            _g(r, "centre_name") or _g(r, "centre_code"),
            _g(r, "area_name") or _g(r, "area_code"),
            _g(r, "batch_name"),
            _g(r, "year"), _g(r, "date_of_joining"), _g(r, "date_of_ll"),
            _g(r, "month_of_bks"), _g(r, "date_of_bks"),
            _g(r, "session_attended"), _g(r, "indicators_talked"),
            _g(r, "story_indicator"),
        ]
        for _label, key in _BKS_TOPICS:
            row.append(_yn(r.get(f"spoke_{key}")))
            row.append(_g(r, f"story_{key}"))
        row.append(_g(r, "created_at"))
        data_rows.append(row)

    # 2026-08-26: WWW tracking columns (Created By / Updated By / Updated At)
    from routes._www_export_tracking import WWW_TRACK_HEADERS as _WT_H, www_tracking_cells as _wt_cells
    all_headers = list(all_headers) + _WT_H
    # 2026-09-19: Record Info banner over Created By + Updated By.
    # 2026-10-01: removed a leftover duplicate append that produced an
    # overlapping Record Info group header and crashed the Excel export
    # with "MergedCell is read-only".
    group_headers = list(group_headers) + [(len(all_headers) - len(_WT_H) + 1, len(all_headers), "Record Info")]
    _wt_rows = _wt_cells(rows, "mis_azad.www_bks", "id")
    for _wi in range(len(data_rows)):
        data_rows[_wi] = list(data_rows[_wi]) + (_wt_rows[_wi] if _wi < len(_wt_rows) else ["", ""])
    sheets = [{
        "name": "BKS",
        "group_headers": group_headers,
        "headers": all_headers,
        "rows": data_rows,
    }]
    return multi_sheet_xlsx_response_v2(
        sheets,
        f"WWW_BKS_{_d.today().isoformat()}.xlsx",
    )
