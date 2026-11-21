"""WWW Master dropdown and create endpoints for the WWW module.

Phase 3 (2026-06-10).  Backs the State / District / Centre / Area /
Batch dropdowns on the WWW Add Trainee Basic Profile tab.

The create endpoints back the WWW Master modals restored in the web UI.
They only write when an authorised user explicitly submits those forms.

Endpoint prefix: /api/www-master  (matches the /api/mgj-master and
/api/ak-master conventions in this codebase).
"""
from fastapi import APIRouter, HTTPException, Request
from routes import _www_scope as _scope
from pydantic import BaseModel
from typing import Optional
import psycopg2
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_cursor
from routes import _www_legacy as _legacy

router = APIRouter(prefix="/api/www-master", tags=["WWW Master"])


class StateCreate(BaseModel):
    state_code: str
    state_name: str
    status: str = "Active"


class DistrictCreate(BaseModel):
    state_code: str
    district_code: str
    district_name: str
    status: str = "Active"


class CentreCreate(BaseModel):
    state_code: str
    district_code: str
    centre_code: str
    centre_name: str
    status: str = "Active"


class AreaCreate(BaseModel):
    state_code: str
    centre_code: str
    area_code: str
    area_name: str
    status: str = "Active"


class BatchCreate(BaseModel):
    state_code: Optional[str] = None
    centre_code: Optional[str] = None
    name: str
    year: Optional[str] = None
    status: str = "Active"


def _clean(value: str, label: str) -> str:
    value = (value or "").strip()
    if not value:
        raise HTTPException(400, f"{label} is required.")
    return value


def _status(value: str) -> str:
    normalized = (value or "Active").strip().title()
    if normalized not in {"Active", "Inactive"}:
        raise HTTPException(400, "Status must be Active or Inactive.")
    return normalized


def _conflict(exc: psycopg2.IntegrityError):
    constraint = getattr(getattr(exc, "diag", None), "constraint_name", None)
    detail = "A record with the same code or name already exists."
    if constraint and "foreign" in constraint.lower():
        detail = "The selected parent record does not exist."
    raise HTTPException(409, detail) from exc


@router.post("/states", status_code=201)
def create_state(body: StateCreate):
    try:
        with get_cursor() as cur:
            cur.execute(
                "INSERT INTO central_states (state_code, state_name, status) VALUES (%s,%s,%s) RETURNING state_code",
                (_clean(body.state_code, "State code"), _clean(body.state_name, "State name"), _status(body.status)),
            )
            code = cur.fetchone()["state_code"]
    except psycopg2.IntegrityError as exc:
        _conflict(exc)
    return {"ok": True, "state_code": code}


@router.post("/districts", status_code=201)
def create_district(body: DistrictCreate):
    try:
        with get_cursor() as cur:
            cur.execute(
                "INSERT INTO central_districts (district_code, district_name, state_code, status) VALUES (%s,%s,%s,%s) RETURNING district_code",
                (_clean(body.district_code, "District code"), _clean(body.district_name, "District name"), _clean(body.state_code, "State"), _status(body.status)),
            )
            code = cur.fetchone()["district_code"]
    except psycopg2.IntegrityError as exc:
        _conflict(exc)
    return {"ok": True, "district_code": code}


@router.post("/centres", status_code=201)
def create_centre(body: CentreCreate):
    try:
        with get_cursor() as cur:
            cur.execute(
                "INSERT INTO central_centres (centre_code, centre_name, district_code, state_code, status) VALUES (%s,%s,%s,%s,%s) RETURNING centre_code",
                (_clean(body.centre_code, "Centre code"), _clean(body.centre_name, "Centre name"), _clean(body.district_code, "District"), _clean(body.state_code, "State"), _status(body.status)),
            )
            code = cur.fetchone()["centre_code"]
    except psycopg2.IntegrityError as exc:
        _conflict(exc)
    return {"ok": True, "centre_code": code}


@router.post("/areas", status_code=201)
def create_area(body: AreaCreate):
    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT district_code, state_code FROM central_centres WHERE centre_code=%s AND deleted_at IS NULL",
                (_clean(body.centre_code, "Centre"),),
            )
            parent = cur.fetchone()
            if not parent:
                raise HTTPException(400, "Selected centre does not exist.")
            if parent["state_code"] != _clean(body.state_code, "State"):
                raise HTTPException(400, "Selected centre does not belong to the selected state.")
            cur.execute(
                "INSERT INTO www_areas (area_code, area_name, centre_code, district_code, state_code, status) VALUES (%s,%s,%s,%s,%s,%s) RETURNING area_code",
                (_clean(body.area_code, "Area code"), _clean(body.area_name, "Area name"), body.centre_code.strip(), parent["district_code"], parent["state_code"], _status(body.status)),
            )
            code = cur.fetchone()["area_code"]
    except psycopg2.IntegrityError as exc:
        _conflict(exc)
    return {"ok": True, "area_code": code}


@router.put("/states/{state_code}")
def update_state(state_code: str, body: StateCreate):
    try:
        with get_cursor() as cur:
            cur.execute(
                "UPDATE central_states SET state_name=%s, status=%s WHERE state_code=%s RETURNING state_code",
                (_clean(body.state_name, "State name"), _status(body.status), state_code),
            )
            if not cur.fetchone():
                raise HTTPException(404, "State not found")
    except psycopg2.IntegrityError as exc:
        _conflict(exc)
    return {"ok": True, "state_code": state_code}


@router.put("/districts/{district_code}")
def update_district(district_code: str, body: DistrictCreate):
    try:
        with get_cursor() as cur:
            cur.execute(
                "UPDATE central_districts SET district_name=%s, state_code=%s, status=%s WHERE district_code=%s RETURNING district_code",
                (_clean(body.district_name, "District name"), _clean(body.state_code, "State"), _status(body.status), district_code),
            )
            if not cur.fetchone():
                raise HTTPException(404, "District not found")
    except psycopg2.IntegrityError as exc:
        _conflict(exc)
    return {"ok": True, "district_code": district_code}


@router.put("/centres/{centre_code}")
def update_centre(centre_code: str, body: CentreCreate):
    try:
        with get_cursor() as cur:
            cur.execute(
                "UPDATE central_centres SET centre_name=%s, district_code=%s, state_code=%s, status=%s WHERE centre_code=%s RETURNING centre_code",
                (_clean(body.centre_name, "Centre name"), _clean(body.district_code, "District"), _clean(body.state_code, "State"), _status(body.status), centre_code),
            )
            if not cur.fetchone():
                raise HTTPException(404, "Centre not found")
    except psycopg2.IntegrityError as exc:
        _conflict(exc)
    return {"ok": True, "centre_code": centre_code}


@router.post("/batches", status_code=201)
def create_batch(body: BatchCreate):
    name = _clean(body.name, "Batch name")
    centre_code = (body.centre_code or "").strip() or None
    try:
        with get_cursor() as cur:
            # 2026-09-12: reject a duplicate batch name within the same centre
            # (names are legitimately reused across different centres).
            cur.execute(
                "SELECT 1 FROM www_master_batches "
                "WHERE deleted_at IS NULL AND LOWER(TRIM(name)) = LOWER(%s) "
                "AND COALESCE(centre_code, '') = COALESCE(%s, '') LIMIT 1",
                (name, centre_code),
            )
            if cur.fetchone():
                raise HTTPException(409, f"A batch named '{name}' already exists for this centre.")
            cur.execute(
                "INSERT INTO www_master_batches (name, year, state_code, centre_code, status) VALUES (%s,%s,%s,%s,%s) RETURNING id",
                (name, (body.year or "").strip() or None,
                 (body.state_code or "").strip() or None, centre_code,
                 _status(body.status)),
            )
            batch_id = cur.fetchone()["id"]
    except psycopg2.IntegrityError as exc:
        _conflict(exc)
    return {"ok": True, "id": batch_id}


@router.put("/batches/{batch_id}")
def update_batch(batch_id: int, body: BatchCreate):
    """Update an existing WWW master batch (Batch Management edit)."""
    name = _clean(body.name, "Batch name")
    centre_code = (body.centre_code or "").strip() or None
    try:
        with get_cursor() as cur:
            # 2026-09-12: reject renaming to a name already used in the same centre.
            cur.execute(
                "SELECT 1 FROM www_master_batches "
                "WHERE deleted_at IS NULL AND id <> %s AND LOWER(TRIM(name)) = LOWER(%s) "
                "AND COALESCE(centre_code, '') = COALESCE(%s, '') LIMIT 1",
                (batch_id, name, centre_code),
            )
            if cur.fetchone():
                raise HTTPException(409, f"A batch named '{name}' already exists for this centre.")
            cur.execute(
                "UPDATE www_master_batches SET name=%s, year=%s, state_code=%s, centre_code=%s, status=%s WHERE id=%s RETURNING id",
                (name, (body.year or "").strip() or None,
                 (body.state_code or "").strip() or None, centre_code,
                 _status(body.status), batch_id),
            )
            if not cur.fetchone():
                raise HTTPException(404, "Batch not found")
    except psycopg2.IntegrityError as exc:
        _conflict(exc)
    return {"ok": True, "id": batch_id}


# ---------------------------------------------------------------------------
# Dropdowns — cascaded so the front-end can chain State -> District -> Centre
# -> Area, and Batch is scoped by State + Centre.
# Every endpoint filters out soft-deleted rows (deleted_at IS NULL) and
# optionally restricts to Active status (the default).  Passing
# include_inactive=1 surfaces Inactive rows too — handy for the admin UI
# but not the trainee form.
# ---------------------------------------------------------------------------

def _status_clause(include_inactive: int) -> str:
    """SQL fragment for the optional 'Active only' filter."""
    return "" if include_inactive else " AND LOWER(status) = 'active'"


@router.get("/dropdown/states")
def dropdown_states(request: Request, include_inactive: int = 0):
    with get_cursor() as cur:
        cur.execute("SELECT to_regclass('mis_azad.central_states') AS table_name")
        if not cur.fetchone()["table_name"]:
            cur.execute("""
                SELECT DISTINCT state_code,
                       COALESCE(NULLIF(state, ''), NULLIF(state_1, ''), state_code) AS state_name
                FROM www_enrollment
                WHERE NULLIF(TRIM(state_code), '') IS NOT NULL
                ORDER BY state_name
            """)
            return cur.fetchall()
        _sc, _, _ = _scope.scope_geo(request, None, None, None)
        _sw = " AND state_code = %s" if _sc else ""
        cur.execute(
            "SELECT state_code, state_name, COALESCE(status, 'Active') AS status FROM central_states "
            "WHERE deleted_at IS NULL" + _sw + _status_clause(include_inactive) +
            " ORDER BY state_name",
            ([_sc] if _sc else []),
        )
        return cur.fetchall()


@router.get("/dropdown/districts")
def dropdown_districts(request: Request, state_code: Optional[str] = None, include_inactive: int = 0):
    with get_cursor() as cur:
        # Legacy fallback: normalized www_districts absent -> derive from enrollment form
        cur.execute("SELECT to_regclass('mis_azad.central_districts') AS t")
        if not cur.fetchone()["t"]:
            lconds = ["NULLIF(TRIM(district_code), '') IS NOT NULL"]
            lparams = []
            if state_code:
                lconds.append("state_code = %s"); lparams.append(state_code)
            cur.execute(
                "SELECT DISTINCT district_code, "
                "       COALESCE(NULLIF(district, ''), NULLIF(district_1, ''), district_code) AS district_name, "
                "       state_code "
                "FROM www_enrollment "
                "WHERE " + " AND ".join(lconds) + " ORDER BY district_name",
                lparams,
            )
            return cur.fetchall()

        _sc, _dc, _ = _scope.scope_geo(request, state_code, None, None)
        conds = ["deleted_at IS NULL"]
        params = []
        if _sc:
            conds.append("state_code = %s"); params.append(_sc)
        if _dc:
            conds.append("district_code = %s"); params.append(_dc)
        if not include_inactive:
            conds.append("LOWER(status) = 'active'")
        cur.execute(
            "SELECT district_code, district_name, state_code, COALESCE(status, 'Active') AS status FROM central_districts "
            "WHERE " + " AND ".join(conds) + " ORDER BY district_name",
            params,
        )
        return cur.fetchall()

@router.get("/dropdown/centres")
def dropdown_centres(request: Request,
                     state_code: Optional[str] = None,
                     district_code: Optional[str] = None,
                     include_inactive: int = 0):
    with get_cursor() as cur:
        cur.execute("SELECT to_regclass('mis_azad.central_centres') AS table_name")
        if not cur.fetchone()["table_name"]:
            legacy_conditions = ["NULLIF(TRIM(centre_census), '') IS NOT NULL"]
            legacy_params = []
            if state_code:
                legacy_conditions.append("state_code = %s")
                legacy_params.append(state_code)
            cur.execute(
                "SELECT DISTINCT centre_census AS centre_code, centre_census AS centre_name, "
                "NULL::text AS district_code, state_code FROM www_enrollment WHERE "
                + " AND ".join(legacy_conditions) + " ORDER BY centre_name",
                legacy_params,
            )
            return cur.fetchall()
        _sc, _dc, _cc = _scope.scope_geo(request, state_code, district_code, None)
        conds = ["deleted_at IS NULL"]
        params = []
        if _sc:
            conds.append("state_code = %s"); params.append(_sc)
        if _dc:
            conds.append("district_code = %s"); params.append(_dc)
        if _cc:
            conds.append("centre_code = %s"); params.append(_cc)
        if not include_inactive:
            conds.append("LOWER(status) = 'active'")
        cur.execute(
            "SELECT centre_code, centre_name, district_code, state_code, COALESCE(status, 'Active') AS status "
            "FROM central_centres "
            "WHERE " + " AND ".join(conds) + " ORDER BY centre_name",
            params,
        )
        return cur.fetchall()


@router.get("/dropdown/areas")
def dropdown_areas(request: Request,
                   centre_code: Optional[str] = None,
                   district_code: Optional[str] = None,
                   state_code: Optional[str] = None,
                   include_inactive: int = 0):
    with get_cursor() as cur:
        # 2026-09-03: The WWW mobiliser mobile app pulls its Area picker
        # from this endpoint. www_areas (+ the legacy enrollment merge
        # below) shows duplicate / variant spellings there. Serve the
        # mobile app the clean FLP master (central_areas) instead.
        # Browsers -- the web Add-Trainee form + Master View -- keep the
        # existing behaviour untouched, because that form saves area_code
        # and changing its options would risk nulling a trainee area on
        # edit. Native (Dart/Flutter) clients send no "Mozilla" token in
        # the User-Agent; every real browser does.
        _ua = (request.headers.get("user-agent") or "")
        if "Mozilla" not in _ua:
            _aconds = ["a.deleted_at IS NULL"]
            _aparams = []
            if state_code:
                _aconds.append("a.state_code = %s"); _aparams.append(state_code)
            if district_code:
                _aconds.append("a.district_code = %s"); _aparams.append(district_code)
            if centre_code:
                # mobile passes the centre NAME; central_areas keys on the code
                _aconds.append("(a.centre_code = %s OR a.centre_code IN (SELECT centre_code FROM central_centres WHERE LOWER(centre_name) = LOWER(%s)))")
                _aparams.append(centre_code); _aparams.append(centre_code)
            if not include_inactive:
                _aconds.append("LOWER(COALESCE(a.status, 'Active')) = 'active'")
            cur.execute(
                "SELECT area_code, area_name, centre_code, district_code, state_code, "
                "COALESCE(status, 'Active') AS status FROM central_areas a WHERE "
                + " AND ".join(_aconds) + " ORDER BY area_name",
                _aparams,
            )
            return cur.fetchall()
        # 2026-09-10: RBAC -- pin browser requests to the caller's geo scope
        # (State Lead=state, District Lead=state+district, PI=state+district+centre)
        # so Master > Area Management shows only the user's own areas.
        state_code, district_code, centre_code = _scope.scope_geo(request, state_code, district_code, centre_code)
        if state_code == _scope.DENY:
            return []
        # Legacy fallback: normalized www_areas absent -> derive from the
        # enrollment import, which stores the area as free text with no code,
        # so the name doubles as the code.
        if not _legacy.table_exists(cur, "www_areas"):
            lconds = ["NULLIF(TRIM(e.area), '') IS NOT NULL"]
            lparams = []
            if centre_code:
                lconds.append(_legacy.centre_filter("e")); lparams.append(centre_code)
            if state_code:
                lconds.append(_legacy.state_filter()); lparams.append(state_code)
            cur.execute(
                "SELECT DISTINCT TRIM(e.area) AS area_code, "
                "       TRIM(e.area) AS area_name, "
                "       " + _legacy.centre_expr("e.centre") + " AS centre_code, "
                "       _gd.district_code, _gs.state_code, "
                "       'Active'::text AS status "
                "FROM mis_azad.www_enrollment e " + _legacy.geo_joins("e") +
                "WHERE " + " AND ".join(lconds) + " ORDER BY area_name",
                lparams,
            )
            return cur.fetchall()

        conds = ["a.deleted_at IS NULL"]
        params = []
        if centre_code:
            conds.append("a.centre_code = %s"); params.append(centre_code)
        if district_code:
            conds.append("a.district_code = %s"); params.append(district_code)
        if state_code:
            conds.append("a.state_code = %s"); params.append(state_code)
        if not include_inactive:
            conds.append("LOWER(a.status) = 'active'")

        # Keep imported enrollment geography visible after the normalized
        # master tables have been created.  The old fallback returned legacy
        # rows only while www_areas did not exist, so creating the first master
        # row could make most historical areas disappear from management.
        legacy_conds = ["NULLIF(TRIM(e.area), '') IS NOT NULL"]
        legacy_params = []
        if centre_code:
            legacy_conds.append(_legacy.centre_filter("e")); legacy_params.append(centre_code)
        if district_code:
            # Legacy enrollments do not store a dependable area->district
            # mapping. A district-scoped request must not leak unrelated rows.
            legacy_conds.append("FALSE")
        if state_code:
            legacy_conds.append(_legacy.state_filter()); legacy_params.append(state_code)
        cur.execute(
            "SELECT area_code, area_name, centre_code, district_code, state_code, status FROM ("
            "  SELECT a.area_code, a.area_name, a.centre_code, a.district_code, a.state_code, "
            "         COALESCE(a.status, 'Active') AS status "
            "  FROM www_areas a WHERE " + " AND ".join(conds) +
            "  UNION ALL "
            "  SELECT DISTINCT TRIM(e.area) AS area_code, "
            "         TRIM(e.area) AS area_name, "
            "         " + _legacy.centre_expr("e.centre") + " AS centre_code, "
            "         NULL::text AS district_code, _gs.state_code, 'Active'::text AS status "
            "  FROM mis_azad.www_enrollment e " + _legacy.geo_joins("e") +
            "  WHERE " + " AND ".join(legacy_conds) +
            "    AND NOT EXISTS (SELECT 1 FROM www_areas n "
            "                    WHERE n.deleted_at IS NULL "
            "                      AND LOWER(TRIM(n.area_name)) = LOWER(TRIM(e.area)) "
            "                      AND COALESCE(n.centre_code, '') = "
            "                          COALESCE(" + _legacy.centre_expr("e.centre") + ", ''))"
            ") merged ORDER BY area_name, centre_code",
            params + legacy_params,
        )
        return cur.fetchall()


@router.get("/dropdown/batches")
def dropdown_batches(request: Request,
                     state_code: Optional[str] = None,
                     centre_code: Optional[str] = None,
                     include_inactive: int = 0):
    with get_cursor() as cur:
        # Legacy fallback: www_master_batches absent, and the legacy import has no
        # batch table -> return an empty list so the dropdown just shows "All Batches"
        # instead of 500-ing. (Matches the trainee list, which returns batch = blank.)
        cur.execute("SELECT to_regclass('mis_azad.www_master_batches') AS t")
        if not cur.fetchone()["t"]:
            return []

        conds = ["deleted_at IS NULL"]
        params = []
        # 2026-09-10: RBAC -- restrict batches to the caller's allowed centres
        # (State Lead=all state centres, District Lead=district centres, PI=own
        # centre). None = unrestricted (admin); empty list = fail-closed.
        _cc = _scope.scoped_centre_codes(request)
        if _cc is not None:
            if not _cc:
                return []
            conds.append("centre_code = ANY(%s)"); params.append(_cc)
        if state_code:
            conds.append("state_code = %s"); params.append(state_code)
        if centre_code:
            conds.append("centre_code = %s"); params.append(centre_code)
        if not include_inactive:
            conds.append("LOWER(status) = 'active'")
        cur.execute(
            "SELECT id, name, year, state_code, centre_code "
            "FROM www_master_batches "
            # 2026-09-10: batches serial-wise -> order by the numeric serial in the
            # name (Batch-1,2,...,10,11), not alphabetical (which put Batch-10<Batch-2).
            "WHERE " + " AND ".join(conds) + " ORDER BY "
            "NULLIF(regexp_replace(name, '[^0-9]', '', 'g'), '')::int NULLS LAST, "
            "year DESC NULLS LAST, name",
            params,
        )
        return cur.fetchall()
