"""WWW role-based data scoping (backend enforcement).

Pins each request's geo (state / district / centre) to the caller's role so a
restricted user cannot widen access by changing query params, IDs, or URLs, and
guards per-record GETs so they cannot open an out-of-scope record by guessing an
id. Reuses the role map from routes._role_scope.

Role behaviour (from _role_scope._RESTRICTED):
  admin / super admin / power user / flp   -> unrestricted (pass through)
  state lead / specialist                  -> pinned to their state
  district lead                            -> pinned to their state + district
  project incharge (pi) / mobiliser /
  sangini                                  -> pinned to state + district + centre

Fail-closed: a restricted user whose required geo code is missing sees NO data
(scope_geo returns the DENY sentinel, which matches no row; guard_detail 404s).
"""
from fastapi import Request, HTTPException
from routes._role_scope import get_current_user, _RESTRICTED
from database import get_cursor

# An impossible geo code: no real state/district/centre_code equals it, so a
# fail-closed user's list / dashboard / export comes back empty with no
# per-endpoint changes. (Plain ASCII -- Postgres text params cannot carry NUL.)
DENY = "__WWW_DENY_NO_ROWS__"


_WWW_CENTRE_MAP = {}


def _www_map_centre(centre_code):
    """Map a central-style centre_code (e.g. 'S07093B3') to the WWW centre_code
    (e.g. 'East Delhi'). central_centres and www_centres share centre_name +
    district_code but use DIFFERENT codes; WWW scoping matches www_centres codes,
    while the Add-User form assigns central codes to PIs -> a PI would otherwise
    see no data. Returns the input unchanged if it is already a www code or
    cannot be mapped. Cached per process."""
    if not centre_code:
        return centre_code
    if centre_code in _WWW_CENTRE_MAP:
        return _WWW_CENTRE_MAP[centre_code]
    out = centre_code
    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT 1 FROM mis_azad.central_centres WHERE centre_code = %s AND deleted_at IS NULL LIMIT 1",
                (centre_code,),
            )
            if not cur.fetchone():
                cur.execute(
                    "SELECT w.centre_code FROM mis_azad.central_centres cc "
                    "JOIN mis_azad.central_centres w "
                    "  ON LOWER(TRIM(w.centre_name)) = LOWER(TRIM(cc.centre_name)) "
                    " AND w.district_code = cc.district_code AND w.deleted_at IS NULL "
                    "WHERE cc.centre_code = %s LIMIT 1",
                    (centre_code,),
                )
                r = cur.fetchone()
                if r:
                    out = r["centre_code"]
    except Exception:
        pass
    _WWW_CENTRE_MAP[centre_code] = out
    return out


def scope_geo(request, state_code=None, district_code=None, centre_code=None):
    """Return (state_code, district_code, centre_code) pinned to the caller.

    Unrestricted roles and unauthenticated requests pass the incoming values
    through unchanged. Restricted roles get their own codes forced in (and may
    still drill DOWN on the un-pinned levels). Fail-closed on missing codes.
    """
    user = get_current_user(request)
    if not user:
        return state_code, district_code, centre_code
    role = user.get("role_name") or ""
    fields = _RESTRICTED.get(role)
    if not fields:
        return state_code, district_code, centre_code
    if not user.get("state_code"):
        return DENY, None, None
    out_s = user["state_code"] if "state_code" in fields else state_code
    out_d = district_code
    out_c = centre_code
    if "district_code" in fields:
        if not user.get("district_code"):
            return DENY, None, None
        out_d = user["district_code"]
    if "centre_code" in fields:
        if not user.get("centre_code"):
            return DENY, None, None
        out_c = _www_map_centre(user["centre_code"])
    return out_s, out_d, out_c


def guard_detail(request, row):
    """Raise 404 if `row` is outside the caller's geo scope.

    `row` must expose the resolved state_code / district_code / centre_code
    (i.e. the SELECT used _www_legacy.geo_cols()). No-op for unrestricted roles
    and unauthenticated requests. Fail-closed on missing caller codes.
    """
    user = get_current_user(request)
    if not user:
        return
    role = user.get("role_name") or ""
    fields = _RESTRICTED.get(role)
    if not fields:
        return
    if not user.get("state_code"):
        raise HTTPException(status_code=404, detail="Not found.")
    r = row or {}
    if "state_code" in fields and r.get("state_code") != user.get("state_code"):
        raise HTTPException(status_code=404, detail="Not found.")
    if "district_code" in fields:
        if not user.get("district_code") or r.get("district_code") != user.get("district_code"):
            raise HTTPException(status_code=404, detail="Not found.")
    if "centre_code" in fields:
        if not user.get("centre_code") or r.get("centre_code") != _www_map_centre(user.get("centre_code")):
            raise HTTPException(status_code=404, detail="Not found.")


def scoped_centre_codes(request):
    """For centre-keyed modules (NT, Mobilisation). Return None if the caller is
    unrestricted (see all centres), else the list of centre_codes they may see
    (empty list = fail-closed / none)."""
    user = get_current_user(request)
    if not user:
        return None
    role = user.get("role_name") or ""
    fields = _RESTRICTED.get(role)
    if not fields:
        return None
    if "centre_code" in fields:
        cc = user.get("centre_code")
        return [_www_map_centre(cc)] if cc else []
    with get_cursor() as cur:
        if "district_code" in fields:
            dc = user.get("district_code")
            if not dc:
                return []
            cur.execute("SELECT centre_code FROM mis_azad.central_centres WHERE district_code = %s AND deleted_at IS NULL", (dc,))
            return [r["centre_code"] for r in cur.fetchall()]
        sc = user.get("state_code")
        if not sc:
            return []
        cur.execute("SELECT centre_code FROM mis_azad.central_centres WHERE state_code = %s AND deleted_at IS NULL", (sc,))
        return [r["centre_code"] for r in cur.fetchall()]


def guard_detail_by_centre(request, row):
    """404 if `row` (exposing centre_code) is outside the caller's allowed centres."""
    cc = scoped_centre_codes(request)
    if cc is None:
        return
    rc = (row or {}).get("centre_code")
    if rc not in cc:
        raise HTTPException(status_code=404, detail="Not found.")
