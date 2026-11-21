"""WWW Case Studies module routes.

Cloned from routes/flp_case_study.py on 2026-09-21 for the WWW module.
The FK is `enrollment_id` -> `www_enrollment.id`. Geography is stored
as the resolved codes (state_code / district_code / centre_code) so
_www_scope can filter without JOINs on every read. The snapshot is
built at insert time from the enrollment row via the same lookup
pattern _www_legacy.geo_joins uses (centre_code first, district fallback).

Endpoints:
  GET    /api/www-case-studies                   - paginated list (scoped)
  GET    /api/www-case-studies/export/excel      - export xlsx (scoped)
  GET    /api/www-case-studies/trainees/picker   - trainee dropdown data (scoped)
  POST   /api/www-case-studies                   - create
  GET    /api/www-case-studies/{id}              - read (guarded)
  PUT    /api/www-case-studies/{id}              - update (guarded)
  DELETE /api/www-case-studies/{id}              - soft-delete (guarded)
  POST   /api/www-case-studies/{id}/photo        - upload profile photo
  POST   /api/www-case-studies/{id}/attachment   - upload extra attachment
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from typing import Optional, List, Any
from pydantic import BaseModel
import sys, os, uuid, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from config import UPLOAD_DIR
from routes._www_scope import scope_geo, guard_detail, DENY
from routes._www_legacy import geo_joins

router = APIRouter(prefix="/api/www-case-studies", tags=["WWW Case Studies"])

_CATEGORIES = (
    'Personal Transformation', 'Family Impact', 'Community Impact',
    'Workplace / Livelihood', 'Gender Justice Advocacy',
    'Health / Wellbeing', 'Education', 'Other',
)
_STATUSES = ('Ongoing', 'Sustained Change', 'Needs Follow-up', 'Completed')


class CaseStudyBody(BaseModel):
    enrollment_id: int
    title: str
    category: Optional[str] = None
    category_other: Optional[str] = None
    story_date: Optional[str] = None
    period: Optional[str] = None
    story: Optional[str] = None
    challenges: Optional[str] = None
    actions: Optional[str] = None
    impact: Optional[str] = None
    quote: Optional[str] = None
    status: Optional[str] = 'Ongoing'
    status_date: Optional[str] = None
    status_notes: Optional[str] = None
    remarks: Optional[str] = None


def _fetch_enrollment_snapshot(cur, enrollment_id: int):
    """Pull denorm fields for a case-study row from www_enrollment,
    resolving the text state/district/centre columns to the codes used
    for RBAC. Same lookup pattern as _www_legacy.geo_joins."""
    joins = geo_joins("e")
    cur.execute(
        f"""
        SELECT e.id,
               e.enrollment_no AS enrollment_number,
               COALESCE(e.name, '') AS member_name,
               COALESCE(_gs.state_code,    '') AS state_code,
               COALESCE(_gd.district_code, '') AS district_code,
               COALESCE(_gc.centre_code,   '') AS centre_code
        FROM mis_azad.www_enrollment e
        {joins}
        WHERE e.id = %s AND e.deleted_at IS NULL
        """,
        (enrollment_id,),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Trainee (enrollment) not found")
    return row


def _list_where(state_code, district_code, centre_code, batch, category, status, q):
    conditions = ["cs.deleted_at IS NULL"]
    params: List[Any] = []
    if state_code:
        conditions.append("cs.state_code = %s"); params.append(state_code)
    if district_code:
        conditions.append("cs.district_code = %s"); params.append(district_code)
    if centre_code:
        conditions.append("cs.centre_code = %s"); params.append(centre_code)
    if batch:
        conditions.append("NULLIF(TRIM(e.batch), '') = %s"); params.append(batch)
    if category:
        conditions.append("cs.category = %s"); params.append(category)
    if status:
        conditions.append("cs.status = %s"); params.append(status)
    if q:
        conditions.append("(cs.title ILIKE %s OR cs.member_name ILIKE %s OR cs.enrollment_number ILIKE %s)")
        like = f"%{q}%"; params.extend([like, like, like])
    return " AND ".join(conditions), params


@router.get("")
def list_case_studies(request: Request,
                      state_code: Optional[str] = None,
                      district_code: Optional[str] = None,
                      centre_code: Optional[str] = None,
                      batch: Optional[str] = None,
                      category: Optional[str] = None,
                      status: Optional[str] = None,
                      q: Optional[str] = None,
                      page: int = 1, limit: int = 10):
    state_code, district_code, centre_code = scope_geo(request, state_code, district_code, centre_code)
    offset = (page - 1) * limit
    where, params = _list_where(state_code, district_code, centre_code, batch, category, status, q)
    with get_cursor() as cur:
        cur.execute(
            f"""SELECT COUNT(*) AS total FROM mis_azad.www_case_studies cs
                LEFT JOIN mis_azad.www_enrollment e ON cs.enrollment_id = e.id
                WHERE {where}""",
            params,
        )
        total = cur.fetchone()["total"]
        cur.execute(
            f"""
            SELECT cs.id, cs.enrollment_id, cs.member_name, cs.enrollment_number,
                   cs.title, cs.category, cs.category_other, cs.story_date,
                   cs.status, cs.status_date, cs.created_at, cs.updated_at,
                   cs.state_code, cs.district_code, cs.centre_code,
                   COALESCE(ws.state_name,   '') AS state_name,
                   COALESCE(wd.district_name,'') AS district_name,
                   COALESCE(wc.centre_name,  '') AS centre_name,
                   NULLIF(TRIM(e.batch), '') AS batch
            FROM mis_azad.www_case_studies cs
            LEFT JOIN mis_azad.www_enrollment e  ON cs.enrollment_id = e.id
            LEFT JOIN mis_azad.central_states    ws ON cs.state_code    = ws.state_code
            LEFT JOIN mis_azad.central_districts wd ON cs.district_code = wd.district_code
            LEFT JOIN mis_azad.central_centres   wc ON cs.centre_code   = wc.centre_code
            WHERE {where}
            ORDER BY cs.created_at DESC, cs.id DESC
            LIMIT %s OFFSET %s
            """,
            params + [limit, offset],
        )
        rows = cur.fetchall()
    return {"total": total, "page": page, "limit": limit, "data": rows}


@router.get("/export/excel")
def export_case_studies(request: Request,
                        state_code: Optional[str] = None,
                        district_code: Optional[str] = None,
                        centre_code: Optional[str] = None,
                        batch: Optional[str] = None,
                        category: Optional[str] = None,
                        status: Optional[str] = None,
                        q: Optional[str] = None):
    from datetime import date
    from export_helper import csv_to_xlsx_response
    state_code, district_code, centre_code = scope_geo(request, state_code, district_code, centre_code)
    where, params = _list_where(state_code, district_code, centre_code, batch, category, status, q)
    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT cs.id, cs.member_name, cs.enrollment_number,
                   COALESCE(wc.centre_name,  '') AS centre_name,
                   COALESCE(wd.district_name,'') AS district_name,
                   COALESCE(ws.state_name,   '') AS state_name,
                   COALESCE(NULLIF(TRIM(e.batch), ''), '') AS batch,
                   cs.title,
                   CASE WHEN cs.category = 'Other' AND cs.category_other IS NOT NULL
                        THEN cs.category || ' - ' || cs.category_other
                        ELSE cs.category END AS category,
                   cs.status, cs.story_date, cs.status_date, cs.period,
                   cs.story, cs.challenges, cs.actions, cs.impact, cs.quote,
                   cs.status_notes, cs.remarks,
                   cs.created_at, cs.updated_at,
                   u1.name AS created_by_name,
                   u2.name AS updated_by_name
            FROM mis_azad.www_case_studies cs
            LEFT JOIN mis_azad.www_enrollment e  ON cs.enrollment_id = e.id
            LEFT JOIN mis_azad.central_states    ws ON cs.state_code    = ws.state_code
            LEFT JOIN mis_azad.central_districts wd ON cs.district_code = wd.district_code
            LEFT JOIN mis_azad.central_centres   wc ON cs.centre_code   = wc.centre_code
            LEFT JOIN mis_azad.mis_user         u1 ON cs.created_by    = u1.id
            LEFT JOIN mis_azad.mis_user         u2 ON cs.updated_by    = u2.id
            WHERE {where}
            ORDER BY cs.created_at DESC, cs.id DESC
            """,
            params,
        )
        rows = cur.fetchall()
    headers = [
        'S.No', 'ID', 'Member Name', 'Enrollment No.', 'Centre', 'District', 'State', 'Batch',
        'Title', 'Category', 'Status', 'Story Date', 'Last Updated', 'Period',
        'Story', 'Challenges', 'Actions', 'Impact', 'Quote',
        'Progress Notes', 'Remarks', 'Created By', 'Updated By',
    ]
    data_rows = []
    for i, r in enumerate(rows, start=1):
        data_rows.append([
            i, r['id'], r['member_name'] or '', r['enrollment_number'] or '',
            r['centre_name'], r['district_name'], r['state_name'], r['batch'] or '',
            r['title'] or '', r['category'] or '', r['status'] or '',
            (r['story_date'].isoformat() if r['story_date'] else ''),
            (r['status_date'].isoformat() if r['status_date'] else ''),
            r['period'] or '',
            r['story'] or '', r['challenges'] or '', r['actions'] or '',
            r['impact'] or '', r['quote'] or '',
            r['status_notes'] or '', r['remarks'] or '',
            r.get('created_by_name') or '',
            r.get('updated_by_name') or '',
        ])
    fname = f"WWW_Case_Studies_Export_{date.today().isoformat()}.xlsx"
    return csv_to_xlsx_response(headers, data_rows, fname)


@router.get("/trainees/picker")
def picker_trainees(request: Request,
                    state_code: Optional[str] = None,
                    district_code: Optional[str] = None,
                    centre_code: Optional[str] = None,
                    q: Optional[str] = None,
                    limit: int = 2000):
    """Trainee list for the Add / Edit picker. Non-deleted, non-draft
    enrollments only. RBAC-scoped."""
    state_code, district_code, centre_code = scope_geo(request, state_code, district_code, centre_code)
    joins = geo_joins("e")
    conds = ["e.deleted_at IS NULL",
             "COALESCE(LOWER(TRIM(e.status)), '') <> 'draft'"]
    params: List[Any] = []
    if state_code:
        conds.append("_gs.state_code = %s"); params.append(state_code)
    if district_code:
        conds.append("_gd.district_code = %s"); params.append(district_code)
    if centre_code:
        conds.append("_gc.centre_code = %s"); params.append(centre_code)
    if q:
        conds.append("(e.name ILIKE %s OR e.enrollment_no ILIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])
    where = " AND ".join(conds)
    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT e.id,
                   e.enrollment_no AS enrollment_number,
                   COALESCE(e.name, '') AS name,
                   COALESCE(_gs.state_name,    '') AS state_name,
                   COALESCE(_gs.state_code,    '') AS state_code,
                   COALESCE(_gd.district_name, '') AS district_name,
                   COALESCE(_gd.district_code, '') AS district_code,
                   COALESCE(_gc.centre_name,   '') AS centre_name,
                   COALESCE(_gc.centre_code,   '') AS centre_code,
                   NULLIF(TRIM(e.batch), '') AS batch,
                   -- 2026-11-10 wwwCsSequence: added so FE can filter trainees by enrollment type.
                   -- 2026-11-10 wwwCsEtypeColFix: column is `type_of_enrollment`, not `enrollment_type`.
                   NULLIF(TRIM(e.type_of_enrollment), '') AS enrollment_type
            FROM mis_azad.www_enrollment e
            {joins}
            WHERE {where}
            ORDER BY e.name NULLS LAST, e.id DESC
            LIMIT %s
            """,
            params + [limit],
        )
        rows = cur.fetchall()
    return {"data": rows}


@router.post("")
def create_case_study(request: Request, body: CaseStudyBody):
    if body.category and body.category not in _CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Unknown category: {body.category}")
    if body.status and body.status not in _STATUSES:
        raise HTTPException(status_code=400, detail=f"Unknown status: {body.status}")
    if body.category == 'Other' and not (body.category_other and body.category_other.strip()):
        raise HTTPException(status_code=400, detail="Please specify the category when 'Other' is selected.")
    with get_cursor() as cur:
        snap = _fetch_enrollment_snapshot(cur, body.enrollment_id)
        s, d, c = scope_geo(request, snap["state_code"], snap["district_code"], snap["centre_code"])
        if s == DENY or (s and snap["state_code"] != s) or (d and snap["district_code"] != d) or (c and snap["centre_code"] != c):
            raise HTTPException(status_code=403, detail="This trainee is outside your scope.")
        cur.execute(
            """
            INSERT INTO mis_azad.www_case_studies (
                enrollment_id, member_name, enrollment_number,
                state_code, district_code, centre_code,
                title, category, category_other, story_date, period,
                story, challenges, actions, impact, quote,
                status, status_date, status_notes, remarks
            ) VALUES (
                %s,%s,%s,
                %s,%s,%s,
                %s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,
                %s,%s,%s,%s
            ) RETURNING id
            """,
            (
                snap["id"], snap["member_name"], snap["enrollment_number"],
                snap["state_code"], snap["district_code"], snap["centre_code"],
                body.title, body.category, body.category_other, body.story_date, body.period,
                body.story, body.challenges, body.actions, body.impact, body.quote,
                body.status or 'Ongoing', body.status_date, body.status_notes, body.remarks,
            ),
        )
        new_id = cur.fetchone()["id"]
    return {"id": new_id, "message": "Case study created"}


@router.get("/{cs_id}")
def get_case_study(request: Request, cs_id: int):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT cs.*,
                   COALESCE(ws.state_name,   '') AS state_name,
                   COALESCE(wd.district_name,'') AS district_name,
                   COALESCE(wc.centre_name,  '') AS centre_name
            FROM mis_azad.www_case_studies cs
            LEFT JOIN mis_azad.central_states    ws ON cs.state_code    = ws.state_code
            LEFT JOIN mis_azad.central_districts wd ON cs.district_code = wd.district_code
            LEFT JOIN mis_azad.central_centres   wc ON cs.centre_code   = wc.centre_code
            WHERE cs.id = %s AND cs.deleted_at IS NULL
            """,
            (cs_id,),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Case study not found")
    guard_detail(request, row)
    return row


@router.put("/{cs_id}")
def update_case_study(request: Request, cs_id: int, body: CaseStudyBody):
    if body.category and body.category not in _CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Unknown category: {body.category}")
    if body.status and body.status not in _STATUSES:
        raise HTTPException(status_code=400, detail=f"Unknown status: {body.status}")
    if body.category == 'Other' and not (body.category_other and body.category_other.strip()):
        raise HTTPException(status_code=400, detail="Please specify the category when 'Other' is selected.")
    with get_cursor() as cur:
        cur.execute(
            "SELECT state_code, district_code, centre_code "
            "  FROM mis_azad.www_case_studies WHERE id = %s AND deleted_at IS NULL",
            (cs_id,),
        )
        existing = cur.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Case study not found")
        guard_detail(request, existing)
        snap = _fetch_enrollment_snapshot(cur, body.enrollment_id)
        s, d, c = scope_geo(request, snap["state_code"], snap["district_code"], snap["centre_code"])
        if s == DENY or (s and snap["state_code"] != s) or (d and snap["district_code"] != d) or (c and snap["centre_code"] != c):
            raise HTTPException(status_code=403, detail="This trainee is outside your scope.")
        cur.execute(
            """
            UPDATE mis_azad.www_case_studies SET
                enrollment_id=%s, member_name=%s, enrollment_number=%s,
                state_code=%s, district_code=%s, centre_code=%s,
                title=%s, category=%s, category_other=%s, story_date=%s, period=%s,
                story=%s, challenges=%s, actions=%s, impact=%s, quote=%s,
                status=%s, status_date=%s, status_notes=%s, remarks=%s,
                updated_at=NOW()
            WHERE id=%s
            """,
            (
                snap["id"], snap["member_name"], snap["enrollment_number"],
                snap["state_code"], snap["district_code"], snap["centre_code"],
                body.title, body.category, body.category_other, body.story_date, body.period,
                body.story, body.challenges, body.actions, body.impact, body.quote,
                body.status or 'Ongoing', body.status_date, body.status_notes, body.remarks,
                cs_id,
            ),
        )
    return {"id": cs_id, "message": "Case study updated"}


@router.delete("/{cs_id}")
def delete_case_study(request: Request, cs_id: int):
    with get_cursor() as cur:
        cur.execute(
            "SELECT state_code, district_code, centre_code "
            "  FROM mis_azad.www_case_studies WHERE id = %s AND deleted_at IS NULL",
            (cs_id,),
        )
        existing = cur.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Case study not found")
        guard_detail(request, existing)
        cur.execute(
            "UPDATE mis_azad.www_case_studies SET deleted_at = NOW() WHERE id = %s",
            (cs_id,),
        )
    return {"id": cs_id, "message": "Case study deleted"}


@router.post("/{cs_id}/photo")
async def upload_photo(request: Request, cs_id: int, file: UploadFile = File(...)):
    with get_cursor() as cur:
        cur.execute(
            "SELECT state_code, district_code, centre_code "
            "  FROM mis_azad.www_case_studies WHERE id = %s AND deleted_at IS NULL",
            (cs_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Case study not found")
        guard_detail(request, row)
    ext = os.path.splitext(file.filename or '')[1].lower()
    if ext not in ('.jpg', '.jpeg', '.png', '.webp'):
        raise HTTPException(status_code=400, detail="Only JPG / PNG / WebP images are allowed")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    saved_name = f"www_cs_{cs_id}_{uuid.uuid4().hex}{ext}"
    disk_path = os.path.join(UPLOAD_DIR, saved_name)
    content = await file.read()
    with open(disk_path, 'wb') as f:
        f.write(content)
    file_url = f"/uploads/{saved_name}"
    with get_cursor() as cur:
        cur.execute(
            "UPDATE mis_azad.www_case_studies SET photo_url=%s, updated_at=NOW() WHERE id=%s",
            (file_url, cs_id),
        )
    return {"id": cs_id, "photo_url": file_url, "message": "Photo uploaded"}


@router.post("/{cs_id}/attachment")
async def upload_attachment(request: Request, cs_id: int, file: UploadFile = File(...)):
    from psycopg2.extras import Json
    with get_cursor() as cur:
        cur.execute(
            "SELECT state_code, district_code, centre_code, attachments_meta "
            "  FROM mis_azad.www_case_studies WHERE id = %s AND deleted_at IS NULL",
            (cs_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Case study not found")
        guard_detail(request, row)
        existing = row.get("attachments_meta") or []
        if isinstance(existing, str):
            try: existing = json.loads(existing)
            except Exception: existing = []
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or '')[1].lower()
    saved_name = f"www_cs_{cs_id}_att_{uuid.uuid4().hex}{ext}"
    disk_path = os.path.join(UPLOAD_DIR, saved_name)
    content = await file.read()
    with open(disk_path, 'wb') as f:
        f.write(content)
    file_url = f"/uploads/{saved_name}"
    meta = {
        "name": file.filename,
        "url":  file_url,
        "size": len(content),
        "mime": file.content_type or '',
    }
    existing.append(meta)
    with get_cursor() as cur:
        cur.execute(
            "UPDATE mis_azad.www_case_studies SET attachments_meta=%s, updated_at=NOW() WHERE id=%s",
            (Json(existing), cs_id),
        )
    return {"id": cs_id, "attachment": meta, "message": "Attachment uploaded"}
