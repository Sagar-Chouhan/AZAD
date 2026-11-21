"""WWW PL (Permanent Licence) Stories."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from pydantic import BaseModel
from typing import Optional, List
import sys, os, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from routes import _www_legacy as _legacy
from routes import _www_scope as _scope
from routes._www_list_sort import www_list_order


def _legacy_row_select():
    """SELECT list mapping an imported www_pl_stories row onto API names.

    The import spells several columns differently from the normalized
    schema — note "qulaification"/"qaulification", both typos carried
    over from the spreadsheet headings — and splits the biological /
    adopted answer across two columns instead of one.
    """
    return (
        "SELECT p.id, p.enrollment_id AS trainee_id, "
        # Stored as 1/0 on the import where the normalized column is boolean.
        "       (p.consent_to_share_photo_and_story <> 0) AS consent_given, "
        # 2026-08-18: text bhejne se View "--" dikhata tha aur Edit ka
        # radio "No" ko truthy maankar "Yes" par set kar deta tha (save
        # karne par jawab palat jata). Asli boolean bhejo.
        "       CASE LOWER(TRIM(COALESCE(p.is_your_qaulification_the_same_as_the_one_you_mentioned, '')))   WHEN 'yes' THEN TRUE  WHEN 'y' THEN TRUE   WHEN 'true' THEN TRUE WHEN '1' THEN TRUE   WHEN 'no' THEN FALSE  WHEN 'n' THEN FALSE   WHEN 'false' THEN FALSE WHEN '0' THEN FALSE   ELSE NULL END "
        "           AS is_qualification_same, "
        "       NULLIF(TRIM(p.if_no_please_specify_your_updated_qualification), '') "
        "           AS updated_qualification, "
        "       p.address, p.marital_status, "
        "       CASE LOWER(TRIM(COALESCE(p.do_you_have_children, '')))   WHEN 'yes' THEN TRUE  WHEN 'y' THEN TRUE   WHEN 'true' THEN TRUE WHEN '1' THEN TRUE   WHEN 'no' THEN FALSE  WHEN 'n' THEN FALSE   WHEN 'false' THEN FALSE WHEN '0' THEN FALSE   ELSE NULL END "
        "           AS has_children, "
        "       COALESCE("
        "           NULLIF(TRIM(p.if_yes_are_they_biological_children_or_adopted_biologic), ''), "
        "           NULLIF(TRIM(p.if_yes_are_they_biological_children_or_adopted_adopted), '')) "
        "           AS children_type, "
        "       p.number_of_children AS num_children, "
        "       p.current_status, "
        "       NULLIF(TRIM(p.if_under_training_which_stage), '') AS under_training_stage, "
        "       p.family_background, "
        "       NULLIF(TRIM(p.what_are_the_2_key_things_you_have_learnt_so_far_in_you), '') "
        "           AS key_things_learnt, "
        "       NULLIF(TRIM(p.how_do_you_feel_after_coming_for_training_in_azad), '') "
        "           AS feeling_after_training, "
        "       NULLIF(TRIM(p.what_is_your_dream_aspiration_for_the_future), '') "
        "           AS dream_aspiration, "
        "       NULLIF(TRIM(p.how_did_you_come_to_know_about_azad_from_whom), '') "
        "           AS how_known_azad, "
        "       NULLIF(TRIM(p.obstacles_or_challenges_that_you_have_overcome), '') "
        "           AS obstacles_overcome, "
        # 2026-08-18: pehle ARRAY[...] ek hi value ko array me lapet
        # deta tha. Ab column me newline se alag ki hui poori list hoti
        # hai -- use tod kar array banao. Purani single-URL rows me koi
        # newline nahi, to wo ek element ki list ban jati hain.
        "       (SELECT COALESCE(ARRAY_AGG(v) FILTER (WHERE v <> ''), ARRAY[]::text[])    FROM (SELECT TRIM(s) AS v            FROM regexp_split_to_table(                  COALESCE(p.photo_of_the_trainee, ''), E'\\n') AS s) q) "
        "           AS image_paths, "
        "       COALESCE(p.is_draft, false) AS is_draft, "
        "       p.created_at, "
        "       " + _legacy.enroll_no() + ", p.name, "
        # 2026-08-18: mobile/batch placeholder the, isliye View par
        # hamesha "--" dikhta tha. _te = www_enrollment (trainee_join).
        "       NULLIF(TRIM(_te.mobile), '') AS mobile, "
        "       " + _legacy.geo_cols() + ", "
        "       p.date_of_joining, p.date_of_birth, p.date_of_pl, "
        "       p.education_qulaification AS education_qualification, "
        "       NULLIF(TRIM(_te.batch), '') AS batch_name, NULL::int AS batch_id, "
        + _legacy.trainee_status("p") +
        "FROM mis_azad.www_pl_stories p " + _legacy.geo_joins("p") + _legacy.trainee_join("p")
    )


def _legacy_filters(state_code, centre_code, current_status, name, district_code=None):
    """WHERE clause + params shared by the legacy list and export paths."""
    conds = ["NULLIF(TRIM(p.name), '') IS NOT NULL", "p.deleted_at IS NULL"]
    params = []
    if state_code:     conds.append(_legacy.state_filter());     params.append(state_code)
    if district_code:  conds.append(_legacy.district_filter());  params.append(district_code)
    if centre_code:    conds.append(_legacy.centre_filter("p")); params.append(centre_code)
    if current_status:
        # 'Under training' aur 'Undertraining' ek hi cheez hain -- space aur
        # case hata kar milao, warna ek record chhoot jata tha.
        conds.append("REPLACE(LOWER(TRIM(p.current_status)), ' ', '') = "
                     "REPLACE(LOWER(TRIM(%s)), ' ', '')")
        params.append(current_status)
    if name:           conds.append("(" + _legacy.name_match("p.name") + " OR _te.enrollment_no ILIKE %s)");          params.append(_legacy.name_pattern(name)); params.append(_legacy.name_pattern(name))
    return "WHERE " + " AND ".join(conds), params


def _yn(v):
    """The import stores the yes/no answers as text, not booleans."""
    if v is None:
        return None
    if isinstance(v, bool):
        return "Yes" if v else "No"
    return v


# API field -> imported www_pl_stories column, for the legacy write path.
# 2026-08-17: is_draft ab apne column me jata hai (pehle drop hota tha, isliye
# "Save as Draft" ke baad list me koi farq nahi dikhta tha); children_type goes to
# the "_biologic" half of the split answer because the read side COALESCEs
# that column first and the "_adopted" half is empty in this import.
_LEGACY_UPDATE_MAP = {
    "is_qualification_same":  "is_your_qaulification_the_same_as_the_one_you_mentioned",
    "updated_qualification":  "if_no_please_specify_your_updated_qualification",
    "address":                "address",
    "marital_status":         "marital_status",
    "has_children":           "do_you_have_children",
    "children_type":          "if_yes_are_they_biological_children_or_adopted_biologic",
    "num_children":           "number_of_children",
    "current_status":         "current_status",
    "under_training_stage":   "if_under_training_which_stage",
    "family_background":      "family_background",
    "key_things_learnt":      "what_are_the_2_key_things_you_have_learnt_so_far_in_you",
    "feeling_after_training": "how_do_you_feel_after_coming_for_training_in_azad",
    "dream_aspiration":       "what_is_your_dream_aspiration_for_the_future",
    "how_known_azad":         "how_did_you_come_to_know_about_azad_from_whom",
    "obstacles_overcome":     "obstacles_or_challenges_that_you_have_overcome",
    "consent_given":          "consent_to_share_photo_and_story",
    "image_paths":            "photo_of_the_trainee",
    "is_draft":               "is_draft",
}

# Fields the import stores as free text where the API models them as bool.
_LEGACY_YN_FIELDS = ("is_qualification_same", "has_children")


def _legacy_value(field, value):
    """Convert one API value to what the import's column expects."""
    if field in _LEGACY_YN_FIELDS:
        return _yn(value)
    if field == "consent_given":
        # Stored 1/0 as an integer on the import.
        return None if value is None else (1 if value else 0)
    if field == "image_paths":
        # 2026-08-18 (Ashish): import ki table me photo ka ek hi column hai,
        # aur yahan pehle sirf value[0] rakha jata tha -- baaki saari image
        # bina kisi warning ke gir jati thin (form "N images added" dikha kar
        # bhi ek hi save karta tha). Ab poori list newline se jod kar usi
        # column me rakhte hain; read side ise wapas array bana leta hai.
        if value is None:
            return None
        if isinstance(value, (list, tuple)):
            paths = [str(x).strip() for x in value if x is not None and str(x).strip()]
            return "\n".join(paths) if paths else None
        return value
    return value
try:
    from config import UPLOAD_DIR, MAX_FILE_SIZE
except Exception:
    UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    MAX_FILE_SIZE = 5 * 1024 * 1024

router = APIRouter(prefix="/api/www-pl-stories", tags=["WWW PL Stories"])


class PLCreate(BaseModel):
    trainee_id: int
    consent_given: Optional[bool] = None
    is_qualification_same: Optional[bool] = None
    updated_qualification: Optional[str] = None
    address: Optional[str] = None
    marital_status: Optional[str] = None
    has_children: Optional[bool] = None
    children_type: Optional[str] = None
    num_children: Optional[int] = None
    current_status: Optional[str] = None
    under_training_stage: Optional[str] = None
    family_background: Optional[str] = None
    key_things_learnt: Optional[str] = None
    feeling_after_training: Optional[str] = None
    dream_aspiration: Optional[str] = None
    how_known_azad: Optional[str] = None
    obstacles_overcome: Optional[str] = None
    image_paths: Optional[List[str]] = None
    is_draft: Optional[bool] = False


class PLUpdate(BaseModel):
    consent_given: Optional[bool] = None
    is_qualification_same: Optional[bool] = None
    updated_qualification: Optional[str] = None
    address: Optional[str] = None
    marital_status: Optional[str] = None
    has_children: Optional[bool] = None
    children_type: Optional[str] = None
    num_children: Optional[int] = None
    current_status: Optional[str] = None
    under_training_stage: Optional[str] = None
    family_background: Optional[str] = None
    key_things_learnt: Optional[str] = None
    feeling_after_training: Optional[str] = None
    dream_aspiration: Optional[str] = None
    how_known_azad: Optional[str] = None
    obstacles_overcome: Optional[str] = None
    image_paths: Optional[List[str]] = None
    is_draft: Optional[bool] = None


def _row_select():
    return (
        "SELECT p.*, t.enrollment_no, t.name, t.mobile, "
        "       t.state_code, t.district_code, t.centre_code, "
        "       t.enrollment_date AS date_of_joining, t.date_of_birth, "
        "       t.education_qualification, "
        "       COALESCE(b.name, NULL) AS batch_name, b.id AS batch_id "
        "FROM www_pl_stories p "
        "JOIN www_enrollment t ON t.id = p.trainee_id "
        "LEFT JOIN www_master_batches b ON b.id = t.batch_id "
    )


@router.get("")
def list_pl(
    request: Request,
    enrollment_id: Optional[int] = None,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    current_status: Optional[str] = None,
    name: Optional[str] = None,
    sort_by: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
):
    page = max(page, 1); limit = max(limit, 1); offset = (page - 1) * limit
    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        # ---- LEGACY FALLBACK: www_pl_stories exists but with legacy columns;
        #      key off www_trainees (the missing join target) instead. ----
        if not _legacy.table_exists(cur, "www_trainees"):
            lwhere, lparams = _legacy_filters(state_code, centre_code, current_status, name, district_code=district_code)
            if enrollment_id:
                lwhere += " AND p.enrollment_id = %s"; lparams.append(enrollment_id)
            _df = request.query_params.get("date_from"); _dt = request.query_params.get("date_to")
            if _df: lwhere += " AND p.created_at >= %s"; lparams.append(_df)
            if _dt: lwhere += " AND p.created_at <= %s"; lparams.append(_dt)
            cur.execute(
                "SELECT COUNT(*) AS total FROM mis_azad.www_pl_stories p "
                + _legacy.geo_joins("p") + _legacy.trainee_join("p") + lwhere,
                lparams,
            )
            total = cur.fetchone()["total"]
            cur.execute(
                _legacy_row_select() + lwhere + " ORDER BY " + www_list_order(sort_by, "p.name", "p.id", "p.id DESC") + " LIMIT %s OFFSET %s",
                lparams + [limit, offset],
            )
            rows = cur.fetchall()
            return {"total": total, "page": page, "limit": limit, "data": rows}

        conds = ["p.deleted_at IS NULL"]
        params = []
        if state_code:    conds.append("t.state_code = %s");      params.append(state_code)
        if district_code: conds.append("t.district_code = %s");   params.append(district_code)
        if centre_code:   conds.append("t.centre_code = %s");     params.append(centre_code)
        if batch_id:      conds.append("t.batch_id = %s");        params.append(batch_id)
        if current_status:conds.append("p.current_status = %s");  params.append(current_status)
        if name:          conds.append(_legacy.name_match("t.name"));        params.append(_legacy.name_pattern(name))
        where = "WHERE " + " AND ".join(conds)
        cur.execute(
            "SELECT COUNT(*) AS total FROM www_pl_stories p "
            "JOIN www_enrollment t ON t.id = p.trainee_id " + where,
            params,
        )
        total = cur.fetchone()["total"]
        sql = _row_select() + where + " ORDER BY " + www_list_order(sort_by, "p.name", "p.created_at", "p.created_at DESC NULLS LAST, p.id DESC") + " LIMIT %s OFFSET %s"
        cur.execute(sql, params + [limit, offset])
        rows = cur.fetchall()
        return {"total": total, "page": page, "limit": limit, "data": rows}

@router.get("/{pl_id}")
def get_pl(request: Request, pl_id: int):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_trainees"):
            cur.execute(_legacy_row_select() + "WHERE p.id = %s", (pl_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "PL Story not found.")
            _scope.guard_detail(request, row)
            return row

        cur.execute(_row_select() + "WHERE p.id = %s AND p.deleted_at IS NULL", (pl_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "PL Story not found.")
    _scope.guard_detail(request, row)
    return row


@router.post("")
def create_pl(body: PLCreate):
    with get_cursor() as cur:
        # 2026-08-18 (Ashish): flow guard -- picker ki rok server par bhi.
        _legacy.assert_flow(cur, body.trainee_id, stage="PL Story")
        # ---- LEGACY FALLBACK: seed the row's identity/geography from the
        #      enrollment it belongs to, exactly as the import itself does. ----
        if not _legacy.table_exists(cur, "www_trainees"):
            payload = body.model_dump(exclude_unset=True)
            cols, vals = [], []
            for field, column in _LEGACY_UPDATE_MAP.items():
                if field not in payload:
                    continue
                cols.append(column)
                vals.append(_legacy_value(field, payload[field]))
            placeholders = "".join(", %s" for _ in cols)
            cur.execute(
                "INSERT INTO mis_azad.www_pl_stories "
                "    (enrollment_id, name, state, district, centre, "
                "     date_of_joining, date_of_birth, education_qulaification"
                + ("".join(", " + c for c in cols)) + ") "
                "SELECT e.id, e.name, e.state, e.district, e.centre, "
                "       e.enrollment_date, e.date_of_birth, e.educational_qualification"
                + placeholders + " "
                "FROM mis_azad.www_enrollment e WHERE e.id = %s "
                "RETURNING id",
                vals + [body.trainee_id],
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Trainee not found.")
            return {"id": row["id"], "ok": True}

        cur.execute("SELECT 1 FROM www_enrollment WHERE id=%s", (body.trainee_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Trainee not found.")
        cur.execute(
            "INSERT INTO www_pl_stories "
            "(trainee_id, consent_given, is_qualification_same, updated_qualification, address, "
            " marital_status, has_children, children_type, num_children, "
            " current_status, under_training_stage, family_background, key_things_learnt, "
            " feeling_after_training, dream_aspiration, how_known_azad, obstacles_overcome, "
            " image_paths, is_draft) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (body.trainee_id, body.consent_given, body.is_qualification_same, body.updated_qualification,
             body.address, body.marital_status, body.has_children, body.children_type, body.num_children,
             body.current_status, body.under_training_stage, body.family_background, body.key_things_learnt,
             body.feeling_after_training, body.dream_aspiration, body.how_known_azad, body.obstacles_overcome,
             body.image_paths or [], bool(body.is_draft)),
        )
        new_id = cur.fetchone()["id"]
    return {"id": new_id, "ok": True}


@router.put("/{pl_id}")
def update_pl(pl_id: int, body: PLUpdate):
    payload = body.model_dump(exclude_unset=True)
    if not payload:
        return {"ok": True}
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_trainees"):
            lfields, lparams = [], []
            for k, v in payload.items():
                col = _LEGACY_UPDATE_MAP.get(k)
                if not col:
                    continue
                lfields.append(f"{col} = %s"); lparams.append(_legacy_value(k, v))
            if not lfields:
                return {"ok": True}
            lparams.append(pl_id)
            cur.execute("UPDATE mis_azad.www_pl_stories SET " + ", ".join(lfields) +
                        " WHERE id = %s", lparams)
            if cur.rowcount == 0:
                raise HTTPException(404, "PL Story not found.")
            return {"ok": True}

        fields = []; params = []
        for k, v in payload.items():
            fields.append(f"{k} = %s"); params.append(v)
        params.append(pl_id)
        cur.execute("UPDATE www_pl_stories SET " + ",".join(fields) +
                    " WHERE id = %s AND deleted_at IS NULL", params)
        if cur.rowcount == 0:
            raise HTTPException(404, "PL Story not found.")
    return {"ok": True}


@router.delete("/{pl_id}")
def delete_pl(pl_id: int):
    with get_cursor() as cur:
        if not _legacy.table_exists(cur, "www_trainees"):
            # 2026-08-19 (Ashish): pehle ye row ko HAMESHA ke liye mita deta tha.
            # Ab deleted_at bhar dete hain -- row DB me bachi rehti hai, bas har
            # list se hat jati hai. Wapas laani ho to deleted_at = NULL.
            cur.execute("UPDATE mis_azad.www_pl_stories SET deleted_at = NOW() "
                        "WHERE id = %s AND deleted_at IS NULL", (pl_id,))
        else:
            cur.execute("UPDATE www_pl_stories SET deleted_at = now() WHERE id=%s AND deleted_at IS NULL", (pl_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "PL Story not found.")
    return {"ok": True}


# =============================================================================
# Image upload for PL Stories (multi-image, decoupled from record)
# =============================================================================
@router.post("/upload-image")
async def upload_pl_image(file: UploadFile = File(...)):
    """Upload a single image, return its public URL. Stored in shared UPLOAD_DIR."""
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/avif", "image/gif"}
    allowed_ext   = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    ctype = (file.content_type or "").split(";")[0].strip().lower()
    # 2026-08-17: pehle content_type AUR extension dono ka match zaroori tha.
    # Windows kai images ka type khali ya "application/octet-stream" bhejta
    # hai, jis se sahi JPG/PNG bhi "failed to upload" ho jati thi. Ab
    # extension hi asli kasauti hai; MIME tabhi rokta hai jab wo saaf taur
    # par koi aur cheez ho.
    ctype_ok = (ctype in allowed_types) or ctype in ("", "application/octet-stream")
    if ext not in allowed_ext or not ctype_ok:
        raise HTTPException(400, "Image must be JPG, PNG, WebP, AVIF or GIF.")
    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "Image exceeds the 25 MB size limit.")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    saved_name = f"www_pl_story_{uuid.uuid4().hex}{ext}"
    disk_path  = os.path.join(UPLOAD_DIR, saved_name)
    try:
        with open(disk_path, "wb") as dst:
            dst.write(content)
    except Exception:
        if os.path.isfile(disk_path):
            os.remove(disk_path)
        raise
    url = f"/uploads/{saved_name}"
    return {"ok": True, "url": url}


# =============================================================================
# EXPORT (Excel) — 2026-08-08
# Section-wise xlsx: Trainee Details + PL Story Details + System.
# =============================================================================
@router.get("/export/excel")
def export_pl_stories_excel(
    request: Request,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    centre_code: Optional[str] = None,
    batch_id: Optional[int] = None,
    enrollment_type: Optional[str] = None,
    current_status: Optional[str] = None,
    name: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    from datetime import date as _d
    from export_helper import multi_sheet_xlsx_response_v2

    state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
    with get_cursor() as cur:
        has_trainees = _legacy.table_exists(cur, "www_trainees")

        if not has_trainees:
            lwhere, lparams = _legacy_filters(state_code, centre_code, current_status, name, district_code=district_code)
            if date_from: lwhere += " AND p.created_at >= %s"; lparams.append(date_from)
            if date_to:   lwhere += " AND p.created_at <= %s"; lparams.append(date_to)
            cur.execute(
                "SELECT " + _legacy.enroll_no() + ", p.id AS id, p.name, "
                "       NULLIF(TRIM(_te.mobile), '') AS mobile, "
                "       NULLIF(TRIM(_te.type_of_enrollment), '') AS enrollment_type, "
                "       p.state AS state_name, p.district AS district_name, "
                "       " + _legacy.centre_expr("p.centre") + " AS centre_name, "
                "       NULL::text AS area_name, "
                "       NULLIF(TRIM(_te.batch), '') AS batch_name, "
                # 2026-08-12: DOB, the qualification as first recorded, and
                # the two dates are on www_pl_stories but were not selected.
                "       p.date_of_birth, p.date_of_joining, "
                "       NULLIF(TRIM(p.date_of_pl), '') AS date_of_pl, "
                "       NULLIF(TRIM(p.education_qulaification), '') "
                "           AS education_qualification, "
                # Stored as 1/0 on the import where the normalized column is boolean.
        "       (p.consent_to_share_photo_and_story <> 0) AS consent_given, "
                "       NULLIF(TRIM(p.is_your_qaulification_the_same_as_the_one_you_mentioned), '') "
                "           AS is_qualification_same, "
                "       NULLIF(TRIM(p.if_no_please_specify_your_updated_qualification), '') "
                "           AS updated_qualification, "
                "       p.address, p.marital_status, "
                "       NULLIF(TRIM(p.do_you_have_children), '') AS has_children, "
                "       COALESCE("
                "           NULLIF(TRIM(p.if_yes_are_they_biological_children_or_adopted_biologic), ''), "
                "           NULLIF(TRIM(p.if_yes_are_they_biological_children_or_adopted_adopted), '')) "
                "           AS children_type, "
                "       p.number_of_children AS num_children, "
                "       p.current_status, "
                "       NULLIF(TRIM(p.if_under_training_which_stage), '') AS under_training_stage, "
                "       p.family_background, "
                "       NULLIF(TRIM(p.what_are_the_2_key_things_you_have_learnt_so_far_in_you), '') "
                "           AS key_things_learnt, "
                "       NULLIF(TRIM(p.how_do_you_feel_after_coming_for_training_in_azad), '') "
                "           AS feeling_after_training, "
                "       NULLIF(TRIM(p.what_is_your_dream_aspiration_for_the_future), '') "
                "           AS dream_aspiration, "
                "       NULLIF(TRIM(p.how_did_you_come_to_know_about_azad_from_whom), '') "
                "           AS how_known_azad, "
                "       NULLIF(TRIM(p.obstacles_or_challenges_that_you_have_overcome), '') "
                "           AS obstacles_overcome, "
                "       (SELECT COALESCE(ARRAY_AGG(v) FILTER (WHERE v <> ''), ARRAY[]::text[])    FROM (SELECT TRIM(s) AS v            FROM regexp_split_to_table(                  COALESCE(p.photo_of_the_trainee, ''), E'\\n') AS s) q) "
                "           AS image_paths, "
                "       NULL::timestamptz AS created_at "
                "FROM mis_azad.www_pl_stories p " + _legacy.geo_joins("p") +
                _legacy.trainee_join("p") + lwhere +
                " ORDER BY p.id DESC",
                lparams,
            )
            rows = cur.fetchall()
        else:
            conds = ["p.deleted_at IS NULL"]; params = []
            if state_code:      conds.append("t.state_code = %s");      params.append(state_code)
            if centre_code:     conds.append("t.centre_code = %s");     params.append(centre_code)
            if batch_id:        conds.append("t.batch_id = %s");        params.append(batch_id)
            if enrollment_type: conds.append("t.enrollment_type = %s"); params.append(enrollment_type)
            if current_status:  conds.append("p.current_status = %s");  params.append(current_status)
            if name:            conds.append(_legacy.name_match("t.name"));        params.append(_legacy.name_pattern(name))
            if date_from:       conds.append("p.created_at >= %s");     params.append(date_from)
            if date_to:         conds.append("p.created_at <= %s");     params.append(date_to)
            where = "WHERE " + " AND ".join(conds)
            cur.execute(
                "SELECT p.id AS id, p.consent_given, p.is_qualification_same, p.updated_qualification, "
                "       p.address, p.marital_status, p.has_children, p.children_type, "
                "       p.num_children, p.current_status, p.under_training_stage, "
                "       p.family_background, p.key_things_learnt, p.feeling_after_training, "
                "       p.dream_aspiration, p.how_known_azad, p.obstacles_overcome, "
                "       p.image_paths, p.created_at, "
                "       t.enrollment_no, t.name, t.mobile, t.enrollment_type, "
                "       t.state_code, t.district_code, t.centre_code, t.area_code, "
                "       s.state_name, d.district_name, c.centre_name, a.area_name, "
                "       b.name AS batch_name "
                "FROM www_pl_stories p "
                "JOIN www_enrollment t ON t.id = p.trainee_id "
                "LEFT JOIN central_states    s ON s.state_code    = t.state_code "
                "LEFT JOIN central_districts d ON d.district_code = t.district_code "
                "LEFT JOIN central_centres   c ON c.centre_code   = t.centre_code "
                "LEFT JOIN www_areas     a ON a.area_code     = t.area_code "
                "LEFT JOIN www_master_batches b ON b.id = t.batch_id " +
                where + " ORDER BY p.created_at DESC",
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

    def _arr(v):
        if not v:
            return ""
        if isinstance(v, (list, tuple)):
            return ", ".join(str(x) for x in v if x is not None)
        return str(v)

    trainee_headers = [
        "Enrollment No.", "Name", "Mobile", "Enrollment Type",
        "State", "District", "Centre", "Area", "Batch",
        "Date of Birth", "Date of Joining", "Date of PL",
    ]
    pl_headers = [
        "Consent Given", "Education Qualification",
        "Is Qualification Same", "Updated Qualification",
        "Address", "Marital Status", "Has Children", "Children Type",
        "Num Children", "Current Status", "Under Training Stage",
        "Family Background", "Key Things Learnt", "Feeling After Training",
        "Dream/Aspiration", "How Known Azad", "Obstacles Overcome",
        "Image Paths",
    ]
    system_headers = ["Created At"]
    all_headers = trainee_headers + pl_headers + system_headers
    n_t, n_p, n_s = len(trainee_headers), len(pl_headers), len(system_headers)
    group_headers = [
        (1, n_t, "Trainee Details"),
        (n_t + 1, n_t + n_p, "PL Story Details"),
        (n_t + n_p + 1, n_t + n_p + n_s, "System"),
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
            _g(r, "date_of_birth"), _g(r, "date_of_joining"), _g(r, "date_of_pl"),
            _yn(r.get("consent_given")), _g(r, "education_qualification"),
            _yn(r.get("is_qualification_same")),
            _g(r, "updated_qualification"), _g(r, "address"),
            _g(r, "marital_status"), _yn(r.get("has_children")),
            _g(r, "children_type"), _g(r, "num_children"),
            _g(r, "current_status"), _g(r, "under_training_stage"),
            _g(r, "family_background"), _g(r, "key_things_learnt"),
            _g(r, "feeling_after_training"), _g(r, "dream_aspiration"),
            _g(r, "how_known_azad"), _g(r, "obstacles_overcome"),
            _arr(r.get("image_paths")),
            _g(r, "created_at"),
        ])

    # 2026-08-26: WWW tracking columns (Created By / Updated By / Updated At)
    from routes._www_export_tracking import WWW_TRACK_HEADERS as _WT_H, www_tracking_cells as _wt_cells
    all_headers = list(all_headers) + _WT_H
    # 2026-09-19: Record Info banner over Created By + Updated By.
    group_headers = list(group_headers) + [(len(all_headers) - len(_WT_H) + 1, len(all_headers), "Record Info")]
    _wt_rows = _wt_cells(rows, "mis_azad.www_pl_stories", "id")
    for _wi in range(len(data_rows)):
        data_rows[_wi] = list(data_rows[_wi]) + (_wt_rows[_wi] if _wi < len(_wt_rows) else ["", ""])
    sheets = [{
        "name": "PL Stories",
        "group_headers": group_headers,
        "headers": all_headers,
        "rows": data_rows,
    }]
    return multi_sheet_xlsx_response_v2(
        sheets,
        f"WWW_PL_Stories_{_d.today().isoformat()}.xlsx",
    )
