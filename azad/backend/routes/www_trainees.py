"""WWW Trainees — full CRUD covering all 10 tabs of Add Trainee.

Phase 3 (2026-06-10) — created the basic profile shell.
Phase 2 backend (2026-06-11) — extended to cover tabs 2-10:
    Tab 2  Family               -> www_trainee_family_members
    Tab 3  Previous Employment  -> cols on www_trainees
    Tab 4  Financial Status     -> cols on www_trainees
    Tab 5  Housing & Asset Info -> cols + 2 child tables
    Tab 6  Disability Info      -> cols on www_trainees
    Tab 7  Org Association      -> cols on www_trainees
    Tab 8  GBV                  -> cols + 3 child tables
    Tab 9  Reference            -> 2 child tables
    Tab 10 Commitment           -> cols on www_trainees

Endpoint prefix: /api/www-trainees

Endpoints
---------
  POST   /                     create trainee + children in one tx
  GET    /                     list with filters + pagination
  GET    /{trainee_id}         read trainee + child collections
  PUT    /{trainee_id}         update trainee + replace children
  DELETE /{trainee_id}         soft delete (sets deleted_at)

Save Draft vs Submit
--------------------
The frontend Save Draft button posts the same payload with
status='Draft'.  Submit posts status='Active'.  Both flows use the
same POST/PUT — only the status string differs.  No validation gates
on Save Draft (partial records allowed).
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from pydantic import BaseModel, Field
from typing import Optional, List
import sys, os, uuid
import sys, os, uuid, re, secrets
from typing import Optional, List, Any
import sys, os, uuid, re, secrets, logging
from passlib.context import CryptContext
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from routes import _www_legacy as _legacy
from routes import _www_scope as _scope
from routes._www_list_sort import www_list_order
from config import UPLOAD_DIR, MAX_FILE_SIZE

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/www-trainees", tags=["WWW Trainees"])


# 2026-09-05: Commitment payments (full + multiple partial). Total commitment
# depends on training type: 2 Wheeler = 1500, 4 Wheeler = 3000. Each payment is a
# row in www_trainee_payment; Amount Paid = SUM(payment).
def _www_commit_total(enrollment_type):
    t = (enrollment_type or "").strip().lower()
    if "4" in t:
        return 3000
    if "2" in t:
        return 1500
    return 0


def _www_fmt_amt(x):
    try:
        xf = float(str(x).replace(",", ""))
        return str(int(xf)) if xf == int(xf) else str(xf)
    except Exception:
        return str(x)


def _www_enroll_paid_amount(paid_status, commit_amount, partial_amt, total):
    """Amount already paid at enrollment, from the legacy commitment columns.
    'Full' anywhere -> the full commitment; otherwise the numeric partial."""
    ps = (str(paid_status or "") + " " + str(commit_amount or "")).lower()
    try:
        pnum = float(str(partial_amt).replace(",", "")) if partial_amt not in (None, "") else 0.0
    except Exception:
        pnum = 0.0
    if "full" in ps:
        return float(total)
    if pnum > 0:
        return min(pnum, float(total)) if total > 0 else pnum
    return 0.0


# =============================================================================
# Pydantic models
# =============================================================================

class TraineeLanguage(BaseModel):
    language: str
    can_understand: bool = False
    can_speak: bool = False
    can_read: bool = False
    can_write: bool = False


class TraineeFamilyMember(BaseModel):
    member_name: Optional[str] = None
    relation: Optional[str] = None
    mobile_no: Optional[str] = None
    age: Optional[int] = None
    education: Optional[str] = None
    occupation: Optional[str] = None
    monthly_income: Optional[float] = None
    monthly_contribution: Optional[float] = None


class TraineeReference(BaseModel):
    ref_name: Optional[str] = None
    relation: Optional[str] = None
    contact_no: Optional[str] = None


class TraineeGbvSituation(BaseModel):
    situation: str
    violence_category: Optional[str] = None


class TraineeDocument(BaseModel):
    file_name: Optional[str] = None
    doc_type: Optional[str] = None
    file_path: Optional[str] = None
    uploaded_by: Optional[str] = None


class TraineeIn(BaseModel):
    # Optional — backend generates one if missing
    enrollment_no: Optional[str] = None
    photo_path: Optional[str] = None

    # Geography
    financial_year: Optional[str] = None
    batch_id: Optional[int] = None
    state_code: str
    district_code: str
    centre_code: str
    area_code: Optional[str] = None
    area_other: Optional[str] = None
    basti: Optional[str] = None

    # Identity
    name: str
    enrollment_date: Optional[str] = None       # ISO date "YYYY-MM-DD"
    enrollment_type: Optional[str] = None       # '2 Wheeler' | '4 Wheeler'
    date_of_birth: Optional[str] = None
    age_at_enrollment: Optional[int] = None
    blood_group: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    current_address: Optional[str] = None
    permanent_address: Optional[str] = None

    # Demographics
    caste_category: Optional[str] = None
    caste_other: Optional[str] = None
    religion: Optional[str] = None
    religion_other: Optional[str] = None
    gender: Optional[str] = None
    gender_other: Optional[str] = None
    marital_status: Optional[str] = None
    age_at_marriage: Optional[int] = None
    living_with: Optional[str] = None
    living_with_other: Optional[str] = None

    # Education
    education_qualification: Optional[str] = None
    education_other: Optional[str] = None
    still_studying: Optional[bool] = None
    studying_class: Optional[str] = None

    # Emergency contacts
    num_emergency_contacts: Optional[int] = 0
    emergency_contacts: List[str] = Field(default_factory=list)

    # Social media
    has_social_media: Optional[bool] = None
    social_platforms: List[str] = Field(default_factory=list)

    # Awareness
    how_known_azad: Optional[str] = None
    how_known_other: Optional[str] = None
    mobilization_activity: Optional[str] = None

    # Languages
    languages: List[TraineeLanguage] = Field(default_factory=list)

    # LL / PL
    came_with_lic_type: Optional[str] = None
    ll_date: Optional[str] = None
    ll_number: Optional[str] = None
    ll_attempts: Optional[int] = None
    pl_date: Optional[str] = None
    pl_number: Optional[str] = None
    pl_attempts: Optional[int] = None
    lic_type_changed: Optional[bool] = False

    # =================================================================
    # NEW PHASE 2 — tabs 2-10
    # =================================================================

    # Tab 2 - Family members (child table)
    family_members: List[TraineeFamilyMember] = Field(default_factory=list)

    # Tab 3 - Previous employment
    worked_before: Optional[str] = None
    prev_work_type: Optional[str] = None
    prev_work_other: Optional[str] = None
    prev_monthly_income: Optional[str] = None

    # Tab 4 - Financial status
    has_bank: Optional[str] = None
    bank_account_type: Optional[str] = None
    bank_name: Optional[str] = None
    bank_acct: Optional[str] = None
    has_savings: Optional[str] = None
    savings_where: Optional[str] = None
    has_debt: Optional[str] = None
    debt_amount: Optional[str] = None
    loan_source: Optional[str] = None
    loan_repay: Optional[str] = None

    # Tab 5 - Housing & assets
    house_ownership: Optional[str] = None
    house_own_detail: Optional[str] = None
    property_name_holder: Optional[str] = None
    property_name_other: Optional[str] = None
    property_paper_keeper: Optional[str] = None
    property_paper_other: Optional[str] = None
    house_type: Optional[str] = None
    has_mobile: Optional[str] = None
    is_smart_phone: Optional[str] = None
    phone_user: Optional[str] = None
    phone_usage: Optional[str] = None
    assets: List[str] = Field(default_factory=list)          # child table
    net_uses: List[str] = Field(default_factory=list)       # child table

    # Tab 6 - Disability info
    disability_in_house: Optional[str] = None
    disability_relation: Optional[str] = None
    disability_type: Optional[str] = None
    has_disability_cert: Optional[str] = None

    # Tab 7 - Org Association
    relative_in_azad: Optional[str] = None
    relative_name: Optional[str] = None
    relative_relation: Optional[str] = None
    relative_org: Optional[str] = None
    relative_designation: Optional[str] = None
    relative_years: Optional[float] = None

    # Tab 8 - GBV
    gbv_situations: List[TraineeGbvSituation] = Field(default_factory=list)
    violence_place: Optional[str] = None
    violence_by: Optional[str] = None
    violence_when: Optional[str] = None
    want_support: Optional[str] = None
    gbv_support_kinds: List[str] = Field(default_factory=list)
    support_other: Optional[str] = None
    housework_hours: Optional[str] = None
    encouraged_by: List[str] = Field(default_factory=list)

    # Tab 9 - Reference
    references: List[TraineeReference] = Field(default_factory=list)
    # 2026-08-10: documents are now managed via the dedicated
    # POST /{id}/documents (upload) and DELETE /{id}/documents/{doc_id}
    # endpoints. Default None so the main upsert does NOT wipe them on
    # every save. Old clients that still POST `documents: []` will hit
    # the guard in _upsert_trainee_children below and be ignored.
    documents: Optional[List[TraineeDocument]] = None

    # Tab 10 - Commitment
    commit_aware: Optional[str] = None
    commit_ready: Optional[str] = None
    commit_amount: Optional[str] = None
    commit_paid_status: Optional[str] = None
    commit_paid_amount: Optional[str] = None
    commit_partial_amt: Optional[str] = None

    status: Optional[str] = "Active"


# =============================================================================
# Helpers
# =============================================================================

# All scalar columns we write straight INTO www_enrollment.  Order matters —
# it must match the column list used in INSERT / UPDATE SQL.
_TRAINEE_COLS = (
    "enrollment_no", "photo_path",
    "financial_year", "batch_id",
    "state_code", "district_code", "centre_code", "area_code", "area_other", "basti",
    "name", "enrollment_date", "enrollment_type", "date_of_birth",
    "age_at_enrollment", "blood_group", "mobile", "email",
    "current_address", "permanent_address",
    "caste_category", "caste_other",
    "religion", "religion_other",
    "gender", "gender_other",
    "marital_status", "age_at_marriage",
    "living_with", "living_with_other",
    "education_qualification", "education_other",
    "still_studying", "studying_class",
    "num_emergency_contacts",
    "has_social_media",
    "how_known_azad", "mobilization_activity",
    "came_with_lic_type",
    "ll_date", "ll_number", "ll_attempts",
    "pl_date", "pl_number", "pl_attempts",
    # Phase 2 — Tab 3
    "worked_before", "prev_work_type", "prev_work_other", "prev_monthly_income",
    # Phase 2 — Tab 4
    "has_bank", "bank_account_type", "bank_name", "bank_acct",
    "has_savings", "savings_where",
    "has_debt", "debt_amount", "loan_source", "loan_repay",
    # Phase 2 — Tab 5 (scalars; assets + net_uses live in child tables)
    "house_ownership", "house_own_detail",
    "property_name_holder", "property_paper_keeper", "house_type",
    "has_mobile", "is_smart_phone", "phone_user", "phone_usage",
    # Phase 2 — Tab 6
    "disability_in_house", "disability_relation",
    "disability_type", "has_disability_cert",
    # Phase 2 — Tab 7
    "relative_in_azad", "relative_name", "relative_relation",
    "relative_org", "relative_designation", "relative_years",
    # Phase 2 — Tab 8 (scalars; multi-checks live in child tables)
    "violence_place", "violence_by", "violence_when",
    "want_support", "support_other", "housework_hours",
    # Phase 2 — Tab 10
    "commit_aware", "commit_ready", "commit_amount",
    "commit_paid_status", "commit_paid_amount", "commit_partial_amt",
    "status",
)


# The import repeats one family-member block ten times across www_enrollment.
# Block 1 is unsuffixed and spells two of its columns differently from the
# rest (`education` vs `educational_qualification_N`), and has no mobile
# column at all; blocks 2..10 are a clean _N suffix.
#
# 2026-08-12: each block also carries the two "Specify, if any other" answers
# that qualify its relation and education dropdowns, numbered in a strict
# pair per block: block 1 -> _6/_7, block 2 -> _8/_9, ... block 10 -> _24/_25.
# Without them a member whose relation was "Any other" rendered as the literal
# "Any other" (52 rows) instead of "Grandmother", and likewise for education.
def _legacy_family_columns(n: int) -> dict:
    other = {"relation_other": f"specify_if_any_other_{6 + 2 * (n - 1)}",
             "education_other": f"specify_if_any_other_{7 + 2 * (n - 1)}"}
    if n == 1:
        return {"member_name": "c_1_name_of_family_members", "relation": "relation",
                "mobile_no": "mobile_1", "age": "age", "education": "education",
                "occupation": "occupation", "monthly_contribution": "monthly_contribution",
                "monthly_income": "monthly_income", **other}
    return {"member_name": f"c_{n}_name_of_family_members", "relation": f"relation_{n}",
            "mobile_no": f"mobile_{n}", "age": f"age_{n}",
            "education": f"educational_qualification_{n}", "occupation": f"occupation_{n}",
            "monthly_contribution": f"monthly_contribution_{n}",
            "monthly_income": f"monthly_income_{n}", **other}


# =============================================================================
# LEGACY EXPORT LAYOUT — 2026-08-12
# The Enrollment "Export" button used to emit nine columns on this schema
# (enrollment no / name / mobile / type / date / status / state / district /
# centre) because the legacy branch of export_trainees_excel was a stub that
# predated the full www_enrollment import.  The normalized branch next to it
# already exported every field, so the two disagreed by 200-odd columns and
# the button silently dropped almost the whole record.
#
# The spec below names every column of the 223-column import, grouped into
# the sections the Add-Trainee form uses.  Family members and references are
# emitted inline (wide format) the same way the normalized export does them.
# Anything added to www_enrollment later is not in the spec, so it lands in
# the "Additional Fields" group instead of disappearing.
# =============================================================================

# Columns the import stores PIPE-joined ("Refrigerator|LPG|Motorcycle").
_LEGACY_MULTI_COLS = {
    "emergency_contact", "social_media_platforms", "language_known",
    "household_assets", "internet_uses", "gbv_situations",
    "type_of_violence_select_all_the_options_that_are_being",
    "support_kinds", "encourage_by",
    "who_discouraged_you_to_join_the_training_program",
    "trainee_photo_and_documents_aadhaar_pan_card",
}

_LEGACY_EXPORT_BASIC = [
    ("Enrollment No.",                            "enrollment_no"),
    ("Status",                                    "status"),
    ("Financial Year",                            "financial_year"),
    ("Batch",                                     "batch"),
    ("State",                                     "state"),
    ("District",                                  "district"),
    ("Centre",                                    "_centre_clean"),
    # The import spells the centre two ways ("Chennai" and
    # "Tamil Nadu-Chennai-Chennai"); "Centre" above is the normalised name,
    # this is what the sheet actually recorded.
    ("Centre (as recorded)",                      "centre"),
    ("Area",                                      "area"),
    ("Area (Specify, if any other)",              "specify_if_any_other"),
    ("Basti",                                     "basti"),
    ("Name",                                      "name"),
    ("Enrollment Date",                           "enrollment_date"),
    ("Enrollment Type",                           "type_of_enrollment"),
    ("Date of Birth",                             "date_of_birth"),
    ("Age at Enrollment",                         "age_at_enrollment"),
    ("Blood Group",                               "blood_group"),
    ("Mobile",                                    "mobile"),
    ("Email",                                     "email"),
    ("No. of Emergency Contacts",                 "no_of_emergency_contact"),
    ("Emergency Contacts",                        "emergency_contact"),
    ("Current Address",                           "current_address"),
    ("Permanent Address",                         "permanent_address"),
    ("Caste Category",                            "caste_category"),
    ("Caste (Specify, if any other)",             "specify_if_any_other_3"),
    ("Religion",                                  "religion"),
    ("Religion (Specify, if any other)",          "specify_if_any_other_4"),
    ("Gender",                                    "gender"),
    ("Category of Women (Specify, if any other)", "specify_if_any_other_category_of_women"),
    ("Marital Status",                            "marital_status"),
    ("Age at Marriage",                           "age_at_marriage"),
    ("Living With",                               "living_with"),
    ("Living With (Specify, if any other)",       "specify_if_any_other_place"),
    ("Education Qualification",                   "educational_qualification"),
    ("Education (Specify, if any other)",         "specify_if_any_other_5"),
    ("Still Studying",                            "still_studying"),
    ("Studying Class",                            "if_yes_in_which_class"),
    ("How Known About Azad",                      "how_know_about_azad"),
    ("Mobilization Activity",                     "mobilization_activity"),
    ("Mobilization (Specify, if any other)",      "specify_if_any_other_2"),
    ("Languages Known",                           "language_known"),
    ("Has Social Media",                          "has_social_media"),
    ("Social Media Platforms",                    "social_media_platforms"),
    ("Internet Uses",                             "internet_uses"),
    ("Came With License Type",                    "come_with_licence_type"),
    ("LL Date",                                   "ll_date"),
    ("LL Number",                                 "ll_number"),
    ("LL Attempts",                               "ll_attempts"),
    ("PL Date",                                   "pl_date"),
    ("PL Number",                                 "pl_number"),
    ("PL Attempts",                               "pl_attempts"),
]

# Per-family-member column order; the values are the keys
# _legacy_family_columns() returns.
_LEGACY_EXPORT_FAMILY_FIELDS = [
    ("Name of the Family Member",           "member_name"),
    ("Relation",                            "relation"),
    ("Relation (Specify, if any other)",    "relation_other"),
    ("Mobile",                              "mobile_no"),
    ("Age",                                 "age"),
    ("Education",                           "education"),
    ("Education (Specify, if any other)",   "education_other"),
    ("Occupation",                          "occupation"),
    ("Monthly Income",                      "monthly_income"),
    ("Monthly Contribution",                "monthly_contribution"),
]

_LEGACY_EXPORT_FAMILY_TOTALS = [
    ("Monthly Family Income", "monthly_family_income"),
    ("Per Capita Income",     "per_capita_income"),
]

# The import keeps its three reference slots as flat columns; _legacy has no
# relation column for them, so only name + contact exist.
_LEGACY_EXPORT_REFERENCE_SLOTS = [
    ("c_1_refrence_name", "relation_11", "contact_no"),
    ("c_2_refrence_name", "relation_12", "contact_no_2"),
    ("c_3_refrence_name", "relation_13", "contact_no_3"),
]

_LEGACY_EXPORT_SECTIONS = [
    ("Encouragement", [
        ("Encouraged By",   "encourage_by"),
        ("Discouraged By",  "who_discouraged_you_to_join_the_training_program"),
    ]),
    ("Previous Employment", [
        ("Worked Before",                        "worked_before"),
        ("Previous Work Type",                   "previous_work_type"),
        ("Previous Work (Specify, if any other)", "specify_if_any_other_26"),
        ("Previous Monthly Income",              "previous_monthly_income"),
    ]),
    ("Financial Status", [
        ("Has Bank Account",   "has_bank_account"),
        ("Bank Account Type",  "bank_account_type"),
        ("Bank Name",          "bank_name"),
        ("Bank Account No.",   "bank_account_number"),
        ("Has Savings",        "has_savings"),
        ("Savings Where",      "savings_where"),
        ("Has Debt",           "has_debit"),
        ("Debt Amount",        "debit_amount"),
        ("Loan Source",        "loan_source"),
        ("Loan Repayment",     "loan_re_payment"),
    ]),
    ("Housing & Assets", [
        ("House Ownership",                          "house_ownership"),
        ("House Ownership (Specify, if any other)",  "specify_if_any_other_place_2"),
        ("House Ownership Detail",                   "house_ownership_details"),
        ("Property Name Holder",                     "property_name_holder"),
        ("Property Name Holder (Specify, if any other)", "specify_if_any_other_27"),
        ("Property Paper Keeper",                    "property_paper_keeper"),
        ("Property Paper Keeper (Specify, if any other)", "specify_if_any_other_28"),
        ("House Type",                               "house_type"),
        ("Household Assets",                         "household_assets"),
        ("Has Mobile",                               "has_mobile"),
        ("Is Smart Phone",                           "is_smartphone"),
        ("Phone User",                               "phone_user"),
        ("Phone Usage",                              "phone_usage"),
    ]),
    ("Disability", [
        ("Disability In House",                       "disability_in_house"),
        ("Disability Relation",                       "disability_relation"),
        ("Disability Relation (Specify, if any other)", "specify_if_any_other_29"),
        ("Disability Type",                           "disability_type"),
        ("Has Disability Certificate",                "has_disability_certificate"),
    ]),
    ("Organization Association", [
        ("Relative In Azad / Sakha",                  "relative_in_azad_or_sakha"),
        ("Relative Name",                             "related_name"),
        ("Relative Relation",                         "relativev_relation"),
        ("Relative Relation (Specify, if any other)", "specify_if_any_other_30"),
        ("Relative Organisation",                     "relative_organization"),
        ("Relative Designation",                      "relative_designation"),
        ("Relative Designation (Specify, if any other)", "specify_if_any_other_31"),
        ("Relative Years",                            "relative_years"),
    ]),
    ("GBV", [
        ("GBV Situations",   "gbv_situations"),
        ("Type of Violence", "type_of_violence_select_all_the_options_that_are_being"),
        ("Violence Place",   "voilence_placed"),
        ("Violence By",      "if_inside_by_whom_state_relation_with_person"),
        ("Violence When",    "voilence_when"),
        ("Wants Support",    "want_support"),
        ("Support Kinds",    "support_kinds"),
        ("Support Other",    "support_other"),
        ("Housework Hours",  "housework_hours"),
    ]),
]

_LEGACY_EXPORT_COMMITMENT = [
    ("Commitment",                   "commitment"),
    ("Commitment Aware",             "commitment_aware"),
    ("Ready to Take Up Driving",     "i_am_fully_ready_to_take_up_driving_as_a_profession_and"),
    ("Commitment Ready",             "commitment_ready"),
    ("Commitment Amount",            "commitment_amount"),
    ("Commitment Paid Status",       "commitment_paid_status"),
    ("Commitment Partial Amount",    "commitment_partial_amount"),
]

_LEGACY_EXPORT_META = [
    ("Trainee Photo",       "trainee_image"),
    ("Documents",           "trainee_photo_and_documents_aadhaar_pan_card"),
    ("Created At",          "createdat"),
    ("Source Row ID",       "id"),
]


def _legacy_export_workbook(rows, filename):
    """Section-wise xlsx of full www_enrollment rows.

    `rows` are raw dicts straight off `SELECT e.*` plus the resolved geography
    columns, so every key present in the row reaches the file: the spec above
    orders and labels the known ones, and whatever is left over is appended
    under "Additional Fields".
    """
    from export_helper import multi_sheet_xlsx_response_v2

    def _cell(r, col):
        v = r.get(col)
        if v is None:
            return ""
        if col in _LEGACY_MULTI_COLS:
            parts = [p.strip() for p in str(v).split("|") if p.strip()]
            if col == "trainee_photo_and_documents_aadhaar_pan_card":
                # 2026-08-14: drop the metadata fragment the uploader appends
                # so the export still reads as a plain list of links.
                parts = [p.partition("#")[0] for p in parts]
            return "; ".join(parts)
        return v

    family_blocks = [_legacy_family_columns(n) for n in range(1, 11)]

    def _member_count(r):
        n = 0
        for i, block in enumerate(family_blocks, start=1):
            if str(r.get(block["member_name"]) or "").strip():
                n = i
        return n

    # Widest actually-used family block, floored at 5 like the normalized
    # export so the sheet's shape does not swing with the filter.
    max_family = min(max([_member_count(r) for r in rows] + [5]), 10)

    headers, group_headers = [], []

    def _add_group(title, spec):
        if not spec:
            return
        start = len(headers) + 1
        headers.extend(h for h, _c in spec)
        group_headers.append((start, len(headers), title))

    _add_group("Basic Profile", _LEGACY_EXPORT_BASIC)

    fam_start = len(headers) + 1
    headers.append("No. of Family Members")
    for i in range(1, max_family + 1):
        for label, _key in _LEGACY_EXPORT_FAMILY_FIELDS:
            headers.append(f"{i}. {label}" if _key == "member_name" else label)
    headers.extend(h for h, _c in _LEGACY_EXPORT_FAMILY_TOTALS)
    group_headers.append((fam_start, len(headers), "Family Members"))

    for title, spec in _LEGACY_EXPORT_SECTIONS:
        _add_group(title, spec)

    ref_start = len(headers) + 1
    for i in range(1, len(_LEGACY_EXPORT_REFERENCE_SLOTS) + 1):
        headers.extend([f"{i}. Reference Name", "Relation", "Contact No."])
    group_headers.append((ref_start, len(headers), "References"))

    _add_group("Commitment", _LEGACY_EXPORT_COMMITMENT)
    _add_group("Meta", _LEGACY_EXPORT_META)

    # Leftover check — any www_enrollment column the spec does not name.
    consumed = {c for _h, c in _LEGACY_EXPORT_BASIC}
    consumed.update(c for _t, spec in _LEGACY_EXPORT_SECTIONS for _h, c in spec)
    consumed.update(c for _h, c in _LEGACY_EXPORT_COMMITMENT)
    consumed.update(c for _h, c in _LEGACY_EXPORT_META)
    consumed.update(c for _h, c in _LEGACY_EXPORT_FAMILY_TOTALS)
    consumed.update(c for b in family_blocks for c in b.values() if c)
    consumed.update(c for slot in _LEGACY_EXPORT_REFERENCE_SLOTS for c in slot)
    consumed.update({"number_of_member_in_family",
                     # Resolved geography, already shown as names above.
                     "state_code", "district_code", "centre_code",
                     # 2026-08-26: tracking cols rendered as the Record Info group.
                     "created_by", "updated_by", "updated_at", "created_at", "deleted_at", "users_id"})
    extra_cols = [k for k in (rows[0].keys() if rows else []) if k not in consumed]
    if extra_cols:
        ex_start = len(headers) + 1
        headers.extend(k.replace("_", " ").title() for k in extra_cols)
        group_headers.append((ex_start, len(headers), "Additional Fields"))

    data_rows = []
    for r in rows:
        row = [_cell(r, c) for _h, c in _LEGACY_EXPORT_BASIC]
        row.append(_cell(r, "number_of_member_in_family"))
        for block in family_blocks[:max_family]:
            for _label, key in _LEGACY_EXPORT_FAMILY_FIELDS:
                col = block.get(key)
                row.append("" if not col else _cell(r, col))
        row.extend(_cell(r, c) for _h, c in _LEGACY_EXPORT_FAMILY_TOTALS)
        for _title, spec in _LEGACY_EXPORT_SECTIONS:
            row.extend(_cell(r, c) for _h, c in spec)
        for name_col, rel_col, contact_col in _LEGACY_EXPORT_REFERENCE_SLOTS:
            row.extend([_cell(r, name_col), _cell(r, rel_col), _cell(r, contact_col)])
        row.extend(_cell(r, c) for _h, c in _LEGACY_EXPORT_COMMITMENT)
        row.extend(_cell(r, c) for _h, c in _LEGACY_EXPORT_META)
        row.extend(_cell(r, c) for c in extra_cols)
        data_rows.append(row)

    # 2026-08-26: WWW tracking columns (Created By / Updated By / Updated At)
    from routes._www_export_tracking import WWW_TRACK_HEADERS as _WT_H, www_tracking_cells_inline as _wt_inline
    headers = list(headers) + _WT_H
    # 2026-09-19: Record Info banner over Created By + Updated By.
    group_headers = list(group_headers) + [(len(headers) - len(_WT_H) + 1, len(headers), "Record Info")]
    _wt_rows = _wt_inline(rows)
    for _wi in range(len(data_rows)):
        data_rows[_wi] = list(data_rows[_wi]) + (_wt_rows[_wi] if _wi < len(_wt_rows) else ["", ""])

    return multi_sheet_xlsx_response_v2(
        [{
            "name": "Enrollment",
            "group_headers": group_headers,
            "headers": headers,
            "rows": data_rows,
        }],
        filename,
    )


def _legacy_family_members(cur, trainee_id: int) -> list:
    """Unpivot the ten repeated blocks into the row shape the View screen wants.

    A block with no name is an unused slot, not an empty member, so it is
    dropped rather than rendered as a blank table row.
    """
    blocks = [_legacy_family_columns(n) for n in range(1, 11)]
    cols = [c for b in blocks for c in b.values() if c]
    cur.execute(
        "SELECT " + ", ".join(f'"{c}"' for c in cols) +
        " FROM mis_azad.www_enrollment WHERE id = %s",
        (trainee_id,),
    )
    row = cur.fetchone()
    if not row:
        return []
    members = []
    for b in blocks:
        name = (row.get(b["member_name"]) or "")
        if not str(name).strip():
            continue
        member = {
            field: (None if col is None else row.get(col))
            for field, col in b.items()
        }
        # "Any other" is the dropdown's placeholder, not the answer — the
        # answer sits in the paired Specify column.
        for field in ("relation", "education"):
            spec = str(member.pop(f"{field}_other", None) or "").strip()
            value = str(member.get(field) or "").strip()
            if spec and (not value or value.lower() == "any other"):
                member[field] = spec
        members.append(member)
    return members


def _legacy_documents(cell) -> list:
    """The enrolment documents for one trainee, stored as URLs in one cell.

    Shaped like the normalized www_trainee_documents rows the View screen
    renders, so docTable() needs no special case.  The sheet keeps only the
    links, so who uploaded them and when are not recoverable.

    2026-08-12: the cell holds a PIPE-joined list, not a single URL — 50 of
    the 167 trainees with documents have two to four.  Treating the whole
    cell as one link produced an href like "url1 |url2", which S3 answered
    with AccessDenied, and only the last file's name ever showed.
    """
    from urllib.parse import unquote, parse_qs
    docs = []
    for entry in str(cell or "").split("|"):
        entry = entry.strip()
        if not entry:
            continue
        # 2026-08-14: uploads made through the form now append their own
        # metadata as a URL fragment -- #n=<file name>&t=<doc type>&b=<who
        # uploaded>&d=<date>.  A fragment is never sent to the server when the
        # link is opened, so the file still resolves, and rows imported from
        # the sheet simply carry none and fall back to the old defaults.
        url, _, frag = entry.partition("#")
        meta = parse_qs(frag) if frag else {}

        def _m(key, _meta=meta):
            return ((_meta.get(key) or [""])[0]).strip() or None

        docs.append({
            # No document table on this schema, so no real key — the 1-based
            # position in the cell is what the delete endpoint addresses.
            "id": len(docs) + 1,
            "doc_type": _m("t") or "Photo / Aadhaar / PAN",
            "file_name": _m("n") or unquote(url.rsplit("/", 1)[-1]),
            "file_path": url,
            "uploaded_at": _m("d"),
            "uploaded_by": _m("b"),
        })
    return docs


def _legacy_references(cur, trainee_id: int) -> list:
    """Unpivot the three reference slots the import keeps as flat columns.

    Shaped like the normalized www_trainee_references rows so refTable()
    needs no special case.  The sheet has no relation column, so that stays
    None.  A slot with neither a name nor a number is unused and dropped.
    """
    slots = [
        ("c_1_refrence_name", "relation_11", "contact_no"),
        ("c_2_refrence_name", "relation_12", "contact_no_2"),
        ("c_3_refrence_name", "relation_13", "contact_no_3"),
    ]
    cols = [c for slot in slots for c in slot]
    cur.execute(
        "SELECT " + ", ".join(f'"{c}"' for c in cols) +
        " FROM mis_azad.www_enrollment WHERE id = %s",
        (trainee_id,),
    )
    row = cur.fetchone()
    if not row:
        return []
    refs = []
    for name_col, relation_col, contact_col in slots:
        name = str(row.get(name_col) or "").strip()
        relation = str(row.get(relation_col) or "").strip()
        contact = str(row.get(contact_col) or "").strip()
        if not name and not contact and not relation:
            continue
        refs.append({
            "ref_name": name or None,
            "relation": relation or None,
            "contact_no": contact or None,
        })
    return refs


# 2026-08-28: enrolment numbers use short state/centre codes (TN/CN/...)
# instead of full names. Map derived from existing enrolment numbers;
# unmapped names fall back to uppercase initials (multi-word) or the
# first two letters (single word).
_WWW_STATE_ABBR = {"delhi": "DL", "rajasthan": "RJ", "tamil nadu": "TN"}
_WWW_CENTRE_ABBR = {"chennai": "CN", "east delhi": "ED", "south delhi": "SD", "jaipur": "JP"}

def _www_enroll_abbr(name, mapping):
    if not name:
        return ""
    key = str(name).strip().lower()
    if key in mapping:
        return mapping[key]
    parts = [w for w in str(name).strip().split() if w]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return str(name).strip()[:2].upper()


# 2026-09-21: outlier-safe enrollment-number series -- see _www_series_next.
_WWW_SERIES_OUTLIER_GAP = 20
_WWW_SERIES_MIN_FOR_OUTLIER = 6
_WWW_ENROLL_NO_RE = r'^[A-Z0-9]+/[A-Z0-9]+/[0-9]{4}-[0-9]{2}/[0-9]+$'


def _www_series_next(seqs) -> int:
    """Next sequence number for ONE enrolment series.

    2026-09-21: replaces a plain MAX(seq)+1, which produced numbers like
    112 at a centre whose last real enrolment was 42. Legacy imports left
    rows such as DL/ND/2026-27/111 sitting above a series that really only
    reaches 39, so every later enrolment jumped past 100.

    A value counts as detached only when the series already has
    _WWW_SERIES_MIN_FOR_OUTLIER numbers in it AND the value is both more
    than double its predecessor AND more than _WWW_SERIES_OUTLIER_GAP
    above it. Whatever comes out is then walked forward past everything
    already used (including the outliers we stepped over), so this can
    never mint a number that already exists.
    """
    used = {int(s) for s in seqs if s is not None and int(s) > 0}
    if not used:
        return 1
    vals = sorted(used)
    # 2026-09-23: two triggers instead of one. The original rule
    #   `vals[-1] > 2 * vals[-2] AND gap > _WWW_SERIES_OUTLIER_GAP`
    # missed borderline cases -- e.g. DL/ND/2026-27 real max 56 + import
    # outlier 111: 111 > 2*56 is 111 > 112 which is FALSE, so the outlier
    # stayed and every new enrolment jumped to 112, 113, ... To catch
    # cases like this without over-flagging natural rapid growth, we OR
    # in a second trigger: the top-gap must be more than a small multiple
    # of the pack's median consecutive-gap. Series with genuine large
    # consecutive gaps (e.g. 10,20,30,40) won't hit either trigger.
    while len(vals) >= _WWW_SERIES_MIN_FOR_OUTLIER:
        top = vals[-1]
        prev = vals[-2]
        top_gap = top - prev
        if top_gap <= _WWW_SERIES_OUTLIER_GAP:
            break
        pack_gaps = [vals[i] - vals[i - 1] for i in range(1, len(vals) - 1)]
        median_pack_gap = (sorted(pack_gaps)[len(pack_gaps) // 2]
                           if pack_gaps else 1)
        if top > 2 * prev or top_gap > 3 * max(median_pack_gap, 1):
            vals.pop()
        else:
            break
    nxt = vals[-1] + 1
    while nxt in used:
        nxt += 1
    return nxt


def _generate_enrollment_no(cur, body: TraineeIn) -> str:
    """Format: {state_abbr}/{centre_abbr}/{financial_year}/{NN}.

    2026-09-21: filter by exact prefix (state_abbr/centre_abbr/FY/) so
    sibling series (e.g. DL/ND vs DL/ND3) do not inherit each other's
    high-water mark, and delegate the next-number pick to
    _www_series_next so a single detached import value cannot inflate
    every subsequent enrolment.

    2026-09-30: two silent-fallback fixes for mobile-synced payloads.
      * Centre abbr used to abbreviate the CODE directly, which for a
        code like 'S19347B3' fell through to 'S1'. We now resolve the
        code to a centre NAME via central_centres (fallback www_centres,
        then the original code) and abbreviate the NAME.
      * financial_year defaulted to '0000' when the payload had none.
        We now derive from body.enrollment_date, then today's date.
    """
    from datetime import date as _date
    def _fy_from(d):
        if isinstance(d, str):
            try: d = _date.fromisoformat(d[:10])
            except Exception: return None
        if not d: return None
        y = d.year; m = d.month
        start_y = y if m >= 4 else y - 1
        return f"{start_y}-{str(start_y + 1)[-2:]}"
    fy = body.financial_year
    if not fy or str(fy).strip() in ('', '0000'):
        fy = _fy_from(getattr(body, 'enrollment_date', None)) or _fy_from(_date.today()) or "0000"
    cur.execute(
        "SELECT state_name FROM central_states WHERE state_code = %s LIMIT 1",
        (body.state_code,),
    )
    row = cur.fetchone()
    state_label = (row and row["state_name"]) or body.state_code
    # 2026-09-30: prefer the centre NAME for the abbreviation. If the
    # payload's centre_code isn't a friendly two-letter code, look up
    # the display name from central_centres / www_centres so the abbr
    # matches what other enrolments at that centre already use.
    centre_label = body.centre_code
    try:
        cur.execute(
            "SELECT centre_name FROM mis_azad.central_centres WHERE centre_code = %s LIMIT 1",
            (body.centre_code,),
        )
        _cr = cur.fetchone()
        if not _cr:
            cur.execute(
                "SELECT centre_name FROM mis_azad.central_centres WHERE centre_code = %s LIMIT 1",
                (body.centre_code,),
            )
            _cr = cur.fetchone()
        if _cr and _cr.get("centre_name"):
            centre_label = _cr["centre_name"]
    except Exception:
        pass
    prefix = (f"{_www_enroll_abbr(state_label, _WWW_STATE_ABBR)}"
              f"/{_www_enroll_abbr(centre_label, _WWW_CENTRE_ABBR)}")
    # The trailing slash keeps DL/ND from also matching DL/ND3.
    # 2026-10-01: include the financial year in the LIKE prefix so the
    # series does NOT pool across FYs (prior FY max would otherwise
    # push current FY next past the real high-water mark).
    like = f"{prefix}/{fy}/%"

    # 2026-10-01: match ONLY on the LIKE prefix + regex. The prefix is
    # computed from state_abbr/centre_abbr/FY (the exact bytes we are
    # about to write), so any row sharing it is in the same series by
    # definition. The old centre_code/financial_year filters compared
    # a client-sent code to the stored NAME and compared stored text
    # against possibly-empty FY, both of which could mismatch and
    # cause zero prior rows -> next=1 every time at that centre.
    if _legacy.table_exists(cur, "www_trainees"):
        cur.execute(
            "SELECT CAST(SPLIT_PART(enrollment_no, '/', 4) AS int) AS seq "
            "FROM www_enrollment "
            "WHERE enrollment_no LIKE %s AND enrollment_no ~ %s",
            (like, _WWW_ENROLL_NO_RE),
        )
    else:
        cur.execute(
            "SELECT CAST(SPLIT_PART(enrollment_no, '/', 4) AS int) AS seq "
            "FROM mis_azad.www_enrollment "
            "WHERE enrollment_no LIKE %s AND enrollment_no ~ %s",
            (like, _WWW_ENROLL_NO_RE),
        )
    nxt = _www_series_next([r["seq"] for r in cur.fetchall()])
    return f"{prefix}/{fy}/{nxt:02d}"


def _replace_children(cur, trainee_id: int, body: TraineeIn) -> None:
    """Wipe + reinsert every child table for this trainee."""

    # ---- 2026-08-01: three Specify-If-other texts (child table because the
    # app role cannot ALTER the postgres-owned www_trainees) ----
    cur.execute(
        "INSERT INTO www_trainee_other_texts "
        "  (trainee_id, how_known_other, property_name_other, property_paper_other) "
        "VALUES (%s, %s, %s, %s) "
        "ON CONFLICT (trainee_id) DO UPDATE SET "
        "  how_known_other = EXCLUDED.how_known_other, "
        "  property_name_other = EXCLUDED.property_name_other, "
        "  property_paper_other = EXCLUDED.property_paper_other",
        (trainee_id, body.how_known_other, body.property_name_other,
         body.property_paper_other),
    )

    # ---- Emergency contacts (existing) ----
    cur.execute("DELETE FROM www_trainee_emergency_contacts WHERE trainee_id = %s", (trainee_id,))
    for i, num in enumerate(body.emergency_contacts or [], start=1):
        num = (num or "").strip()
        if not num: continue
        cur.execute(
            "INSERT INTO www_trainee_emergency_contacts (trainee_id, seq, contact_no) "
            "VALUES (%s, %s, %s)",
            (trainee_id, i, num),
        )

    # ---- Social platforms (existing) ----
    cur.execute("DELETE FROM www_trainee_social_platforms WHERE trainee_id = %s", (trainee_id,))
    for p in set(body.social_platforms or []):
        p = (p or "").strip()
        if not p: continue
        cur.execute(
            "INSERT INTO www_trainee_social_platforms (trainee_id, platform) "
            "VALUES (%s, %s)",
            (trainee_id, p),
        )

    # ---- Languages (existing) ----
    cur.execute("DELETE FROM www_trainee_languages WHERE trainee_id = %s", (trainee_id,))
    for lang in (body.languages or []):
        if not lang.language: continue
        if not (lang.can_understand or lang.can_speak or lang.can_read or lang.can_write):
            continue
        cur.execute(
            "INSERT INTO www_trainee_languages "
            "(trainee_id, language, can_understand, can_speak, can_read, can_write) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (trainee_id, lang.language,
             bool(lang.can_understand), bool(lang.can_speak),
             bool(lang.can_read), bool(lang.can_write)),
        )

    # ---- PHASE 2: Family members (Tab 2) ----
    cur.execute("DELETE FROM www_trainee_family_members WHERE trainee_id = %s", (trainee_id,))
    for i, fm in enumerate(body.family_members or [], start=1):
        # Skip totally empty rows
        if not any([fm.member_name, fm.relation, fm.mobile_no, fm.age,
                    fm.education, fm.occupation,
                    fm.monthly_income, fm.monthly_contribution]):
            continue
        cur.execute(
            "INSERT INTO www_trainee_family_members "
            "(trainee_id, seq, member_name, relation, mobile_no, age, "
            " education, occupation, monthly_income, monthly_contribution) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (trainee_id, i,
             fm.member_name, fm.relation, fm.mobile_no, fm.age,
             fm.education, fm.occupation,
             fm.monthly_income, fm.monthly_contribution),
        )

    # ---- PHASE 2: Assets (Tab 5) ----
    cur.execute("DELETE FROM www_trainee_assets WHERE trainee_id = %s", (trainee_id,))
    for a in set(body.assets or []):
        a = (a or "").strip()
        if not a: continue
        cur.execute(
            "INSERT INTO www_trainee_assets (trainee_id, asset) "
            "VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (trainee_id, a),
        )

    # ---- PHASE 2: Net uses (Tab 5) ----
    cur.execute("DELETE FROM www_trainee_net_uses WHERE trainee_id = %s", (trainee_id,))
    for n in set(body.net_uses or []):
        n = (n or "").strip()
        if not n: continue
        cur.execute(
            "INSERT INTO www_trainee_net_uses (trainee_id, net_use) "
            "VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (trainee_id, n),
        )

    # ---- PHASE 2: GBV situations (Tab 8) ----
    cur.execute("DELETE FROM www_trainee_gbv_situations WHERE trainee_id = %s", (trainee_id,))
    for s in (body.gbv_situations or []):
        if not s.situation: continue
        cur.execute(
            "INSERT INTO www_trainee_gbv_situations "
            "(trainee_id, situation, violence_category) VALUES (%s, %s, %s) "
            "ON CONFLICT DO NOTHING",
            (trainee_id, s.situation, s.violence_category),
        )

    # ---- PHASE 2: GBV support kinds (Tab 8) ----
    cur.execute("DELETE FROM www_trainee_gbv_support_kinds WHERE trainee_id = %s", (trainee_id,))
    for k in set(body.gbv_support_kinds or []):
        k = (k or "").strip()
        if not k: continue
        cur.execute(
            "INSERT INTO www_trainee_gbv_support_kinds (trainee_id, support_kind) "
            "VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (trainee_id, k),
        )

    # ---- PHASE 2: Encouraged-by (Tab 8) ----
    cur.execute("DELETE FROM www_trainee_encouraged_by WHERE trainee_id = %s", (trainee_id,))
    for e in set(body.encouraged_by or []):
        e = (e or "").strip()
        if not e: continue
        cur.execute(
            "INSERT INTO www_trainee_encouraged_by (trainee_id, encourager) "
            "VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (trainee_id, e),
        )

    # ---- PHASE 2: References (Tab 9) ----
    cur.execute("DELETE FROM www_trainee_references WHERE trainee_id = %s", (trainee_id,))
    for i, r in enumerate(body.references or [], start=1):
        if not any([r.ref_name, r.relation, r.contact_no]): continue
        cur.execute(
            "INSERT INTO www_trainee_references "
            "(trainee_id, seq, ref_name, relation, contact_no) "
            "VALUES (%s, %s, %s, %s, %s)",
            (trainee_id, i, r.ref_name, r.relation, r.contact_no),
        )

    # ---- PHASE 2: Documents (Tab 9) ----
    # 2026-08-10: documents now have their own upload/delete endpoints
    # (POST /{id}/documents, DELETE /{id}/documents/{doc_id}), which own
    # the file binary and the DB row together. The main upsert must NOT
    # touch this table unless the caller explicitly sent a documents
    # payload with real content. Guard: skip entirely when None; also
    # skip when it's an empty list (silent-drop the safe default that
    # the old frontend sent) so that reopening an Edit page never wipes
    # previously uploaded files.
    if body.documents is not None and len(body.documents) > 0:
        # 2026-08-10: reject any entry that has no real file_path. This
        # blocks stale-client sends where the OLD collector shipped
        # {file_name, doc_type} metadata only — which produced orphan
        # rows in www_trainee_documents that had no file behind them
        # (the View screen then showed a dash instead of an eye icon).
        # Real docs must come in via POST /{id}/documents, which sets
        # file_path to a /uploads/ URL.
        real = [d for d in body.documents if (d.file_path or "").strip()]
        if real:
            cur.execute("DELETE FROM www_trainee_documents WHERE trainee_id = %s", (trainee_id,))
            for d in real:
                cur.execute(
                    "INSERT INTO www_trainee_documents "
                    "(trainee_id, file_name, doc_type, file_path, uploaded_by) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (trainee_id, d.file_name, d.doc_type, d.file_path, d.uploaded_by),
                )


# =============================================================================
# LEGACY WRITE SUPPORT — 2026-08-13
# This deployment has no normalized www_trainees; www_enrollment is the trainee
# master. The maps below are the exact inverse of the legacy SELECT in
# get_trainee(), so a field written here is read back by that same SELECT.
#
# Five API fields have no column in the import and are silently not stored:
#   batch_id, num_emergency_contacts, how_known_other, came_with_lic_type,
#   commit_paid_amount
# and the LL/PL prefill fields (ll_*, pl_*) live in www_ll / www_pl, which the
# Add-LL and Add-PL screens own — a trainee save must not touch them.
# =============================================================================
_ENR_SCALARS = {
    "enrollment_no": "enrollment_no", "photo_path": "trainee_image",
    "financial_year": "financial_year", "basti": "basti", "name": "name",
    "enrollment_date": "enrollment_date", "enrollment_type": "type_of_enrollment",
    "date_of_birth": "date_of_birth", "age_at_enrollment": "age_at_enrollment",
    "blood_group": "blood_group", "mobile": "mobile", "email": "email",
    "current_address": "current_address", "permanent_address": "permanent_address",
    "caste_category": "caste_category", "caste_other": "specify_if_any_other_3",
    "religion": "religion", "religion_other": "specify_if_any_other_4",
    "gender": "gender", "gender_other": "specify_if_any_other_category_of_women",
    "marital_status": "marital_status", "age_at_marriage": "age_at_marriage",
    "living_with": "living_with", "living_with_other": "specify_if_any_other_place",
    "education_qualification": "educational_qualification",
    "education_other": "specify_if_any_other_5",
    "still_studying": "still_studying", "studying_class": "if_yes_in_which_class",
    "how_known_azad": "how_know_about_azad",
    "mobilization_activity": "mobilization_activity",
    "mobilization_other": "specify_if_any_other_2",
    "area_code": "area", "area_other": "specify_if_any_other", "status": "status",
    "has_social_media": "has_social_media", "housework_hours": "housework_hours",
    "worked_before": "worked_before", "prev_work_type": "previous_work_type",
    "prev_work_other": "specify_if_any_other_26",
    "prev_monthly_income": "previous_monthly_income",
    "has_bank": "has_bank_account", "bank_account_type": "bank_account_type",
    "bank_name": "bank_name", "bank_acct": "bank_account_number",
    "has_savings": "has_savings", "savings_where": "savings_where",
    "has_debt": "has_debit", "debt_amount": "debit_amount",
    "loan_source": "loan_source", "loan_repay": "loan_re_payment",
    "house_ownership": "house_ownership",
    "house_own_detail": "house_ownership_details", "house_type": "house_type",
    "property_name_holder": "property_name_holder",
    "property_paper_keeper": "property_paper_keeper",
    "property_name_other": "specify_if_any_other_27",
    "property_paper_other": "specify_if_any_other_28",
    "has_mobile": "has_mobile", "is_smart_phone": "is_smartphone",
    "phone_user": "phone_user", "phone_usage": "phone_usage",
    "disability_in_house": "disability_in_house",
    "disability_relation": "disability_relation",
    "disability_type": "disability_type",
    "has_disability_cert": "has_disability_certificate",
    "relative_in_azad": "relative_in_azad_or_sakha",
    "relative_name": "related_name", "relative_relation": "relativev_relation",
    "relative_relation_other": "specify_if_any_other_30",
    "relative_org": "relative_organization",
    "relative_designation": "relative_designation",
    "relative_years": "relative_years",
    "violence_place": "voilence_placed",
    "violence_by": "if_inside_by_whom_state_relation_with_person",
    "violence_when": "voilence_when", "want_support": "want_support",
    "support_other": "support_other",
    "commit_aware": "commitment_aware", "commit_ready": "commitment_ready",
    "commit_amount": "commitment_amount",
    "commit_paid_status": "commitment_paid_status",
    "commit_partial_amt": "commitment_partial_amount",
    "commit_ready_driving": "i_am_fully_ready_to_take_up_driving_as_a_profession_and",
    "family_member_count": "number_of_member_in_family",
    "family_monthly_income": "monthly_family_income",
    "family_per_capita_income": "per_capita_income",
}

# Multi-selects are PIPE-joined cells — see _www_legacy.multi_select_array,
# which is what reads them back. Comma would break every one of them.
_ENR_MULTIS = {
    "emergency_contacts": "emergency_contact",
    "social_platforms": "social_media_platforms",
    "assets": "household_assets",
    "net_uses": "internet_uses",
    "gbv_support_kinds": "support_kinds",
    "encouraged_by": "encourage_by",
    "discouraged_by": "who_discouraged_you_to_join_the_training_program",
    "violence_types": "type_of_violence_select_all_the_options_that_are_being",
}

_ENR_REF_SLOTS = [("c_1_refrence_name", "relation_11", "contact_no"),
                  ("c_2_refrence_name", "relation_12", "contact_no_2"),
                  ("c_3_refrence_name", "relation_13", "contact_no_3")]

_ENR_MAX_FAMILY = 10
_ENR_MAX_REFS = len(_ENR_REF_SLOTS)


def _enr_pipe(values):
    """Join a multi-select back into the cell shape the reader expects."""
    out = []
    for v in values or []:
        if v is None:
            continue
        s = str(v).strip()
        if s:
            out.append(s)
    return "|".join(out) or None


def _enr_geo(cur, body):
    """The import stores geography as names; the API speaks codes."""
    vals = {}
    cur.execute("SELECT state_name FROM mis_azad.central_states WHERE state_code = %s",
                (body.state_code,))
    r = cur.fetchone()
    vals["state"] = (r["state_name"] if r else None) or body.state_code
    cur.execute("SELECT district_name FROM mis_azad.central_districts "
                "WHERE district_code = %s", (body.district_code,))
    r = cur.fetchone()
    vals["district"] = (r["district_name"] if r else None) or body.district_code
    # 2026-09-30: centre now stores the NAME too, mirroring state /
    # district above. Previously the raw code (e.g. 'S19347B3') got
    # written, which broke the enrollment_no centre-abbr fallback and
    # made the NT attendance roster miss same-centre trainees whose
    # centre was stored as the name. Fallback chain: www_centres ->
    # central_centres -> raw code.
    _cname = None
    try:
        cur.execute("SELECT centre_name FROM mis_azad.central_centres WHERE centre_code = %s",
                    (body.centre_code,))
        _cr = cur.fetchone()
        if _cr and _cr.get("centre_name"):
            _cname = _cr["centre_name"]
        else:
            cur.execute("SELECT centre_name FROM mis_azad.central_centres WHERE centre_code = %s",
                        (body.centre_code,))
            _cr = cur.fetchone()
            if _cr and _cr.get("centre_name"):
                _cname = _cr["centre_name"]
    except Exception:
        _cname = None
    vals["centre"] = _cname or body.centre_code
    return vals


def _enr_payload(cur, body):
    """Every www_enrollment column this trainee save writes, as {col: value}."""
    out = {}
    for field, col in _ENR_SCALARS.items():
        out[col] = getattr(body, field, None)
    out.update(_enr_geo(cur, body))

    # 2026-08-14: the Batch dropdown sends a www_master_batches id while the
    # import keeps the batch as free text, so batch_id used to be dropped on
    # save and the View page showed "-".  Write the master's name.  When no
    # batch is chosen the column is left out of the payload entirely, so an
    # edit cannot wipe a batch the import already carries (the sheet holds
    # plain numbers like "4" that have no master row to select).
    if getattr(body, "batch_id", None):
        cur.execute("SELECT name FROM mis_azad.www_master_batches WHERE id = %s",
                    (body.batch_id,))
        _b = cur.fetchone()
        if _b and _b.get("name"):
            out["batch"] = _b["name"]

    # 2026-08-14: the Full-payment amount (commit_paid_amount) has no column
    # of its own in the import, so it used to be dropped on save.  Store it in
    # commitment_partial_amount instead -- the form's Full / Partial branches
    # clear each other's input, so at most one of the two amounts arrives, and
    # commitment_paid_status says which one this is.  A typed Partial amount
    # still wins if both ever show up.
    if out.get("commitment_partial_amount") in (None, ""):
        _amt = str(getattr(body, "commit_paid_amount", None) or "").strip()
        if _amt:
            out["commitment_partial_amount"] = _amt
        elif str(getattr(body, "commit_paid_status", None) or "").strip() == "Full":
            # 2026-08-14 (v2 form): the Yes/No -> Full/Partial cascade has no
            # amount input on the Full branch, so a Full edit arrives
            # amount-less -- leave any stored amount untouched rather than
            # nulling it.
            out.pop("commitment_partial_amount", None)

    for field, col in _ENR_MULTIS.items():
        out[col] = _enr_pipe(getattr(body, field, None))

    # Objects, not plain strings: keep the part the reader surfaces.
    out["language_known"] = _enr_pipe(
        [getattr(l, "language", None) for l in (body.languages or [])])
    out["gbv_situations"] = _enr_pipe(
        [getattr(s, "situation", None) for s in (body.gbv_situations or [])])

    # Family: blocks 1..10, same columns _legacy_family_members() reads.
    members = list(body.family_members or [])[:_ENR_MAX_FAMILY]
    for n in range(1, _ENR_MAX_FAMILY + 1):
        cols = _legacy_family_columns(n)
        m = members[n - 1] if n <= len(members) else None
        for api_key, col in cols.items():
            if not col:
                continue          # block 1 has no mobile column
            out[col] = getattr(m, api_key, None) if m else None

    # References: three flat slots. 2026-08-28: the relation the form
    # collects now persists to relation_11/12/13 (was silently dropped).
    refs = list(body.references or [])[:_ENR_MAX_REFS]
    for i, (name_col, relation_col, contact_col) in enumerate(_ENR_REF_SLOTS):
        r = refs[i] if i < len(refs) else None
        out[name_col] = getattr(r, "ref_name", None) if r else None
        out[relation_col] = getattr(r, "relation", None) if r else None
        out[contact_col] = getattr(r, "contact_no", None) if r else None

    # Documents: one pipe-joined cell of URLs (doc_type / uploader are lost).
    #
    # 2026-08-14: this used to be written unconditionally.  Since 2026-08-10
    # the form no longer sends documents in the trainee payload -- they go
    # through POST /{id}/documents -- so `body.documents` is None on every
    # save and the cell was being NULLed each time, deleting the URL of every
    # file that endpoint had just stored.  The files stayed on disk, which is
    # why View and Edit showed nothing after a save.  Only write the cell when
    # the caller actually sent documents; the normalized branch in
    # _replace_children() already guards the same way.
    if body.documents:
        out["trainee_photo_and_documents_aadhaar_pan_card"] = _enr_pipe(
            [getattr(d, "file_path", None) for d in body.documents])
    return out


def _enr_doc_urls(cur, trainee_id):
    """The URLs currently in the import's single document cell, or None."""
    cur.execute("SELECT trainee_photo_and_documents_aadhaar_pan_card AS c "
                "FROM mis_azad.www_enrollment WHERE id = %s", (trainee_id,))
    row = cur.fetchone()
    if not row:
        return None
    return [u.strip() for u in str(row["c"] or "").split("|") if u.strip()]


def _enr_set_doc_urls(cur, trainee_id, urls):
    cur.execute("UPDATE mis_azad.www_enrollment "
                "SET trainee_photo_and_documents_aadhaar_pan_card = %s "
                "WHERE id = %s", ("|".join(urls) or None, trainee_id))


def _auto_assign_llpl(cur, trainee_id, body):
    """2026-08-31: When the Add-Trainee "came with LL/PL" fields are filled,
    create the matching www_ll / www_pl record so the trainee shows in the LL/PL
    lists and drops off the Add-LL / Add-PL trainee picker. Idempotent — skips
    when a record already exists for this enrollment."""
    ll_date = getattr(body, "ll_date", None)
    ll_number = getattr(body, "ll_number", None)
    if str(ll_date or "").strip() or str(ll_number or "").strip():
        cur.execute(
            "SELECT 1 FROM mis_azad.www_ll WHERE enrollment_id=%s AND deleted_at IS NULL LIMIT 1",
            (trainee_id,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO mis_azad.www_ll "
                "    (enrollment_id, name, mobile_number, type_of_enrollment, "
                "     state, district, centre, batch_number, "
                "     date_of_ll, ll_number, duration_in_days, "
                "     attempts_taken_to_clear_ll, module_done, "
                "     module_start_date, module_end_date) "
                "SELECT e.id, e.name, e.mobile, e.type_of_enrollment, "
                "       e.state, e.district, e.centre, e.batch, "
                "       %s, %s, %s, %s, %s, %s, %s "
                "FROM mis_azad.www_enrollment e WHERE e.id = %s",
                (str(ll_date) if ll_date else None, (ll_number or None), None,
                 getattr(body, "ll_attempts", None), "No", None, None, trainee_id),
            )
    pl_date = getattr(body, "pl_date", None)
    pl_number = getattr(body, "pl_number", None)
    if str(pl_date or "").strip() or str(pl_number or "").strip():
        cur.execute(
            "SELECT 1 FROM mis_azad.www_pl WHERE enrollment_id=%s AND deleted_at IS NULL LIMIT 1",
            (trainee_id,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO mis_azad.www_pl "
                "    (enrollment_id, name, type_of_enrollment, "
                "     state, district, centre, batch_number, date_of_birth, "
                "     date_of_pl, pl_number, duration_in_days, "
                "     attempts_taken_to_clear_pl) "
                "SELECT e.id, e.name, e.type_of_enrollment, "
                "       e.state, e.district, e.centre, e.batch, e.date_of_birth, "
                "       %s, %s, %s, %s "
                "FROM mis_azad.www_enrollment e WHERE e.id = %s",
                (str(pl_date) if pl_date else None, (pl_number or None), None,
                 getattr(body, "pl_attempts", None), trainee_id),
            )


def _sync_llpl_update(cur, trainee_id, body):
    """2026-09-14: On enrollment EDIT, push the edited 'came with LL/PL' values
    into the SAME www_ll / www_pl row the trainee View reads (latest by date,
    then id) so the change actually shows. www_enrollment has its own ll_/pl_
    columns but the View COALESCEs the module tables first, so _enr_update's
    write to the enrollment row alone is masked. _auto_assign_llpl (called just
    before) still creates a brand-new row; this updates an existing one. Rows are
    never removed when 'None' is chosen -- www_ll/www_pl are shared with the
    LL/PL modules. 2026-09-14: also REMOVE a licence when the user explicitly
    switched the 'Came with LL/PL' choice away from it (lic_type_changed) -- never
    on a plain open+save (the single radio clears the other type's fields on load,
    so empty fields alone are not intent)."""
    lic = str(getattr(body, "came_with_lic_type", "") or "").strip().upper()
    changed = bool(getattr(body, "lic_type_changed", False))
    ll_order = _legacy.safe_date("date_of_ll")
    ll_date = getattr(body, "ll_date", None)
    ll_number = getattr(body, "ll_number", None)
    ll_attempts = getattr(body, "ll_attempts", None)
    if str(ll_date or "").strip() or str(ll_number or "").strip():
        cur.execute(
            "SELECT id FROM mis_azad.www_ll WHERE enrollment_id = %s AND deleted_at IS NULL "
            "ORDER BY " + ll_order + " DESC NULLS LAST, id DESC LIMIT 1",
            (trainee_id,),
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE mis_azad.www_ll SET date_of_ll = %s, ll_number = %s, "
                "attempts_taken_to_clear_ll = %s WHERE id = %s",
                (str(ll_date) if ll_date else None, (ll_number or None), ll_attempts, row["id"]),
            )
    elif changed and lic != "LL":
        cur.execute(
            "UPDATE mis_azad.www_ll SET deleted_at = NOW() "
            "WHERE enrollment_id = %s AND deleted_at IS NULL",
            (trainee_id,),
        )
    pl_date = getattr(body, "pl_date", None)
    pl_number = getattr(body, "pl_number", None)
    pl_attempts = getattr(body, "pl_attempts", None)
    if str(pl_date or "").strip() or str(pl_number or "").strip():
        cur.execute(
            "SELECT id FROM mis_azad.www_pl WHERE enrollment_id = %s AND deleted_at IS NULL "
            "ORDER BY date_of_pl DESC NULLS LAST, id DESC LIMIT 1",
            (trainee_id,),
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE mis_azad.www_pl SET date_of_pl = %s, pl_number = %s, "
                "attempts_taken_to_clear_pl = %s WHERE id = %s",
                (str(pl_date) if pl_date else None, (pl_number or None), pl_attempts, row["id"]),
            )
    elif changed and lic != "PL":
        cur.execute(
            "UPDATE mis_azad.www_pl SET deleted_at = NOW() "
            "WHERE enrollment_id = %s AND deleted_at IS NULL",
            (trainee_id,),
        )


def _enr_insert(cur, body):
    payload = _enr_payload(cur, body)
    payload.pop("created_at", None)
    cols = list(payload.keys())
    # 2026-08-31: stamp created_at = NOW() so the Enrollment List can enforce
    # the 2-day Edit window on newly-added trainees.
    cur.execute(
        'INSERT INTO mis_azad.www_enrollment (%s, "created_at") VALUES (%s, NOW()) RETURNING id'
        % (", ".join('"%s"' % c for c in cols),
           ", ".join(["%s"] * len(cols))),
        [payload[c] for c in cols],
    )
    return cur.fetchone()["id"]


def _enr_update(cur, trainee_id, body):
    payload = _enr_payload(cur, body)
    # The photo travels via its own endpoint and is absent from the form
    # payload, so a None here must not wipe an uploaded image.
    if body.photo_path is None:
        payload.pop("trainee_image", None)
    cols = list(payload.keys())
    cur.execute(
        "UPDATE mis_azad.www_enrollment SET %s WHERE id = %%s"
        % ", ".join('"%s" = %%s' % c for c in cols),
        [payload[c] for c in cols] + [trainee_id],
    )
    return cur.rowcount


# 2026-08-13: create / edit / photo / documents now write to www_enrollment,
# so this is left for DELETE alone - the import has no deleted_at column and
# no soft-delete semantics, and hard-deleting an enrollment would orphan every
# module row that points at it by enrollment_id.
_LEGACY_WRITE_MSG = (
    "Deleting a trainee is not available on this deployment: trainees live in "
    "the www_enrollment import, which has no soft-delete column, and removing "
    "the row would orphan the induction, licence, BKS and other records linked "
    "to it. Mark the trainee as a Dropout from the Walkout screen instead."
)


def _reject_legacy_write(cur) -> None:
    """Refuse a trainee write when only the import table is available.

    Better a clear 501 than half-writing a 224-column enrollment row and
    silently dropping the tabs that have nowhere to go.
    """
    if not _legacy.table_exists(cur, "www_trainees"):
        raise HTTPException(status_code=501, detail=_LEGACY_WRITE_MSG)


def _legacy_ll_pl_joins(alias: str = "e") -> str:
    """LATERAL joins bringing an enrollment's latest LL and PL rows alongside.

    2026-08-12: the trainee record has always advertised ll_date / ll_number /
    ll_attempts / pl_date / pl_number / pl_attempts — TraineeCreate declares
    them and the Excel export prints a column for each — but www_enrollment
    has no such columns, so the legacy branch returned none of them.  Two
    screens autofill from those fields when you pick a trainee (Add Learning
    Licence and Add Permanent Licence), and both came up blank; the export's
    six columns were empty on every row.  www_ll and www_pl hold the data and
    both link back by enrollment_id.

    A trainee can have more than one row in either table (a renewal, a second
    attempt), so each join takes the most recent one — the same ordering the
    LL and PL lists use.  www_ll.date_of_ll is text on the import, hence
    safe_date(); www_pl.date_of_pl is already a date.
    """
    ll_date = _legacy.safe_date("_ll_src.date_of_ll")
    return (
        f" LEFT JOIN LATERAL ("
        f"     SELECT {ll_date} AS ll_date, "
        f"            NULLIF(TRIM(_ll_src.ll_number), '') AS ll_number, "
        f"            _ll_src.attempts_taken_to_clear_ll AS ll_attempts "
        f"       FROM mis_azad.www_ll _ll_src "
        f"      WHERE _ll_src.enrollment_id = {alias}.id "
        f"      ORDER BY {ll_date} DESC NULLS LAST, _ll_src.id DESC "
        f"      LIMIT 1 "
        f" ) _ll ON TRUE "
        f" LEFT JOIN LATERAL ("
        f"     SELECT _pl_src.date_of_pl AS pl_date, "
        f"            NULLIF(TRIM(_pl_src.pl_number), '') AS pl_number, "
        f"            _pl_src.attempts_taken_to_clear_pl AS pl_attempts "
        f"       FROM mis_azad.www_pl _pl_src "
        f"      WHERE _pl_src.enrollment_id = {alias}.id "
        f"      ORDER BY _pl_src.date_of_pl DESC NULLS LAST, _pl_src.id DESC "
        f"      LIMIT 1 "
        f" ) _pl ON TRUE "
    )


def _legacy_safe_int(col: str) -> str:
    """Cast a legacy text column to int, yielding NULL on anything else.

    Same idea as _www_legacy.safe_date(): www_enrollment stores the attempt
    counts as text, and a plain ::int would fail the whole query the day
    somebody types "2 times" into the sheet.
    """
    return ("CASE WHEN TRIM(COALESCE(%s, '')) ~ '^[0-9]+$' "
            "THEN TRIM(%s)::int END" % (col, col))


def _legacy_ll_pl_cols(alias: str = "e") -> str:
    """SELECT-list fragment exposing what _legacy_ll_pl_joins() brought in.

    www_enrollment has its own ll_/pl_ columns — all text, and empty on every
    row of this import — so the module tables win and the enrollment's copy is
    only a fallback.  Both fallbacks are parsed defensively: neither a junk
    date nor a non-numeric attempt count can break the query.
    """
    return (
        f"COALESCE(_ll.ll_date, {_legacy.safe_date(alias + '.ll_date')}) AS ll_date, "
        f"COALESCE(_ll.ll_number, NULLIF(TRIM({alias}.ll_number), '')) AS ll_number, "
        f"COALESCE(_ll.ll_attempts, {_legacy_safe_int(alias + '.ll_attempts')}) AS ll_attempts, "
        f"COALESCE(_pl.pl_date, {_legacy.safe_date(alias + '.pl_date')}) AS pl_date, "
        f"COALESCE(_pl.pl_number, NULLIF(TRIM({alias}.pl_number), '')) AS pl_number, "
        f"COALESCE(_pl.pl_attempts, {_legacy_safe_int(alias + '.pl_attempts')}) AS pl_attempts"
    )


def _legacy_trainee_select() -> str:
    """SELECT list mapping a www_enrollment row onto the trainee API shape.

    www_enrollment is the trainee master on deployments without the
    normalized www_trainees table: one row per enrollment, geography as
    plain names, and no batch master to join to.
    """
    return (
        "SELECT e.id, e.enrollment_no, e.name, e.mobile, "
        "       e.type_of_enrollment AS enrollment_type, "
        "       e.enrollment_date, "
        "       COALESCE(NULLIF(TRIM(e.status), ''), 'Active') AS status, "
        "       " + _legacy.geo_cols() + ", "
        "       NULLIF(TRIM(e.area), '') AS area_code, "
        "       (SELECT b.id FROM mis_azad.www_master_batches b "
        "         WHERE b.deleted_at IS NULL "
        "           AND b.name = NULLIF(TRIM(e.batch), '') "
        "         ORDER BY (b.centre_code = " + _legacy.centre_expr("e.centre") + ") DESC, b.id "
        "         LIMIT 1) AS batch_id, "
        "       e.state AS state_name, e.district AS district_name, "
        "       " + _legacy.centre_expr("e.centre") + " AS centre_name, "
        "       COALESCE(NULLIF(TRIM(e.batch), ''), "
        "         (SELECT NULLIF(TRIM(l.batch_number),'') FROM mis_azad.www_ll l WHERE l.enrollment_id=e.id AND l.deleted_at IS NULL AND NULLIF(TRIM(l.batch_number),'') IS NOT NULL ORDER BY l.id DESC LIMIT 1), "
        "         (SELECT NULLIF(TRIM(i.batch),'') FROM mis_azad.www_induction i WHERE i.enrollment_id=e.id AND i.deleted_at IS NULL AND NULLIF(TRIM(i.batch),'') IS NOT NULL ORDER BY i.id DESC LIMIT 1), "
        "         (SELECT NULLIF(TRIM(p.batch_number),'') FROM mis_azad.www_pl p WHERE p.enrollment_id=e.id AND p.deleted_at IS NULL AND NULLIF(TRIM(p.batch_number),'') IS NOT NULL ORDER BY p.id DESC LIMIT 1), "
        "         (SELECT NULLIF(TRIM(d.batch),'') FROM mis_azad.www_driving_practice d WHERE d.enrollment_id=e.id AND d.deleted_at IS NULL AND NULLIF(TRIM(d.batch),'') IS NOT NULL ORDER BY d.id DESC LIMIT 1), "
        "         (SELECT NULLIF(TRIM(em.batch_number),'') FROM mis_azad.www_employment em WHERE em.enrollment_id=e.id AND em.deleted_at IS NULL AND NULLIF(TRIM(em.batch_number),'') IS NOT NULL ORDER BY em.id DESC LIMIT 1), "
        "         (SELECT NULLIF(TRIM(si.batch_number),'') FROM mis_azad.www_sakha_internal si WHERE si.enrollment_id=e.id AND si.deleted_at IS NULL AND NULLIF(TRIM(si.batch_number),'') IS NOT NULL ORDER BY si.id DESC LIMIT 1), "
        "         (SELECT NULLIF(TRIM(se.batch_number),'') FROM mis_azad.www_sakha_external se WHERE se.enrollment_id=e.id AND se.deleted_at IS NULL AND NULLIF(TRIM(se.batch_number),'') IS NOT NULL ORDER BY se.id DESC LIMIT 1), "
        "         (SELECT NULLIF(TRIM(w.batch),'') FROM mis_azad.www_walkout w WHERE w.enrollment_id=e.id AND w.deleted_at IS NULL AND NULLIF(TRIM(w.batch),'') IS NOT NULL ORDER BY w.id DESC LIMIT 1) "
        "       ) AS batch_name, "
        "       COALESCE(e.lms_user, 0) AS lms_user, "
        "       e.created_at "
        "FROM mis_azad.www_enrollment e " + _legacy.geo_joins("e")
    )


# exclude_with -> the legacy table that already holds a record for this
# trainee, matched on enrollment number since there is no trainee FK.
_LEGACY_EXCLUDE_TABLES = {
    "induction": "www_induction",
    "ll":        "www_ll",
    "dp":        "www_driving_practice",
    "plic":      "www_pl",
    # 2026-09-12: hide a trainee from Add Internal/External Sakha once they
    # already have a sakha record (NOT EXISTS -> excludes at >=1).
    "internal_sakha": "www_sakha_internal",
    "external_sakha": "www_sakha_external",
}

# 2026-08-18 (Ashish): require_with -> wo table jisme record HONA zaroori hai
# tabhi trainee picker me aayegi. exclude_with ka ulta.
#
# Sirf wahi rishte rakhe hain jo sach me causal hain -- Permanent Licence aur
# Driving Practice, dono Learning License ke bina ho hi nahi sakte (259
# trainees ke data me aisa ek bhi record nahi hai, yani ye rule kisi maujooda
# trainee ko nahi rokta). Induction/GBV/FAT/Sakha jaise stage jaan-boojh kar
# nahi daale -- wo sab ke liye nahi hote (FAT sirf 2 trainees ka hai, Sakha
# 5-5 ka), unhe zaroori banane se sahi entry rukne lagti.
_LEGACY_REQUIRE_TABLES = {
    "ll": "www_ll",
}


def _legacy_trainee_filters(state_code, district_code, centre_code, area_code,
                            batch_id, enrollment_type, status, name,
                            date_from, date_to, exclude_with=None,
                            include_draft=False, require_with=None):
    """WHERE clause + params shared by the legacy list and export paths.

    2026-08-17: a Draft enrollment is a half-filled form, so it must not leak
    into anything downstream -- the Induction / LL / DP / PL / BKS / Sakha /
    Employment trainee pickers all read this same endpoint. Draft rows are
    therefore hidden unless the caller either asks for them by name
    (status=Draft) or sets include_draft=1, which only the Enrollment List
    and its Export do.
    """
    # 2026-08-19: soft-delete ki hui enrollment kisi list, export ya picker
    # me nahi aani chahiye.
    conds = ["NULLIF(TRIM(e.name), '') IS NOT NULL", "e.deleted_at IS NULL"]
    params = []
    if state_code:      conds.append(_legacy.state_filter());      params.append(state_code)
    if district_code:   conds.append(_legacy.district_filter());   params.append(district_code)
    if centre_code:     conds.append(_legacy.centre_filter("e"));  params.append(centre_code)
    if area_code:       conds.append("TRIM(e.area) = %s");         params.append(area_code)
    if enrollment_type: conds.append("e.type_of_enrollment = %s"); params.append(enrollment_type)
    if status:          conds.append("e.status = %s");             params.append(status)
    elif not include_draft:
        conds.append("COALESCE(NULLIF(TRIM(e.status), ''), 'Active') <> 'Draft'")
    if name:
        conds.append("(" + _legacy.name_match("e.name") + " OR e.enrollment_no ILIKE %s)")
        params.append(_legacy.name_pattern(name)); params.append(_legacy.name_pattern(name))
    if date_from: conds.append("e.enrollment_date >= %s"); params.append(date_from)
    if date_to:   conds.append("e.enrollment_date <= %s"); params.append(date_to)
    if batch_id:
        conds.append("NULLIF(TRIM(e.batch), '') = "
                     "(SELECT name FROM mis_azad.www_master_batches WHERE id = %s)")
        params.append(batch_id)
    tbl = _LEGACY_EXCLUDE_TABLES.get(exclude_with or "")
    if tbl:
        if exclude_with == "plic":
            # 2026-09-28: revert to hide-on-any-record. User rule: a
            # trainee whose PL has already been recorded must not reappear
            # on the Add PL list (was: allow up to 3 attempts, 2026-09-10).
            conds.append(
                "NOT EXISTS (SELECT 1 FROM mis_azad.www_pl x "
                "            WHERE x.enrollment_id = e.id AND x.deleted_at IS NULL)")
        else:
            conds.append(
                f"NOT EXISTS (SELECT 1 FROM mis_azad.{tbl} x "
                f"            WHERE x.enrollment_id = e.id)")
    # 2026-08-18: pichhla stage hona hi chahiye, warna trainee list me nahi.
    rtbl = _LEGACY_REQUIRE_TABLES.get(require_with or "")
    if rtbl:
        conds.append(
            f"EXISTS (SELECT 1 FROM mis_azad.{rtbl} x "
            f"        WHERE x.enrollment_id = e.id)")
    return "WHERE " + " AND ".join(conds), params


def _row_to_dict(row) -> dict:
    """RealDictRow -> plain dict; serialise date/datetime to ISO."""
    out = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


# www_trainee_family_members.monthly_income / monthly_contribution are
# NUMERIC(12,2) — Postgres rejects absolute values >= 10^10 with a 500.
_MAX_MONEY_AMOUNT = 9_999_999_999


def _validate_amounts(body: TraineeIn) -> None:
    # 2026-09-18: Partial commitment amount cap by vehicle type
    # (2 Wheeler < 1500, 4 Wheeler < 3000). Full amounts are auto-filled on
    # the form and not editable, so this only affects Partial entries.
    if str(getattr(body, 'commit_paid_status', None) or '').strip() == 'Partial':
        _et = (getattr(body, 'enrollment_type', None) or getattr(body, 'type_of_enrollment', None) or '').strip()
        _cap = 1500 if _et[:1] == '2' else (3000 if _et[:1] == '4' else 0)
        _raw = getattr(body, 'commit_partial_amt', None)
        try:
            _num = float(str(_raw).replace(',', '')) if _raw not in (None, '') else 0.0
        except (TypeError, ValueError):
            raise HTTPException(400, 'Partial payment amount must be a number.')
        if _num <= 0:
            raise HTTPException(400, 'Partial payment amount must be greater than 0.')
        if _cap and _num > _cap:
            raise HTTPException(400,
                f'Partial payment for {_et} cannot exceed ₹{_cap}. '
                'Choose Full if the trainee has paid the total.')
    for i, fm in enumerate(body.family_members or [], start=1):
        for label, val in (("Monthly Income", fm.monthly_income),
                           ("Monthly Contribution", fm.monthly_contribution)):
            if val is not None and abs(val) > _MAX_MONEY_AMOUNT:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Family member #{i}: {label} value ({val:,.0f}) is too "
                        f"large to be a real amount. Please check the Family "
                        f"Details tab and enter a valid amount."
                    ),
                )


# =============================================================================
# 2026-09-22: Live preview of the next enrollment number for the Add screen.
# NOT reserved -- another save can race and take it. When that happens, the
# create handler below detects the collision (existing check) and regenerates
# a fresh one before insert. So the persisted number is always unique even if
# the client's previewed value was stale.
# =============================================================================
@router.get("/preview-enrollment-no")
def preview_enrollment_no(state_code: Optional[str] = None,
                         district_code: Optional[str] = None,
                         centre_code: Optional[str] = None,
                         financial_year: Optional[str] = None):
    if not (state_code and centre_code and financial_year):
        return {"enrollment_no": "", "ready": False,
                "reason": "state_code, centre_code and financial_year are all required"}
    # _generate_enrollment_no only reads body.state_code / centre_code /
    # financial_year, so a minimal TraineeIn is enough.
    body = TraineeIn(
        state_code=state_code,
        district_code=district_code or "",
        centre_code=centre_code,
        financial_year=financial_year,
        name="preview",
    )
    with get_cursor() as cur:
        enr = _generate_enrollment_no(cur, body)
    return {"enrollment_no": enr, "ready": True}


# =============================================================================
# CREATE
# =============================================================================
@router.post("")
def create_trainee(body: TraineeIn):
    if not (body.name or "").strip():
        raise HTTPException(status_code=400, detail="Trainee name is required.")
    if not body.state_code or not body.district_code or not body.centre_code:
        raise HTTPException(status_code=400, detail="State, District and Centre are required.")
    _validate_amounts(body)

    # 2026-10-01: wrap generate+insert in a SAVEPOINT retry loop so a
    # parallel-create UniqueViolation (defensive -- would only fire if
    # a DB-level unique guard existed) regenerates and retries rather
    # than 500ing. The old client-preview pre-check is removed because
    # it was a TOCTOU bug: by the time INSERT ran another request could
    # have claimed the number anyway.
    import psycopg2 as _pg2
    with get_cursor() as cur:
        legacy = not _legacy.table_exists(cur, "www_trainees")
        _MAX_RETRIES = 5
        for _attempt in range(_MAX_RETRIES):
            cur.execute("SAVEPOINT enr_create")
            try:
                body.enrollment_no = _generate_enrollment_no(cur, body)
                if legacy:
                    trainee_id = _enr_insert(cur, body)
                    _auto_assign_llpl(cur, trainee_id, body)
                    cur.execute("RELEASE SAVEPOINT enr_create")
                    return {"id": trainee_id, "enrollment_no": body.enrollment_no}
                cur.execute("RELEASE SAVEPOINT enr_create")
                break
            except _pg2.errors.UniqueViolation:
                cur.execute("ROLLBACK TO SAVEPOINT enr_create")
                if _attempt == _MAX_RETRIES - 1:
                    raise HTTPException(status_code=409,
                        detail="Could not allocate a unique enrollment number after retries. Please try again.")

        cols = list(_TRAINEE_COLS)
        placeholders = ", ".join(["%s"] * len(cols))
        values = [getattr(body, c) for c in cols]

        cur.execute(
            f"INSERT INTO www_enrollment ({', '.join(cols)}) "
            f"VALUES ({placeholders}) RETURNING id, enrollment_no",
            values,
        )
        row = cur.fetchone()
        trainee_id = row["id"]
        _replace_children(cur, trainee_id, body)

    return {"id": trainee_id, "enrollment_no": row["enrollment_no"]}


@router.post("/{trainee_id}/photo")
async def upload_trainee_photo(trainee_id: int, file: UploadFile = File(...)):
    """Store a WWW trainee profile photo and update only that trainee row."""
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/avif"}
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
    extension = os.path.splitext(file.filename or "")[1].lower()
    if file.content_type not in allowed_types or extension not in allowed_extensions:
        raise HTTPException(400, "Photo must be a JPG, PNG, WebP or AVIF image.")

    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "Photo exceeds the 25 MB size limit.")

    with get_cursor() as cur:
        legacy = not _legacy.table_exists(cur, "www_trainees")
        cur.execute(
            "SELECT 1 FROM mis_azad.www_enrollment WHERE id=%s" if legacy
            else "SELECT 1 FROM www_enrollment WHERE id=%s AND deleted_at IS NULL",
            (trainee_id,),
        )
        if not cur.fetchone():
            raise HTTPException(404, "Trainee not found.")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    saved_name = f"www_trainee_{trainee_id}_{uuid.uuid4().hex}{extension}"
    disk_path = os.path.join(UPLOAD_DIR, saved_name)
    try:
        with open(disk_path, "wb") as destination:
            destination.write(content)
        photo_path = f"/uploads/{saved_name}"
        with get_cursor() as cur:
            if legacy:
                # The import's own photo column; read back as photo_path.
                cur.execute(
                    "UPDATE mis_azad.www_enrollment SET trainee_image=%s "
                    "WHERE id=%s",
                    (photo_path, trainee_id),
                )
            else:
                cur.execute(
                    "UPDATE www_enrollment SET photo_path=%s, updated_at=NOW() "
                    "WHERE id=%s AND deleted_at IS NULL",
                    (photo_path, trainee_id),
                )
    except Exception:
        if os.path.isfile(disk_path):
            os.remove(disk_path)
        raise
    return {"ok": True, "photo_path": photo_path, "photo_url": photo_path}


# -----------------------------------------------------------------------------
# 2026-08-10: Reference Documents — upload + delete endpoints
# -----------------------------------------------------------------------------
# The View screen renders each stored document with an eye icon that
# opens `file_path` in a new tab. These endpoints own the file binary
# so file_path is always a real URL under /uploads/. The main upsert
# no longer wipes this table (see body.documents guard above).
# -----------------------------------------------------------------------------
_ALLOWED_DOC_EXT = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".docx"}


@router.post("/{trainee_id}/documents")
async def upload_trainee_document(
    trainee_id: int,
    file: UploadFile = File(...),
    doc_type: str = Form(""),
    uploaded_by: str = Form(""),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _ALLOWED_DOC_EXT:
        raise HTTPException(400, "Document must be PDF, JPG, PNG, WebP or DOCX.")
    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "Document exceeds the 25 MB size limit.")
    with get_cursor() as cur:
        doc_legacy = not _legacy.table_exists(cur, "www_trainees")
        cur.execute(
            "SELECT 1 FROM mis_azad.www_enrollment WHERE id=%s" if doc_legacy
            else "SELECT 1 FROM www_enrollment WHERE id=%s AND deleted_at IS NULL",
            (trainee_id,),
        )
        if not cur.fetchone():
            raise HTTPException(404, "Trainee not found.")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    saved_name = f"www_doc_{trainee_id}_{uuid.uuid4().hex}{ext}"
    disk_path = os.path.join(UPLOAD_DIR, saved_name)
    try:
        with open(disk_path, "wb") as fh:
            fh.write(content)
        file_path = f"/uploads/{saved_name}"
        with get_cursor() as cur:
            if doc_legacy:
                # One cell holds every URL; append and report the new position.
                # 2026-08-14: the chosen document type, the original file name
                # and the uploader used to be thrown away here, so View showed
                # a server-side file name, a hard-coded type and a blank By.
                # Carry them in the entry's URL fragment -- see
                # _legacy_documents(), which reads them back.
                import datetime as _dt
                from urllib.parse import urlencode
                _today = _dt.date.today().isoformat()
                _meta = urlencode([(k, v) for k, v in (
                    ("n", (file.filename or "").strip()),
                    ("t", (doc_type or "").strip()),
                    ("b", (uploaded_by or "").strip()),
                    ("d", _today),
                ) if v])
                urls = _enr_doc_urls(cur, trainee_id) or []
                urls.append(file_path + ("#" + _meta if _meta else ""))
                _enr_set_doc_urls(cur, trainee_id, urls)
                return {"id": len(urls), "file_name": file.filename,
                        "doc_type": doc_type or "Photo / Aadhaar / PAN",
                        "file_path": file_path, "uploaded_by": uploaded_by or None,
                        "uploaded_at": _today}
            cur.execute(
                "INSERT INTO www_trainee_documents "
                "(trainee_id, file_name, doc_type, file_path, uploaded_by) "
                "VALUES (%s, %s, %s, %s, %s) "
                "RETURNING id, file_name, doc_type, file_path, uploaded_by, uploaded_at",
                (trainee_id, file.filename, doc_type or None, file_path, uploaded_by or None),
            )
            row = cur.fetchone()
    except Exception:
        if os.path.isfile(disk_path):
            os.remove(disk_path)
        raise
    return _row_to_dict(row)


@router.delete("/{trainee_id}/documents/{doc_id}")
def delete_trainee_document(trainee_id: int, doc_id: int):
    with get_cursor() as cur:
        # 2026-08-12: www_trainee_documents only exists alongside the
        # normalized schema.  Without this the delete blew up with an
        # UndefinedTable 500; the upload endpoint next to it already
        # answers 501 here, so match it.
        if not _legacy.table_exists(cur, "www_trainees"):
            # doc_id is the 1-based position handed out by _legacy_documents.
            urls = _enr_doc_urls(cur, trainee_id)
            if urls is None:
                raise HTTPException(404, "Trainee not found.")
            if doc_id < 1 or doc_id > len(urls):
                raise HTTPException(404, "Document not found.")
            file_path = urls.pop(doc_id - 1)
            _enr_set_doc_urls(cur, trainee_id, urls)
        else:
            cur.execute(
                "SELECT file_path FROM www_trainee_documents "
                "WHERE id=%s AND trainee_id=%s",
                (doc_id, trainee_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Document not found.")
            cur.execute(
                "DELETE FROM www_trainee_documents WHERE id=%s AND trainee_id=%s",
                (doc_id, trainee_id),
            )
            file_path = row["file_path"] if isinstance(row, dict) else row[0]
    if file_path and file_path.startswith("/uploads/"):
        disk_path = os.path.join(UPLOAD_DIR, os.path.basename(file_path))
        if os.path.isfile(disk_path):
            try:
                os.remove(disk_path)
            except Exception:
                pass  # DB row already gone; leftover file on disk is harmless
    return {"ok": True}


# =============================================================================
# PATCH single-field (2026-08-21) — used by View Trainee inline-edit.
# Whitelisted to the specific fields the View screen exposes as editable.
# Handles both normalized (www_trainees) and legacy (www_enrollment) schemas.
# =============================================================================
class TraineeFieldPatch(BaseModel):
    field: str
    value: Optional[str] = None


# Only these columns may be updated via this endpoint. Extending the list is
# a two-line change: add the column name here and (optionally) map it below
# for the legacy schema which uses different column names in a few places.
class WwwTraineePaymentIn(BaseModel):
    payment: float
    payment_date: str


@router.post("/{trainee_id}/payments")
def add_trainee_payment(trainee_id: int, body: WwwTraineePaymentIn):
    """Add a commitment payment (full or partial). Amount Paid = SUM of these."""
    from datetime import date as _date
    try:
        from routes._www_meta import get_current_user_id as _uidfn
        _uid = _uidfn() or 1
    except Exception:
        _uid = 1
    try:
        amt = float(body.payment)
    except Exception:
        raise HTTPException(400, "Payment amount is required.")
    if amt <= 0:
        raise HTTPException(400, "Payment amount must be greater than 0.")
    pdate = (body.payment_date or "").strip()
    if not pdate:
        raise HTTPException(400, "Payment date is required.")
    with get_cursor() as cur:
        cur.execute(
            "SELECT type_of_enrollment, commitment_paid_status, commitment_amount, "
            "commitment_partial_amount, enrollment_date FROM mis_azad.www_enrollment "
            "WHERE id = %s AND deleted_at IS NULL",
            (trainee_id,),
        )
        er = cur.fetchone()
        if not er:
            raise HTTPException(404, "Trainee not found.")
        total = _www_commit_total(er["type_of_enrollment"])
        cur.execute(
            "SELECT COALESCE(SUM(NULLIF(TRIM(payment), '')::numeric), 0) AS s, "
            "COUNT(*) AS n FROM mis_azad.www_trainee_payment "
            "WHERE trainee_id = %s AND deleted_at IS NULL",
            (trainee_id,),
        )
        pr = cur.fetchone()
        real_sum = float(pr["s"] or 0)
        n = int(pr["n"] or 0)
        enroll_amt = _www_enroll_paid_amount(
            er["commitment_paid_status"], er["commitment_amount"],
            er["commitment_partial_amount"], total)
        current_paid = real_sum if n > 0 else enroll_amt
        remaining = total - current_paid
        if total > 0 and remaining <= 0:
            raise HTTPException(400, "This commitment is already fully paid.")
        if total > 0 and amt > remaining:
            raise HTTPException(
                400,
                "Payment amount cannot exceed the remaining amount of \u20b9" + _www_fmt_amt(remaining) + ".")
        if n == 0 and enroll_amt > 0:
            cur.execute(
                "INSERT INTO mis_azad.www_trainee_payment "
                "(trainee_id, payment, payment_date, users_id, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, NOW(), NOW())",
                (trainee_id, _www_fmt_amt(enroll_amt), (er["enrollment_date"] or _date.today()), _uid),
            )
        cur.execute(
            "INSERT INTO mis_azad.www_trainee_payment "
            "(trainee_id, payment, payment_date, users_id, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, NOW(), NOW()) RETURNING id",
            (trainee_id, _www_fmt_amt(amt), pdate, _uid),
        )
        new_id = cur.fetchone()["id"]
    return {"ok": True, "id": new_id}


_ALLOWED_PATCH_FIELDS = {"gender", "gender_other", "commit_partial_amt"}

# When the DB is on the legacy www_enrollment schema, some field names
# differ. This map translates the View-screen field name to the actual
# column name on the legacy table. Missing keys fall through to the
# View-screen name unchanged.
_LEGACY_FIELD_MAP = {
    # gender / gender_other exist on www_enrollment with same names.
    # 2026-08-31: Amount Paid (View screen) -> legacy commitment column.
    "commit_partial_amt": "commitment_partial_amount",
}


@router.patch("/{trainee_id}/field")
def patch_trainee_field(trainee_id: int, body: TraineeFieldPatch):
    field = (body.field or "").strip()
    if field not in _ALLOWED_PATCH_FIELDS:
        raise HTTPException(400, f"Field '{field}' is not editable via this endpoint.")
    val = None if body.value is None else str(body.value).strip()
    if val == "":
        val = None
    # 2026-09-18: same Partial-amount cap for the Amount Paid inline edit --
    # only applies when the underlying commitment is Partial. Reads the
    # trainee's current type + status so callers do not have to send them.
    if field == 'commit_partial_amt' and val is not None:
        try:
            _pnum = float(val.replace(',', ''))
        except (TypeError, ValueError):
            raise HTTPException(400, 'Partial payment amount must be a number.')
        if _pnum <= 0:
            raise HTTPException(400, 'Partial payment amount must be greater than 0.')
        with get_cursor() as _cur:
            _is_legacy = not _legacy.table_exists(_cur, 'www_trainees')
            if _is_legacy:
                _cur.execute('SELECT type_of_enrollment AS et, commitment_paid_status AS ps '
                             'FROM mis_azad.www_enrollment WHERE id=%s', (trainee_id,))
            else:
                _cur.execute('SELECT enrollment_type AS et, commit_paid_status AS ps '
                             'FROM www_enrollment WHERE id=%s AND deleted_at IS NULL', (trainee_id,))
            _rw = _cur.fetchone()
        if _rw and (str(_rw.get('ps') or '').strip() == 'Partial'):
            _et = (_rw.get('et') or '').strip()
            _cap = 1500 if _et[:1] == '2' else (3000 if _et[:1] == '4' else 0)
            if _cap and _pnum > _cap:
                raise HTTPException(400,
                    f'Partial payment for {_et} cannot exceed ₹{_cap}. '
                    'Choose Full if the trainee has paid the total.')
    with get_cursor() as cur:
        is_legacy = not _legacy.table_exists(cur, "www_trainees")
        if is_legacy:
            table = "mis_azad.www_enrollment"
            col = _LEGACY_FIELD_MAP.get(field, field)
            cur.execute(f"SELECT 1 FROM {table} WHERE id=%s", (trainee_id,))
        else:
            table = "www_trainees"
            col = field
            cur.execute(
                f"SELECT 1 FROM {table} WHERE id=%s AND deleted_at IS NULL",
                (trainee_id,),
            )
        if not cur.fetchone():
            raise HTTPException(404, "Trainee not found.")
        # Legacy www_enrollment schema is missing several columns the
        # normalized table has (gender_other, updated_at, ...). Check for
        # column existence before UPDATE. If the column is absent and the
        # caller sent an empty value, treat it as a silent no-op (the
        # frontend blindly clears gender_other when switching away from
        # Other; on legacy schemas that column simply doesn't exist).
        # If the caller sent a real value against a missing column, surface
        # a clean 400 so the UI can react.
        _schema, _tbl = ("mis_azad", "www_enrollment") if is_legacy else ("public", "www_trainees")
        cur.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = %s AND table_name = %s AND column_name = %s",
            (_schema, _tbl, col),
        )
        if not cur.fetchone():
            if val is None or val == "":
                return {"ok": True, "field": field, "value": val, "skipped": "column-missing"}
            raise HTTPException(400, f"Field '{field}' is not supported on this schema.")

        if is_legacy:
            cur.execute(
                f"UPDATE {table} SET {col} = %s WHERE id = %s",
                (val, trainee_id),
            )
        else:
            cur.execute(
                f"UPDATE {table} SET {col} = %s, updated_at = NOW() WHERE id = %s",
                (val, trainee_id),
            )
    return {"ok": True, "field": field, "value": val}


# =============================================================================
# ELIGIBLE SURVEYS (Through-Survey Add Trainee) — 2026-08-21
# Reads mis_azad.www_survey_form: women aged 18+ who were surveyed and can be
# enrolled into the WWW program. The Add Trainee "Through Survey" modal shows
# this list; picking a row prefills the enrollment form.
# =============================================================================

_SURVEY_LIST_COLS = (
    "_pk", "response_id", "state", "state_code", "district", "district_code",
    "centre_census", "name_of_the_women_family_members_who_are_18",
    "contact_number_1", "age"
)


@router.get("/eligible-surveys")
def list_eligible_surveys(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_name: Optional[str] = None,
    name: Optional[str] = None,
    limit: int = 100,
):
    """List survey-eligible women for the Through-Survey Add Trainee flow.
    All filters are optional and combined with AND. Rows already enrolled
    (matched loosely by name + mobile against www_trainees / www_enrollment)
    are excluded so the picker only shows enrollable candidates.
    """
    conds = ["s.deleted_at IS NULL",
             "COALESCE(s.name_of_the_women_family_members_who_are_18, '') <> ''"]
    params: list = []
    state_code, district_code, _sc = _scope.scope_geo(request, state_code, district_code, None)
    if state_code:
        conds.append("s.state_code = %s"); params.append(state_code)
    if district_code:
        conds.append("s.district_code = %s"); params.append(district_code)
    if centre_name:
        conds.append("LOWER(TRIM(s.centre_census)) = LOWER(TRIM(%s))"); params.append(centre_name)
    if name:
        conds.append("(s.name_of_the_women_family_members_who_are_18 ILIKE %s OR s.name_with_whom_the_survey_is_done ILIKE %s)")
        params.append(f"%{name.strip()}%")
        params.append(f"%{name.strip()}%")
    where = " AND ".join(conds)
    lim = max(1, min(int(limit or 100), 500))
    with get_cursor() as cur:
        # Skip already-enrolled candidates. Only checks normalized www_trainees;
        # on legacy-only DBs this dedup is skipped (harmless — the picker
        # simply shows everyone, and the enrolment form is the source of truth).
        enrolled_join = ""
        if _legacy.table_exists(cur, "www_trainees"):
            enrolled_join = (
                " AND NOT EXISTS (SELECT 1 FROM www_enrollment t "
                "                 WHERE t.deleted_at IS NULL "
                "                   AND LOWER(TRIM(t.name)) = LOWER(TRIM(s.name_of_the_women_family_members_who_are_18)) "
                "                   AND COALESCE(t.mobile, '') = COALESCE(s.contact_number_1, '')) "
            )
        cur.execute(
            f"""
            SELECT s._pk AS id,
                   s.response_id,
                   s.name_of_the_women_family_members_who_are_18 AS name,
                   s.state, s.state_code,
                   s.district, s.district_code,
                   s.centre_census AS centre_name,
                   CASE WHEN LOWER(TRIM(COALESCE(s.name_of_area_census, ''))) IN ('any other','other','others','any others')
                             AND NULLIF(TRIM(s.specify_if_any_other), '') IS NOT NULL
                        THEN s.specify_if_any_other ELSE s.name_of_area_census END AS area,
                   s.date_of_survey,
                   s.contact_number_1 AS mobile,
                   s.name_with_whom_the_survey_is_done AS respondent_name,
                   s.name_of_surveyer AS surveyor_name
            FROM mis_azad.www_survey_form s
            WHERE {where}
              {enrolled_join}
            ORDER BY s._pk DESC
            LIMIT {lim}
            """,
            tuple(params),
        )
        rows = cur.fetchall()
    return {"data": rows, "total": len(rows)}


@router.get("/eligible-surveys/{survey_pk}")
def get_eligible_survey(survey_pk: int):
    """Full survey row for the picked candidate — used to prefill the Add form.
    Returns a compact subset (only fields the frontend maps into wwwAt* inputs).
    """
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT s._pk AS id, s.response_id,
                   s.state, s.state_code, s.district, s.district_code,
                   s.centre_census AS centre_name,
                   s.name_of_the_women_family_members_who_are_18 AS name,
                   s.contact_number_1 AS mobile,
                   s.age,
                   s.address,
                   s.caste_category,
                   s.specify_if_any_other_1 AS caste_other,
                   s.religion,
                   s.specify_if_any_other_2 AS religion_other,
                   s.name_with_whom_the_survey_is_done AS respondent_name,
                   s.name_of_area_census AS area,
                   s.name_of_basti AS basti,
                   s.name_of_the_primary_decision_maker_in_the_family AS dm_name,
                   s.who_is_the_primary_decision_maker_in_the_family AS dm_relation,
                   s.what_is_the_occupation_of_primary_decision_maker_of_the_family AS dm_occupation,
                   s.total_monthly_income AS monthly_income
            FROM mis_azad.www_survey_form s
            WHERE s._pk = %s AND s.deleted_at IS NULL
            """,
            (survey_pk,),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Survey record not found.")
    return row


# =============================================================================
# LIST
# =============================================================================
@router.get("")
def list_trainees(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    area_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    enrollment_type: Optional[str] = None,
    status: Optional[str] = None,
    name: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    include_deleted: int = 0,
    exclude_with: Optional[str] = None,
    # 2026-08-18 (Ashish): "ll" bhejne par sirf wahi trainee aayengi jinki
    # Learning License ban chuki hai -- Add Permanent Licence aur Add Driving
    # Practice ke picker yahi bhejte hain.
    require_with: Optional[str] = None,
    include_draft: int = 0,
    sort_by: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
):
    offset = (max(page, 1) - 1) * max(limit, 1)
    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    conds, params = [], []
    if not include_deleted:
        conds.append("t.deleted_at IS NULL")
    if state_code:        conds.append("t.state_code = %s");      params.append(state_code)
    if district_code:     conds.append("t.district_code = %s");   params.append(district_code)
    if centre_code:       conds.append("t.centre_code = %s");     params.append(centre_code)
    if area_code:         conds.append("t.area_code = %s");       params.append(area_code)
    if batch_id:          conds.append("t.batch_id = %s");        params.append(batch_id)
    if enrollment_type:   conds.append("t.enrollment_type = %s"); params.append(enrollment_type)
    if status:            conds.append("t.status = %s");          params.append(status)
    # 2026-08-19: default hides Draft trainees from downstream
    # module pickers (Add IS/ES/BKS/etc.). Enrollment List opts
    # in via include_draft=1 to show them.
    elif not include_draft:
        conds.append("COALESCE(NULLIF(TRIM(t.status), ''), 'Active') <> 'Draft'")
    if name:
        conds.append(_legacy.name_match("t.name"))
        params.append(_legacy.name_pattern(name))
    if date_from:         conds.append("t.enrollment_date >= %s"); params.append(date_from)
    if date_to:           conds.append("t.enrollment_date <= %s"); params.append(date_to)
    # 2026-08-01: hide trainees who already have a record of the named type.
    # Legacy fallback branch (below) reads a different table and ignores this.
    if exclude_with == "induction":
        conds.append("NOT EXISTS (SELECT 1 FROM www_inductions x WHERE x.trainee_id = t.id AND x.deleted_at IS NULL)")
    elif exclude_with == "ll":
        conds.append(
            "(NOT EXISTS (SELECT 1 FROM www_learning_licenses x "
            "WHERE x.trainee_id = t.id AND x.deleted_at IS NULL) "
            "AND NOT EXISTS (SELECT 1 FROM www_ll_form x "
            "WHERE x.enrollment_number = t.enrollment_no))"
        )
    elif exclude_with == "dp":
        conds.append("NOT EXISTS (SELECT 1 FROM www_driving_practices x WHERE x.trainee_id = t.id AND x.deleted_at IS NULL)")
    elif exclude_with == "plic":
        conds.append("(SELECT COUNT(*) FROM www_permanent_licenses x WHERE x.trainee_id = t.id AND x.deleted_at IS NULL) < 3")
    where = ("WHERE " + " AND ".join(conds)) if conds else ""

    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_trainees"):
            lwhere, lparams = _legacy_trainee_filters(
                state_code, district_code, centre_code, area_code, batch_id,
                enrollment_type, status, name, date_from, date_to, exclude_with,
                include_draft=bool(include_draft), require_with=require_with)
            cur.execute(
                "SELECT COUNT(*) AS total FROM mis_azad.www_enrollment e "
                + _legacy.geo_joins("e") + lwhere,
                lparams,
            )
            total = cur.fetchone()["total"]
            cur.execute(
                _legacy_trainee_select() + lwhere +
                " ORDER BY " + www_list_order(sort_by, "e.name", "e.id", "e.id DESC") +
                " LIMIT %s OFFSET %s",
                lparams + [limit, offset],
            )
            rows = [_row_to_dict(r) for r in cur.fetchall()]
            return {"total": total, "page": page, "limit": limit, "data": rows}

        cur.execute(f"SELECT COUNT(*) AS total FROM www_enrollment t {where}", params)
        total = cur.fetchone()["total"]
        cur.execute(
            f"""SELECT t.id, t.enrollment_no, t.name, t.mobile,
                       t.enrollment_type, t.enrollment_date, t.status,
                       t.state_code, t.district_code, t.centre_code,
                       t.batch_id,
                       COALESCE(t.lms_user, 0) AS lms_user,
                       s.state_name, d.district_name, c.centre_name,
                       b.name AS batch_name
                FROM www_enrollment t
                LEFT JOIN central_states          s ON t.state_code    = s.state_code
                LEFT JOIN central_districts       d ON t.district_code = d.district_code
                LEFT JOIN central_centres         c ON t.centre_code   = c.centre_code
                LEFT JOIN www_master_batches  b ON t.batch_id      = b.id
                {where}
                ORDER BY " + www_list_order(sort_by, "t.name", "t.created_at", "t.created_at DESC NULLS LAST, t.id DESC") + "
                LIMIT %s OFFSET %s""",
            params + [limit, offset],
        )
        rows = [_row_to_dict(r) for r in cur.fetchall()]
        return {"total": total, "page": page, "limit": limit, "data": rows}


# =============================================================================
# EXPORT (Excel) — 2026-08-05 (v2: full-record export)
# The Enrollment List "Export" button was a frontend stub; this endpoint
# feeds it.  Accepts the same filters as list_trainees and returns a real
# .xlsx via export_helper (same convention as /mgj/export/excel).
# v2: exports EVERY field across the 10 Add-Trainee tabs + child tables
# (aggregated per trainee), not just the Tab-1 basics.  Any column added
# to www_trainees later is appended automatically via the leftover check.
# =============================================================================
@router.get("/export/excel")
def export_trainees_excel(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    area_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    enrollment_type: Optional[str] = None,
    status: Optional[str] = None,
    name: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    include_draft: int = 0,
):
    from datetime import date
    from export_helper import multi_sheet_xlsx_response_v2

    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        has_table = _legacy.table_exists(cur, "www_trainees")

        if not has_table:
            # ---- LEGACY EXPORT: the whole www_enrollment row ----
            # Same source and same filters list_trainees uses when the
            # normalized table is absent.  SELECT e.* so no column of the
            # import can be missed; _legacy_export_workbook orders and
            # labels them.  area_code is honoured here too — the legacy
            # branch used to drop it, so an area-filtered list exported
            # every area.
            lwhere, lparams = _legacy_trainee_filters(
                state_code, district_code, centre_code, area_code, batch_id,
                enrollment_type, status, name, date_from, date_to,
                include_draft=bool(include_draft))
            cur.execute(
                "SELECT e.*, " + _legacy.geo_cols() + ", " +
                _legacy.centre_expr("e.centre") + " AS _centre_clean, " +
                # The workbook has a column for each of these six; without the
                # join they printed empty on every row.
                _legacy_ll_pl_cols() + " "
                "FROM mis_azad.www_enrollment e " + _legacy.geo_joins("e") +
                _legacy_ll_pl_joins("e") +
                lwhere + " ORDER BY e.id DESC",
                lparams,
            )
            legacy_rows = [dict(r) for r in cur.fetchall()]
            # 2026-09-10: some rows store the area CENSUS CODE (e.g. S07098B1GP8)
            # in e.area instead of the name -> resolve codes to names for export.
            _amap = {}
            cur.execute("SELECT area_code, area_name FROM mis_azad.www_areas "
                        "WHERE deleted_at IS NULL AND NULLIF(TRIM(area_name),'') IS NOT NULL")
            for _ar in cur.fetchall():
                _amap[(_ar["area_code"] or "").strip()] = _ar["area_name"]
            cur.execute("SELECT area_code, area_name FROM mis_azad.central_areas "
                        "WHERE NULLIF(TRIM(area_name),'') IS NOT NULL")
            for _ar in cur.fetchall():
                _k = (_ar["area_code"] or "").strip()
                if _k and _k not in _amap:
                    _amap[_k] = _ar["area_name"]
            for _r in legacy_rows:
                _a = (_r.get("area") or "").strip()
                if _a in _amap:
                    _r["area"] = _amap[_a]
            # 2026-09-29 v2: fill Per Capita Income for blank rows.
            # Order of precedence:
            #   1. row's monthly_family_income + number_of_member_in_family
            #      when both are usable (FLP's rule, routes/flps.py:234)
            #   2. flat family-member slots: SUM(monthly_income_N)
            #      / COUNT(non-empty c_N_name_of_family_members),
            #      because ~150 of the 194 blank rows still carry
            #      per-member data in the sheet even though the two
            #      total columns above were left empty at import.
            # A row with no derivable inputs (no row-level totals AND
            # no per-member data) stays blank -- there is nothing to
            # fabricate.
            def _blank(v):
                return v is None or str(v).strip() in ('', '0', '0.0', '0.00')
            def _num(v):
                try:
                    if v is None: return 0.0
                    s = str(v).strip().replace(',', '')
                    if not s: return 0.0
                    return float(s)
                except (TypeError, ValueError):
                    return 0.0
            _MEM_NAME_COLS = ['c_1_name_of_family_members',
                              'c_2_name_of_family_members',
                              'c_3_name_of_family_members',
                              'c_4_name_of_family_members',
                              'c_5_name_of_family_members',
                              'c_6_name_of_family_members',
                              'c_7_name_of_family_members',
                              'c_8_name_of_family_members',
                              'c_9_name_of_family_members',
                              'c_10_name_of_family_members']
            _MEM_INC_COLS  = ['monthly_income',       'monthly_income_2',
                              'monthly_income_3',     'monthly_income_4',
                              'monthly_income_5',     'monthly_income_6',
                              'monthly_income_7',     'monthly_income_8',
                              'monthly_income_9',     'monthly_income_10']
            # 2026-10-06 (user ask): compute per_capita_income to match
            # the Trainee View screen's famTotals() -- sum of family rows'
            # monthly income divided by (count + 1) counting the trainee
            # herself as a household member. Overrides the stored column
            # for every row so Excel reads the same value users see on
            # screen (e.g. Jenifer: 22000/(3+1)=5500, previously 7333).
            # Keeps the earlier backfill of monthly_family_income /
            # number_of_member_in_family from slot data when they are blank.
            for _r in legacy_rows:
                _member_count = sum(1 for _c in _MEM_NAME_COLS
                                      if str(_r.get(_c) or '').strip())
                _sum_inc = sum(_num(_r.get(_c)) for _c in _MEM_INC_COLS)
                if _member_count > 0 and _sum_inc > 0:
                    # Backfill the two total columns in the same row so
                    # the export prints consistent numbers.
                    if _blank(_r.get('monthly_family_income')):
                        _r['monthly_family_income'] = int(round(_sum_inc))
                    if _blank(_r.get('number_of_member_in_family')):
                        _r['number_of_member_in_family'] = _member_count
                    _r['per_capita_income'] = round(_sum_inc / (_member_count + 1), 2)
                    continue
                # Fallback: use the typed-in family totals.
                _inc = _num(_r.get('monthly_family_income'))
                _mem = 0
                try:
                    _m = _r.get('number_of_member_in_family')
                    if _m not in (None, ''):
                        _mem = int(float(str(_m).strip()))
                except (TypeError, ValueError):
                    _mem = 0
                if _inc > 0 and _mem > 0:
                    _r['per_capita_income'] = round(_inc / (_mem + 1), 2)
            return _legacy_export_workbook(
                legacy_rows,
                f"WWW_Enrollment_List_{date.today().isoformat()}.xlsx",
            )

        conds, params = ["t.deleted_at IS NULL"], []
        if state_code:      conds.append("t.state_code = %s");      params.append(state_code)
        if district_code:   conds.append("t.district_code = %s");   params.append(district_code)
        if centre_code:     conds.append("t.centre_code = %s");     params.append(centre_code)
        if area_code:       conds.append("t.area_code = %s");       params.append(area_code)
        if batch_id:        conds.append("t.batch_id = %s");        params.append(batch_id)
        if enrollment_type: conds.append("t.enrollment_type = %s"); params.append(enrollment_type)
        if status:          conds.append("t.status = %s");          params.append(status)
        if name:
            conds.append(_legacy.name_match("t.name"))
            params.append(_legacy.name_pattern(name))
        if date_from:       conds.append("t.enrollment_date >= %s"); params.append(date_from)
        if date_to:         conds.append("t.enrollment_date <= %s"); params.append(date_to)

        cur.execute(
            f"""SELECT t.*,
                       s.state_name, d.district_name, c.centre_name,
                       a.area_name, b.name AS batch_name,
                       ot.how_known_other, ot.property_name_other, ot.property_paper_other,
                       (SELECT string_agg(ec.contact_no, '; ' ORDER BY ec.seq)
                          FROM www_trainee_emergency_contacts ec
                         WHERE ec.trainee_id = t.id) AS agg_emergency,
                       (SELECT string_agg(l.language || ' (' || concat_ws('/',
                                 CASE WHEN l.can_understand THEN 'Understand' END,
                                 CASE WHEN l.can_speak      THEN 'Speak'      END,
                                 CASE WHEN l.can_read       THEN 'Read'       END,
                                 CASE WHEN l.can_write      THEN 'Write'      END) || ')', '; ')
                          FROM www_trainee_languages l
                         WHERE l.trainee_id = t.id) AS agg_languages,
                       (SELECT string_agg(sp.platform, '; ')
                          FROM www_trainee_social_platforms sp
                         WHERE sp.trainee_id = t.id) AS agg_social,
                       (SELECT string_agg(nu.net_use, '; ')
                          FROM www_trainee_net_uses nu
                         WHERE nu.trainee_id = t.id) AS agg_net_uses,
                       (SELECT string_agg(concat_ws(', ',
                                 fm.member_name, fm.relation,
                                 'Age ' || fm.age,
                                 fm.education, fm.occupation,
                                 'Mob ' || fm.mobile_no,
                                 'Income ' || fm.monthly_income,
                                 'Contributes ' || fm.monthly_contribution),
                                 ' | ' ORDER BY fm.seq)
                          FROM www_trainee_family_members fm
                         WHERE fm.trainee_id = t.id) AS agg_family,
                       (SELECT string_agg(eb.encourager, '; ')
                          FROM www_trainee_encouraged_by eb
                         WHERE eb.trainee_id = t.id) AS agg_encouraged,
                       (SELECT string_agg(ast.asset, '; ')
                          FROM www_trainee_assets ast
                         WHERE ast.trainee_id = t.id) AS agg_assets,
                       (SELECT string_agg(gs.situation ||
                                 COALESCE(' (' || gs.violence_category || ')', ''), '; ')
                          FROM www_trainee_gbv_situations gs
                         WHERE gs.trainee_id = t.id) AS agg_gbv_situations,
                       (SELECT string_agg(gk.support_kind, '; ')
                          FROM www_trainee_gbv_support_kinds gk
                         WHERE gk.trainee_id = t.id) AS agg_gbv_support,
                       (SELECT string_agg(rf.ref_name ||
                                 COALESCE(' (' || rf.relation || ')', '') ||
                                 COALESCE(' - ' || rf.contact_no, ''), '; ' ORDER BY rf.seq)
                          FROM www_trainee_references rf
                         WHERE rf.trainee_id = t.id) AS agg_references,
                       (SELECT COUNT(*)
                          FROM www_trainee_documents dc
                         WHERE dc.trainee_id = t.id) AS agg_doc_count
                FROM www_enrollment t
                LEFT JOIN central_states              s ON t.state_code    = s.state_code
                LEFT JOIN central_districts           d ON t.district_code = d.district_code
                LEFT JOIN central_centres             c ON t.centre_code   = c.centre_code
                LEFT JOIN www_areas               a ON t.area_code     = a.area_code
                LEFT JOIN www_master_batches      b ON t.batch_id      = b.id
                LEFT JOIN www_trainee_other_texts ot ON ot.trainee_id  = t.id
                WHERE {' AND '.join(conds)}
                ORDER BY t.created_at DESC""",
            params,
        )
        rows = cur.fetchall()

    # 2026-08-06 — pull per-trainee family members separately so we can
    # emit them INLINE (wide format, one row per trainee) instead of the
    # old delimited "agg_family" string. Same pattern as FLP List export.
    fam_map = {}
    # 2026-08-06 — same treatment for References: bulk-fetch the child rows
    # and emit N * 3 columns (Name / Relation / Contact No) inline instead
    # of the old delimited agg_references string.
    ref_map = {}
    if rows:
        ids = [r['id'] for r in rows]
        ph = ','.join(['%s'] * len(ids))
        with get_cursor() as fcur:
            fcur.execute(
                f"SELECT * FROM www_trainee_family_members "
                f"WHERE trainee_id IN ({ph}) ORDER BY trainee_id, seq",
                ids,
            )
            for fm in fcur.fetchall():
                fam_map.setdefault(fm['trainee_id'], []).append(fm)
        with get_cursor() as rcur:
            rcur.execute(
                f"SELECT * FROM www_trainee_references "
                f"WHERE trainee_id IN ({ph}) ORDER BY trainee_id, seq",
                ids,
            )
            for rf in rcur.fetchall():
                ref_map.setdefault(rf['trainee_id'], []).append(rf)
    # Floor at 5 so every export has at least 5 family slots (matches FLP).
    max_family_members = max([len(v) for v in fam_map.values()] + [5])
    # Floor at 3 references — the form defaults to 3 reference rows.
    max_references = max([len(v) for v in ref_map.values()] + [3])

    def _g(r, key):
        v = r.get(key)
        return '' if v is None else str(v)

    def _res(r, key, other_key):
        # Resolve an "Other" selection to its free-text value.
        v = r.get(key)
        o = r.get(other_key)
        if v == 'Other' and o:
            return 'Other - ' + str(o)
        return '' if v is None else str(v)

    def _yn(r, key):
        v = r.get(key)
        if v is None or v == '':
            return ''
        if isinstance(v, bool):
            return 'Yes' if v else 'No'
        return str(v)

    # 2026-08-06 v3 — section-wise column groups with merged headers +
    # family members inline in wide format. Each SECTION becomes a merged
    # row-1 title; row 2 holds the per-field headers. Family sits between
    # Basic Profile and Previous Employment, mirroring the FLP List export.
    BASIC_PROFILE = [
        ('Enrollment No.',            lambda r: _g(r, 'enrollment_no')),
        ('Status',                    lambda r: _g(r, 'status')),
        ('Financial Year',            lambda r: _g(r, 'financial_year')),
        ('Batch',                     lambda r: _g(r, 'batch_name') or _g(r, 'batch_id')),
        ('State',                     lambda r: _g(r, 'state_name') or _g(r, 'state_code')),
        ('District',                  lambda r: _g(r, 'district_name') or _g(r, 'district_code')),
        ('Centre',                    lambda r: _g(r, 'centre_name') or _g(r, 'centre_code')),
        ('Area',                      lambda r: _g(r, 'area_name') or _g(r, 'area_other') or _g(r, 'area_code')),
        ('Basti',                     lambda r: _g(r, 'basti')),
        ('Name',                      lambda r: _g(r, 'name')),
        ('Enrollment Date',           lambda r: _g(r, 'enrollment_date')),
        ('Enrollment Type',           lambda r: _g(r, 'enrollment_type')),
        ('Date of Birth',             lambda r: _g(r, 'date_of_birth')),
        ('Age at Enrollment',         lambda r: _g(r, 'age_at_enrollment')),
        ('Blood Group',               lambda r: _g(r, 'blood_group')),
        ('Mobile',                    lambda r: _g(r, 'mobile')),
        ('Email',                     lambda r: _g(r, 'email')),
        ('No. of Emergency Contacts', lambda r: _g(r, 'num_emergency_contacts')),
        ('Emergency Contacts',        lambda r: _g(r, 'agg_emergency')),
        ('Current Address',           lambda r: _g(r, 'current_address')),
        ('Permanent Address',         lambda r: _g(r, 'permanent_address')),
        ('Caste Category',            lambda r: _res(r, 'caste_category', 'caste_other')),
        ('Religion',                  lambda r: _res(r, 'religion', 'religion_other')),
        ('Gender',                    lambda r: _res(r, 'gender', 'gender_other')),
        ('Marital Status',            lambda r: _g(r, 'marital_status')),
        ('Age at Marriage',           lambda r: _g(r, 'age_at_marriage')),
        ('Living With',               lambda r: _res(r, 'living_with', 'living_with_other')),
        ('Education Qualification',   lambda r: _res(r, 'education_qualification', 'education_other')),
        ('Still Studying',            lambda r: _yn(r, 'still_studying')),
        ('Studying Class',            lambda r: _g(r, 'studying_class')),
        ('How Known About Azad',      lambda r: _res(r, 'how_known_azad', 'how_known_other')),
        ('Mobilization Activity',     lambda r: _g(r, 'mobilization_activity')),
        ('Languages Known',           lambda r: _g(r, 'agg_languages')),
        ('Has Social Media',          lambda r: _yn(r, 'has_social_media')),
        ('Social Media Platforms',    lambda r: _g(r, 'agg_social')),
        ('Internet Uses',             lambda r: _g(r, 'agg_net_uses')),
        ('Came With License Type',    lambda r: _g(r, 'came_with_lic_type')),
        ('LL Date',                   lambda r: _g(r, 'll_date')),
        ('LL Number',                 lambda r: _g(r, 'll_number')),
        ('LL Attempts',               lambda r: _g(r, 'll_attempts')),
        ('PL Date',                   lambda r: _g(r, 'pl_date')),
        ('PL Number',                 lambda r: _g(r, 'pl_number')),
        ('PL Attempts',               lambda r: _g(r, 'pl_attempts')),
    ]
    ENCOURAGEMENT = [
        ('Encouraged By',             lambda r: _g(r, 'agg_encouraged')),
    ]
    PREV_EMPLOYMENT = [
        ('Worked Before',             lambda r: _yn(r, 'worked_before')),
        ('Previous Work Type',        lambda r: _res(r, 'prev_work_type', 'prev_work_other')),
        ('Previous Monthly Income',   lambda r: _g(r, 'prev_monthly_income')),
    ]
    FINANCIAL = [
        ('Has Bank Account',          lambda r: _yn(r, 'has_bank')),
        ('Bank Account Type',         lambda r: _g(r, 'bank_account_type')),
        ('Bank Name',                 lambda r: _g(r, 'bank_name')),
        ('Bank Account No.',          lambda r: _g(r, 'bank_acct')),
        ('Has Savings',               lambda r: _yn(r, 'has_savings')),
        ('Savings Where',             lambda r: _g(r, 'savings_where')),
        ('Has Debt',                  lambda r: _yn(r, 'has_debt')),
        ('Debt Amount',               lambda r: _g(r, 'debt_amount')),
        ('Loan Source',               lambda r: _g(r, 'loan_source')),
        ('Loan Repayment',            lambda r: _g(r, 'loan_repay')),
    ]
    HOUSING = [
        ('House Ownership',           lambda r: _g(r, 'house_ownership')),
        ('House Ownership Detail',    lambda r: _g(r, 'house_own_detail')),
        ('Property Name Holder',      lambda r: _res(r, 'property_name_holder', 'property_name_other')),
        ('Property Paper Keeper',     lambda r: _res(r, 'property_paper_keeper', 'property_paper_other')),
        ('House Type',                lambda r: _g(r, 'house_type')),
        ('Household Assets',          lambda r: _g(r, 'agg_assets')),
        ('Has Mobile',                lambda r: _yn(r, 'has_mobile')),
        ('Is Smart Phone',            lambda r: _yn(r, 'is_smart_phone')),
        ('Phone User',                lambda r: _g(r, 'phone_user')),
        ('Phone Usage',               lambda r: _g(r, 'phone_usage')),
    ]
    DISABILITY = [
        ('Disability In House',       lambda r: _yn(r, 'disability_in_house')),
        ('Disability Relation',       lambda r: _g(r, 'disability_relation')),
        ('Disability Type',           lambda r: _g(r, 'disability_type')),
        ('Has Disability Certificate',lambda r: _yn(r, 'has_disability_cert')),
    ]
    ORG_ASSOC = [
        ('Relative In Azad',          lambda r: _yn(r, 'relative_in_azad')),
        ('Relative Name',             lambda r: _g(r, 'relative_name')),
        ('Relative Relation',         lambda r: _g(r, 'relative_relation')),
        ('Relative Organisation',     lambda r: _g(r, 'relative_org')),
        ('Relative Designation',      lambda r: _g(r, 'relative_designation')),
        ('Relative Years',            lambda r: _g(r, 'relative_years')),
    ]
    GBV = [
        ('Violence Place',            lambda r: _g(r, 'violence_place')),
        ('Violence By',               lambda r: _g(r, 'violence_by')),
        ('Violence When',             lambda r: _g(r, 'violence_when')),
        ('GBV Situations',            lambda r: _g(r, 'agg_gbv_situations')),
        ('Wants Support',             lambda r: _yn(r, 'want_support')),
        ('Support Kinds',             lambda r: _g(r, 'agg_gbv_support')),
        ('Support Other',             lambda r: _g(r, 'support_other')),
        ('Housework Hours',           lambda r: _g(r, 'housework_hours')),
    ]
    # References are emitted INLINE (wide format) — see the group builder
    # below. No flat SPEC entry needed.
    COMMITMENT = [
        ('Commitment Aware',          lambda r: _yn(r, 'commit_aware')),
        ('Commitment Ready',          lambda r: _yn(r, 'commit_ready')),
        ('Commitment Amount',         lambda r: _g(r, 'commit_amount')),
        ('Commitment Paid Status',    lambda r: _g(r, 'commit_paid_status')),
        ('Commitment Paid Amount',    lambda r: _g(r, 'commit_paid_amount')),
        ('Commitment Partial Amount', lambda r: _g(r, 'commit_partial_amt')),
    ]
    META = [
        ('Photo Uploaded',            lambda r: 'Yes' if r.get('photo_path') else 'No'),
        ('Documents Uploaded',        lambda r: _g(r, 'agg_doc_count')),
        ('Created',                   lambda r: str(r['created_at'])[:10] if r.get('created_at') else ''),
    ]

    # Every column the SPEC consumes (directly or via joins/aggregates).
    # Anything in the row NOT listed here gets appended as its own
    # "Additional Fields" group so newly added DB fields can never
    # silently drop out of the export.
    _CONSUMED = {
        'id', 'enrollment_no', 'photo_path', 'financial_year', 'batch_id',
        'state_code', 'district_code', 'centre_code', 'area_code', 'area_other',
        'basti', 'name', 'enrollment_date', 'enrollment_type', 'date_of_birth',
        'age_at_enrollment', 'blood_group', 'mobile', 'email',
        'current_address', 'permanent_address', 'caste_category', 'religion',
        'gender', 'marital_status', 'age_at_marriage', 'living_with',
        'education_qualification', 'still_studying', 'studying_class',
        'how_known_azad', 'mobilization_activity', 'status',
        'source_response_id', 'created_at', 'updated_at', 'deleted_at',
        'created_by', 'updated_by', 'users_id',
        'caste_other', 'religion_other', 'gender_other', 'living_with_other',
        'education_other', 'num_emergency_contacts', 'has_social_media',
        'came_with_lic_type', 'll_date', 'll_number', 'll_attempts',
        'pl_date', 'pl_number', 'pl_attempts', 'worked_before',
        'prev_work_type', 'prev_work_other', 'prev_monthly_income',
        'has_bank', 'bank_account_type', 'bank_name', 'bank_acct',
        'has_savings', 'savings_where', 'has_debt', 'debt_amount',
        'loan_source', 'loan_repay', 'house_ownership', 'house_own_detail',
        'property_name_holder', 'property_paper_keeper', 'house_type',
        'has_mobile', 'is_smart_phone', 'phone_user', 'phone_usage',
        'disability_in_house', 'disability_relation', 'disability_type',
        'has_disability_cert', 'relative_in_azad', 'relative_name',
        'relative_relation', 'relative_org', 'relative_designation',
        'relative_years', 'violence_place', 'violence_by', 'violence_when',
        'want_support', 'support_other', 'housework_hours', 'commit_aware',
        'commit_ready', 'commit_amount', 'commit_paid_status',
        'commit_paid_amount', 'commit_partial_amt',
        'state_name', 'district_name', 'centre_name', 'area_name', 'batch_name',
        'how_known_other', 'property_name_other', 'property_paper_other',
        'agg_emergency', 'agg_languages', 'agg_social', 'agg_net_uses',
        'agg_family', 'agg_encouraged', 'agg_assets', 'agg_gbv_situations',
        'agg_gbv_support', 'agg_references', 'agg_doc_count',
    }
    extra_cols = [k for k in (rows[0].keys() if rows else []) if k not in _CONSUMED]

    # Build headers + group-header ranges (1-indexed for merged row-1 cells)
    headers = []
    group_headers = []

    def _add_group(title, spec):
        if not spec:
            return
        start = len(headers) + 1
        headers.extend(h for h, _fn in spec)
        group_headers.append((start, len(headers), title))

    _add_group('Basic Profile', BASIC_PROFILE)

    # Family Members — inline wide format, 8 cols per member
    if max_family_members > 0:
        fam_start = len(headers) + 1
        for i in range(max_family_members):
            n = i + 1
            headers.extend([
                f'{n}. Name of the Family Member',
                'Relation',
                'Mobile',
                'Age',
                'Education',
                'Occupation',
                'Monthly Income',
                'Monthly Contribution',
            ])
        group_headers.append((fam_start, len(headers), 'Family Members'))

    _add_group('Encouragement',            ENCOURAGEMENT)
    _add_group('Previous Employment',      PREV_EMPLOYMENT)
    _add_group('Financial Status',         FINANCIAL)
    _add_group('Housing & Assets',         HOUSING)
    _add_group('Disability',               DISABILITY)
    _add_group('Organization Association', ORG_ASSOC)
    _add_group('GBV',                      GBV)

    # Reference — inline wide format, 3 cols per reference
    if max_references > 0:
        ref_start = len(headers) + 1
        for i in range(max_references):
            n = i + 1
            headers.extend([
                f'{n}. Reference Name',
                'Relation',
                'Contact No.',
            ])
        group_headers.append((ref_start, len(headers), 'References'))

    _add_group('Commitment',               COMMITMENT)
    _add_group('Meta',                     META)

    if extra_cols:
        ex_start = len(headers) + 1
        headers.extend(k.replace('_', ' ').title() for k in extra_cols)
        group_headers.append((ex_start, len(headers), 'Additional Fields'))

    # Build data rows in the same column order
    data_rows = []
    for r in rows:
        row = [fn(r) for _h, fn in BASIC_PROFILE]
        # Family cells (inline wide format, 8 cols per member, padded)
        members = fam_map.get(r['id'], [])
        for i in range(max_family_members):
            if i < len(members):
                m = members[i]
                row.extend([
                    _g(m, 'member_name'),
                    _g(m, 'relation'),
                    _g(m, 'mobile_no'),
                    _g(m, 'age'),
                    _g(m, 'education'),
                    _g(m, 'occupation'),
                    _g(m, 'monthly_income'),
                    _g(m, 'monthly_contribution'),
                ])
            else:
                row.extend([''] * 8)
        for spec in (ENCOURAGEMENT, PREV_EMPLOYMENT, FINANCIAL, HOUSING,
                     DISABILITY, ORG_ASSOC, GBV):
            row.extend(fn(r) for _h, fn in spec)
        # Reference cells (inline wide format, 3 cols per reference, padded)
        refs = ref_map.get(r['id'], [])
        for i in range(max_references):
            if i < len(refs):
                rf = refs[i]
                row.extend([
                    _g(rf, 'ref_name'),
                    _g(rf, 'relation'),
                    _g(rf, 'contact_no'),
                ])
            else:
                row.extend([''] * 3)
        for spec in (COMMITMENT, META):
            row.extend(fn(r) for _h, fn in spec)
        row.extend(_g(r, k) for k in extra_cols)
        data_rows.append(row)

    # 2026-08-26: WWW tracking columns (Created By / Updated By / Updated At)
    from routes._www_export_tracking import WWW_TRACK_HEADERS as _WT_H, www_tracking_cells as _wt_cells
    headers = list(headers) + _WT_H
    # 2026-09-19: Record Info banner over Created By + Updated By.
    group_headers = list(group_headers) + [(len(headers) - len(_WT_H) + 1, len(headers), "Record Info")]
    _wt_rows = _wt_cells(rows, "mis_azad.www_enrollment", "id", "id")
    for _wi in range(len(data_rows)):
        data_rows[_wi] = list(data_rows[_wi]) + (_wt_rows[_wi] if _wi < len(_wt_rows) else ["", ""])
    sheet = {
        'name': 'Enrollment',
        'group_headers': group_headers,
        'headers': headers,
        'rows': data_rows,
    }
    return multi_sheet_xlsx_response_v2(
        [sheet],
        f"WWW_Enrollment_List_{date.today().isoformat()}.xlsx",
    )


# =============================================================================
# READ (trainee + all child collections)
# =============================================================================
@router.get("/{trainee_id}")
def get_trainee(request: Request, trainee_id: int):
    with get_cursor() as cur:
        # ---- LEGACY FALLBACK: no normalized tables — read one row raw ----
        if not _legacy.table_exists(cur, "www_trainees"):
            # The import keeps every "Specify, if other" answer in a column
            # that immediately follows the field it qualifies.
            cur.execute(
                "SELECT e.id, e.enrollment_no, "
                "       NULLIF(TRIM(e.trainee_image), '') AS photo_path, "
                "       e.financial_year, "
                "       (SELECT b.id FROM mis_azad.www_master_batches b "
                "         WHERE b.deleted_at IS NULL "
                "           AND b.name = NULLIF(TRIM(e.batch), '') "
                "         ORDER BY (b.centre_code = " + _legacy.centre_expr("e.centre") + ") DESC, b.id "
                "         LIMIT 1) AS batch_id, "
                "       " + _legacy.geo_cols() + ", "
                "       NULLIF(TRIM(e.area), '') AS area_code, "
                "       NULLIF(TRIM(e.specify_if_any_other), '') AS area_other, "
                "       e.basti, e.name, "
                "       e.enrollment_date, e.type_of_enrollment AS enrollment_type, "
                "       e.date_of_birth, e.age_at_enrollment, "
                "       e.blood_group, e.mobile, e.email, "
                "       e.current_address, e.permanent_address, "
                "       e.caste_category, "
                "       NULLIF(TRIM(e.specify_if_any_other_3), '') AS caste_other, "
                "       e.religion, "
                "       NULLIF(TRIM(e.specify_if_any_other_4), '') AS religion_other, "
                "       e.gender, "
                "       NULLIF(TRIM(e.specify_if_any_other_category_of_women), '') "
                "           AS gender_other, "
                "       e.marital_status, e.age_at_marriage, "
                "       e.living_with, "
                "       NULLIF(TRIM(e.specify_if_any_other_place), '') AS living_with_other, "
                "       e.educational_qualification AS education_qualification, "
                "       NULLIF(TRIM(e.specify_if_any_other_5), '') AS education_other, "
                "       e.still_studying, "
                "       e.if_yes_in_which_class AS studying_class, "
                "       e.how_know_about_azad AS how_known_azad, "
                "       e.mobilization_activity, "
                "       NULLIF(TRIM(e.specify_if_any_other_2), '') AS mobilization_other, "
                "       COALESCE(NULLIF(TRIM(e.status), ''), 'Active') AS status, "
                "       e.state AS state_name, e.district AS district_name, "
                "       " + _legacy.centre_expr("e.centre") + " AS centre_name, "
                # 2026-09-02: resolve the area CODE stored in e.area to its
                # human name from www_areas (the View showed the raw code
                # e.g. 'S07092B4GP18' instead of 'Bhajan Pura'). Falls back
                # to the code when no master row matches.
                "       COALESCE((SELECT a.area_name FROM mis_azad.www_areas a "
                "                  WHERE a.area_code = NULLIF(TRIM(e.area), '') "
                "                    AND a.deleted_at IS NULL LIMIT 1), "
                "                 NULLIF(TRIM(e.area), '')) AS area_name, "
                "       NULLIF(TRIM(e.batch), '') AS batch_name, "
                # Multi-value answers are comma-joined cells on the import.
                "       " + _legacy.multi_select_array("e.emergency_contact") + " AS emergency_contacts, "
                "       " + _legacy.multi_select_array("e.social_media_platforms") + " AS social_platforms, "
                "       " + _legacy.multi_select_array("e.language_known") + " AS languages, "
                # 2026-08-11: everything below was missing from this SELECT, so
                # the Livelihood / Banking / Housing / Phone / Disability /
                # Relative / Commitment / GBV cards on the View screen rendered
                # every field as "—" even though the import carries the data.
                "       e.has_social_media, e.housework_hours, "
                "       e.worked_before, e.previous_work_type AS prev_work_type, "
                "       e.specify_if_any_other_26 AS prev_work_other, "
                "       e.previous_monthly_income AS prev_monthly_income, "
                "       e.has_bank_account AS has_bank, e.bank_account_type, "
                "       e.bank_name, e.bank_account_number AS bank_acct, "
                "       e.has_savings, e.savings_where, "
                # 2026-08-12: the import spells these two "debit", so the
                # Financial card's Has Debt? / Debt Amount read nothing.
                "       e.has_debit AS has_debt, e.debit_amount AS debt_amount, "
                "       e.loan_source, e.loan_re_payment AS loan_repay, "
                "       e.house_ownership, "
                "       e.house_ownership_details AS house_own_detail, e.house_type, "
                "       e.property_name_holder, e.property_paper_keeper, "
                "       e.specify_if_any_other_27 AS property_name_other, "
                "       e.specify_if_any_other_28 AS property_paper_other, "
                "       e.has_mobile, e.is_smartphone AS is_smart_phone, "
                "       e.phone_user, e.phone_usage, "
                "       e.disability_in_house, e.disability_relation, e.disability_type, "
                "       e.has_disability_certificate AS has_disability_cert, "
                "       e.relative_in_azad_or_sakha AS relative_in_azad, "
                "       e.related_name AS relative_name, "
                # The import misspells this one; the API name stays correct.
                "       e.relativev_relation AS relative_relation, "
                "       e.specify_if_any_other_30 AS relative_relation_other, "
                "       e.relative_organization AS relative_org, "
                "       e.relative_designation, e.relative_years, "
                # 2026-08-12: the import misspells "violence" as "voilence" in
                # two of these three, which is why the GBV card showed nothing.
                "       e.voilence_placed AS violence_place, "
                '       e."if_inside_by_whom_state_relation_with_person" '
                "           AS violence_by, "
                "       e.voilence_when AS violence_when, "
                "       e.want_support, e.support_other, "
                "       e.commitment_aware AS commit_aware, "
                "       e.commitment_ready AS commit_ready, "
                "       e.commitment_amount AS commit_amount, "
                "       e.commitment_paid_status AS commit_paid_status, "
                "       e.commitment_partial_amount AS commit_partial_amt, "
                '       e."i_am_fully_ready_to_take_up_driving_as_a_profession_and" '
                "           AS commit_ready_driving, "
                # The sheet states these three itself; the View screen used to
                # derive income totals from the member rows alone.
                "       e.number_of_member_in_family AS family_member_count, "
                "       e.monthly_family_income AS family_monthly_income, "
                "       e.per_capita_income AS family_per_capita_income, "
                # Multi-selects the View screen renders as chip rows.
                "       " + _legacy.multi_select_array("e.household_assets") + " AS assets, "
                "       " + _legacy.multi_select_array("e.internet_uses") + " AS net_uses, "
                "       " + _legacy.multi_select_array("e.gbv_situations") + " AS gbv_situations, "
                # 2026-08-12: the import's own categorisation of the abuse
                # (Physical Abuse / Financial restriction / ...).  Distinct
                # from gbv_situations, which holds the long situation
                # sentences — no row carries the same text in both — so
                # leaving this unread hid it from every screen.
                "       " + _legacy.multi_select_array(
                    'e."type_of_violence_select_all_the_options_that_are_being"'
                ) + " AS violence_types, "
                "       " + _legacy.multi_select_array("e.support_kinds") + " AS gbv_support_kinds, "
                "       " + _legacy.multi_select_array("e.encourage_by") + " AS encouraged_by, "
                "       " + _legacy.multi_select_array(
                    'e."who_discouraged_you_to_join_the_training_program"'
                ) + " AS discouraged_by, "
                "       NULLIF(TRIM(e.trainee_photo_and_documents_aadhaar_pan_card), '') "
                "           AS _document_url, "
                # The Add-LL and Add-PL screens prefill from these.
                "       " + _legacy_ll_pl_cols() + " "
                "FROM mis_azad.www_enrollment e " + _legacy.geo_joins("e") +
                _legacy_ll_pl_joins("e") +
                # 2026-08-19: delete ki hui trainee ka View 404 de, khule nahi.
                "WHERE e.id = %s AND e.deleted_at IS NULL",
                (trainee_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Trainee not found.")
            result = _row_to_dict(row)
            result["documents"] = _legacy_documents(result.pop("_document_url", None))
            result["family_members"] = _legacy_family_members(cur, trainee_id)
            # 2026-08-12: was hardcoded to [] on the belief that the import
            # carries no references. It does — three flat name/contact slots.
            result["references"] = _legacy_references(cur, trainee_id)
            # 2026-09-05: commitment payment summary. Amount Paid = SUM of
            # www_trainee_payment rows; when none exist yet the enrollment-time
            # amount is shown virtually until the first partial payment materialises it.
            _ct = _www_commit_total(result.get("enrollment_type"))
            cur.execute(
                "SELECT COALESCE(SUM(NULLIF(TRIM(payment), '')::numeric), 0) AS s, "
                "COUNT(*) AS n FROM mis_azad.www_trainee_payment "
                "WHERE trainee_id = %s AND deleted_at IS NULL",
                (trainee_id,),
            )
            _pr = cur.fetchone()
            _psum = float(_pr["s"] or 0)
            _pn = int(_pr["n"] or 0)
            if _pn > 0:
                _paid = _psum
                cur.execute(
                    "SELECT payment, payment_date FROM mis_azad.www_trainee_payment "
                    "WHERE trainee_id = %s AND deleted_at IS NULL "
                    "ORDER BY payment_date, id",
                    (trainee_id,),
                )
                _pays = [
                    {"payment": _r["payment"],
                     "payment_date": (_r["payment_date"].isoformat() if _r["payment_date"] else None)}
                    for _r in cur.fetchall()
                ]
            else:
                _enr = _www_enroll_paid_amount(
                    result.get("commit_paid_status"), result.get("commit_amount"),
                    result.get("commit_partial_amt"), _ct)
                _paid = _enr
                _pays = ([{"payment": _www_fmt_amt(_enr),
                           "payment_date": result.get("enrollment_date")}] if _enr > 0 else [])
            result["commit_total"] = _ct
            result["commit_paid"] = _paid
            result["commit_remaining"] = max(0.0, _ct - _paid)
            result["commit_status"] = (
                "Paid" if (_ct > 0 and _paid >= _ct) else ("Partial" if _paid > 0 else "Unpaid"))
            result["payments"] = _pays
            _scope.guard_detail(request, result)
            return result

        # 2026-07-31 fix: main trainee row + geo joins.  Missing assignment to
        # `result` caused UnboundLocalError when the child-table queries below
        # tried to write into it after a successful POST/PUT.
        cur.execute(
            """SELECT t.*, s.state_name, d.district_name, c.centre_name,
                       a.area_name, b.name AS batch_name
                  FROM www_enrollment t
                  LEFT JOIN central_states         s ON t.state_code    = s.state_code
                  LEFT JOIN central_districts      d ON t.district_code = d.district_code
                  LEFT JOIN central_centres        c ON t.centre_code   = c.centre_code
                  LEFT JOIN www_areas          a ON t.area_code     = a.area_code
                  LEFT JOIN www_master_batches b ON t.batch_id      = b.id
                 WHERE t.id = %s AND t.deleted_at IS NULL""",
            (trainee_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Trainee not found.")
        result = _row_to_dict(row)

        # 2026-08-01: Specify-If-other texts child row
        cur.execute(
            "SELECT how_known_other, property_name_other, property_paper_other "
            "FROM www_trainee_other_texts WHERE trainee_id = %s",
            (trainee_id,),
        )
        _ot = cur.fetchone()
        result["how_known_other"] = _ot["how_known_other"] if _ot else None
        result["property_name_other"] = _ot["property_name_other"] if _ot else None
        result["property_paper_other"] = _ot["property_paper_other"] if _ot else None

        # Basic Profile child tables
        cur.execute(
            "SELECT seq, contact_no FROM www_trainee_emergency_contacts "
            "WHERE trainee_id = %s ORDER BY seq",
            (trainee_id,),
        )
        result["emergency_contacts"] = [r["contact_no"] for r in cur.fetchall()]

        cur.execute(
            "SELECT platform FROM www_trainee_social_platforms "
            "WHERE trainee_id = %s ORDER BY platform",
            (trainee_id,),
        )
        result["social_platforms"] = [r["platform"] for r in cur.fetchall()]

        cur.execute(
            "SELECT language, can_understand, can_speak, can_read, can_write "
            "FROM www_trainee_languages WHERE trainee_id = %s ORDER BY language",
            (trainee_id,),
        )
        result["languages"] = [dict(r) for r in cur.fetchall()]

        # Phase 2 child tables
        cur.execute(
            "SELECT seq, member_name, relation, mobile_no, age, education, "
            "       occupation, monthly_income, monthly_contribution "
            "FROM www_trainee_family_members "
            "WHERE trainee_id = %s ORDER BY seq",
            (trainee_id,),
        )
        result["family_members"] = [_row_to_dict(r) for r in cur.fetchall()]

        cur.execute(
            "SELECT asset FROM www_trainee_assets WHERE trainee_id = %s ORDER BY asset",
            (trainee_id,),
        )
        result["assets"] = [r["asset"] for r in cur.fetchall()]

        cur.execute(
            "SELECT net_use FROM www_trainee_net_uses WHERE trainee_id = %s ORDER BY net_use",
            (trainee_id,),
        )
        result["net_uses"] = [r["net_use"] for r in cur.fetchall()]

        cur.execute(
            "SELECT situation, violence_category FROM www_trainee_gbv_situations "
            "WHERE trainee_id = %s ORDER BY situation",
            (trainee_id,),
        )
        result["gbv_situations"] = [dict(r) for r in cur.fetchall()]

        cur.execute(
            "SELECT support_kind FROM www_trainee_gbv_support_kinds "
            "WHERE trainee_id = %s ORDER BY support_kind",
            (trainee_id,),
        )
        result["gbv_support_kinds"] = [r["support_kind"] for r in cur.fetchall()]

        cur.execute(
            "SELECT encourager FROM www_trainee_encouraged_by "
            "WHERE trainee_id = %s ORDER BY encourager",
            (trainee_id,),
        )
        result["encouraged_by"] = [r["encourager"] for r in cur.fetchall()]

        cur.execute(
            "SELECT seq, ref_name, relation, contact_no "
            "FROM www_trainee_references "
            "WHERE trainee_id = %s ORDER BY seq",
            (trainee_id,),
        )
        result["references"] = [_row_to_dict(r) for r in cur.fetchall()]

        cur.execute(
            "SELECT id, file_name, doc_type, file_path, uploaded_by, uploaded_at "
            "FROM www_trainee_documents "
            "WHERE trainee_id = %s ORDER BY uploaded_at DESC",
            (trainee_id,),
        )
        result["documents"] = [_row_to_dict(r) for r in cur.fetchall()]

    _scope.guard_detail(request, result)
    return result


# =============================================================================
# UPDATE
# =============================================================================
@router.put("/{trainee_id}")
def update_trainee(trainee_id: int, body: TraineeIn):
    if not (body.name or "").strip():
        raise HTTPException(status_code=400, detail="Trainee name is required.")
    _validate_amounts(body)

    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_trainees"):
            cur.execute("SELECT id FROM mis_azad.www_enrollment WHERE id = %s",
                        (trainee_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Trainee not found.")
            _enr_update(cur, trainee_id, body)
            _auto_assign_llpl(cur, trainee_id, body)
            _sync_llpl_update(cur, trainee_id, body)
            return {"id": trainee_id, "ok": True}

        cur.execute("SELECT id FROM www_enrollment WHERE id = %s AND deleted_at IS NULL", (trainee_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Trainee not found.")

        cols = list(_TRAINEE_COLS)
        # 2026-08-01: photo_path is set by the separate /photo upload endpoint
        # and never travels in the form payload -- a None here must not wipe an
        # already-uploaded photo on every subsequent save.
        if body.photo_path is None and "photo_path" in cols:
            cols.remove("photo_path")
        assignments = ", ".join([f"{c} = %s" for c in cols])
        values = [getattr(body, c) for c in cols]
        values.append(trainee_id)
        cur.execute(
            f"UPDATE www_enrollment SET {assignments}, updated_at = NOW() "
            f"WHERE id = %s",
            values,
        )
        _replace_children(cur, trainee_id, body)
    return {"id": trainee_id, "ok": True}


# =============================================================================
# DELETE (soft)
# =============================================================================
@router.delete("/{trainee_id}")
def delete_trainee(trainee_id: int):
    """Trainee ko soft-delete karo -- uske module records ke saath.

    2026-08-19 (Ashish): pehle ye 501 deta tha, kyunki import ki table
    www_enrollment me deleted_at tha hi nahi aur row sach me hatane se induction
    / licence / BKS jaisa saara juda data bin-maalik ho jata. Aaj saare www
    tables me deleted_at jud gaya, isliye ab asli soft delete hota hai: row DB
    me bachi rehti hai, bas har list se hat jati hai. Ashish ne option (b)
    chuna -- enrollment ke saath uske saare module records bhi mark hote hain.
    Wapas laana ho to: UPDATE ... SET deleted_at = NULL.
    """
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_trainees"):
            res = _legacy.soft_delete_trainee(cur, trainee_id)
            if not res["enrollment"]:
                raise HTTPException(
                    status_code=404,
                    detail="Trainee not found or already deleted.")
            return {"id": trainee_id, "ok": True, "deleted_with": res["children"]}
        cur.execute(
            "UPDATE www_enrollment SET deleted_at = NOW() "
            "WHERE id = %s AND deleted_at IS NULL RETURNING id",
            (trainee_id,),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Trainee not found or already deleted.")
    return {"id": trainee_id, "ok": True}

# =============================================================================
# CREATE LMS USER
# =============================================================================
_lms_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _build_lms_username(trainee_id: int, enrollment_no: Optional[str] = None, name: Optional[str] = None) -> str:
    target_name = name or enrollment_no or ""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(target_name).strip().lower()).strip("_")[:20]
    return f"{slug}_{trainee_id}" if slug else f"user_{trainee_id}"


def _generate_lms_password(name: Any = None, mobile: Optional[str] = None, length: int = 10) -> str:
    if isinstance(name, int):
        length = name
        name = None
    clean_name = re.sub(r"[^a-zA-Z]", "", str(name or "").strip()).capitalize()
    name_part = clean_name[:4] if len(clean_name) >= 4 else (clean_name or "Azad")
    digits = re.sub(r"[^0-9]", "", str(mobile or "").strip())
    mobile_part = digits[-4:] if len(digits) >= 4 else (digits or "".join(secrets.choice("23456789") for _ in range(4)))
    return f"{name_part}@{mobile_part}"


def _resolve_age(row: dict) -> int:
    raw_age = row.get("age_at_enrollment")
    if raw_age is not None and str(raw_age).strip() != "":
        try:
            val = int(float(str(raw_age).strip()))
            if val > 0:
                return val
        except (TypeError, ValueError):
            pass
    dob = row.get("date_of_birth")
    if dob:
        from datetime import date as _date
        try:
            d = dob if isinstance(dob, _date) else _date.fromisoformat(str(dob)[:10])
            today = _date.today()
            age = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
            if age > 0:
                return age
        except Exception:
            pass
    return 18


@router.post("/{trainee_id}/create-lms-user")
def create_lms_user(trainee_id: int):
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT id, enrollment_no, name, email, mobile, mobile_1,
                       gender, date_of_birth, age_at_enrollment,
                       current_address, permanent_address,
                       state, district, centre, batch, status,
                       COALESCE(lms_user, 0) AS lms_user
                FROM mis_azad.www_enrollment
                WHERE id = %s AND deleted_at IS NULL
                LIMIT 1
                """,
                (trainee_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Trainee enrollment not found.")

            if int(row.get("lms_user") or 0) == 1:
                raise HTTPException(status_code=409, detail="User already exists. Unable to create LMS user.")

            mobile_no = ((row.get("mobile") or row.get("mobile_1") or "").strip()) or None
            if mobile_no:
                mobile_no = mobile_no[:20]
            enroll_no = ((row.get("enrollment_no") or "").strip()[:50]) or None
            part_name = ((row.get("name") or "").strip()[:255]) or None

            # Check against mis_azad.participantmasters:
            # enrollment_no, participant_name, and mobile_no must ALL be unique.
            # If ANY of these three matches an existing record, return 409 "User already exists. Unable to create LMS user."
            dup_conds = []
            dup_params = []
            if enroll_no:
                dup_conds.append("LOWER(TRIM(enrollment_no)) = LOWER(TRIM(%s))")
                dup_params.append(enroll_no)
            if part_name:
                dup_conds.append("LOWER(TRIM(participant_name)) = LOWER(TRIM(%s))")
                dup_params.append(part_name)
            if mobile_no:
                dup_conds.append("TRIM(mobile_no) = TRIM(%s)")
                dup_params.append(mobile_no)

            if dup_conds:
                cur.execute(
                    f"""
                    SELECT participant_id FROM mis_azad.participantmasters
                    WHERE ({" OR ".join(dup_conds)}) AND deleted_at IS NULL
                    LIMIT 1
                    """,
                    dup_params,
                )
                if cur.fetchone():
                    raise HTTPException(status_code=409, detail="User already exists. Unable to create LMS user.")

            username = _build_lms_username(trainee_id, enroll_no, part_name)
            plain_password = _generate_lms_password(part_name, mobile_no)
            password_hash = _lms_pwd_ctx.hash(plain_password)

            address = ((row.get("current_address") or row.get("permanent_address") or "").strip()) or None
            location_parts = [
                str(p).strip()
                for p in (row.get("centre"), row.get("district"), row.get("state"))
                if p and str(p).strip()
            ]
            location = (", ".join(location_parts))[:200] if location_parts else None
            age = _resolve_age(row)
            tr_status = ((row.get("status") or "Active").strip())[:6] or "Active"
            email_val = ((row.get("email") or "").strip()[:500]) or None
            gender_val = ((row.get("gender") or "").strip()[:50]) or None

            cur.execute(
                """
                INSERT INTO mis_azad.participantmasters (
                    enrollment_no, participant_name, username, password,
                    gender, age, email, mobile_no, location, address,
                    status, trainee_status,
                    created_at, updated_at, progress_status, course_progress
                )
                VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    '1', %s,
                    NOW(), NOW(), 0, 0
                )
                RETURNING participant_id
                """,
                (
                    enroll_no,
                    part_name,
                    username[:255],
                    password_hash,
                    gender_val,
                    age,
                    email_val,
                    mobile_no,
                    location,
                    address,
                    tr_status,
                ),
            )
            inserted = cur.fetchone()
            participant_id = inserted["participant_id"] if inserted else None

            cur.execute(
                """
                UPDATE mis_azad.www_enrollment
                SET lms_user = 1,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (trainee_id,),
            )

        return {
            "ok": True,
            "trainee_id": trainee_id,
            "participant_id": participant_id,
            "username": username,
            "password": plain_password,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create LMS user for trainee %s: %s", trainee_id, e)
        raise HTTPException(status_code=500, detail="Unable to create LMS user.")

