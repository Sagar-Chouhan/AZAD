"""WWW Data Form.

Admin builds forms (Google-Forms-style). Each form is assigned to one or
more states. Published forms are visible to PI / State Lead / District
Lead whose state matches an assigned state. Those users submit the form
(multiple times) and see their own submissions. Admin sees every
submission form-wise with filters (duration + state + district + centre).

Routes are scoped under /api/www-data-forms. The table set is isolated:
mis_azad.www_data_form, _field, _state, _submission. No other module /
table is touched.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from routes._role_scope import get_current_user

router = APIRouter(prefix="/api/www-data-forms", tags=["WWW Data Form"])

# ------- role helpers -------
_ADMIN_ROLES = {"super admin", "admin", "super_admin",
                "power user", "power_user"}
_FILLER_ROLES = {"pi", "project incharge (pi)", "state lead", "district lead"}

def _role_lc(user) -> str:
    return (user.get("role_name") or "").strip().lower() if user else ""

def _is_admin(user) -> bool:
    return _role_lc(user) in _ADMIN_ROLES

def _is_filler(user) -> bool:
    return _role_lc(user) in _FILLER_ROLES

def _require_login(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Login required.")
    return user

def _require_admin(request: Request):
    user = _require_login(request)
    if not _is_admin(user):
        raise HTTPException(403, "Admin only.")
    return user

# -------------- models --------------
class FormCreate(BaseModel):
    title: str
    description: Optional[str] = None

class FormUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class FieldCreate(BaseModel):
    label: str
    field_type: str                     # see allowed list below
    options: Optional[List[str]] = None
    is_required: Optional[bool] = False
    display_order: Optional[int] = 0

class FieldUpdate(BaseModel):
    label: Optional[str] = None
    field_type: Optional[str] = None
    options: Optional[List[str]] = None
    is_required: Optional[bool] = None
    display_order: Optional[int] = None

class StatesSet(BaseModel):
    state_codes: List[str]

class SubmissionCreate(BaseModel):
    data: Dict[str, Any]                # {"<field_id>": value, ...}

_ALLOWED_TYPES = {
    "short_text", "paragraph", "number", "date", "email", "phone",
    "dropdown", "radio", "checkbox", "yes_no",
}

# -------------- helpers --------------
def _form_row(cur, form_id):
    cur.execute("""SELECT id, title, description, is_published, published_at,
                          created_by, created_at, updated_at
                     FROM mis_azad.www_data_form
                    WHERE id = %s AND deleted_at IS NULL""", (form_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Form not found.")
    return row

def _form_states(cur, form_id):
    cur.execute("""SELECT s.state_code,
                          COALESCE(c.state_name, s.state_code) AS state_name
                     FROM mis_azad.www_data_form_state s
                LEFT JOIN mis_azad.central_states c ON c.state_code = s.state_code
                    WHERE s.form_id = %s
                    ORDER BY state_name""", (form_id,))
    return cur.fetchall()

def _form_fields(cur, form_id):
    cur.execute("""SELECT id, label, field_type, options, is_required, display_order
                     FROM mis_azad.www_data_form_field
                    WHERE form_id = %s AND deleted_at IS NULL
                    ORDER BY display_order, id""", (form_id,))
    out = []
    for r in cur.fetchall():
        d = dict(r)
        if isinstance(d.get("options"), str):
            try: d["options"] = json.loads(d["options"])
            except Exception: pass
        out.append(d)
    return out

def _user_scope_state(user):
    """The state_code that scopes a filler-user to a form."""
    return (user.get("state_code") or "").strip() or None

# -------------- FORM list / detail --------------
@router.get("")
def list_forms(request: Request,
               only_published: Optional[bool] = None,
               state_code: Optional[str] = None):
    user = _require_login(request)
    is_adm = _is_admin(user)
    with get_cursor() as cur:
        conds = ["f.deleted_at IS NULL"]
        params = []
        if is_adm:
            if only_published is True:
                conds.append("f.is_published = TRUE")
            if only_published is False:
                conds.append("f.is_published = FALSE")
            if state_code:
                conds.append("EXISTS (SELECT 1 FROM mis_azad.www_data_form_state s "
                             "WHERE s.form_id = f.id AND s.state_code = %s)")
                params.append(state_code)
        else:
            if not _is_filler(user):
                raise HTTPException(403, "Not permitted.")
            sc = _user_scope_state(user)
            if not sc:
                return {"data": []}
            conds.append("f.is_published = TRUE")
            conds.append("EXISTS (SELECT 1 FROM mis_azad.www_data_form_state s "
                         "WHERE s.form_id = f.id AND s.state_code = %s)")
            params.append(sc)

        where = "WHERE " + " AND ".join(conds)
        cur.execute(
            "SELECT f.id, f.title, f.description, f.is_published, f.published_at, "
            "       f.created_by, f.created_at, f.updated_at, "
            "       (SELECT array_agg(s.state_code ORDER BY s.state_code) "
            "          FROM mis_azad.www_data_form_state s WHERE s.form_id = f.id) AS state_codes, "
            "       (SELECT COUNT(*) FROM mis_azad.www_data_form_field fd "
            "         WHERE fd.form_id = f.id AND fd.deleted_at IS NULL) AS field_count "
            "FROM mis_azad.www_data_form f "
            + where + " ORDER BY f.id DESC",
            params
        )
        return {"data": cur.fetchall()}


@router.get("/{form_id}")
def get_form(request: Request, form_id: int):
    user = _require_login(request)
    is_adm = _is_admin(user)
    with get_cursor() as cur:
        row = _form_row(cur, form_id)
        states = _form_states(cur, form_id)
        fields = _form_fields(cur, form_id)
        # Filler users can only read published forms assigned to their state.
        if not is_adm:
            if not _is_filler(user):
                raise HTTPException(403, "Not permitted.")
            if not row["is_published"]:
                raise HTTPException(403, "Form not available.")
            sc = _user_scope_state(user)
            allowed = {s["state_code"] for s in states}
            if sc not in allowed:
                raise HTTPException(403, "Form not assigned to your state.")
        return {"form": row, "states": states, "fields": fields}


@router.post("")
def create_form(request: Request, body: FormCreate):
    user = _require_admin(request)
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO mis_azad.www_data_form (title, description, created_by) "
            "VALUES (%s, %s, %s) RETURNING id",
            (body.title.strip(), (body.description or "").strip() or None, user.get("id"))
        )
        new_id = cur.fetchone()["id"]
    return {"id": new_id, "message": "Form created."}


@router.put("/{form_id}")
def update_form(request: Request, form_id: int, body: FormUpdate):
    _require_admin(request)
    sets, params = [], []
    if body.title is not None:
        sets.append("title = %s"); params.append(body.title.strip())
    if body.description is not None:
        sets.append("description = %s"); params.append((body.description or "").strip() or None)
    if not sets:
        return {"message": "No change."}
    sets.append("updated_at = NOW()")
    params.append(form_id)
    with get_cursor() as cur:
        _form_row(cur, form_id)
        cur.execute(
            f"UPDATE mis_azad.www_data_form SET {', '.join(sets)} WHERE id = %s",
            params
        )
    return {"message": "Form updated."}


@router.delete("/{form_id}")
def delete_form(request: Request, form_id: int):
    _require_admin(request)
    with get_cursor() as cur:
        _form_row(cur, form_id)
        cur.execute(
            "UPDATE mis_azad.www_data_form SET deleted_at = NOW() WHERE id = %s",
            (form_id,)
        )
    return {"message": "Form deleted."}


@router.post("/{form_id}/publish")
def publish_form(request: Request, form_id: int):
    _require_admin(request)
    with get_cursor() as cur:
        _form_row(cur, form_id)
        # must have at least one field + one state
        cur.execute("SELECT COUNT(*) AS n FROM mis_azad.www_data_form_field "
                    "WHERE form_id = %s AND deleted_at IS NULL", (form_id,))
        if int(cur.fetchone()["n"] or 0) == 0:
            raise HTTPException(400, "Add at least one field before publishing.")
        cur.execute("SELECT COUNT(*) AS n FROM mis_azad.www_data_form_state "
                    "WHERE form_id = %s", (form_id,))
        if int(cur.fetchone()["n"] or 0) == 0:
            raise HTTPException(400, "Assign at least one state before publishing.")
        cur.execute(
            "UPDATE mis_azad.www_data_form "
            "   SET is_published = TRUE, published_at = NOW(), updated_at = NOW() "
            " WHERE id = %s", (form_id,)
        )
    return {"message": "Form published."}


@router.post("/{form_id}/unpublish")
def unpublish_form(request: Request, form_id: int):
    _require_admin(request)
    with get_cursor() as cur:
        _form_row(cur, form_id)
        cur.execute(
            "UPDATE mis_azad.www_data_form "
            "   SET is_published = FALSE, updated_at = NOW() WHERE id = %s",
            (form_id,)
        )
    return {"message": "Form unpublished."}

# -------------- FIELDS --------------
@router.get("/{form_id}/fields")
def list_fields(request: Request, form_id: int):
    _require_login(request)
    with get_cursor() as cur:
        _form_row(cur, form_id)
        return {"data": _form_fields(cur, form_id)}


@router.post("/{form_id}/fields")
def add_field(request: Request, form_id: int, body: FieldCreate):
    _require_admin(request)
    if body.field_type not in _ALLOWED_TYPES:
        raise HTTPException(400, f"field_type must be one of: {sorted(_ALLOWED_TYPES)}")
    options_json = json.dumps(body.options) if body.options else None
    with get_cursor() as cur:
        _form_row(cur, form_id)
        cur.execute(
            "INSERT INTO mis_azad.www_data_form_field "
            "  (form_id, label, field_type, options, is_required, display_order) "
            "VALUES (%s, %s, %s, %s::jsonb, %s, %s) RETURNING id",
            (form_id, body.label.strip(), body.field_type,
             options_json, bool(body.is_required), int(body.display_order or 0))
        )
        new_id = cur.fetchone()["id"]
    return {"id": new_id, "message": "Field added."}


@router.put("/{form_id}/fields/{field_id}")
def update_field(request: Request, form_id: int, field_id: int, body: FieldUpdate):
    _require_admin(request)
    sets, params = [], []
    if body.label is not None:
        sets.append("label = %s"); params.append(body.label.strip())
    if body.field_type is not None:
        if body.field_type not in _ALLOWED_TYPES:
            raise HTTPException(400, f"field_type must be one of: {sorted(_ALLOWED_TYPES)}")
        sets.append("field_type = %s"); params.append(body.field_type)
    if body.options is not None:
        sets.append("options = %s::jsonb"); params.append(json.dumps(body.options))
    if body.is_required is not None:
        sets.append("is_required = %s"); params.append(bool(body.is_required))
    if body.display_order is not None:
        sets.append("display_order = %s"); params.append(int(body.display_order))
    if not sets:
        return {"message": "No change."}
    sets.append("updated_at = NOW()")
    params.extend([form_id, field_id])
    with get_cursor() as cur:
        cur.execute(
            f"UPDATE mis_azad.www_data_form_field SET {', '.join(sets)} "
            " WHERE form_id = %s AND id = %s AND deleted_at IS NULL",
            params
        )
    return {"message": "Field updated."}


@router.delete("/{form_id}/fields/{field_id}")
def delete_field(request: Request, form_id: int, field_id: int):
    _require_admin(request)
    with get_cursor() as cur:
        cur.execute(
            "UPDATE mis_azad.www_data_form_field "
            "   SET deleted_at = NOW() "
            " WHERE form_id = %s AND id = %s AND deleted_at IS NULL",
            (form_id, field_id)
        )
    return {"message": "Field deleted."}


# -------------- STATE ASSIGNMENT --------------
@router.post("/{form_id}/states")
def set_states(request: Request, form_id: int, body: StatesSet):
    _require_admin(request)
    codes = [c.strip() for c in (body.state_codes or []) if c and c.strip()]
    with get_cursor() as cur:
        _form_row(cur, form_id)
        cur.execute("DELETE FROM mis_azad.www_data_form_state WHERE form_id = %s", (form_id,))
        for code in codes:
            cur.execute(
                "INSERT INTO mis_azad.www_data_form_state (form_id, state_code) "
                "VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (form_id, code)
            )
    return {"message": f"{len(codes)} state(s) assigned."}


# -------------- SUBMISSIONS --------------
@router.post("/{form_id}/submissions")
def create_submission(request: Request, form_id: int, body: SubmissionCreate):
    user = _require_login(request)
    is_adm = _is_admin(user)
    if not (is_adm or _is_filler(user)):
        raise HTTPException(403, "Not permitted.")
    with get_cursor() as cur:
        form = _form_row(cur, form_id)
        if not form["is_published"] and not is_adm:
            raise HTTPException(403, "Form not available.")
        fields = _form_fields(cur, form_id)
        if not is_adm:
            states = _form_states(cur, form_id)
            sc = _user_scope_state(user)
            allowed = {s["state_code"] for s in states}
            if sc not in allowed:
                raise HTTPException(403, "Form not assigned to your state.")

        # Validate required fields are present + non-empty.
        data = body.data or {}
        for f in fields:
            if f["is_required"]:
                v = data.get(str(f["id"])) or data.get(f["id"])
                missing = v is None or v == "" or (isinstance(v, list) and not v)
                if missing:
                    raise HTTPException(400, f'Required field missing: "{f["label"]}"')

        # Build the stored data with field_id keys as strings.
        clean = {}
        for f in fields:
            k = str(f["id"])
            v = data.get(k, data.get(f["id"]))
            if v is not None:
                clean[k] = v

        cur.execute(
            "INSERT INTO mis_azad.www_data_form_submission "
            "  (form_id, submitted_by, state_code, district_code, centre_code, data) "
            "VALUES (%s, %s, %s, %s, %s, %s::jsonb) RETURNING id",
            (form_id, user.get("id"),
             user.get("state_code"), user.get("district_code"), user.get("centre_code"),
             json.dumps(clean))
        )
        new_id = cur.fetchone()["id"]
    return {"id": new_id, "message": "Submission saved."}


@router.get("/{form_id}/submissions")
def list_submissions(request: Request, form_id: int,
                     date_from: Optional[str] = None,
                     date_to: Optional[str] = None,
                     state_code: Optional[str] = None,
                     district_code: Optional[str] = None,
                     centre_code: Optional[str] = None,
                     page: int = 1, limit: int = 50):
    user = _require_login(request)
    is_adm = _is_admin(user)
    page = max(page, 1); limit = max(min(limit, 500), 1); offset = (page - 1) * limit
    with get_cursor() as cur:
        _form_row(cur, form_id)
        conds = ["s.deleted_at IS NULL", "s.form_id = %s"]
        params = [form_id]
        if is_adm:
            if date_from:    conds.append("s.created_at::date >= %s"); params.append(date_from)
            if date_to:      conds.append("s.created_at::date <= %s"); params.append(date_to)
            if state_code:   conds.append("s.state_code = %s");        params.append(state_code)
            if district_code:conds.append("s.district_code = %s");     params.append(district_code)
            if centre_code:  conds.append("s.centre_code = %s");       params.append(centre_code)
        else:
            if not _is_filler(user):
                raise HTTPException(403, "Not permitted.")
            conds.append("s.submitted_by = %s"); params.append(user.get("id"))
        where = " WHERE " + " AND ".join(conds)
        cur.execute("SELECT COUNT(*) AS n FROM mis_azad.www_data_form_submission s " + where, params)
        total = int(cur.fetchone()["n"] or 0)
        cur.execute(
            "SELECT s.id, s.form_id, s.submitted_by, s.state_code, s.district_code, s.centre_code, "
            "       s.data, s.created_at, s.updated_at, "
            "       u.username AS submitted_by_name, "
            "       cs.state_name, cd.district_name, cc.centre_name "
            "  FROM mis_azad.www_data_form_submission s "
            "  LEFT JOIN mis_azad.mis_user u ON u.id = s.submitted_by "
            "  LEFT JOIN mis_azad.central_states cs ON cs.state_code = s.state_code "
            "  LEFT JOIN mis_azad.central_districts cd ON cd.district_code = s.district_code "
            "  LEFT JOIN mis_azad.central_centres cc ON cc.centre_code = s.centre_code "
            + where + " ORDER BY s.id DESC LIMIT %s OFFSET %s",
            params + [limit, offset]
        )
        rows = cur.fetchall()
    return {"total": total, "page": page, "limit": limit, "data": rows}


@router.get("/{form_id}/submissions/{sub_id}")
def get_submission(request: Request, form_id: int, sub_id: int):
    user = _require_login(request)
    is_adm = _is_admin(user)
    with get_cursor() as cur:
        _form_row(cur, form_id)
        cur.execute(
            "SELECT s.*, u.username AS submitted_by_name "
            "  FROM mis_azad.www_data_form_submission s "
            "  LEFT JOIN mis_azad.mis_user u ON u.id = s.submitted_by "
            " WHERE s.id = %s AND s.form_id = %s AND s.deleted_at IS NULL",
            (sub_id, form_id)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Submission not found.")
        if not is_adm and row["submitted_by"] != user.get("id"):
            raise HTTPException(403, "Not permitted.")
        fields = _form_fields(cur, form_id)
    return {"submission": row, "fields": fields}


@router.delete("/{form_id}/submissions/{sub_id}")
def delete_submission(request: Request, form_id: int, sub_id: int):
    user = _require_login(request)
    is_adm = _is_admin(user)
    with get_cursor() as cur:
        cur.execute(
            "SELECT submitted_by FROM mis_azad.www_data_form_submission "
            " WHERE id = %s AND form_id = %s AND deleted_at IS NULL",
            (sub_id, form_id)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Submission not found.")
        if not is_adm and row["submitted_by"] != user.get("id"):
            raise HTTPException(403, "Not permitted.")
        cur.execute(
            "UPDATE mis_azad.www_data_form_submission "
            "   SET deleted_at = NOW() WHERE id = %s", (sub_id,)
        )
    return {"message": "Submission deleted."}
