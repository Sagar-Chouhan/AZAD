"""Shared helpers for reading WWW data out of this deployment's legacy tables.

Background
----------
The WWW route modules were written against a normalized schema —
www_trainees plus one table per module (www_inductions,
www_learning_licenses, www_nt_trainings, ...).  That schema was never
created on this database.  What this database has instead is the
cleaned-up import of the programme's spreadsheets: www_induction,
www_ll, www_pl, www_ntt_training, www_sakha_internal,
www_sakha_external, www_gbv, www_bks, www_employment, www_walkout,
www_driving_practice and the 224-column www_enrollment.

Every route already had a "legacy fallback" branch guarded by
to_regclass(), but those branches named a third set of tables
(www_ll_form, www_non_technical_trainings, www_badlav_ka_safarnama, ...)
that do not exist here either, so both branches failed.  The fallbacks
now read the tables this database actually has, and this module holds
the parts they all need to agree on.

Geography
---------
The legacy tables store geography as plain names ("Tamil Nadu",
"Chennai") while the UI filters by the codes in www_states /
www_districts / www_centres ("S33", "S33632", "Chennai").  Note that
www_centres.centre_code *is* the centre name — the master table uses the
name as its key — so only state and district need a real lookup.

The centre column is also dirty: roughly a third of www_ll and
www_ntt_training spell it "Tamil Nadu-Chennai-Chennai" instead of
"Chennai".  CENTRE_EXPR takes the last dash-separated segment, which
normalises both spellings to the bare centre name.

Linking to the trainee
----------------------
Every module table now carries `enrollment_id`, a BIGINT FK to
www_enrollment(id) added by sql/072 and moved into position by sql/073.
Joins go through that column.  They used to go through the text
enrollment number with the punctuation stripped off both sides, because
the sheets disagree on it — www_enrollment writes "TN/CN/2026-27/33"
where www_induction writes "TN-CN/2026-27/33" — and the raw strings
matched nothing.  The text columns are still there, but they are display
data now, not the join key.
"""

# Last dash-separated segment of a dirty centre value, trimmed, NULL if empty.
import re


def centre_expr(col: str) -> str:
    return (
        "NULLIF(TRIM(REVERSE(SPLIT_PART(REVERSE(COALESCE(%s, '')), '-', 1))), '')"
        % col
    )


def geo_joins(alias: str, s="_gs", d="_gd", c="_gc") -> str:
    """LEFT JOINs that resolve a legacy row's name-based geography to codes.

    `alias` is the legacy table's alias; it must expose state / district /
    centre text columns.  District is matched inside the resolved state so
    same-named districts in different states cannot collide.
    """
    # 2026-09-07: resolve DISTRICT from the row's CENTRE (via www_centres,
    # the authoritative centre->district map) and fall back to the row's
    # district TEXT only when the centre does not resolve. Import data files
    # many rows under a phantom district (e.g. Kolkata trainees under
    # "Kolkata" though their centre North/South Kolkata belongs to North/
    # South 24 Parganas), which made district-scoped leads miss most of
    # their data. Centre-derived district keeps everyone consistent.
    return (
        f" LEFT JOIN mis_azad.central_states {s} "
        f"        ON {s}.state_name = NULLIF(TRIM({alias}.state), '') "
        f" LEFT JOIN mis_azad.central_centres {c} "
        # 2026-09-25: match either by centre_code OR centre_name. Live now
        # stores standard codes for the Kolkata centres in www_centres, but
        # legacy rows carry the NAME (e.g. 'North Kolkata') -> code-only
        # match failed and Location showed as ', West Bengal'.
        f"        ON ({c}.centre_code = {centre_expr(alias + '.centre')} OR {c}.centre_name = {centre_expr(alias + '.centre')}) "
        f" LEFT JOIN mis_azad.central_districts {d} "
        f"        ON {d}.district_code = COALESCE({c}.district_code, ("
        f"             SELECT _dt.district_code FROM mis_azad.central_districts _dt "
        f"              WHERE _dt.district_name = NULLIF(TRIM({alias}.district), '') "
        f"                AND ({s}.state_code IS NULL OR _dt.state_code = {s}.state_code) "
        f"              ORDER BY _dt.district_code LIMIT 1)) "
    )


def geo_cols(s="_gs", d="_gd", c="_gc") -> str:
    """SELECT-list fragment exposing the resolved codes under API names."""
    return (
        f"{s}.state_code AS state_code, "
        f"{s}.state_name AS state_name, "
        f"{d}.district_code AS district_code, "
        f"{d}.district_name AS district_name, "
        f"{c}.centre_code AS centre_code, "
        f"{c}.centre_name AS centre_name"
    )


def trainee_join(alias: str, e="_te") -> str:
    """LEFT JOIN onto www_enrollment through the module row's FK.

    sql/075 dropped the enrollment number each module table used to carry
    its own copy of, so the number the API reports now comes from the one
    place that owns it.  `alias` is the module table's alias.
    """
    return (
        f" LEFT JOIN mis_azad.www_enrollment {e} "
        f"        ON {e}.id = {alias}.enrollment_id "
    )


def enroll_no(e="_te") -> str:
    """SELECT-list fragment exposing the trainee's enrollment number.

    Aliased so the API field name is unchanged from when each module table
    stored the number itself; the frontend still reads `enrollment_no`.
    """
    return f"{e}.enrollment_no AS enrollment_no"


# 2026-09-15: a trainee's batch. www_enrollment.batch is blank for most trainees
# (esp. WB / North Delhi imports), so fall back to the most recent batch recorded in
# any sub-module keyed on enrollment id -- the same resolution the Enrollment List uses.
_BATCH_SUBS = [
    ("www_ll", "_bl", "batch_number"),
    ("www_induction", "_bi", "batch"),
    ("www_pl", "_bp", "batch_number"),
    ("www_driving_practice", "_bd", "batch"),
    ("www_employment", "_be", "batch_number"),
    ("www_sakha_internal", "_bsi", "batch_number"),
    ("www_sakha_external", "_bse", "batch_number"),
    ("www_walkout", "_bw", "batch"),
]


def batch_name(batch_col: str = "e.batch", enr_id: str = "e.id") -> str:
    """COALESCE expression resolving a trainee's batch by enrollment id.

    `batch_col` is the enrollment row's own batch column; `enr_id` is the
    enrollment-id expression the sub-module lookups correlate against.
    """
    parts = ["NULLIF(TRIM(%s), '')" % batch_col]
    for tbl, al, col in _BATCH_SUBS:
        parts.append(
            "(SELECT NULLIF(TRIM(%s.%s), '') FROM mis_azad.%s %s "
            "WHERE %s.enrollment_id=%s AND %s.deleted_at IS NULL "
            "AND NULLIF(TRIM(%s.%s), '') IS NOT NULL ORDER BY %s.id DESC LIMIT 1)"
            % (al, col, tbl, al, al, enr_id, al, al, col, al)
        )
    return "COALESCE(" + ", ".join(parts) + ")"


# Filter predicates. Kept next to the joins so a route never has to know
# whether a code or a name is on the disk side of the comparison.
def trainee_status(alias: str, e="_te") -> str:
    """SELECT fragment giving the trainee's current status.

    The import left www_enrollment.status as 'Active' on every row, so a
    walkout only exists in www_walkout.  A View page reading the enrollment
    column alone therefore called a trainee who had left "Active".  Take
    that trainee's most recent walkout row: still walked out -> 'Walkout';
    walked back in, or no row at all -> whatever the enrollment says.
    """
    return (
        f" COALESCE("
        f"   (SELECT CASE WHEN TRIM(_w.status) ILIKE 'walkout' THEN 'Walkout' END"
        f"      FROM mis_azad.www_walkout _w"
        f"     WHERE _w.enrollment_id = {alias}.enrollment_id"
        f"     ORDER BY _w.id DESC LIMIT 1),"
        f"   NULLIF(TRIM({e}.status), ''),"
        f"   'Active') AS trainee_status "
    )


def name_match(col: str) -> str:
    """Whitespace-tolerant, case-insensitive predicate for a name search.

    Pair with name_pattern().  The typed text used to be interpolated into
    the LIKE pattern verbatim, so a trailing space ("ashish ") searched for
    '%ashish %' and found nothing.  Collapsing runs of whitespace on both
    sides makes the box behave the way people actually type.
    """
    return f"regexp_replace(BTRIM({col}), '\\s+', ' ', 'g') ILIKE %s"


def name_pattern(name: str) -> str:
    """The %%...%% parameter that goes with name_match()."""
    return "%" + re.sub(r"\s+", " ", name or "").strip() + "%"


def state_filter(s="_gs") -> str:
    return f"{s}.state_code = %s"


def district_filter(d="_gd") -> str:
    return f"{d}.district_code = %s"


def centre_filter(alias: str) -> str:
    # 2026-09-26: canonicalise the row's centre to its www_centres CODE
    # (via code-or-name match) so a scoped user's centre_code compares
    # against the same shape on both sides. Live stores centre_code as
    # the NAME for Delhi/Chennai and as a canonical code (e.g.
    # S19347B4) for Kolkata, and the row's raw `centre` follows suit;
    # comparing raw name -> code missed North/South Kolkata scopes.
    return (
        f"COALESCE("
        f"  (SELECT centre_code FROM mis_azad.central_centres "
        f"    WHERE centre_code = {centre_expr(alias + '.centre')} "
        f"       OR centre_name = {centre_expr(alias + '.centre')} "
        f"    LIMIT 1), "
        f"  {centre_expr(alias + '.centre')}"
        f") = %s"
    )


def safe_date(col: str) -> str:
    """Cast a legacy text date column to date, yielding NULL on junk.

    Some of these columns are text and hold either "YYYY-MM-DD hh:mm:ss",
    an empty string, or a note the data-entry team typed instead of a date
    ("Came with LL").  A plain ::date cast errors out on the whole query
    when it hits one of those, so guard it with the pattern first.
    """
    # 2026-09-16: was ISO-only, which silently dropped DD-MM-YYYY text dates
    # (the majority of WWW legacy date columns) from every date-range filter.
    # Delegate to the exception-safe parser so DD-MM-YYYY / DD-MM-YYYY dates count
    # too; ::text keeps it valid whether the column is text or already a date.
    return "mis_azad.www_flex_date((%s)::text)" % col


def multi_select_array(col: str) -> str:
    """Turn a multi-select cell into a text[], preserving the sheet's order.

    The import joins multi-selects with a PIPE, not a comma:
    "Refrigerator|LPG|Motorcycle/Van".  This used to split on "," under the
    name csv_array(), which meant every multi-value answer came back as a
    single element — one long chip in the UI, and a form_of_violence filter
    in www_gbv that could never match a row with more than one value.  No
    multi-select column in this import contains a comma at all.
    """
    return (
        "(SELECT COALESCE(ARRAY_AGG(TRIM(_x) ORDER BY _o), ARRAY[]::text[]) "
        "   FROM unnest(string_to_array(COALESCE(%s, ''), '|')) "
        "        WITH ORDINALITY AS _t(_x, _o) "
        "  WHERE NULLIF(TRIM(_x), '') IS NOT NULL)" % col
    )


# ---------------------------------------------------------------------------
# Flow guard -- 2026-08-18 (Ashish)
#
# Picker me ye rok pehle se thi (www_trainees ka exclude_with / require_with),
# par wo sirf UI ki rok hai: purana khula page ya seedha API call usse bacha
# nikal sakta tha. Ye helper wahi niyam server par lagata hai, insert se
# pehle.
#
# Sirf wahi rishte rakhe hain jo data me sach hain -- Learning License ke
# bina Permanent Licence / Driving Practice / GBV / FAT ka ek bhi record nahi
# hai (259 trainees me 0 violation). Induction / Sakha / BKS jaise stage
# jaan-boojh kar zaroori nahi banaye: wo sab ke liye nahi hote.
_FLOW_TABLES = {
    "ll": ("www_ll", "Learning License"),
}


def assert_flow(cur, enrollment_id, requires=None, stage="ye record"):
    """Trainee is stage ke liye taiyar hai? Warna HTTPException.

    1. enrollment maujood ho aur Draft na ho
    2. `requires` bataye gaye pichhle stage ka record maujood ho
    """
    from fastapi import HTTPException

    def _v(row, key, idx):
        if row is None:
            return None
        return row.get(key) if hasattr(row, "get") else row[idx]

    if enrollment_id is None:
        raise HTTPException(400, "Pehle trainee chunein.")

    cur.execute(
        "SELECT COALESCE(NULLIF(TRIM(status), ''), 'Active') AS st, name "
        "FROM mis_azad.www_enrollment WHERE id = %s",
        (enrollment_id,))
    row = cur.fetchone()
    if row is None:
        raise HTTPException(404, "Is trainee ka enrollment nahi mila.")
    if str(_v(row, "st", 0) or "").strip().lower() == "draft":
        raise HTTPException(
            400,
            "Is trainee ka enrollment abhi Draft me hai. Pehle enrollment "
            "submit karein, tab %s add ho sakega." % stage)

    if requires:
        tbl, label = _FLOW_TABLES[requires]
        cur.execute(
            "SELECT 1 FROM mis_azad.%s WHERE enrollment_id = %%s LIMIT 1" % tbl,
            (enrollment_id,))
        if cur.fetchone() is None:
            nm = _v(row, "name", 1) or "is trainee"
            raise HTTPException(
                400,
                "%s add karne se pehle %s zaroori hai -- %s ka %s abhi nahi "
                "bana hai." % (stage, label, nm, label))


# ---------------------------------------------------------------------------
# Soft delete -- 2026-08-19 (Ashish)
#
# Import ki tables me pehle koi deleted_at nahi tha, isliye trainee ka delete
# 501 deta tha aur module ka delete row ko HAMESHA ke liye mita deta tha.
# 19 Aug ko saare www tables me deleted_at joda gaya; ab delete matlab
# "deleted_at bhar do", row DB me bachi rehti hai.
#
# Trainee (enrollment) delete par uske saare module records bhi mark hote hain
# -- Ashish ka chuna hua option (b) -- warna un tabs me bin-maalik data ghoomta
# rehta.  (table, FK column)
TRAINEE_CHILD_TABLES = (
    ("www_induction",                        "enrollment_id"),
    ("www_ll",                               "enrollment_id"),
    ("www_pl",                               "enrollment_id"),
    ("www_ntt_training",                     "enrollment_id"),
    ("www_nt_attendance",                    "trainee_id"),
    ("www_gbv",                              "enrollment_id"),
    ("www_financial_assistance_to_trainees", "enrollment_id"),
    ("www_driving_practice",                 "enrollment_id"),
    ("www_bks",                              "enrollment_id"),
    ("www_pl_stories",                       "enrollment_id"),
    ("www_sakha_internal",                   "enrollment_id"),
    ("www_sakha_external",                   "enrollment_id"),
    ("www_employment",                       "enrollment_id"),
    ("www_walkout",                          "enrollment_id"),
)


def soft_delete_trainee(cur, enrollment_id):
    """Enrollment aur uske saare module records ko deleted mark karo.

    Lautata hai: {"enrollment": 0/1, "children": {table: kitne}}.
    Pehle se deleted row dobara mark nahi hoti (deleted_at IS NULL ki shart).
    """
    cur.execute(
        "UPDATE mis_azad.www_enrollment SET deleted_at = NOW() "
        "WHERE id = %s AND deleted_at IS NULL RETURNING id",
        (enrollment_id,))
    hit = 1 if cur.fetchone() else 0

    kids = {}
    for tbl, fk in TRAINEE_CHILD_TABLES:
        cur.execute(
            "UPDATE mis_azad.%s SET deleted_at = NOW() "
            "WHERE %s = %%s AND deleted_at IS NULL" % (tbl, fk),
            (enrollment_id,))
        if cur.rowcount:
            kids[tbl] = cur.rowcount
    return {"enrollment": hit, "children": kids}


def table_exists(cur, name: str) -> bool:
    """True when the normalized table exists, i.e. skip the legacy branch."""
    cur.execute("SELECT to_regclass(%s) AS t", (f"mis_azad.{name}",))
    return cur.fetchone()["t"] is not None


def is_normalized(cur, name: str, marker: str = "trainee_id") -> bool:
    """True when `name` is the normalized table rather than the import.

    Four names collide: www_gbv, www_employment, www_walkout and
    www_pl_stories exist in both schemas, so to_regclass() cannot tell
    them apart and would send those routes down the normalized path
    against an import table.  The normalized versions all hang off
    www_trainees, so the presence of the FK column is the discriminator.
    """
    cur.execute(
        "SELECT 1 FROM information_schema.columns "
        " WHERE table_schema = 'mis_azad' AND table_name = %s AND column_name = %s",
        (name, marker),
    )
    return cur.fetchone() is not None
