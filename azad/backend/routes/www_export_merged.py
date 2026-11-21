# -*- coding: utf-8 -*-
"""
WWW cross-list export merger (2026-09-18, stage, joined version).

Given two WWW-list export endpoints, produces ONE xlsx workbook with ONE sheet:
  * left half  = the source list's rows (as-is, all its columns)
  * right half = the "other" list's columns for that same trainee, joined on
                 Enrollment No.
When a trainee has multiple records on the other side (e.g. 2 LL attempts),
the FIRST-match wins. When a trainee has no matching record, the appended
cells are blank. Duplicate trainee columns (Enrollment No, Name, Mobile,
State, District, Centre, Area, Enrollment Type, Block, S. No.) on the other
side are stripped so the same value never appears twice on a row.

If either side lacks an "Enrollment No." column (safety net -- all 17 WWW
lists have one today), the endpoint falls back to a 2-sheet workbook so the
download is never empty.

The merger reuses the existing /www-*/export/excel endpoints instead of
re-implementing each list's SQL, so RBAC scoping, filters, formatting and
column layout inherit automatically.
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
import urllib.request, urllib.parse
from copy import copy
from openpyxl import load_workbook, Workbook
from openpyxl.utils import get_column_letter, column_index_from_string


WWW_EXPORT_MODULES = {
    # slug                : (path,                                              label)
    "trainees":            ("/www-trainees/export/excel",                       "Enrollment"),
    "inductions":          ("/www-inductions/export/excel",                     "Induction"),
    "learning-licenses":   ("/www-learning-licenses/export/excel",              "Learning License"),
    "driving-practices":   ("/www-driving-practices/export/excel",              "Driving Practice"),
    "permanent-licenses":  ("/www-permanent-licenses/export/excel",             "Permanent License"),
    "nt-trainings":        ("/www-nt-trainings/export/excel",                   "NT Trainings"),
    "nt-attendance":       ("/www-nt-trainings/attendance/export/excel",        "NT Attendance"),
    "gbv":                 ("/www-gbv/export/excel",                            "GBV"),
    "fat":                 ("/www-fat/export/excel",                            "FAT"),
    "bks":                 ("/www-bks/export/excel",                            "BKS"),
    "pl-stories":          ("/www-pl-stories/export/excel",                    "PL Stories"),
    "internal-sakha":      ("/www-internal-sakha/export/excel",                "Internal Sakha"),
    "external-sakha":      ("/www-external-sakha/export/excel",                "External Sakha"),
    "employment":          ("/www-employment/export/excel",                     "Employment"),
    "walkout":             ("/www-walkout/export/excel",                        "Walkout"),
    "mobilisation":        ("/www-mobilisation/export/excel",                   "Mobilisation"),
    "surveys":             ("/www-surveys/export/excel",                        "Survey"),
}

# Columns to strip from the other side when joining, so a trainee's identity
# columns do not repeat on the same row. Case-insensitive header match.
_DUP_COL_NAMES = {
    "enrollment no.", "enrollment no", "enrollment number", "enrollment_no",
    "name", "trainee name",
    "mobile", "mobile no.", "mobile no", "phone",
    "enrollment type", "type of enrollment", "type",
    "state", "district", "centre", "center", "area", "block",
    "s. no.", "s.no.", "s no", "sno", "serial no", "serial no.",
}

router = APIRouter(prefix="/api", tags=["www-export-merged"])


# ---------------------------------------------------------------------------
# Loopback fetch
# ---------------------------------------------------------------------------
def _fetch_export_bytes(request: Request, path: str, forward_qs: str) -> bytes:
    """Loopback GET to /api/<path>?<forward_qs>, propagating auth headers."""
    url = "http://127.0.0.1:8080/api" + path
    if forward_qs:
        url = url + ("&" if "?" in path else "?") + forward_qs
    req = urllib.request.Request(url, method="GET")
    for h in ("authorization", "cookie", "x-forwarded-for", "user-agent"):
        v = request.headers.get(h)
        if v:
            req.add_header(h, v)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        detail = e.read()[:200].decode("utf-8", "replace") if hasattr(e, "read") else str(e)
        raise HTTPException(e.code if hasattr(e, "code") else 502, f"Sub-export {path} returned {e.code}: {detail}")
    except Exception as e:
        raise HTTPException(502, f"Sub-export {path} failed: {e}")


# ---------------------------------------------------------------------------
# Style copy helper
# ---------------------------------------------------------------------------
def _copy_cell_style(src_cell, dst_cell) -> None:
    try:
        if hasattr(src_cell, "has_style") and src_cell.has_style:
            dst_cell.font = copy(src_cell.font)
            dst_cell.fill = copy(src_cell.fill)
            dst_cell.alignment = copy(src_cell.alignment)
            dst_cell.border = copy(src_cell.border)
            dst_cell.number_format = src_cell.number_format
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Fallback 2-sheet layout (retained for the safety net path)
# ---------------------------------------------------------------------------
def _copy_sheet_into(src_ws, dst_wb, sheet_name: str) -> None:
    name = (sheet_name or "Sheet")[:31]
    dst_ws = dst_wb.create_sheet(title=name)
    for row in src_ws.iter_rows():
        for cell in row:
            new_cell = dst_ws.cell(row=cell.row, column=cell.column, value=cell.value)
            _copy_cell_style(cell, new_cell)
    for col_letter, dim in src_ws.column_dimensions.items():
        if dim and dim.width:
            dst_ws.column_dimensions[col_letter].width = dim.width
    for row_num, dim in src_ws.row_dimensions.items():
        if dim and dim.height:
            dst_ws.row_dimensions[row_num].height = dim.height
    for mr in list(src_ws.merged_cells.ranges):
        try:
            dst_ws.merge_cells(str(mr))
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Header detection: find the "Enrollment No." column in a header row
# ---------------------------------------------------------------------------
def _find_enrollment_col(header_row) -> int:
    for i, cell in enumerate(header_row):
        t = str(cell.value or "").strip().lower()
        if "enrollment" in t and "no" in t:
            return i
    return -1


# ---------------------------------------------------------------------------
# The JOINED single-sheet build.  Returns a Workbook, or None to signal
# fallback to the 2-sheet layout.
# ---------------------------------------------------------------------------
def _build_joined_workbook(ws_s, ws_o, src_label: str, other_label: str):
    rows_s = list(ws_s.iter_rows())
    rows_o = list(ws_o.iter_rows())
    if len(rows_s) < 2 or len(rows_o) < 2:
        return None

    # Every WWW export uses row 1 = grouped banner (may be merged), row 2 =
    # column names, row 3+ = data. NT Trainings is different: it has a
    # single header row at row 1 and data at row 2+. We detect this by
    # asking: does row-1 contain "Enrollment No." directly? If yes, treat
    # row-1 as headers and skip the banner layer.
    header_row_idx_s = 0 if _find_enrollment_col(rows_s[0]) >= 0 else 1
    header_row_idx_o = 0 if _find_enrollment_col(rows_o[0]) >= 0 else 1
    banner_row_s = rows_s[0] if header_row_idx_s == 1 else None
    banner_row_o = rows_o[0] if header_row_idx_o == 1 else None
    header_s = rows_s[header_row_idx_s]
    header_o = rows_o[header_row_idx_o]
    data_s   = rows_s[header_row_idx_s + 1:]
    data_o   = rows_o[header_row_idx_o + 1:]

    enr_s = _find_enrollment_col(header_s)
    enr_o = _find_enrollment_col(header_o)
    if enr_s < 0 or enr_o < 0:
        return None

    # Lookup for the other side: enrollment_no -> row cells. First match wins.
    other_by_enr = {}
    for row in data_o:
        if enr_o >= len(row):
            continue
        v = row[enr_o].value
        if v is None or str(v).strip() == "":
            continue
        key = str(v).strip()
        if key not in other_by_enr:
            other_by_enr[key] = row

    # Which columns of "other" to keep (skip duplicates of source or the
    # standard trainee-identity block).
    src_names = set()
    for cell in header_s:
        t = str(cell.value or "").strip().lower()
        if t:
            src_names.add(t)
    other_keep = []
    for i, cell in enumerate(header_o):
        t = str(cell.value or "").strip().lower()
        if not t:
            continue                                # drop columns without a header name
        if t in _DUP_COL_NAMES or t in src_names:
            continue
        other_keep.append(i)

    src_ncols = ws_s.max_column

    # Build the merged workbook
    merged_wb = Workbook()
    merged_wb.remove(merged_wb.active)
    title = ("%s + %s" % (src_label, other_label))[:31]
    ws = merged_wb.create_sheet(title=title)

    # Which output row each original source-row lands on
    dst_header_row = 1 if banner_row_s is None else 2
    dst_data_start = dst_header_row + 1

    # ---- Row 1 (banner, if present) ----
    if banner_row_s is not None:
        for i, cell in enumerate(banner_row_s, start=1):
            new_cell = ws.cell(row=1, column=i, value=cell.value)
            _copy_cell_style(cell, new_cell)
    if banner_row_o is not None:
        for k, o_i in enumerate(other_keep):
            if o_i < len(banner_row_o):
                new_cell = ws.cell(row=1, column=src_ncols + 1 + k, value=banner_row_o[o_i].value)
                _copy_cell_style(banner_row_o[o_i], new_cell)

    # ---- Header row (col names) ----
    for i, cell in enumerate(header_s, start=1):
        new_cell = ws.cell(row=dst_header_row, column=i, value=cell.value)
        _copy_cell_style(cell, new_cell)
    for k, o_i in enumerate(other_keep):
        if o_i < len(header_o):
            new_cell = ws.cell(row=dst_header_row, column=src_ncols + 1 + k, value=header_o[o_i].value)
            _copy_cell_style(header_o[o_i], new_cell)

    # ---- Data rows: source + matched other ----
    for r_off, src_row in enumerate(data_s):
        dst_row = dst_data_start + r_off
        for col_idx, cell in enumerate(src_row, start=1):
            new_cell = ws.cell(row=dst_row, column=col_idx, value=cell.value)
            _copy_cell_style(cell, new_cell)
        # look up the other-side match
        key = ""
        if enr_s < len(src_row) and src_row[enr_s].value is not None:
            key = str(src_row[enr_s].value).strip()
        o_row = other_by_enr.get(key) if key else None
        for k, o_i in enumerate(other_keep):
            dst_col = src_ncols + 1 + k
            if o_row is not None and o_i < len(o_row):
                oc = o_row[o_i]
                new_cell = ws.cell(row=dst_row, column=dst_col, value=oc.value)
                _copy_cell_style(oc, new_cell)
            # else: leave blank

    # ---- Merged ranges from source (only banner row, column positions unchanged) ----
    if banner_row_s is not None:
        for mr in list(ws_s.merged_cells.ranges):
            try:
                if mr.min_row == 1 and mr.max_row == 1:
                    ws.merge_cells(str(mr))
            except Exception:
                pass

    # ---- Merged ranges from the OTHER side (row-1 banners), shifted right by
    # src_ncols and filtered to columns we actually kept. 2026-09-19: this
    # restores the "Induction Details" (and any similar) group-header banner
    # so it spans all its data cols in the merged file, not just the first.
    if banner_row_o is not None:
        for mr in list(ws_o.merged_cells.ranges):
            if mr.min_row != 1 or mr.max_row != 1:
                continue
            lo0, hi0 = mr.min_col - 1, mr.max_col - 1     # 0-indexed source range
            in_range = [ok for ok in other_keep if lo0 <= ok <= hi0]
            if len(in_range) < 2:
                continue                                    # single-col: nothing to merge
            first_pos = other_keep.index(in_range[0])
            last_pos  = other_keep.index(in_range[-1])
            first_out = src_ncols + 1 + first_pos
            last_out  = src_ncols + 1 + last_pos
            try:
                ws.merge_cells(start_row=1, start_column=first_out,
                                end_row=1, end_column=last_out)
            except Exception:
                pass

    # ---- Column widths ----
    for col_letter, dim in ws_s.column_dimensions.items():
        if dim and dim.width:
            try:
                ws.column_dimensions[col_letter].width = dim.width
            except Exception:
                pass
    for col_letter, dim in ws_o.column_dimensions.items():
        if not dim or not dim.width:
            continue
        try:
            orig_idx0 = column_index_from_string(col_letter) - 1
            if orig_idx0 in other_keep:
                k = other_keep.index(orig_idx0)
                new_idx = src_ncols + 1 + k
                ws.column_dimensions[get_column_letter(new_idx)].width = dim.width
        except Exception:
            pass

    return merged_wb


@router.get("/www/export-merged")
def export_merged(request: Request, src: str, other: str):
    if src not in WWW_EXPORT_MODULES:
        raise HTTPException(400, f"Unknown src module '{src}'")
    if other not in WWW_EXPORT_MODULES:
        raise HTTPException(400, f"Unknown other module '{other}'")
    if src == other:
        raise HTTPException(400, "src and other must be different modules")

    qp = [(k, v) for (k, v) in request.query_params.multi_items()
          if k not in ("src", "other")]
    forward_qs = urllib.parse.urlencode(qp, quote_via=urllib.parse.quote)
    src_path,   src_label   = WWW_EXPORT_MODULES[src]
    other_path, other_label = WWW_EXPORT_MODULES[other]

    src_bytes   = _fetch_export_bytes(request, src_path,   forward_qs)
    other_bytes = _fetch_export_bytes(request, other_path, forward_qs)

    try:
        wb_s = load_workbook(BytesIO(src_bytes))
        wb_o = load_workbook(BytesIO(other_bytes))
    except Exception as e:
        raise HTTPException(500, f"Could not read sub-export workbook: {e}")

    # Try the joined single-sheet build first. If either side lacks an
    # Enrollment No. column, fall back to the 2-sheet layout so users
    # still get a workbook.
    merged = _build_joined_workbook(wb_s.active, wb_o.active, src_label, other_label)
    if merged is None:
        merged = Workbook()
        merged.remove(merged.active)
        _copy_sheet_into(wb_s.active, merged, src_label)
        _copy_sheet_into(wb_o.active, merged, other_label)

    buf = BytesIO()
    merged.save(buf)
    buf.seek(0)
    fname = ("WWW_%s_+_%s.xlsx" % (src_label, other_label)).replace(" ", "_")
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="%s"' % fname},
    )
