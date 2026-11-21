"""Shared ORDER BY resolver for WWW trainee list endpoints.

MGJ-style Sort By: A-Z / Z-A by trainee name, Newest/Oldest by insertion
order (the row id, which is monotonic and reliable even for historic
rows that all share one tracking-migration created_at). Values are safe
column fragments chosen by the caller — the raw `sort_by` string is only
matched against a fixed set of keys, never interpolated.
"""

def www_list_order(sort_by, name_col, id_col, default, enroll_col="enrollment_no", batch_col="batch_name", date_col=None):
    # 2026-08-29: added Enrollment No. Low/High. enroll_col defaults to the
    # SELECT output alias every WWW list exposes, so no call site changes.
    # 2026-11-04: Low-to-High / High-to-Low now sort by BATCH first then by
    # enrollment_no. Must reference batch_col as a plain SELECT alias --
    # PostgreSQL refuses alias references inside function calls in ORDER BY
    # (an earlier regexp_replace wrapper raised "column batch_name does not
    # exist"). Alphabetic sort by alias is safe everywhere. Lists with no
    # batch column (e.g. mobilisation) pass batch_col=None to skip batch.
    def _batch_prefix(direction):
        if not batch_col:
            return ""
        return batch_col + " " + direction + " NULLS LAST, "
    if sort_by == "enroll_asc":
        return _batch_prefix("ASC") + enroll_col + " ASC NULLS LAST, " + id_col + " DESC"
    if sort_by == "enroll_desc":
        return _batch_prefix("DESC") + enroll_col + " DESC NULLS LAST, " + id_col + " DESC"
    if sort_by == "name_asc":
        return name_col + " ASC, " + id_col + " DESC"
    if sort_by == "name_desc":
        return name_col + " DESC, " + id_col + " DESC"
    # 2026-11-04: Newest/Oldest sort by the list's primary date column when
    # provided (enrollment_date, walkout_date, start_date, ...). id_col acts
    # as tiebreaker (newest-first) so rows sharing the same date stay stable.
    # Lists without a meaningful primary date pass date_col=None.
    if sort_by == "added_newest":
        if date_col:
            return date_col + " DESC NULLS LAST, " + id_col + " DESC"
        return id_col + " DESC"
    if sort_by == "added_oldest":
        if date_col:
            return date_col + " ASC NULLS LAST, " + id_col + " DESC"
        return id_col + " ASC"
    return default
