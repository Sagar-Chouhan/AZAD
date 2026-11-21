"""WWW Pipeline routes."""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import date, datetime
import sys, os, io, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from routes import _www_legacy as _legacy
from routes import _www_scope as _scope
from models.www import WWWStageUpdate

router = APIRouter(prefix="/api/www", tags=["WWW Pipeline"])


def _dashboard_rows(cur, sql, params=()):
    """Run one dashboard query without letting an optional WWW table break the page."""
    cur.execute("SAVEPOINT www_dashboard_query")
    try:
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.execute("RELEASE SAVEPOINT www_dashboard_query")
        return rows
    except Exception:
        cur.execute("ROLLBACK TO SAVEPOINT www_dashboard_query")
        cur.execute("RELEASE SAVEPOINT www_dashboard_query")
        return []


def _dashboard_count(cur, table, trainee_where, params, extra=""):
    rows = _dashboard_rows(
        cur,
        f"""
            SELECT COUNT(DISTINCT x.trainee_id) AS n
            FROM {table} x
            JOIN www_enrollment t ON t.id = x.trainee_id
            WHERE {trainee_where} {extra}
        """,
        params,
    )
    return int(rows[0]["n"] or 0) if rows else 0


def _legacy_text(value):
    return str(value or "").strip()


def _legacy_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _legacy_text(value)
    for fmt in ("%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%d.%m.%y", "%d-%m-%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def _legacy_geo_reach(cur, state_code=None, centre_code=None, district_code=None):
    """The programme's geography footprint for the States / Centres KPI cards.

    2026-08-11: these two counted DISTINCT state/centre over the enrolled rows,
    which always read 1 / 1 — every row in all thirteen WWW tables is Tamil
    Nadu / Chennai, so the count was accurate but told the user nothing.  The
    cards sit next to "Trainees Enrolled" and their placeholder markup ships a
    4, i.e. they were meant to be the master's footprint (Delhi, Rajasthan,
    West Bengal, Tamil Nadu / seven centres).  Read the masters instead, and
    narrow them when the dashboard's own geography filter is applied.
    """
    if centre_code:
        cur.execute(
            "SELECT COUNT(DISTINCT state_code) AS s FROM mis_azad.central_centres "
            " WHERE centre_code = %s AND deleted_at IS NULL",
            (centre_code,),
        )
        return int((cur.fetchone() or {}).get("s") or 0), 1

    where = "WHERE deleted_at IS NULL AND COALESCE(status, 'Active') = 'Active'"
    if district_code:
        cur.execute(
            "SELECT COUNT(*) AS n FROM mis_azad.central_centres " + where + " AND district_code = %s",
            (district_code,),
        )
        return 1, int(cur.fetchone()["n"] or 0)
    if state_code:
        cur.execute(
            "SELECT COUNT(*) AS n FROM mis_azad.central_centres " + where + " AND state_code = %s",
            (state_code,),
        )
        return 1, int(cur.fetchone()["n"] or 0)

    cur.execute("SELECT COUNT(*) AS n FROM mis_azad.central_states " + where)
    states = int(cur.fetchone()["n"] or 0)
    cur.execute("SELECT COUNT(*) AS n FROM mis_azad.central_centres " + where)
    return states, int(cur.fetchone()["n"] or 0)


def _legacy_www_dashboard(cur, state_code=None, centre_code=None, status=None,
                          date_from=None, date_to=None, district_code=None):
    """Build the dashboard from the imported Kobo WWW tables when v2 tables are absent."""
    # Every query below keys on enrollment_id, the FK to www_enrollment added
    # by sql/072, so the set arithmetic further down lines up on integers.
    # This used to normalise the text enrollment number on both sides because
    # the sheets disagree on punctuation ("TN/CN/..." vs "TN-CN/...").
    enrollments = _dashboard_rows(cur, f"""
        SELECT e.id AS enrollment_id,
               e.enrollment_no AS enrollment_display,
               _gs.state_code, e.state, _gd.district_code AS district_code,
               -- 2026-09-26: prefer the www_centres-resolved code so downstream
               -- centre-code checks work for PIs whose scope is the canonical
               -- code (e.g. S19347B4) while e.centre stores the raw name.
               COALESCE(_gc.centre_code, {_legacy.centre_expr('e.centre')}) AS centre,
               -- 2026-09-30: separate name column so display code paths
               -- (e.g. Sakha pass-rate bar chart) don't show S-codes.
               COALESCE(_gc.centre_name, {_legacy.centre_expr('e.centre')}) AS centre_name,
               e.financial_year, e.enrollment_date, e.created_at,
               e.name, e.age_at_enrollment AS age,
               e.caste_category AS caste
        FROM mis_azad.www_enrollment e {_legacy.geo_joins('e')}
        WHERE NULLIF(TRIM(e.enrollment_no), '') IS NOT NULL
          AND e.deleted_at IS NULL
    """)
    if not enrollments:
        return None

    ll_rows = _dashboard_rows(cur, f"""
        SELECT l.enrollment_id, l.date_of_joining, l.created_at,
               {_legacy.safe_date('l.date_of_ll')} AS date_of_ll,
               (NULLIF(TRIM(COALESCE(l.date_of_ll, '')), '') IS NOT NULL
                OR NULLIF(TRIM(COALESCE(l.ll_number, '')), '') IS NOT NULL) AS has_ll
        FROM mis_azad.www_ll l
        WHERE l.enrollment_id IS NOT NULL
          AND l.deleted_at IS NULL
    """)
    induction_rows = _dashboard_rows(cur, """
        SELECT i.enrollment_id, i.start_date
        FROM mis_azad.www_induction i
        WHERE i.start_date IS NOT NULL AND i.enrollment_id IS NOT NULL
          AND i.deleted_at IS NULL
    """)
    # 2026-10-13 (user ask): also expose walkout_stage so State-wise
    # table can split out Employable rows and count per-record.
    walkout_rows = _dashboard_rows(cur, """
        SELECT w.enrollment_id, w.walkout_date, w.walkout_stage
        FROM mis_azad.www_walkout w
        WHERE COALESCE(NULLIF(TRIM(w.status), ''), 'Walkout') = 'Walkout'
          AND w.enrollment_id IS NOT NULL
          AND w.deleted_at IS NULL
    """)
    internal_rows = _dashboard_rows(cur, """
        SELECT s.enrollment_id, s.date_of_pl,
               s.have_the_trainee_passed_the_internal_test AS passed,
               s.if_yes_date_of_internal_sakha_pass AS pass_date
        FROM mis_azad.www_sakha_internal s
        WHERE s.enrollment_id IS NOT NULL
          AND s.deleted_at IS NULL
    """)
    external_rows = _dashboard_rows(cur, """
        SELECT s.enrollment_id,
               s.if_yes_date_of_external_sakha_pass AS external_pass_date
        FROM mis_azad.www_sakha_external s
        WHERE s.if_yes_date_of_external_sakha_pass IS NOT NULL
          AND s.enrollment_id IS NOT NULL
          AND s.deleted_at IS NULL
    """)
    emp_rows = _dashboard_rows(cur, """
        SELECT e.enrollment_id, e.date_of_pl,
               e.what_is_your_current_status AS current_status,
               e.type_of_job, e.date_of_job
        FROM mis_azad.www_employment e
        WHERE e.enrollment_id IS NOT NULL
          AND e.deleted_at IS NULL
    """)
    # 2026-08-14: the PL KPI used to be inferred from Sakha / Employment PL
    # dates and PL stories alone and never read www_pl itself, so it showed
    # 91 of the 181 licence rows.  A row counts once it carries either a PL
    # date or a PL number; rows with neither are still in the PL pipeline.
    pl_rows = _dashboard_rows(cur, """
        SELECT p.enrollment_id, p.date_of_pl, p.created_at
        FROM mis_azad.www_pl p
        WHERE p.enrollment_id IS NOT NULL
          AND p.deleted_at IS NULL
          AND (p.date_of_pl IS NOT NULL
               OR NULLIF(TRIM(COALESCE(p.pl_number, '')), '') IS NOT NULL)
    """)

    def row_ids(rows):
        return {r["enrollment_id"] for r in rows if r.get("enrollment_id") is not None}

    # 2026-08-14: counting only rows whose date_of_ll parsed as a date hid
    # every trainee whose sheet cell reads "Came with LL" (she arrived with
    # her licence) -- she stayed in the PL and Placed cards while dropping
    # out of LL, so Got PL could exceed Got LL.  Count the licence itself.
    ll_ids = {r["enrollment_id"] for r in ll_rows if r.get("has_ll")}
    induction_ids = row_ids(induction_rows)
    internal_ids = row_ids(internal_rows)
    internal_passed = {r["enrollment_id"] for r in internal_rows
                       if _legacy_text(r.get("passed")).lower() == "yes"}
    internal_failed = {r["enrollment_id"] for r in internal_rows
                       if _legacy_text(r.get("passed")).lower() == "no"}
    external_ids = row_ids(external_rows)
    placed_ids = {r["enrollment_id"] for r in emp_rows
                  if _legacy_text(r.get("current_status")).lower() == "on job"}
    employment_ids = row_ids(emp_rows)
    walkout_ids = row_ids(walkout_rows)
    pl_ids = row_ids(pl_rows) | {r["enrollment_id"] for r in internal_rows + emp_rows
                                 if r.get("date_of_pl")}

    # Every module table exposes the FK under the same name, so unlike the
    # text-key version this no longer has to spell out a per-table column.
    module_sources = {
        "nt_training": "www_ntt_training",
        "gbv":         "www_gbv",
        "fat":         "www_financial_assistance_to_trainees",
        "bks":         "www_bks",
        "pl_stories":  "www_pl_stories",
    }
    module_ids = {}
    for key, table in module_sources.items():
        rows = _dashboard_rows(
            cur,
            f"SELECT enrollment_id FROM mis_azad.{table} "
            f"WHERE enrollment_id IS NOT NULL AND deleted_at IS NULL",
        )
        module_ids[key] = row_ids(rows)
    pl_ids |= module_ids.get("pl_stories", set())
    # A permanent licence is only issued to a learning-licence holder, so
    # anyone counted in PL counts in LL too -- this stops a blank LL cell
    # from making the funnel widen further down the pipeline.
    ll_ids |= pl_ids

    def lifecycle(enrollment_id):
        if enrollment_id in walkout_ids:
            return "Walkout"
        if enrollment_id in placed_ids:
            return "Placed"
        return "Active"

    wanted_status = "Walkout" if status == "Dropout" else status
    filtered = []
    for row in enrollments:
        enrollment_id = row["enrollment_id"]
        enrolled_on = _legacy_date(row.get("enrollment_date"))
        if state_code and state_code not in (_legacy_text(row.get("state_code")), _legacy_text(row.get("state"))):
            continue
        # 2026-09-26: match centre_code against the CODE (from _gc.centre_code)
        # AND the raw NAME (fallback for rows www_centres does not cover).
        _row_centre = _legacy_text(row.get("centre"))
        if centre_code and centre_code != _row_centre:
            continue
        if district_code and district_code != _legacy_text(row.get("district_code")):
            continue
        if wanted_status and lifecycle(enrollment_id) != wanted_status:
            continue
        if date_from and (not enrolled_on or enrolled_on < date_from):
            continue
        if date_to and (not enrolled_on or enrolled_on > date_to):
            continue
        row = dict(row)
        row["enrolled_on"] = enrolled_on
        row["status"] = lifecycle(enrollment_id)
        filtered.append(row)

    allowed = {r["enrollment_id"] for r in filtered}
    # 2026-10-04: Pass-rate bar chart must stay cumulative across the
    # whole FY and NOT be narrowed by the dashboard date window (a
    # Sakha pass that happened before the window still counts). Build a
    # parallel "geo-only" set with the same state/centre/district rules
    # as the main loop but without the enrolled_on date predicates.
    allowed_geo = set()
    for _row in enrollments:
        if state_code and state_code not in (_legacy_text(_row.get("state_code")), _legacy_text(_row.get("state"))):
            continue
        if centre_code and centre_code != _legacy_text(_row.get("centre")):
            continue
        if district_code and district_code != _legacy_text(_row.get("district_code")):
            continue
        allowed_geo.add(_row["enrollment_id"])
    geo_states, geo_centres = _legacy_geo_reach(cur, state_code, centre_code, district_code)
    kpi = {
        "enrolled": len(allowed),
        "received_ll": len(allowed & ll_ids),
        "received_pl": len(allowed & pl_ids),
        # 2026-09-15: exclude trainees who later walked out (lifecycle gives
        # Walkout precedence) so this KPI matches the per-state table + funnel.
        "placed": len(allowed & (placed_ids - walkout_ids)),
        # 2026-10-13 (user ask): default-view walkout KPI counts
        # per-record Walkout-only (excludes Employable + Walkin),
        # matching the Walkout List with the "Walkout" filter.
        "walkouts": sum(1 for _wr in walkout_rows
                        if _wr.get("enrollment_id") in allowed
                        and (_wr.get("walkout_stage") or "") not in
                            {"After PL","Before Internal Sakha","After Internal Sakha",
                             "Before External Sakha","After External Sakha"}),
        "states": geo_states,
        "centres": geo_centres,
    }

    state_groups = {}
    age_groups = {}
    caste_counts = {}
    status_counts = {}
    trend = {}
    years = {}
    names = {}
    for row in filtered:
        enrollment_id = row["enrollment_id"]
        names[enrollment_id] = (_legacy_text(row.get("name"))
                                or _legacy_text(row.get("enrollment_display")))
        state = _legacy_text(row.get("state")) or _legacy_text(row.get("state_code")) or "Unknown"
        state_key = _legacy_text(row.get("state_code")) or state
        group = state_groups.setdefault(state_key, {
            "state": state, "state_code": state_key, "total": 0, "active": 0,
            "walkout": 0, "placed": 0, "got_ll": 0, "got_pl": 0,
        })
        group["total"] += 1
        # 2026-10-13: walkout column populated below from walkout_rows
        # (per-record, excludes Employable). Active/Placed stay lifecycle.
        if row["status"] != "Walkout":
            group[row["status"].lower()] += 1
        group["got_ll"] += int(enrollment_id in ll_ids)
        group["got_pl"] += int(enrollment_id in pl_ids)

        age_group = age_groups.setdefault(state, {
            "state": state,
            "age_18_20": 0, "age_21_25": 0, "age_26_30": 0,
            "age_31_35": 0, "age_36_40": 0, "above_40": 0,
            "unknown_age": 0,
            # kept so any client on the old key still sees 0 instead of undefined
            "above_25": 0,
        })
        try:
            age = int(float(_legacy_text(row.get("age"))))
        except ValueError:
            age = None
        if age is None:
            age_group["unknown_age"] += 1
        elif 18 <= age <= 20:
            age_group["age_18_20"] += 1
        elif 21 <= age <= 25:
            age_group["age_21_25"] += 1
        elif 26 <= age <= 30:
            age_group["age_26_30"] += 1
        elif 31 <= age <= 35:
            age_group["age_31_35"] += 1
        elif 36 <= age <= 40:
            age_group["age_36_40"] += 1
        elif age > 40:
            age_group["above_40"] += 1
        else:
            age_group["unknown_age"] += 1

        caste = _legacy_text(row.get("caste")) or "Not specified"
        caste_counts[caste] = caste_counts.get(caste, 0) + 1
        # 2026-10-13: Walkout tally built per-record after the loop.
        if row["status"] != "Walkout":
            status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
        if row.get("enrolled_on"):
            ym = row["enrolled_on"].strftime("%Y-%m")
            trend[ym] = trend.get(ym, 0) + 1
        year = _legacy_text(row.get("financial_year")) or (
            row["enrolled_on"].strftime("%Y") if row.get("enrolled_on") else "Unknown"
        )
        funnel = years.setdefault(year, {"year": year, "enrolled": 0, "got_ll": 0, "got_pl": 0, "placed": 0})
        funnel["enrolled"] += 1
        funnel["got_ll"] += int(enrollment_id in ll_ids)
        funnel["got_pl"] += int(enrollment_id in pl_ids)
        funnel["placed"] += int(enrollment_id in placed_ids)

    # 2026-10-13 (user ask): default-view (no date filter) walkout
    # column = per-record count of the derived "Walkout" category
    # (walkout_stage NOT in Employable set, status=Walkout only).
    # This replaces the earlier lifecycle-based distinct-trainee count
    # so the State-wise table aligns with the Walkout List + KPI card.
    _WO_EMPLOYABLE_DEF = {"After PL","Before Internal Sakha","After Internal Sakha",
                          "Before External Sakha","After External Sakha"}
    _eid_skey_default = {}
    for _r in filtered:
        _st = (_legacy_text(_r.get("state"))
               or _legacy_text(_r.get("state_code")) or "Unknown")
        _sk = _legacy_text(_r.get("state_code")) or _st
        _eid_skey_default[_r["enrollment_id"]] = _sk
    _wo_default_total = 0
    for _wr in walkout_rows:
        _eid = _wr.get("enrollment_id")
        if _eid not in allowed:
            continue
        if (_wr.get("walkout_stage") or "") in _WO_EMPLOYABLE_DEF:
            continue
        _wo_default_total += 1
        _sk = _eid_skey_default.get(_eid)
        if _sk in state_groups:
            state_groups[_sk]["walkout"] += 1
    # Chart "Trainee Status Distribution" bucket for Walkout matches
    # the table + KPI (per-record Walkout-only).
    status_counts["Walkout"] = _wo_default_total

    by_caste = [
        {"caste": key, "count": value, "pct": round(100 * value / len(filtered), 1) if filtered else 0}
        for key, value in sorted(caste_counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    by_tab = {
        "enrollment": len(allowed),
        "induction": len(allowed & induction_ids),
        "learning_license": len(allowed & ll_ids),
        "driving_practice": len(allowed & internal_ids),
        "nt_training": len(allowed & module_ids.get("nt_training", set())),
        "gbv": len(allowed & module_ids.get("gbv", set())),
        "fat": len(allowed & module_ids.get("fat", set())),
        "bks": len(allowed & module_ids.get("bks", set())),
        "pl_stories": len(allowed & module_ids.get("pl_stories", set())),
        "permanent_license": len(allowed & pl_ids),
        "internal_sakha": {
            "total": len(allowed & internal_ids), "passed": len(allowed & internal_passed),
            "failed": len(allowed & internal_failed),
        },
        "external_sakha": {
            "total": len(allowed & external_ids), "passed": len(allowed & external_ids), "failed": 0,
        },
        "employment": {"total": len(allowed & employment_ids)},
        "walkout": {"total": len(allowed & walkout_ids)},
    }

    employment_counts = {}
    for row in emp_rows:
        if row.get("enrollment_id") not in allowed:
            continue
        # 2026-10-04: chart bucketing — any non-'On Job' status renders as 'On Bench'.
        raw = _legacy_text(row.get("current_status"))
        current = "On Job" if raw == "On Job" else "On Bench"
        employment_counts[current] = employment_counts.get(current, set())
        employment_counts[current].add(row["enrollment_id"])

    # enrollment_id is the join key; show the number the way the sheet spells it.
    display = {r["enrollment_id"]: _legacy_text(r.get("enrollment_display"))
               for r in filtered}

    activities = []
    for row in filtered:
        if row.get("enrolled_on"):
            shown = display.get(row["enrollment_id"], "")
            activities.append({"module": "Enrollment", "trainee": names[row["enrollment_id"]],
                               "event_date": row["enrolled_on"], "detail": shown,
                               "rec_id": shown})
    activity_sources = [
        ("Learning License", ll_rows, "date_of_ll", "LL received"),
        ("Internal Sakha", internal_rows, "pass_date", "Internal test"),
        ("Employment", emp_rows, "date_of_job", "Employment"),
    ]
    for module, rows, date_key, fallback_detail in activity_sources:
        for row in rows:
            enrollment_id = row.get("enrollment_id")
            event_date = _legacy_date(row.get(date_key))
            if enrollment_id in allowed and event_date:
                detail = _legacy_text(row.get("current_status")) or _legacy_text(row.get("passed")) or fallback_detail
                shown = display.get(enrollment_id, "")
                activities.append({"module": module, "trainee": names.get(enrollment_id, shown),
                                   "event_date": event_date, "detail": detail, "rec_id": shown})
    activities.sort(key=lambda row: row["event_date"], reverse=True)

    # 2026-09-15: Duration filter = PERIOD ACTIVITY. When a date range is set, each
    # headline KPI (and per-state row) counts records whose OWN date falls in the
    # window within the geo scope, instead of the enrolled-in-window cohort's
    # lifetime totals. Date used per card (user, 2026-09-17):
    #   Trainees Enrolled -> www_enrollment.enrollment_date
    #   Got LL            -> www_ll.date_of_ll          (LL records)
    #   Got PL            -> www_pl.date_of_pl
    #   Trainees Placed   -> www_employment.date_of_job (On-job RECORDS, minus walkouts)
    #   Walkouts          -> www_walkout.walkout_date
    # No date filter => nothing here runs and the dashboard is unchanged.
    if date_from or date_to:
        def _win(v):
            d = _legacy_date(v)
            if d is None: return False
            if date_from and d < date_from: return False
            if date_to and d > date_to: return False
            return True
        def _geo_ok(r):
            if state_code and state_code not in (_legacy_text(r.get("state_code")), _legacy_text(r.get("state"))): return False
            if centre_code and centre_code != _legacy_text(r.get("centre")): return False
            if district_code and district_code != _legacy_text(r.get("district_code")): return False
            if wanted_status and lifecycle(r["enrollment_id"]) != wanted_status: return False
            return True
        geo_rows = [r for r in enrollments if _geo_ok(r)]
        geo_ids = {r["enrollment_id"] for r in geo_rows}
        # 2026-09-16: "Received LL" counts LL RECORDS (matching the LL list + DB), not
        # distinct trainees -- a trainee with >1 LL in the window (e.g. renewals) is
        # counted per LL. Other metrics keep their distinct-trainee basis.
        ll_recs = [r for r in ll_rows if r.get("enrollment_id") in geo_ids and _win(r.get("date_of_ll"))]
        ll_win  = {r["enrollment_id"] for r in ll_recs}
        pl_win  = geo_ids & {r["enrollment_id"] for r in pl_rows      if _win(r.get("date_of_pl"))}
        placed_win  = geo_ids & {r["enrollment_id"] for r in emp_rows
                                 if _legacy_text(r.get("current_status")).lower() == "on job" and _win(r.get("date_of_job"))}
        walkout_win = geo_ids & {r["enrollment_id"] for r in walkout_rows if _win(r.get("walkout_date"))}
        enrolled_win = {r["enrollment_id"] for r in geo_rows if _win(r.get("enrollment_date"))}
        # 2026-09-17: "Trainees Placed" counts ON-JOB EMPLOYMENT RECORDS in the window (a
        # trainee with two jobs counts twice), matching the Employment list. Trainees who
        # walked out in the window stay excluded.
        placed_recs = [r for r in emp_rows
                       if r.get("enrollment_id") in placed_win
                       and r.get("enrollment_id") not in walkout_win
                       and _legacy_text(r.get("current_status")).lower() == "on job"
                       and _win(r.get("date_of_job"))]
        # 2026-10-04: align the Employment by Status chart to the
        # 'Trainees on Job' KPI card. When a date window is applied,
        # the chart's 'On Job' bucket must equal kpi.placed (record
        # count of on-job employments in the window, excluding
        # walkouts). 'On Bench' uses the same geo+walkout+window
        # predicates but with non-'On Job' status.
        bench_recs = [r for r in emp_rows
                      if r.get("enrollment_id") in geo_ids
                      and r.get("enrollment_id") not in walkout_win
                      and _legacy_text(r.get("current_status")).lower() != "on job"
                      and _win(r.get("date_of_job"))]
        employment_counts = {}
        if placed_recs:
            employment_counts["On Job"]   = [r.get("enrollment_id") for r in placed_recs]
        if bench_recs:
            employment_counts["On Bench"] = [r.get("enrollment_id") for r in bench_recs]
        kpi["enrolled"]    = len(enrolled_win)
        kpi["received_ll"] = len(ll_recs)
        kpi["received_pl"] = len(pl_win)
        kpi["placed"]      = len(placed_recs)
        # 2026-10-13 (user ask): KPI walkouts = per-record Walkout-only
        # (excludes Employable + Walkin), matching the Walkout List with
        # the "Walkout" filter + the State-wise table column.
        _WO_EMP = {"After PL","Before Internal Sakha","After Internal Sakha",
                   "Before External Sakha","After External Sakha"}
        _wo_only = [r for r in walkout_rows
                      if r.get("enrollment_id") in geo_ids
                      and _win(r.get("walkout_date"))
                      and (r.get("walkout_stage") or "") not in _WO_EMP]
        kpi["walkouts"]    = len(_wo_only)
        _sg = {}
        _eid_skey = {}
        # 2026-10-05: 'State-wise Trainee Count' column semantics -- use
        # DISTINCT trainee counts for Placed / Walkout / Active so the
        # table agrees with the 'Trainee Status Distribution' chart.
        # Previously Placed summed placed_recs (record count), which
        # mixed with distinct-trainee totals/walkouts and could push
        # active negative (clamped to 0). The KPI card 'Trainees on Job'
        # keeps its record-count semantic (kpi.placed = len(placed_recs))
        # so it continues to match the Employment list row count.
        for r in geo_rows:
            eid = r["enrollment_id"]
            _state = _legacy_text(r.get("state")) or _legacy_text(r.get("state_code")) or "Unknown"
            _skey = _legacy_text(r.get("state_code")) or _state
            _eid_skey[eid] = _skey
            g = _sg.setdefault(_skey, {"state": _state, "state_code": _skey, "total": 0,
                                       "active": 0, "walkout": 0, "placed": 0, "got_ll": 0, "got_pl": 0})
            g["total"]   += int(eid in enrolled_win)
            g["got_pl"]  += int(eid in pl_win)
            pass  # 2026-10-13: walkout count is now per-record (filled after this loop)
            # 2026-10-05: distinct-trainee placed count. A trainee who
            # walked out in the window is NOT counted as placed (matches
            # the Trainees-on-Job filter: placed_win minus walkout_win).
            g["placed"]  += int(eid in placed_win and eid not in walkout_win)
        # 2026-10-13 (user ask): walkout column = per-record count of the
        # derived "Walkout" category (excludes Employable + Walkin).
        _WO_EMPLOYABLE = {"After PL","Before Internal Sakha","After Internal Sakha",
                           "Before External Sakha","After External Sakha"}
        for wr in walkout_rows:
            if not _win(wr.get("walkout_date")):
                continue
            if (wr.get("walkout_stage") or "") in _WO_EMPLOYABLE:
                continue   # Employable rows go in a separate bucket (not here)
            _sk = _eid_skey.get(wr.get("enrollment_id"))
            if _sk in _sg:
                _sg[_sk]["walkout"] += 1
        for r in ll_recs:
            _sk = _eid_skey.get(r.get("enrollment_id"))
            if _sk in _sg: _sg[_sk]["got_ll"] += 1
        for g in _sg.values():
            g["active"] = max(0, g["total"] - g["placed"] - g["walkout"])
        # 2026-10-05: chart 'Trainee Status Distribution' uses the same
        # distinct-trainee semantics as the state table so chart and
        # table agree, column by column. Previously status_counts was
        # built from lifecycle() all-time status which drifted from the
        # window-filtered KPIs / table.
        _placed_distinct = len(placed_win - walkout_win)
        status_counts["Placed"]  = _placed_distinct
        status_counts["Walkout"] = len(_wo_only)  # 2026-10-13: per-record Walkout-only (matches KPI + state table)
        status_counts["Active"]  = max(0, len(enrolled_win) - _placed_distinct - len(walkout_win))
        state_groups = _sg

    # 2026-09-24: per-centre Sakha (attempts + passed) for the new bar
    # chart replacing the pass/fail/pending donut. Each trainee counts
    # once per centre; a trainee w/o a centre lookup lands in "Unknown".
    # 2026-09-30: use the display NAME (not the resolved code) so the
    # Sakha pass-rate bar chart reads South Kolkata / North Kolkata
    # instead of S19347B3 / S19347B4.
    _centre_by_eid = {r["enrollment_id"]: (_legacy_text(r.get("centre_name")) or "Unknown")
                      for r in enrollments}
    def _sakha_bar(row_ids, pass_ids):
        # 2026-10-04: use allowed_geo (geo-scoped, date-agnostic) so
        # the Pass-Rate chart shows every centre the caller can see,
        # regardless of the duration filter.
        centres = {}
        for eid in (row_ids & allowed_geo):
            centre = _centre_by_eid.get(eid, "Unknown")
            item = centres.setdefault(centre, {"centre": centre, "attempts": 0, "passed": 0})
            item["attempts"] += 1
            if eid in pass_ids:
                item["passed"] += 1
        return sorted(centres.values(), key=lambda item: item["centre"])
    internal_sakha_by_centre = _sakha_bar(internal_ids, internal_passed)
    # External: any row present = attempted; pass_date present = passed.
    _external_pass_ids = {r["enrollment_id"] for r in external_rows if r.get("external_pass_date")}
    external_sakha_by_centre = _sakha_bar(external_ids, _external_pass_ids)

    return {
        "kpi": kpi,
        "by_state": sorted(state_groups.values(), key=lambda row: row["state"]),
        "internal_sakha_by_centre": internal_sakha_by_centre,
        "external_sakha_by_centre": external_sakha_by_centre,
        "by_age": sorted(age_groups.values(), key=lambda row: row["state"]),
        "by_caste": by_caste,
        "funnel_by_year": sorted(years.values(), key=lambda row: row["year"]),
        "by_tab": by_tab,
        "enrollment_trend": [{"ym": key, "n": trend[key]} for key in sorted(trend)[-12:]],
        "status_distribution": [{"status": key, "n": value} for key, value in status_counts.items()],
        "employment_status_dist": [{"status": key, "n": len(value)} for key, value in employment_counts.items()],
        "recent_activities": activities[:10],
    }


@router.get("-dashboard/income-buckets")
def www_dashboard_income_buckets(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    """2026-09-30: bucket www_enrollment.per_capita_income into 6
    bands for the Home dashboard's income-distribution chart. Same
    scoping and filter shape the main /www-dashboard endpoint uses."""
    state_code, district_code, centre_code = _scope.scope_geo(
        request, state_code, district_code, centre_code)
    # 2026-10-13 (user ask): match the "New Enrollments" KPI by excluding
    # Draft-status rows. Previously the PCI chart counted 4 extra Draft
    # enrollments the dashboard KPI skips, so totals didn't match.
    conds = ["e.deleted_at IS NULL",
             "NULLIF(TRIM(e.enrollment_no), '') IS NOT NULL",
             "COALESCE(e.status, 'Active') <> 'Draft'"]
    params = []
    if state_code:  conds.append("_gs.state_code = %s");   params.append(state_code)
    if centre_code: conds.append("(_gc.centre_code = %s OR " +
                                  _legacy.centre_expr('e.centre') + " = %s)")
    if centre_code: params.extend([centre_code, centre_code])
    if status:      conds.append("COALESCE(e.status, 'Active') = %s"); params.append(status)
    if date_from:   conds.append("e.enrollment_date >= %s"); params.append(date_from)
    if date_to:     conds.append("e.enrollment_date <= %s"); params.append(date_to)
    where = " AND ".join(conds)
    sql = (
        "WITH pcin AS ("
        "  SELECT CASE "
        "           WHEN e.per_capita_income IS NOT NULL AND e.per_capita_income > 0 THEN e.per_capita_income "
        "           WHEN e.monthly_family_income IS NOT NULL AND e.monthly_family_income > 0 "
        "                AND e.number_of_member_in_family IS NOT NULL AND e.number_of_member_in_family > 0 "
        "             THEN (e.monthly_family_income::numeric / e.number_of_member_in_family) "
        "           ELSE NULL "
        "         END AS pci "
        "    FROM mis_azad.www_enrollment e " + _legacy.geo_joins('e') +
        "   WHERE " + where +
        ") "
        "SELECT CASE "
        "         WHEN pci IS NULL       THEN 'Not Specified' "
        "         WHEN pci <= 1000       THEN '<1000' "
        "         WHEN pci <= 2000       THEN '1001-2000' "
        "         WHEN pci <= 3000       THEN '2001-3000' "
        "         WHEN pci <= 4000       THEN '3001-4000' "
        "         WHEN pci <= 5000       THEN '4001-5000' "
        "         ELSE '>5000' "
        "       END AS bucket, "
        "       COUNT(*) AS n "
        "  FROM pcin "
        " GROUP BY 1"
    )
    order = ['<1000', '1001-2000', '2001-3000', '3001-4000', '4001-5000', '>5000', 'Not Specified']
    with get_cursor() as cur:
        rows = _dashboard_rows(cur, sql, params) or []
    counts = {r['bucket']: int(r['n'] or 0) for r in rows}
    total = sum(counts.values()) or 0
    return {
        'buckets': [
            {'label': label,
             'count': counts.get(label, 0),
             'pct': round(100.0 * counts.get(label, 0) / total, 1) if total else 0}
            for label in order
        ],
        'total': total,
    }


@router.get("-dashboard")
def www_dashboard(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    """Dashboard data used by the WWW home page."""
    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    conditions = ["t.deleted_at IS NULL"]
    params = []
    if state_code:
        conditions.append("t.state_code = %s")
        params.append(state_code)
    if district_code:
        conditions.append("t.district_code = %s")
        params.append(district_code)
    if centre_code:
        conditions.append("t.centre_code = %s")
        params.append(centre_code)
    if status:
        conditions.append("t.status = %s")
        params.append("Walkout" if status == "Dropout" else status)
    if date_from:
        conditions.append("t.enrollment_date >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("t.enrollment_date <= %s")
        params.append(date_to)
    trainee_where = " AND ".join(conditions)

    with get_cursor() as cur:
        base = _dashboard_rows(
            cur,
            f"""
                SELECT COUNT(*) AS enrolled,
                       COUNT(DISTINCT t.state_code) AS states,
                       COUNT(DISTINCT t.centre_code) AS centres,
                       COUNT(*) FILTER (WHERE t.status = 'Placed') AS placed,
                       COUNT(*) FILTER (WHERE t.status = 'Walkout') AS walkouts
                FROM www_enrollment t
                WHERE {trainee_where}
            """,
            params,
        )
        base = base[0] if base else {}
        if int(base.get("enrolled") or 0) == 0:
            legacy = _legacy_www_dashboard(
                cur, state_code=state_code, centre_code=centre_code, status=status,
                date_from=date_from, date_to=date_to, district_code=district_code,
            )
            if legacy is not None:
                return legacy

        received_ll = _dashboard_count(
            cur, "www_learning_licenses", trainee_where, params, "AND x.deleted_at IS NULL"
        )
        received_pl = _dashboard_count(
            cur, "www_permanent_licenses", trainee_where, params, "AND x.deleted_at IS NULL"
        )
        employed = _dashboard_count(
            cur, "www_employment", trainee_where, params, "AND x.deleted_at IS NULL AND COALESCE(x.is_active, TRUE) = TRUE"
        )
        walkout_records = _dashboard_count(
            cur,
            "www_walkout",
            trainee_where,
            params,
            "AND x.deleted_at IS NULL AND COALESCE(x.is_active, TRUE) = TRUE AND COALESCE(x.status, 'Walkout') = 'Walkout'",
        )

        # States/Centres cards show programme coverage from the master tables
        # (www_states/www_centres), not distinct values among enrolled trainees.
        state_master_where = ["deleted_at IS NULL"]
        state_master_params = []
        if state_code:
            state_master_where.append("state_code = %s")
            state_master_params.append(state_code)
        centre_master_where = list(state_master_where)
        centre_master_params = list(state_master_params)
        if district_code:
            centre_master_where.append("district_code = %s")
            centre_master_params.append(district_code)
        if centre_code:
            centre_master_where.append("centre_code = %s")
            centre_master_params.append(centre_code)
        master_states = _dashboard_rows(
            cur,
            f"SELECT COUNT(*) AS n FROM central_states WHERE {' AND '.join(state_master_where)}",
            state_master_params,
        )
        master_centres = _dashboard_rows(
            cur,
            f"SELECT COUNT(*) AS n FROM central_centres WHERE {' AND '.join(centre_master_where)}",
            centre_master_params,
        )

        kpi = {
            "enrolled": int(base.get("enrolled") or 0),
            "received_ll": received_ll,
            "received_pl": received_pl,
            "placed": max(int(base.get("placed") or 0), employed),
            "walkouts": max(int(base.get("walkouts") or 0), walkout_records),
            "states": int(master_states[0]["n"] or 0) if master_states else 0,
            "centres": int(master_centres[0]["n"] or 0) if master_centres else 0,
        }

        by_state = _dashboard_rows(
            cur,
            f"""
                SELECT COALESCE(s.state_name, t.state_code, 'Unknown') AS state,
                       t.state_code,
                       COUNT(*) AS total,
                       COUNT(*) FILTER (
                         WHERE NOT EXISTS (SELECT 1 FROM www_walkout w
                                           WHERE w.trainee_id=t.id
                                             AND w.deleted_at IS NULL
                                             AND COALESCE(w.is_active,TRUE)=TRUE
                                             AND COALESCE(w.status,'Walkout')='Walkout')
                           AND NOT EXISTS (SELECT 1 FROM www_employment e
                                           WHERE e.trainee_id=t.id
                                             AND e.deleted_at IS NULL
                                             AND COALESCE(e.is_active,TRUE)=TRUE)
                       ) AS active,
                       COUNT(*) FILTER (
                         WHERE EXISTS (SELECT 1 FROM www_walkout w
                                       WHERE w.trainee_id=t.id
                                         AND w.deleted_at IS NULL
                                         AND COALESCE(w.is_active,TRUE)=TRUE
                                         AND COALESCE(w.status,'Walkout')='Walkout')
                       ) AS walkout,
                       COUNT(*) FILTER (
                         WHERE EXISTS (SELECT 1 FROM www_employment e
                                       WHERE e.trainee_id=t.id
                                         AND e.deleted_at IS NULL
                                         AND COALESCE(e.is_active,TRUE)=TRUE)
                       ) AS placed
                FROM www_enrollment t
                LEFT JOIN central_states s ON s.state_code = t.state_code
                WHERE {trainee_where}
                GROUP BY s.state_name, t.state_code
                ORDER BY state
            """,
            params,
        )
        state_map = {r["state_code"]: r for r in by_state}
        for row in by_state:
            row["got_ll"] = 0
            row["got_pl"] = 0
        for key, table in (("got_ll", "www_learning_licenses"), ("got_pl", "www_permanent_licenses")):
            grouped = _dashboard_rows(
                cur,
                f"""
                    SELECT t.state_code, COUNT(DISTINCT x.trainee_id) AS n
                    FROM {table} x JOIN www_enrollment t ON t.id = x.trainee_id
                    WHERE {trainee_where} AND x.deleted_at IS NULL
                    GROUP BY t.state_code
                """,
                params,
            )
            for row in grouped:
                if row["state_code"] in state_map:
                    state_map[row["state_code"]][key] = int(row["n"] or 0)

        by_age = _dashboard_rows(
            cur,
            f"""
                SELECT COALESCE(s.state_name, t.state_code, 'Unknown') AS state,
                       COUNT(*) FILTER (WHERE COALESCE(EXTRACT(YEAR FROM age(CURRENT_DATE, t.date_of_birth))::int,
                           t.age_at_enrollment) BETWEEN 18 AND 20) AS age_18_20,
                       COUNT(*) FILTER (WHERE COALESCE(EXTRACT(YEAR FROM age(CURRENT_DATE, t.date_of_birth))::int,
                           t.age_at_enrollment) BETWEEN 21 AND 25) AS age_21_25,
                       COUNT(*) FILTER (WHERE COALESCE(EXTRACT(YEAR FROM age(CURRENT_DATE, t.date_of_birth))::int,
                           t.age_at_enrollment) BETWEEN 26 AND 30) AS age_26_30,
                       COUNT(*) FILTER (WHERE COALESCE(EXTRACT(YEAR FROM age(CURRENT_DATE, t.date_of_birth))::int,
                           t.age_at_enrollment) BETWEEN 31 AND 35) AS age_31_35,
                       COUNT(*) FILTER (WHERE COALESCE(EXTRACT(YEAR FROM age(CURRENT_DATE, t.date_of_birth))::int,
                           t.age_at_enrollment) BETWEEN 36 AND 40) AS age_36_40,
                       COUNT(*) FILTER (WHERE COALESCE(EXTRACT(YEAR FROM age(CURRENT_DATE, t.date_of_birth))::int,
                           t.age_at_enrollment) > 40) AS above_40,
                       COUNT(*) FILTER (WHERE COALESCE(EXTRACT(YEAR FROM age(CURRENT_DATE, t.date_of_birth))::int,
                           t.age_at_enrollment) IS NULL) AS unknown_age
                FROM www_enrollment t
                LEFT JOIN central_states s ON s.state_code = t.state_code
                WHERE {trainee_where}
                GROUP BY s.state_name, t.state_code
                ORDER BY state
            """,
            params,
        )
        by_caste = _dashboard_rows(
            cur,
            f"""
                SELECT COALESCE(NULLIF(t.caste_category, ''), 'Not specified') AS caste,
                       COUNT(*) AS count,
                       ROUND(100.0 * COUNT(*) / NULLIF(SUM(COUNT(*)) OVER (), 0), 1) AS pct
                FROM www_enrollment t
                WHERE {trainee_where}
                GROUP BY COALESCE(NULLIF(t.caste_category, ''), 'Not specified')
                ORDER BY count DESC, caste
            """,
            params,
        )
        status_distribution = _dashboard_rows(
            cur,
            f"""
                SELECT COALESCE(NULLIF(t.status, ''), 'Unknown') AS status, COUNT(*) AS n
                FROM www_enrollment t WHERE {trainee_where}
                GROUP BY COALESCE(NULLIF(t.status, ''), 'Unknown') ORDER BY n DESC
            """,
            params,
        )
        enrollment_trend = _dashboard_rows(
            cur,
            f"""
                SELECT TO_CHAR(DATE_TRUNC('month', t.enrollment_date), 'YYYY-MM') AS ym, COUNT(*) AS n
                FROM www_enrollment t
                WHERE {trainee_where} AND t.enrollment_date IS NOT NULL
                GROUP BY DATE_TRUNC('month', t.enrollment_date)
                ORDER BY DATE_TRUNC('month', t.enrollment_date)
            """,
            params,
        )

        module_tables = {
            "induction": ("www_inductions", "AND x.deleted_at IS NULL"),
            "learning_license": ("www_learning_licenses", "AND x.deleted_at IS NULL"),
            "driving_practice": ("www_driving_practices", "AND x.deleted_at IS NULL"),
            "gbv": ("www_gbv", "AND x.deleted_at IS NULL"),
            "fat": ("www_fat", "AND x.deleted_at IS NULL"),
            "bks": ("www_bks", "AND x.deleted_at IS NULL"),
            "pl_stories": ("www_pl_stories", "AND x.deleted_at IS NULL"),
            "permanent_license": ("www_permanent_licenses", "AND x.deleted_at IS NULL"),
        }
        by_tab = {"enrollment": kpi["enrolled"]}
        for key, (table, extra) in module_tables.items():
            by_tab[key] = _dashboard_count(cur, table, trainee_where, params, extra)

        nt_conditions = ["n.deleted_at IS NULL"]
        nt_params = []
        if centre_code:
            nt_conditions.append("n.centre_code = %s")
            nt_params.append(centre_code)
        if state_code:
            nt_conditions.append("c.state_code = %s")
            nt_params.append(state_code)
        if date_from:
            nt_conditions.append("n.start_date >= %s")
            nt_params.append(date_from)
        if date_to:
            nt_conditions.append("n.start_date <= %s")
            nt_params.append(date_to)
        nt_rows = _dashboard_rows(
            cur,
            "SELECT COUNT(*) AS n FROM www_nt_trainings n "
            "LEFT JOIN central_centres c ON c.centre_code=n.centre_code WHERE " + " AND ".join(nt_conditions),
            nt_params,
        )
        by_tab["nt_training"] = int(nt_rows[0]["n"] or 0) if nt_rows else 0

        def pass_stats(table, column):
            rows = _dashboard_rows(
                cur,
                f"""
                    SELECT COUNT(DISTINCT x.trainee_id) AS total,
                           COUNT(DISTINCT x.trainee_id) FILTER (WHERE x.{column} IS TRUE) AS passed,
                           COUNT(DISTINCT x.trainee_id) FILTER (WHERE x.{column} IS FALSE) AS failed
                    FROM {table} x JOIN www_enrollment t ON t.id=x.trainee_id
                    WHERE {trainee_where} AND x.deleted_at IS NULL
                """,
                params,
            )
            row = rows[0] if rows else {}
            return {k: int(row.get(k) or 0) for k in ("total", "passed", "failed")}

        by_tab["internal_sakha"] = pass_stats("www_internal_sakha", "passed_internal")
        by_tab["external_sakha"] = pass_stats("www_external_sakha", "passed_external")
        by_tab["employment"] = {"total": employed}
        by_tab["walkout"] = {"total": walkout_records}

        employment_status_dist = _dashboard_rows(
            cur,
            f"""
                SELECT CASE WHEN x.current_status = 'On Job'
                            THEN 'On Job' ELSE 'On Bench' END AS status,
                       COUNT(DISTINCT x.trainee_id) AS n
                FROM www_employment x JOIN www_enrollment t ON t.id=x.trainee_id
                WHERE {trainee_where} AND x.deleted_at IS NULL AND COALESCE(x.is_active, TRUE)=TRUE
                GROUP BY CASE WHEN x.current_status = 'On Job'
                              THEN 'On Job' ELSE 'On Bench' END ORDER BY n DESC
            """,
            params,
        )

        funnel_by_year = _dashboard_rows(
            cur,
            f"""
                SELECT COALESCE(NULLIF(t.financial_year, ''),
                                TO_CHAR(t.enrollment_date, 'YYYY'), 'Unknown') AS year,
                       COUNT(*) AS enrolled,
                       COUNT(*) FILTER (
                         WHERE EXISTS (SELECT 1 FROM www_employment e
                                       WHERE e.trainee_id=t.id
                                         AND e.deleted_at IS NULL
                                         AND COALESCE(e.is_active,TRUE)=TRUE)
                       ) AS placed
                FROM www_enrollment t WHERE {trainee_where}
                GROUP BY COALESCE(NULLIF(t.financial_year, ''), TO_CHAR(t.enrollment_date, 'YYYY'), 'Unknown')
                ORDER BY year
            """,
            params,
        )
        year_map = {r["year"]: r for r in funnel_by_year}
        for row in funnel_by_year:
            row["got_ll"] = 0
            row["got_pl"] = 0
        for key, table in (("got_ll", "www_learning_licenses"), ("got_pl", "www_permanent_licenses")):
            grouped = _dashboard_rows(
                cur,
                f"""
                    SELECT COALESCE(NULLIF(t.financial_year, ''), TO_CHAR(t.enrollment_date, 'YYYY'), 'Unknown') AS year,
                           COUNT(DISTINCT x.trainee_id) AS n
                    FROM {table} x JOIN www_enrollment t ON t.id=x.trainee_id
                    WHERE {trainee_where} AND x.deleted_at IS NULL
                    GROUP BY COALESCE(NULLIF(t.financial_year, ''), TO_CHAR(t.enrollment_date, 'YYYY'), 'Unknown')
                """,
                params,
            )
            for row in grouped:
                if row["year"] in year_map:
                    year_map[row["year"]][key] = int(row["n"] or 0)

        recent_queries = [
            ("Enrollment", "www_trainees x", "x.id", "x.enrollment_date", "x.enrollment_no", "x.id=t.id"),
            ("Induction", "www_inductions x", "x.id", "x.start_date", "'Induction started'", "x.trainee_id=t.id AND x.deleted_at IS NULL"),
            ("Learning License", "www_learning_licenses x", "x.id", "x.date_of_ll", "x.ll_number", "x.trainee_id=t.id AND x.deleted_at IS NULL"),
            ("Permanent License", "www_permanent_licenses x", "x.id", "x.date_of_pl", "x.pl_number", "x.trainee_id=t.id AND x.deleted_at IS NULL"),
            ("Internal Sakha", "www_internal_sakha x", "x.id", "x.internal_pass_date", "CASE WHEN x.passed_internal THEN 'Passed' WHEN x.passed_internal IS FALSE THEN 'Failed' ELSE 'Pending' END", "x.trainee_id=t.id AND x.deleted_at IS NULL"),
            ("External Sakha", "www_external_sakha x", "x.id", "x.external_pass_date", "CASE WHEN x.passed_external THEN 'Passed' WHEN x.passed_external IS FALSE THEN 'Failed' ELSE 'Pending' END", "x.trainee_id=t.id AND x.deleted_at IS NULL"),
            ("Employment", "www_employment x", "x.id", "x.date_of_job", "COALESCE(x.current_status, x.type_of_job, 'Employment')", "x.trainee_id=t.id AND x.deleted_at IS NULL AND COALESCE(x.is_active, TRUE)=TRUE"),
            ("Walkout", "www_walkout x", "x.id", "x.walkout_date", "COALESCE(x.walkout_reason, 'Walkout')", "x.trainee_id=t.id AND x.deleted_at IS NULL AND COALESCE(x.is_active, TRUE)=TRUE"),
        ]
        recent_activities = []
        for module, source, rec_id, event_date, detail, join_condition in recent_queries:
            rows = _dashboard_rows(
                cur,
                f"""
                    SELECT %s AS module, t.name AS trainee, {event_date} AS event_date,
                           {detail} AS detail, {rec_id} AS rec_id
                    FROM {source} JOIN www_enrollment t ON {join_condition}
                    WHERE {trainee_where} AND {event_date} IS NOT NULL
                    ORDER BY {event_date} DESC LIMIT 10
                """,
                [module] + params,
            )
            recent_activities.extend(rows)

    def event_sort(row):
        value = row.get("event_date")
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        return datetime.min

    recent_activities.sort(key=event_sort, reverse=True)
    return {
        "kpi": kpi,
        "by_state": by_state,
        "by_age": by_age,
        "by_caste": by_caste,
        "funnel_by_year": funnel_by_year,
        "by_tab": by_tab,
        "enrollment_trend": enrollment_trend,
        "status_distribution": status_distribution,
        "employment_status_dist": employment_status_dist,
        "recent_activities": recent_activities[:10],
    }


@router.get("-dashboard/export")
def www_dashboard_export(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    """Excel export of WWW dashboard data, respecting the same filters as /api/www-dashboard.

    Multi-sheet .xlsx mirroring the FLP dashboard export style. Reuses the
    dashboard payload from ``www_dashboard(...)`` in-process so the numbers
    match the on-screen KPIs and charts exactly.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from fastapi.responses import StreamingResponse
    import io as _io

    data = www_dashboard(
        request=request, state_code=state_code, district_code=district_code, centre_code=centre_code, status=status,
        date_from=date_from, date_to=date_to,
    )
    kpi = data.get("kpi") or {}
    by_state = data.get("by_state") or []
    by_age = data.get("by_age") or []
    by_caste = data.get("by_caste") or []
    funnel_by_year = data.get("funnel_by_year") or []
    by_tab = data.get("by_tab") or {}
    employment_status_dist = data.get("employment_status_dist") or []
    recent_activities = data.get("recent_activities") or []
    # 2026-08-12: the dashboard renders these two as charts but the export
    # left them out, so the workbook covered six of the eight panels.
    enrollment_trend = data.get("enrollment_trend") or []
    status_distribution = data.get("status_distribution") or []

    wb = Workbook()
    header_fill = PatternFill(start_color="732269", end_color="732269", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    center_align = Alignment(horizontal="center", vertical="center")

    def _style_header(ws, ncols):
        for col_idx in range(1, ncols + 1):
            c = ws.cell(row=1, column=col_idx)
            c.fill = header_fill
            c.font = header_font
            c.alignment = center_align
        ws.freeze_panes = "A2"

    def _autosize(ws, headers):
        for col_idx, h in enumerate(headers, start=1):
            letter = ws.cell(row=1, column=col_idx).column_letter
            ws.column_dimensions[letter].width = max(15, len(str(h)) + 4)

    def _as_int(v):
        try:
            return int(v or 0)
        except (TypeError, ValueError):
            return 0

    # Sheet 1: KPIs
    ws = wb.active
    ws.title = "KPIs"
    hdrs = ["Metric", "Value"]
    ws.append(hdrs); _style_header(ws, len(hdrs))
    ws.append(["Enrolled",    _as_int(kpi.get("enrolled"))])
    ws.append(["Received LL", _as_int(kpi.get("received_ll"))])
    ws.append(["Received PL", _as_int(kpi.get("received_pl"))])
    ws.append(["Placed",      _as_int(kpi.get("placed"))])
    ws.append(["Walkouts",    _as_int(kpi.get("walkouts"))])
    ws.append(["States",      _as_int(kpi.get("states"))])
    ws.append(["Centres",     _as_int(kpi.get("centres"))])
    _autosize(ws, hdrs)

    # Sheet 2: By State
    ws = wb.create_sheet("By State")
    hdrs = ["State", "Total", "Active", "Walkout", "Placed", "Got LL", "Got PL"]
    ws.append(hdrs); _style_header(ws, len(hdrs))
    for r in by_state:
        ws.append([
            r.get("state") or "",
            _as_int(r.get("total")),
            _as_int(r.get("active")),
            _as_int(r.get("walkout")),
            _as_int(r.get("placed")),
            _as_int(r.get("got_ll")),
            _as_int(r.get("got_pl")),
        ])
    _autosize(ws, hdrs)

    # Sheet 3: By Age Band
    ws = wb.create_sheet("By Age Band")
    hdrs = ["State", "18-20", "21-25", "25+", "Unknown"]
    ws.append(hdrs); _style_header(ws, len(hdrs))
    for r in by_age:
        ws.append([
            r.get("state") or "",
            _as_int(r.get("age_18_20")),
            _as_int(r.get("age_21_25")),
            _as_int(r.get("above_25")),
            _as_int(r.get("unknown_age")),
        ])
    _autosize(ws, hdrs)

    # Sheet 4: By Caste
    ws = wb.create_sheet("By Caste")
    hdrs = ["Caste", "Count", "%"]
    ws.append(hdrs); _style_header(ws, len(hdrs))
    for r in by_caste:
        pct = r.get("pct")
        try:
            pct_val = float(pct) if pct is not None else 0.0
        except (TypeError, ValueError):
            pct_val = 0.0
        ws.append([
            r.get("caste") or "",
            _as_int(r.get("count")),
            pct_val,
        ])
    _autosize(ws, hdrs)

    # Sheet 5: By Tab
    ws = wb.create_sheet("By Tab")
    hdrs = ["Module", "Count"]
    ws.append(hdrs); _style_header(ws, len(hdrs))
    is_ = by_tab.get("internal_sakha") or {}
    es_ = by_tab.get("external_sakha") or {}
    emp_ = by_tab.get("employment") or {}
    wo_ = by_tab.get("walkout") or {}
    tab_rows = [
        ("Enrollment",              _as_int(by_tab.get("enrollment"))),
        ("Induction",               _as_int(by_tab.get("induction"))),
        ("Learning License",        _as_int(by_tab.get("learning_license"))),
        ("Driving Practice",        _as_int(by_tab.get("driving_practice"))),
        ("GBV",                     _as_int(by_tab.get("gbv"))),
        ("FAT",                     _as_int(by_tab.get("fat"))),
        ("BKS",                     _as_int(by_tab.get("bks"))),
        ("PL Stories",              _as_int(by_tab.get("pl_stories"))),
        ("Permanent License",       _as_int(by_tab.get("permanent_license"))),
        ("NT Training",             _as_int(by_tab.get("nt_training"))),
        ("Internal Sakha (Total)",  _as_int(is_.get("total"))),
        ("Internal Sakha (Passed)", _as_int(is_.get("passed"))),
        ("Internal Sakha (Failed)", _as_int(is_.get("failed"))),
        ("External Sakha (Total)",  _as_int(es_.get("total"))),
        ("External Sakha (Passed)", _as_int(es_.get("passed"))),
        ("External Sakha (Failed)", _as_int(es_.get("failed"))),
        ("Employment",              _as_int(emp_.get("total"))),
        ("Walkout",                 _as_int(wo_.get("total"))),
    ]
    for label, count in tab_rows:
        ws.append([label, count])
    _autosize(ws, hdrs)

    # Sheet 6: Trainees by Year
    ws = wb.create_sheet("Trainees by Year")
    hdrs = ["Year", "Enrolled", "Got LL", "Got PL", "Placed"]
    ws.append(hdrs); _style_header(ws, len(hdrs))
    for r in funnel_by_year:
        ws.append([
            r.get("year") or "",
            _as_int(r.get("enrolled")),
            _as_int(r.get("got_ll")),
            _as_int(r.get("got_pl")),
            _as_int(r.get("placed")),
        ])
    _autosize(ws, hdrs)

    # Sheet 7: Enrollment Trend
    ws = wb.create_sheet("Enrollment Trend")
    hdrs = ["Month", "Enrollments"]
    ws.append(hdrs); _style_header(ws, len(hdrs))
    for r in enrollment_trend:
        ws.append([r.get("ym") or "", _as_int(r.get("n"))])
    _autosize(ws, hdrs)

    # Sheet 8: Status Distribution
    ws = wb.create_sheet("Status Distribution")
    hdrs = ["Status", "Count"]
    ws.append(hdrs); _style_header(ws, len(hdrs))
    for r in status_distribution:
        ws.append([r.get("status") or "", _as_int(r.get("n"))])
    _autosize(ws, hdrs)

    # Sheet 9: Employment Status
    ws = wb.create_sheet("Employment Status")
    hdrs = ["Status", "Count"]
    ws.append(hdrs); _style_header(ws, len(hdrs))
    for r in employment_status_dist:
        ws.append([
            r.get("status") or "",
            _as_int(r.get("n")),
        ])
    _autosize(ws, hdrs)

    # Sheet 10: Recent Activities
    ws = wb.create_sheet("Recent Activities")
    hdrs = ["Module", "Trainee", "Event Date", "Detail"]
    ws.append(hdrs); _style_header(ws, len(hdrs))
    for r in recent_activities:
        ev = r.get("event_date")
        if isinstance(ev, datetime):
            ev_out = ev.strftime("%Y-%m-%d")
        elif isinstance(ev, date):
            ev_out = ev.isoformat()
        else:
            ev_out = str(ev or "")
        ws.append([
            r.get("module") or "",
            r.get("trainee") or "",
            ev_out,
            r.get("detail") or "",
        ])
    _autosize(ws, hdrs)

    buf = _io.BytesIO()
    wb.save(buf); buf.seek(0)
    fname = f"www_dashboard_{date.today().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )

@router.get("/export/excel")
def export_www_excel(stage: Optional[str] = None, training_pref: Optional[str] = None,
                     state: Optional[str] = None):
    """Export WWW pipeline as CSV."""
    with get_cursor() as cur:
        cur.execute("SELECT to_regclass('mis_azad.www_pipeline') AS t")
        if not cur.fetchone()["t"]:
            rows = []
        else:
            conditions = []
            params = []
            if stage:
                conditions.append("w.stage = %s"); params.append(stage)
            if training_pref:
                conditions.append("w.training_preference = %s"); params.append(training_pref)
            if state:
                conditions.append("ns.state_name = %s"); params.append(state)
            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
            cur.execute(f"""
                SELECT w.name, w.age, w.district, w.training_preference, w.stage,
                       s.survey_id_code, f.name as surveyed_by_flp_name
                FROM www_pipeline w
                LEFT JOIN surveys s ON w.survey_id = s.id
                LEFT JOIN flps f ON w.surveyed_by_flp_id = f.id
                LEFT JOIN central_districts nd ON f.district_code = nd.district_code
                LEFT JOIN central_states ns ON nd.state_code = ns.state_code
                {where} ORDER BY w.id
            """, params)
            rows = cur.fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Age', 'District', 'Training Preference', 'Stage', 'Survey ID', 'Surveyed By'])
    for r in rows:
        writer.writerow([r['name'] or '', r['age'] or '', r['district'] or '', r['training_preference'] or '',
                         r['stage'] or '', r['survey_id_code'] or '', r['surveyed_by_flp_name'] or ''])
    from datetime import date
    from export_helper import csv_string_to_xlsx_response
    return csv_string_to_xlsx_response(output.getvalue(), f"WWW_Pipeline_Export_{date.today().isoformat()}.xlsx")

@router.get("")
def list_www(stage: Optional[str] = None, training_pref: Optional[str] = None,
             state: Optional[str] = None, page: int = 1, limit: int = 10):
    offset = (page - 1) * limit
    with get_cursor() as cur:
        cur.execute("SELECT to_regclass('mis_azad.www_pipeline') AS t")
        if not cur.fetchone()["t"]:
            return {"total": 0, "page": page, "limit": limit, "data": []}

        conditions = []
        params = []
        if stage:
            conditions.append("w.stage = %s")
            params.append(stage)
        if training_pref:
            conditions.append("w.training_preference = %s")
            params.append(training_pref)
        if state:
            conditions.append("ns.state_name = %s")
            params.append(state)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        join_clause = """
            FROM www_pipeline w
            LEFT JOIN surveys s ON w.survey_id = s.id
            LEFT JOIN flps f ON w.surveyed_by_flp_id = f.id
            LEFT JOIN central_districts nd ON f.district_code = nd.district_code
            LEFT JOIN central_states ns ON nd.state_code = ns.state_code
        """

        cur.execute(f"SELECT COUNT(*) as total {join_clause} {where}", params)
        total = cur.fetchone()["total"]

        cur.execute(f"""
            SELECT w.id, w.name, w.age, w.district, w.training_preference, w.stage,
                   s.survey_id_code, f.name as surveyed_by_flp_name
            {join_clause}
            {where}
            ORDER BY w.id
            LIMIT %s OFFSET %s
        """, params + [limit, offset])
        rows = cur.fetchall()

    return {"total": total, "page": page, "limit": limit, "data": rows}


@router.put("/{www_id}/stage")
def update_stage(www_id: int, update: WWWStageUpdate):
    with get_cursor() as cur:
        cur.execute("SELECT to_regclass('mis_azad.www_pipeline') AS t")
        if not cur.fetchone()["t"]:
            raise HTTPException(status_code=404, detail="Pipeline entry not found")
        cur.execute("UPDATE www_pipeline SET stage = %s WHERE id = %s RETURNING id", (update.stage, www_id))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Pipeline entry not found")
        return {"message": f"Stage updated to {update.stage}"}


@router.get("/stats")
def www_stats():
    with get_cursor() as cur:
        cur.execute("SELECT to_regclass('mis_azad.www_pipeline') AS t")
        if not cur.fetchone()["t"]:
            return {"by_stage": {}, "by_preference": {}}
        cur.execute("""
            SELECT stage, COUNT(*) as count FROM www_pipeline GROUP BY stage
        """)
        by_stage = {r["stage"]: r["count"] for r in cur.fetchall()}

        cur.execute("""
            SELECT training_preference, COUNT(*) as count FROM www_pipeline
            WHERE training_preference IS NOT NULL GROUP BY training_preference
        """)
        by_pref = {r["training_preference"]: r["count"] for r in cur.fetchall()}

    return {"by_stage": by_stage, "by_preference": by_pref}