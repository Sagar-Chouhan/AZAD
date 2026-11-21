"""WWW Mobilisers — CRUD (admin) + mobile auth (login/refresh/change-password)
+ survey submission from the FLP mobile app.

Design goals
------------
- Provide the account layer for mobilisers who conduct WWW surveys via the
  FLP mobile app. Auth response shape mirrors /api/auth/flp-login so the
  mobile app can consume it with minimal changes.
- Survey submissions land in the same www_survey_form table that
  /api/www-surveys reads, so entries appear in the WWW Survey List
  identically to how FLP surveys appear in the FLP Survey List.
- Isolated to the WWW namespace — never touches flps / surveys tables.

Endpoints (13 total):
  GET    /api/www-mobilisers                     admin list
  POST   /api/www-mobilisers                     admin create
  GET    /api/www-mobilisers/{mid}               admin detail
  PUT    /api/www-mobilisers/{mid}               admin update
  DELETE /api/www-mobilisers/{mid}               admin soft-delete
  PATCH  /api/www-mobilisers/{mid}/status        admin status change
  POST   /api/www-mobilisers/{mid}/reset-password admin password reset
  GET    /api/www-mobilisers/export/excel        admin filter-honoring export
  POST   /api/www-mobilisers/auth/login          mobile login
  POST   /api/www-mobilisers/auth/refresh-token  mobile refresh (30-day grace)
  POST   /api/www-mobilisers/auth/change-password mobile self-service pw change
  GET    /api/www-mobilisers/me                  mobile: current mobiliser profile
  POST   /api/www-mobilisers/surveys             mobile: submit survey to www_survey_form
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from routes import _www_scope as _scope
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# 2026-08-26: HTTPBearer scheme so Swagger's Authorize dialog
# attaches the Bearer token to any endpoint that declares it as
# a dependency. The endpoints below still read the raw header
# via `request` — the dependency is only there to make the
# OpenAPI spec declare the security requirement.
_bearer = HTTPBearer(auto_error=False)
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date as _date, datetime as _dt
import sys, os, io, csv, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from routes.auth import pwd_context, create_token
from jose import jwt as _jwt
from config import JWT_SECRET as _SECRET, JWT_ALGORITHM as _ALGO

router = APIRouter(prefix="/api/www-mobilisers", tags=["WWW Mobilisers"])

# ─── constants ──────────────────────────────────────────────────────────
_REFRESH_GRACE_DAYS = 30
_ALLOWED_STATUS = {"Active", "Inactive", "Walkout"}


# ─── Pydantic ───────────────────────────────────────────────────────────

class MobiliserCreate(BaseModel):
    mobiliser_id: str  # login username
    name: str
    password: str
    mobile: Optional[str] = None
    email: Optional[str] = None
    state_code: Optional[str] = None
    district_code: Optional[str] = None
    centre_code: Optional[str] = None
    area_code: Optional[str] = None
    status: Optional[str] = "Active"


class MobiliserUpdate(BaseModel):
    name: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    state_code: Optional[str] = None
    district_code: Optional[str] = None
    centre_code: Optional[str] = None
    area_code: Optional[str] = None


class StatusBody(BaseModel):
    status: str


class ResetPwBody(BaseModel):
    new_password: str


class LoginRequest(BaseModel):
    username: str  # matches mobiliser_id
    password: str


class UserResponse(BaseModel):
    id: int
    enrollment_number: str  # = mobiliser_id (mobile app expects this key)
    name: str
    username: Optional[str] = None
    centre_id: Optional[int] = None
    centre_name: Optional[str] = None
    district_name: Optional[str] = None
    location: Optional[str] = None
    mobile: Optional[str] = None


class LoginResponse(BaseModel):
    token: str
    user: UserResponse


class ChangePwBody(BaseModel):
    old_password: str
    new_password: str


class SurveyBody(BaseModel):
    """Free-form survey payload. Any key that matches a www_survey_form
    column is inserted; unknown keys are ignored. user_id/user_name are
    stamped from the authenticated mobiliser (client cannot forge them)."""
    data: Dict[str, Any]


# ─── helpers ────────────────────────────────────────────────────────────



# 2026-10-01: mobile mobilisers were silently invisible in the Activity
# Log because this file never wrote to system_activity_log. Keep this
# a best-effort INSERT; a logging failure must never block login or a
# submitted survey.
def _mob_log_activity(request, mobiliser_row, action, resource_type=None,
                      resource_id=None, description=None, source='mobile'):
    try:
        _ip = None
        try:
            _ip = (request.headers.get('x-forwarded-for') or '').split(',')[0].strip() or \
                  request.headers.get('x-real-ip') or \
                  (request.client.host if request.client else None)
        except Exception:
            _ip = None
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO system_activity_log
                    (user_id, user_name, role_name, action,
                     resource_type, resource_id, ip_address, description, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (None,
                 (mobiliser_row or {}).get('name'),
                 'Mobiliser (WWW)',
                 action,
                 resource_type,
                 resource_id,
                 _ip,
                 description,
                 source),
            )
    except Exception:
        pass

def _authed_mobiliser(request: Request) -> Dict[str, Any]:
    """Decode Bearer token → verify mobiliser is Active. Raises 401/403."""
    auth = request.headers.get("authorization", "") or ""
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = auth.split(" ", 1)[1].strip()
    try:
        payload = _jwt.decode(token, _SECRET, algorithms=[_ALGO])
    except _jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired — please login again")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        mid = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, mobiliser_id, name, mobile, email, "
            "state_code, district_code, centre_code, area_code, status "
            "FROM www_mobilisers WHERE id = %s AND deleted_at IS NULL",
            (mid,),
        )
        m = cur.fetchone()
    if not m:
        raise HTTPException(status_code=401, detail="Mobiliser not found — please logout and login again")
    if m["status"] != "Active":
        raise HTTPException(status_code=403, detail=f"Your account is {m['status']}. Please contact admin.")
    return dict(m)


def _row_for_response(row) -> Dict[str, Any]:
    """Map a mobiliser DB row → response payload (mirrors FLP mobile user shape)."""
    return {
        "id": row["id"],
        "enrollment_number": row["mobiliser_id"],
        "name": row["name"],
        "username": row["mobiliser_id"],
        "centre_id": None,
        "centre_name": row.get("centre_name") or row.get("centre_code") or None,
        "district_name": row.get("district_name") or row.get("district_code") or None,
        "location": row.get("state_name") or row.get("state_code") or None,
        "mobile": row.get("mobile") or None,
    }


# Columns writable via /surveys — everything in www_survey_form except
# server-managed columns (_pk, server_synced_at, server_modified_at,
# deleted_at). Whitelist keeps rogue keys from injecting SQL.
_SURVEY_WRITABLE_COLS = None  # lazy-populated on first submit


def _survey_writable_cols(cur):
    global _SURVEY_WRITABLE_COLS
    if _SURVEY_WRITABLE_COLS is not None:
        return _SURVEY_WRITABLE_COLS
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'mis_azad' AND table_name = 'www_survey_form'"
    )
    all_cols = {r["column_name"] for r in cur.fetchall()}
    exclude = {"_pk", "server_synced_at", "server_modified_at", "deleted_at"}
    _SURVEY_WRITABLE_COLS = all_cols - exclude
    return _SURVEY_WRITABLE_COLS


# ─── STATIC ROUTES FIRST (avoid /{mid} eating them) ────────────────────

# 9) MOBILE LOGIN --------------------------------------------------------

@router.post("/auth/login", response_model=LoginResponse)
def mobiliser_login(req: LoginRequest):
    """
    Mobile login for WWW mobilisers.
    Response shape mirrors /api/auth/flp-login so the mobile app can consume
    it interchangeably: {token, user:{id, enrollment_number, name, username,
    centre_id, centre_name, location, mobile}}.
    """
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT m.*,
                   COALESCE(nc.centre_name, m.centre_code) AS centre_name,
                   COALESCE(nd.district_name, m.district_code) AS district_name,
                   COALESCE(ns.state_name, m.state_code)   AS state_name
            FROM www_mobilisers m
            LEFT JOIN central_centres nc ON m.centre_code = nc.centre_code
            LEFT JOIN central_districts nd ON m.district_code = nd.district_code
            LEFT JOIN central_states  ns ON m.state_code  = ns.state_code
            WHERE LOWER(m.mobiliser_id) = LOWER(%s) AND m.deleted_at IS NULL
            """,
            (req.username,),
        )
        m = cur.fetchone()

    if not m:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if m["status"] == "Inactive":
        raise HTTPException(status_code=403, detail="Your account is inactive. Please contact admin.")
    if m["status"] == "Walkout":
        raise HTTPException(status_code=403, detail="Your account has been marked as Walkout. Please contact admin.")

    valid = False
    if m["password_hash"]:
        try:
            valid = pwd_context.verify(req.password, m["password_hash"])
        except Exception:
            pass
    if not valid and req.password == m["mobiliser_id"]:  # enrollment-fallback (prototype parity)
        valid = True
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    with get_cursor() as cur:
        cur.execute("UPDATE www_mobilisers SET last_login_at = NOW() WHERE id = %s", (m["id"],))

    # 2026-10-01: best-effort audit entry so the WWW Activity Log
    # shows mobile Mobiliser logins alongside web users.
    try:
        _mob_log_activity(request=None, mobiliser_row=m, action="Login",
                          resource_type="Mobiliser",
                          description=f"Mobiliser {m['name']} logged in via mobile",
                          source="mobile")
    except Exception:
        pass

    token = create_token(m["id"], m["mobiliser_id"])
    return LoginResponse(token=token, user=UserResponse(**_row_for_response(m)))


# 10) MOBILE REFRESH TOKEN ----------------------------------------------

@router.post("/auth/refresh-token")
def mobiliser_refresh(request: Request, _cred: HTTPAuthorizationCredentials = Depends(_bearer)):
    """Re-issue a fresh JWT. Grace window: 30 days past exp."""
    auth = request.headers.get("authorization", "") or ""
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = auth.split(" ", 1)[1].strip()
    try:
        payload = _jwt.decode(token, _SECRET, algorithms=[_ALGO], options={"verify_exp": False})
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token — please logout and login again")

    try:
        mid = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    with get_cursor() as cur:
        cur.execute(
            "SELECT id, mobiliser_id, status FROM www_mobilisers "
            "WHERE id = %s AND deleted_at IS NULL",
            (mid,),
        )
        m = cur.fetchone()
    if not m:
        raise HTTPException(status_code=401, detail="Mobiliser not found — please logout and login again")
    if m["status"] in ("Inactive", "Walkout"):
        raise HTTPException(status_code=403, detail=f"Your account is {m['status']}. Please contact admin.")

    import time as _t
    exp = payload.get("exp")
    if exp:
        try:
            expired_by = _t.time() - int(exp)
            if expired_by > (_REFRESH_GRACE_DAYS * 24 * 3600):
                raise HTTPException(status_code=401, detail="Refresh window expired — please login again")
        except HTTPException:
            raise
        except Exception:
            pass

    new_token = create_token(m["id"], m["mobiliser_id"])
    return {"token": new_token}


# 11) MOBILE CHANGE PASSWORD --------------------------------------------

@router.post("/auth/change-password")
def mobiliser_change_password(request: Request, body: ChangePwBody, _cred: HTTPAuthorizationCredentials = Depends(_bearer)):
    me = _authed_mobiliser(request)
    if not body.new_password or len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    with get_cursor() as cur:
        cur.execute("SELECT password_hash FROM www_mobilisers WHERE id = %s", (me["id"],))
        row = cur.fetchone()
        valid = False
        if row and row["password_hash"]:
            try:
                valid = pwd_context.verify(body.old_password, row["password_hash"])
            except Exception:
                pass
        if not valid:
            raise HTTPException(status_code=401, detail="Old password is incorrect")
        new_hash = pwd_context.hash(body.new_password)
        cur.execute(
            "UPDATE www_mobilisers SET password_hash = %s, updated_at = NOW() WHERE id = %s",
            (new_hash, me["id"]),
        )
    return {"message": "Password updated"}


# 12) CURRENT PROFILE ---------------------------------------------------

@router.get("/me")
def mobiliser_me(request: Request, _cred: HTTPAuthorizationCredentials = Depends(_bearer)):
    me = _authed_mobiliser(request)
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT m.id, m.mobiliser_id, m.name, m.mobile, m.email,
                   m.state_code, m.district_code, m.centre_code, m.area_code,
                   m.status, m.last_login_at, m.created_at,
                   COALESCE(nc.centre_name, m.centre_code) AS centre_name,
                   COALESCE(ns.state_name,  m.state_code)  AS state_name,
                   COALESCE(nd.district_name, m.district_code) AS district_name
            FROM www_mobilisers m
            LEFT JOIN central_centres   nc ON m.centre_code   = nc.centre_code
            LEFT JOIN central_states    ns ON m.state_code    = ns.state_code
            LEFT JOIN central_districts nd ON m.district_code = nd.district_code
            WHERE m.id = %s AND m.deleted_at IS NULL
            """,
            (me["id"],),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return row


# 13) SURVEY SUBMISSION -------------------------------------------------

# 2026-08-27: Contract alignment — mobile app posts an FLP-format
# payload with sec_a_/sec_b_/sec_c_/sec_d_ keys, `head_*`, `comment`
# and an `eligible_women` array. Map each to its www_survey_form
# column; resolve state/district/area codes to names via the central_*
# tables; JSON-encode `eligible_women`; honour `mobile_local_id` as an
# idempotency key so a retry from a weak network returns the same row.
_WWWMOB_SURVEY_ALIASES = {
    # A) survey meta
    "date":                     "date_of_survey",
    "sec_a_surveyor":           "name_of_surveyer",   # server-stamped later, but honoured if present
    "sec_a_designation":        "designation",
    "sec_a_quarter":            "quarter_of_survey",
    # B) location
    "sec_b_basti":              "name_of_basti",
    "sec_b_centre":             "centre_census",       # centre NAME (per user contract)
    "sec_b_area_other":         "specify_if_any_other",
    # respondent / family head
    "sec_c_respondent_name":    "name_with_whom_the_survey_is_done",
    "sec_c_contact":            "contact_number",
    "sec_c_caste":              "caste_category",
    "sec_c_caste_other":        "specify_if_any_other_1",
    "sec_c_community":          "religion",
    "sec_c_community_other":    "specify_if_any_other_2",
    "head_name":                "head_name",
    "head_phone":               "head_phone",
    "head_address":             "address",
    # D) family + decision maker
    "sec_d_total_family_members":  "total_family_members",
    "sec_d_earning_members":       "how_many_earning_members_are_there_in_the_family",
    "sec_d_monthly_income":        "total_monthly_income",
    "sec_d_per_capita":            "per_capita_income",
    "sec_d_decision_maker":        "who_is_the_primary_decision_maker_in_the_family",
    "sec_d_decision_maker_other":  "specify_if_any_other_3",
    "sec_d_decision_maker_name":   "name_of_the_primary_decision_maker_in_the_family",
    "comment":                     "decision_maker_education",
    "sec_d_occupation":            "what_is_the_occupation_of_primary_decision_maker_of_the_family",
    "sec_d_native_place":          "family_s_native_place",
    "sec_d_male_family":           "total_male_members_in_the_family",
    "sec_d_prefer_boy":            "if_there_is_a_boy_in_the_age_group_of_13_18_in_the_house_will_y",
    "sec_d_boys_group":            "how_many_boys_in_this_age_group",
    "sec_d_female_family":         "total_female_members_in_the_family",
    "sec_d_prefer_girl":           "if_there_are_13_15_year_old_girls_in_the_family_will_you_prefer",
    "sec_d_age_girl":              "how_many_girls_in_the_family_in_this_age_group",
    "sec_d_women18_count":         "how_many_women_in_the_family_who_are_18",
    # metadata (kept for provenance)
    "mobile_local_id":          "mobile_local_id",
    "schema_version":           "schema_version",
    "mobile_app_version":       "app_version_during_data_fill",
    "build_number":             "build_number",
    # legacy short-forms (kept from earlier smoke tests)
    "surveyor_name":            "name_of_surveyer",
    "surveyor":                 "name_of_surveyer",
    "name_of_surveyor":         "name_of_surveyer",
    "name":                     "name_with_whom_the_survey_is_done",
    "respondent_name":          "name_with_whom_the_survey_is_done",
    "mobile":                   "contact_number",
    "mobile_number":            "contact_number",
    "phone":                    "contact_number",
    "phone_number":             "contact_number",
    "state_name":               "state",
    "district_name":            "district",
    "block_name":               "block",
    "grampanchayat_name":       "grampanchayat",
    "monthly_family_income":    "total_monthly_income",
    "monthly_income":           "total_monthly_income",
    "earning_members":          "how_many_earning_members_are_there_in_the_family",
    "latitude":                 "latitude_mobile",
    "longitude":                "longitude_mobile",
    "accuracy":                 "accuracy_mobile",
    "app_version":              "app_version_during_data_fill",
}

# Keys we intentionally swallow (server derives them elsewhere).
_WWWMOB_SURVEY_META_SKIP = {
    "flp_id",                 # user identity — comes from JWT
    "program",                # always WWW for this endpoint
    "eligible_women_count",   # derivable from array length
    "data", "answers", "form_data", "survey_data",
    "token", "auth", "authorization",
}

# Flat columns filled from eligible_women[0] so the existing View page
# section still shows the primary woman without JSON parsing.
_WWWMOB_ELIGIBLE_WOMAN_FLAT = {
    "name":                        "name_of_the_women_family_members_who_are_18",
    "contact":                     "contact_number_1",
    "phone":                       "contact_number_1",
    "age":                         "age",
    "marital_status":              "marital_status",
    "education":                   "education",
    "education_other":             "specify_any_other",
    "living_with_whom":            "living_with_whom",
    "living_with_whom_other":      "specify_any_other_1",
    "is_working":                  "is_she_working",
    "kind_of_work":                "what_kind_of_work_is_she_doing",
    "monthly_income":              "what_is_the_monthly_income",
    "documents":                   "how_many_women_in_the_family_who_are_18_what_documents_does_she",
    "documents_other":             "specify_any_other_2",
    "interested":                  "are_you_intrested_joining_www_program_at_azad",
    "challenges":                  "if_yes_what_challenges_you_might_face",
    "training_type":               "which_type_of_training_do_you_want_to_do_post_joining_azad_www_",
    "eligible":                    "is_she_eligible_to_join_the_www_program",
    "comments":                    "comments_of_the_surveyer_on_the_readiness_of_the_women_with_who",
    "eligible_and_interested":     "is_she_eligible_and_intrested",
}


def _wwwmob_resolve_state(cur, code_or_name):
    """sec_a_state can arrive as a code (S07) or a plain state name.
    Return (state_code, state_name)."""
    if not code_or_name: return (None, None)
    v = str(code_or_name).strip()
    cur.execute(
        "SELECT state_code, state_name FROM central_states "
        "WHERE deleted_at IS NULL AND (state_code = %s OR LOWER(state_name) = LOWER(%s)) "
        "LIMIT 1",
        (v, v),
    )
    r = cur.fetchone()
    return (r["state_code"], r["state_name"]) if r else (v, v)


def _wwwmob_resolve_district(cur, code_or_name):
    if not code_or_name: return (None, None)
    v = str(code_or_name).strip()
    cur.execute(
        "SELECT district_code, district_name FROM central_districts "
        "WHERE (district_code = %s OR LOWER(district_name) = LOWER(%s)) "
        "LIMIT 1",
        (v, v),
    )
    r = cur.fetchone()
    return (r["district_code"], r["district_name"]) if r else (v, v)


def _wwwmob_resolve_area(cur, code_or_name):
    if not code_or_name: return (None, None)
    v = str(code_or_name).strip()
    cur.execute(
        "SELECT area_code, area_name FROM central_areas "
        "WHERE (area_code = %s OR LOWER(area_name) = LOWER(%s)) "
        "LIMIT 1",
        (v, v),
    )
    r = cur.fetchone()
    return (r["area_code"], r["area_name"]) if r else (v, v)


@router.post("/surveys")
async def submit_survey(request: Request, _cred: HTTPAuthorizationCredentials = Depends(_bearer)):
    """Mobile app posts a survey → row inserted into www_survey_form.

    2026-08-27: full contract with the FLP-format mobile payload.
      * All 44 sec_*/head_*/comment/eligible_women keys map to real columns.
      * State / district / area codes are resolved to names via central_*.
      * eligible_women array is stored as JSON in eligible_women_json AND
        the first woman flat-populates the primary-woman columns.
      * mobile_local_id makes retries idempotent — returns the existing
        row's id on repeat.
    """
    me = _authed_mobiliser(request)

    try:
        raw = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Request body must be valid JSON")
    if not isinstance(raw, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")

    # Unwrap common wrapper keys.
    payload = None
    for wrap_key in ("data", "answers", "form_data", "survey_data"):
        v = raw.get(wrap_key)
        if isinstance(v, dict) and v:
            payload = v; break
    if payload is None:
        payload = {k: v for k, v in raw.items() if k not in _WWWMOB_SURVEY_META_SKIP}

    # Idempotency — same mobiliser + mobile_local_id → return existing row.
    mobile_local_id = payload.get("mobile_local_id")
    if mobile_local_id:
        with get_cursor() as cur:
            cur.execute(
                "SELECT _pk FROM www_survey_form "
                "WHERE user_id = %s AND mobile_local_id = %s AND deleted_at IS NULL "
                "ORDER BY _pk DESC LIMIT 1",
                (str(me["id"]), str(mobile_local_id)),
            )
            existing = cur.fetchone()
        if existing:
            import sys as _sys
            _sys.stdout.write(
                f"[www-mob-survey] IDEMPOTENT hit — mobile_local_id={mobile_local_id} → pk={existing['_pk']}\n"
            )
            _sys.stdout.flush()
            return {"id": existing["_pk"], "message": "Survey already submitted",
                    "saved_fields": 0, "rejected_fields": []}

    with get_cursor() as cur:
        writable = _survey_writable_cols(cur)
        forbidden = {"user_id", "user_name", "server_synced_at",
                     "server_modified_at", "_pk", "deleted_at"}
        col_val = {}   # column → value (last-wins), keeps insertion order
        rejected = []

        # Extract + JSON-encode eligible_women; also flat-populate primary woman.
        eligible = payload.pop("eligible_women", None)
        if isinstance(eligible, list) and eligible:
            col_val["eligible_women_json"] = json.dumps(eligible, ensure_ascii=False)
            first = eligible[0] if isinstance(eligible[0], dict) else {}
            for src_k, dst_col in _WWWMOB_ELIGIBLE_WOMAN_FLAT.items():
                v = first.get(src_k)
                if v is not None and v != "" and dst_col in writable:
                    col_val[dst_col] = v

        # Resolve geo codes → both the code AND the name column.
        st_val = payload.pop("sec_a_state", None)
        if st_val is not None:
            code, name = _wwwmob_resolve_state(cur, st_val)
            if code is not None: col_val["state_code"] = code
            if name is not None: col_val["state"] = name
        ds_val = payload.pop("sec_b_district", None)
        if ds_val is not None:
            code, name = _wwwmob_resolve_district(cur, ds_val)
            if code is not None: col_val["district_code"] = code
            if name is not None: col_val["district"] = name
        ar_val = payload.pop("sec_b_area", None)
        if ar_val is not None:
            # www_survey_form has no area_code column — only the name.
            _, name = _wwwmob_resolve_area(cur, ar_val)
            if name is not None: col_val["name_of_area_census"] = name

        # Walk the rest of the payload.
        for k, v in payload.items():
            if k in _WWWMOB_SURVEY_META_SKIP: continue
            if k in forbidden: continue
            dst = _WWWMOB_SURVEY_ALIASES.get(k, k)
            if dst not in writable:
                rejected.append(k); continue
            if isinstance(v, (dict, list)):
                col_val[dst] = json.dumps(v, ensure_ascii=False)
            else:
                col_val[dst] = v

        # Server-stamped identity + timestamps (always win).
        col_val["user_id"]          = me["id"]
        col_val["user_name"]        = me["mobiliser_id"]
        col_val["name_of_surveyer"] = me["name"]
        col_val["server_synced_at"] = _dt.utcnow()

        cols = list(col_val.keys())
        vals = [col_val[c] for c in cols]
        placeholders = ", ".join(["%s"] * len(cols))
        cols_sql = ", ".join(cols)
        cur.execute(
            f"INSERT INTO www_survey_form ({cols_sql}) VALUES ({placeholders}) RETURNING _pk",
            vals,
        )
        new_pk = cur.fetchone()["_pk"]

    import sys as _sys
    _sys.stdout.write(
        f"[www-mob-survey] pk={new_pk} user={me.get('mobiliser_id')} "
        f"raw_keys={list(raw.keys())} saved={len(cols)-4} rejected={rejected}\n"
    )
    _sys.stdout.flush()

    return {"id": new_pk, "message": "Survey submitted",
            "saved_fields": len(cols) - 4, "rejected_fields": rejected}

# ─── EXPORT (static before /{mid}) ─────────────────────────────────────

# 8) ADMIN EXPORT -------------------------------------------------------

@router.get("/export/excel")
def export_mobilisers(request: Request,
                      state_code: Optional[str] = None,
                      district_code: Optional[str] = None,
                      centre_code: Optional[str] = None,
                      status: Optional[str] = None,
                      name: Optional[str] = None):
    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    conds = ["m.deleted_at IS NULL"]
    params: list = []
    if state_code:    conds.append("m.state_code = %s");    params.append(state_code)
    if district_code: conds.append("m.district_code = %s"); params.append(district_code)
    if centre_code:   conds.append("m.centre_code = %s");   params.append(centre_code)
    if status:        conds.append("m.status = %s");        params.append(status)
    if name:          conds.append("m.name ILIKE %s");      params.append(f"%{name}%")
    where = " AND ".join(conds)
    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT m.id, m.mobiliser_id, m.name, m.mobile, m.email,
                   COALESCE(ns.state_name, m.state_code)      AS state_name,
                   COALESCE(nd.district_name, m.district_code) AS district_name,
                   COALESCE(nc.centre_name, m.centre_code)     AS centre_name,
                   m.status, m.last_login_at, m.created_at
            FROM www_mobilisers m
            LEFT JOIN central_states    ns ON m.state_code    = ns.state_code
            LEFT JOIN central_districts nd ON m.district_code = nd.district_code
            LEFT JOIN central_centres   nc ON m.centre_code   = nc.centre_code
            WHERE {where} ORDER BY m.id DESC
            """,
            params,
        )
        rows = cur.fetchall()
    from routes._www_export_tracking import www_tracking_cells as _wt_cells
    _wt = _wt_cells(rows, "mis_azad.www_mobilisers", "id", "id")
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["S.No", "Mobiliser ID", "Name", "Mobile", "Email",
                "State", "District", "Centre", "Status",
                "Last Login", "Created At", "Created By", "Updated By", "Updated At"])
    for i, r in enumerate(rows, 1):
        w.writerow([
            i, r.get("mobiliser_id") or "", r.get("name") or "",
            r.get("mobile") or "", r.get("email") or "",
            r.get("state_name") or "", r.get("district_name") or "",
            r.get("centre_name") or "", r.get("status") or "",
            r["last_login_at"].isoformat() if r.get("last_login_at") else "",
            r["created_at"].isoformat() if r.get("created_at") else "",
        ] + _wt[i-1])
    from export_helper import csv_string_to_xlsx_response
    return csv_string_to_xlsx_response(
        out.getvalue(),
        f"WWW_Mobilisers_{_date.today().isoformat()}.xlsx",
    )


# ─── ADMIN CRUD ────────────────────────────────────────────────────────

# 1) LIST ---------------------------------------------------------------

@router.get("")
def list_mobilisers(request: Request,
                    state_code: Optional[str] = None,
                    district_code: Optional[str] = None,
                    centre_code: Optional[str] = None,
                    status: Optional[str] = None,
                    name: Optional[str] = None,
                    page: int = 1, limit: int = 10):
    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    offset = max(0, (page - 1) * limit)
    conds = ["m.deleted_at IS NULL"]
    params: list = []
    if state_code:    conds.append("m.state_code = %s");    params.append(state_code)
    if district_code: conds.append("m.district_code = %s"); params.append(district_code)
    if centre_code:   conds.append("m.centre_code = %s");   params.append(centre_code)
    if status:        conds.append("m.status = %s");        params.append(status)
    if name:          conds.append("(m.name ILIKE %s OR m.mobiliser_id ILIKE %s)"); params += [f"%{name}%", f"%{name}%"]
    where = " AND ".join(conds)
    with get_cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS total FROM www_mobilisers m WHERE {where}", params)
        total = cur.fetchone()["total"]
        cur.execute(
            f"""
            SELECT m.id, m.mobiliser_id, m.name, m.mobile, m.email,
                   m.state_code, m.district_code, m.centre_code, m.area_code,
                   m.status, m.last_login_at, m.created_at, m.updated_at,
                   COALESCE(ns.state_name, m.state_code)      AS state_name,
                   COALESCE(nd.district_name, m.district_code) AS district_name,
                   COALESCE(nc.centre_name, m.centre_code)     AS centre_name
            FROM www_mobilisers m
            LEFT JOIN central_states    ns ON m.state_code    = ns.state_code
            LEFT JOIN central_districts nd ON m.district_code = nd.district_code
            LEFT JOIN central_centres   nc ON m.centre_code   = nc.centre_code
            WHERE {where} ORDER BY m.id DESC LIMIT %s OFFSET %s
            """,
            params + [limit, offset],
        )
        rows = cur.fetchall()
    return {"total": total, "page": page, "limit": limit, "data": rows}


# 2) CREATE -------------------------------------------------------------

@router.post("")
def create_mobiliser(body: MobiliserCreate):
    if not body.mobiliser_id or not body.mobiliser_id.strip():
        raise HTTPException(400, "mobiliser_id is required")
    if not body.name or not body.name.strip():
        raise HTTPException(400, "name is required")
    if not body.password or len(body.password) < 6:
        raise HTTPException(400, "password must be at least 6 characters")
    status = (body.status or "Active").strip()
    if status not in _ALLOWED_STATUS:
        raise HTTPException(400, f"status must be one of {sorted(_ALLOWED_STATUS)}")

    with get_cursor() as cur:
        cur.execute(
            "SELECT id FROM www_mobilisers WHERE LOWER(mobiliser_id) = LOWER(%s) AND deleted_at IS NULL",
            (body.mobiliser_id.strip(),),
        )
        if cur.fetchone():
            raise HTTPException(409, "A mobiliser with this ID already exists")
        pw = pwd_context.hash(body.password)
        cur.execute(
            """
            INSERT INTO www_mobilisers
              (mobiliser_id, name, password_hash, mobile, email,
               state_code, district_code, centre_code, area_code, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (body.mobiliser_id.strip(), body.name.strip(), pw,
             body.mobile, body.email,
             body.state_code, body.district_code, body.centre_code, body.area_code,
             status),
        )
        new_id = cur.fetchone()["id"]
    return {"id": new_id, "message": "Mobiliser created"}


# 3) DETAIL -------------------------------------------------------------

@router.get("/{mid}")
def get_mobiliser(request: Request, mid: int):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT m.id, m.mobiliser_id, m.name, m.mobile, m.email,
                   m.state_code, m.district_code, m.centre_code, m.area_code,
                   m.status, m.last_login_at, m.created_at, m.updated_at,
                   COALESCE(ns.state_name, m.state_code)      AS state_name,
                   COALESCE(nd.district_name, m.district_code) AS district_name,
                   COALESCE(nc.centre_name, m.centre_code)     AS centre_name
            FROM www_mobilisers m
            LEFT JOIN central_states    ns ON m.state_code    = ns.state_code
            LEFT JOIN central_districts nd ON m.district_code = nd.district_code
            LEFT JOIN central_centres   nc ON m.centre_code   = nc.centre_code
            WHERE m.id = %s AND m.deleted_at IS NULL
            """,
            (mid,),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Mobiliser not found")
    _scope.guard_detail(request, row)
    return row


# 4) UPDATE -------------------------------------------------------------

@router.put("/{mid}")
def update_mobiliser(mid: int, body: MobiliserUpdate):
    with get_cursor() as cur:
        cur.execute("SELECT id FROM www_mobilisers WHERE id = %s AND deleted_at IS NULL", (mid,))
        if not cur.fetchone():
            raise HTTPException(404, "Mobiliser not found")
        fields, params = [], []
        for k in ("name", "mobile", "email", "state_code", "district_code",
                  "centre_code", "area_code"):
            v = getattr(body, k, None)
            if v is not None:
                fields.append(f"{k} = %s"); params.append(v)
        if not fields:
            raise HTTPException(400, "Nothing to update")
        params.append(mid)
        cur.execute(
            f"UPDATE www_mobilisers SET {', '.join(fields)}, updated_at = NOW() WHERE id = %s",
            params,
        )
    return {"message": "Mobiliser updated"}


# 5) SOFT-DELETE --------------------------------------------------------

@router.delete("/{mid}")
def delete_mobiliser(mid: int):
    with get_cursor() as cur:
        cur.execute("SELECT id FROM www_mobilisers WHERE id = %s AND deleted_at IS NULL", (mid,))
        if not cur.fetchone():
            raise HTTPException(404, "Mobiliser not found")
        cur.execute("UPDATE www_mobilisers SET deleted_at = NOW() WHERE id = %s", (mid,))
    return {"message": "Mobiliser deleted"}


# 6) STATUS CHANGE ------------------------------------------------------

@router.patch("/{mid}/status")
def set_mobiliser_status(mid: int, body: StatusBody):
    s = (body.status or "").strip()
    if s not in _ALLOWED_STATUS:
        raise HTTPException(400, f"status must be one of {sorted(_ALLOWED_STATUS)}")
    with get_cursor() as cur:
        cur.execute("SELECT id FROM www_mobilisers WHERE id = %s AND deleted_at IS NULL", (mid,))
        if not cur.fetchone():
            raise HTTPException(404, "Mobiliser not found")
        cur.execute(
            "UPDATE www_mobilisers SET status = %s, updated_at = NOW() WHERE id = %s",
            (s, mid),
        )
    return {"message": f"Status set to {s}"}


# 7) ADMIN RESET PASSWORD ----------------------------------------------

@router.post("/{mid}/reset-password")
def reset_mobiliser_password(mid: int, body: ResetPwBody):
    if not body.new_password or len(body.new_password) < 6:
        raise HTTPException(400, "new_password must be at least 6 characters")
    with get_cursor() as cur:
        cur.execute("SELECT id FROM www_mobilisers WHERE id = %s AND deleted_at IS NULL", (mid,))
        if not cur.fetchone():
            raise HTTPException(404, "Mobiliser not found")
        new_hash = pwd_context.hash(body.new_password)
        cur.execute(
            "UPDATE www_mobilisers SET password_hash = %s, updated_at = NOW() WHERE id = %s",
            (new_hash, mid),
        )
    return {"message": "Password reset"}
