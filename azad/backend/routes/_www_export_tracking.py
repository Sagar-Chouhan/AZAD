"""WWW export tracking -- resolve Created At / Created By / Updated At / Updated By.

Given the DB row dicts an export already fetched (each carrying the base
table PK under `pk_key`), look up created_at/created_by/updated_at/
updated_by from `base_table` and resolve the user ids to users.name.
Returns a list of
[created_at_formatted, created_by_name, updated_at_formatted, updated_by_name]
aligned 1:1 with `rows`. Never raises -- any failure yields blank cells
so an export still succeeds.
"""
from database import get_cursor
from routes._www_meta import format_dt_ap

# 2026-09-28: reinstated Created At + Updated At (with time) alongside
# Created By / Updated By per user request.
WWW_TRACK_HEADERS = ["Created At", "Created By", "Updated At", "Updated By"]
_BLANK = ["", "", "", ""]


def www_tracking_cells(rows, base_table, pk_key="id", pk_col="id"):
    n = len(rows)
    out = [list(_BLANK) for _ in range(n)]
    pks = []
    for r in rows:
        try:
            pks.append(r.get(pk_key))
        except AttributeError:
            pks.append(None)
    valid = sorted({p for p in pks if p is not None})
    if not valid:
        return out
    track, uids = {}, set()
    try:
        with get_cursor() as cur:
            cur.execute(
                f"SELECT {pk_col} AS _k, created_at, created_by, updated_at, updated_by "
                f"FROM {base_table} WHERE {pk_col} = ANY(%s)",
                (valid,),
            )
            for tr in cur.fetchall():
                track[tr["_k"]] = tr
                if tr.get("created_by"):
                    uids.add(tr["created_by"])
                if tr.get("updated_by"):
                    uids.add(tr["updated_by"])
    except Exception:
        return out
    names = {}
    if uids:
        try:
            with get_cursor() as cur:
                cur.execute(
                    "SELECT id, name FROM mis_user WHERE id = ANY(%s)",
                    (sorted(uids),),
                )
                for u in cur.fetchall():
                    names[u["id"]] = u["name"]
        except Exception:
            names = {}
    for i, p in enumerate(pks):
        tr = track.get(p)
        if not tr:
            continue
        cb, ub = tr.get("created_by"), tr.get("updated_by")
        out[i] = [
            format_dt_ap(tr.get("created_at")),
            names.get(cb, "") if cb else "",
            format_dt_ap(tr.get("updated_at")),
            names.get(ub, "") if ub else "",
        ]
    return out


def www_tracking_cells_inline(rows, cb_key="created_by", ub_key="updated_by",
                              ua_key="updated_at", ca_key="created_at"):
    """Variant for rows that already carry created_at/created_by/updated_at/
    updated_by (e.g. SELECT e.* or explicit a.created_at etc.). Resolves the
    two user ids to names in one batch; formats both timestamps. Aligned 1:1."""
    uids = set()
    for r in rows:
        try:
            if r.get(cb_key): uids.add(r[cb_key])
            if r.get(ub_key): uids.add(r[ub_key])
        except AttributeError:
            pass
    names = {}
    if uids:
        try:
            with get_cursor() as cur:
                cur.execute("SELECT id, name FROM mis_user WHERE id = ANY(%s)", (sorted(uids),))
                for u in cur.fetchall():
                    names[u["id"]] = u["name"]
        except Exception:
            names = {}
    out = []
    for r in rows:
        try:
            ca, cb, ua, ub = r.get(ca_key), r.get(cb_key), r.get(ua_key), r.get(ub_key)
        except AttributeError:
            out.append(list(_BLANK)); continue
        out.append([
            format_dt_ap(ca),
            names.get(cb, "") if cb else "",
            format_dt_ap(ua),
            names.get(ub, "") if ub else "",
        ])
    return out
