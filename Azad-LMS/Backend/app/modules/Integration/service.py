import logging
import os
import re
from datetime import date, datetime

import httpx
from fastapi import HTTPException, status
from sqlalchemy import String, cast, func, text
from sqlalchemy.orm import Session

from app.modules.batch.model import BatchMaster
from app.modules.centres.model import CentreMaster
from app.modules.users.model import ParticipantMaster
from app.modules.users.repository import UserRepository
from app.modules.users.schema import ParticipantCreateRequest

from .schema import WWWTraineeCreateRequest


# ==========================================================
# LMS participant login URL returned to WWW.
#
# WWW requires a `url` field in the response. This is the LMS
# web app where the trainee logs in (the same frontend listed
# in app.main CORS origins). Configurable per environment via
# LMS_LOGIN_URL; defaults to the stage frontend.
# ==========================================================
LMS_LOGIN_URL = os.getenv(
    "LMS_LOGIN_URL",
    "https://demo-azadlms.indevconsultancy.in",
)


# ==========================================================
# Diagnostic logger: records incoming WWW identifiers and the
# resolved LMS centre/batch (no password/PIN, photo as presence).
# Writes to the uvicorn log, tagged [WWW-DIAG].
# ==========================================================
_diag = logging.getLogger("uvicorn.error")


# ==========================================================
# GENDER NORMALIZATION
#
# WWW sends gender values that must be normalized to the LMS
# vocabulary before insert. Matching is case-insensitive and
# whitespace-trimmed. Any value NOT in the map is passed
# through unchanged (unrelated gender values are untouched).
# ==========================================================
_GENDER_MAP = {
    "cis woman": "women",
}


def _normalize_gender(value):
    if value is None:
        return value
    key = str(value).strip().lower()
    return _GENDER_MAP.get(key, value)


# ==========================================================
# BATCH IDENTIFIER NORMALIZATION
#
# Reduce a WWW/LMS batch identifier to a comparable core token:
# lowercased, trimmed, internal whitespace collapsed, and a
# leading "batch" plus its separator (space / - / _) removed.
# So "258", 258, "Batch-258", "Batch 258", "batch_258" all
# compare equal as "258". Returns "" for None/empty so empty
# tokens never match anything.
# ==========================================================
def _normalize_batch_token(value):
    if value is None:
        return ""
    s = re.sub(r"\s+", " ", str(value).strip().lower())
    s = re.sub(r"^batch[\s\-_]*", "", s)
    return s.strip()


def _calculate_age_from_dob(dob):
    """
    Calculate completed age from date_of_birth.

    Supports:
      YYYY-MM-DD
      YYYY/MM/DD
      DD-MM-YYYY
      DD/MM/YYYY

    Returns None when DOB is missing or invalid.
    """

    if not dob:
        return None

    if isinstance(dob, datetime):
        dob = dob.date()

    if isinstance(dob, date):
        dob_date = dob
    else:
        value = str(dob).strip()

        formats = (
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
        )

        dob_date = None

        for fmt in formats:
            try:
                dob_date = datetime.strptime(
                    value,
                    fmt,
                ).date()
                break
            except ValueError:
                continue

        if dob_date is None:
            return None

    today = date.today()

    age = (
        today.year
        - dob_date.year
        - (
            (today.month, today.day)
            < (dob_date.month, dob_date.day)
        )
    )

    if age < 1 or age > 120:
        return None

    return age


def _current_financial_year():
    """Indian financial year (April-March), e.g. '2026-27'. Used as the
    default fy_year when auto-creating a batch that WWW did not specify."""
    today = date.today()
    start = today.year if today.month >= 4 else today.year - 1
    return f"{start}-{str(start + 1)[-2:]}"


def _resolve_batch_name_from_mis(www_batch_id):
    """
    Optional outbound resolver for the case where WWW omits batch_name.

    When (and only when) a MIS batch endpoint is configured via env, fetch
    the batch's REAL name from the MIS source so the LMS batch is created
    with the actual name (never an invented one). Returns the resolved
    name, or None when not configured / unreachable / unresolved.

    Env (all optional; unset -> resolver is inert, no HTTP call is made):
      MIS_BATCH_API_URL    : URL template, e.g.
                             "https://mis-azad.indevconsultancy.com/api/batches/{batch_id}"
      MIS_BATCH_API_TOKEN  : bearer token sent as Authorization, if set
      MIS_BATCH_NAME_FIELD : dotted path to the name in the JSON response
                             (default "batch_name"), e.g. "data.name"
    """
    url_tmpl = os.getenv("MIS_BATCH_API_URL")
    if not url_tmpl or not www_batch_id:
        return None

    try:
        url = url_tmpl.format(batch_id=www_batch_id)
        headers = {}
        token = os.getenv("MIS_BATCH_API_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        resp = httpx.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None

        data = resp.json()
        for key in os.getenv("MIS_BATCH_NAME_FIELD", "batch_name").split("."):
            data = data.get(key) if isinstance(data, dict) else None
            if data is None:
                break

        name = str(data).strip() if data else ""
        return name or None
    except Exception:
        # Resolver must never break trainee creation; fall through to the
        # clear "batch name required" error instead.
        return None


class WWWIntegrationService:

    # ==========================================================
    # FIND CENTRE
    # ==========================================================

    @staticmethod
    def find_centre(
        db: Session,
        centre_code,
    ):
        """
        Resolve the WWW centre_id to an LMS centre strictly via
        centre_masters.mis_center_id (case-insensitive & trimmed).
        Returns None if not found (triggers the 'NO' response flow).
        No other centre, name, or numeric ID fallback is allowed.
        """
        if centre_code is None:
            return None

        value = str(centre_code).strip()
        if not value:
            return None

        val_lower = value.lower()

        return (
            db.query(CentreMaster)
            .filter(
                CentreMaster.deleted_at.is_(None),
                func.lower(func.trim(CentreMaster.mis_center_id)) == val_lower,
            )
            .first()
        )

    # ==========================================================
    # BATCH RESOLUTION LOOKUPS
    # ==========================================================

    @staticmethod
    def find_batch_by_mis_batch_id(
        db: Session,
        centre_id: int,
        www_batch_id: str | int | None,
    ):
        """
        Primary batch lookup: scoped strictly to the resolved LMS centre_id,
        matching LMS batch_masters.mis_batch_id == WWW batch_id (case-insensitive & trimmed).
        """
        if not centre_id or www_batch_id is None:
            return None

        cid = centre_id.centre_id if hasattr(centre_id, "centre_id") else centre_id
        val = str(www_batch_id).strip()
        if not val:
            return None

        val_lower = val.lower()

        return (
            db.query(BatchMaster)
            .filter(
                BatchMaster.centre_id == cid,
                BatchMaster.deleted_at.is_(None),
                func.lower(func.trim(cast(BatchMaster.mis_batch_id, String))) == val_lower,
            )
            .first()
        )

    @staticmethod
    def find_batch_by_name(
        db: Session,
        centre_id: int,
        batch_name: str | None,
    ):
        """
        Fallback lookup: scoped strictly to the same LMS centre_id,
        matching LMS batch_masters.batch_name == WWW batch_name (case-insensitive & trimmed).
        """
        if not centre_id or not batch_name:
            return None

        cid = centre_id.centre_id if hasattr(centre_id, "centre_id") else centre_id
        name = str(batch_name).strip()
        if not name:
            return None

        name_lower = name.lower()

        return (
            db.query(BatchMaster)
            .filter(
                BatchMaster.centre_id == cid,
                BatchMaster.deleted_at.is_(None),
                func.lower(func.trim(BatchMaster.batch_name)) == name_lower,
            )
            .order_by(
                func.coalesce(
                    func.nullif(func.trim(cast(BatchMaster.mis_batch_id, String)), ""),
                    "",
                )
            )
            .first()
        )

    @staticmethod
    def find_batch(
        db: Session,
        centre,
        batch_value,
    ):
        """Backward-compatibility alias pointing to primary mis_batch_id lookup."""
        if centre is None or batch_value is None:
            return None
        cid = centre.centre_id if hasattr(centre, "centre_id") else centre
        return WWWIntegrationService.find_batch_by_mis_batch_id(db, cid, batch_value)

    # ==========================================================
    # RESOLVE OR CREATE BATCH
    # ==========================================================

    @staticmethod
    def resolve_or_create_batch(
        db: Session,
        centre,
        www_batch_id: str | None,
        www_batch_name: str | None,
    ):
        """
        Resolve a WWW batch to an LMS batch under `centre`, implementing:

        1. Primary Batch Lookup:
           Search LMS centre_id + LMS mis_batch_id (where mis_batch_id == WWW batch_id).
           If found -> Use that existing LMS batch. Do not create another batch.

        2. Batch ID Not Found -> Batch Name Fallback:
           Search same LMS centre_id + same batch_name.

           - Batch Name Not Found:
             Create a new LMS batch using:
               batch_name = WWW batch_name
               centre_id = resolved LMS centre_id
               mis_batch_id = WWW batch_id

           - Same Batch Name Found:
             * Case A (mis_batch_id is NULL / EMPTY):
               Reuse existing batch, backfill existing batch.mis_batch_id = WWW batch_id.
             * Case B (existing mis_batch_id is DIFFERENT):
               Do NOT reuse that batch. Create a new LMS batch with:
                 batch_name = WWW batch_name
                 centre_id = resolved LMS centre_id
                 mis_batch_id = WWW batch_id
        """
        clean_batch_id = str(www_batch_id).strip() if www_batch_id is not None else ""
        clean_batch_name = str(www_batch_name).strip() if www_batch_name is not None else ""

        # 1. Primary Batch Lookup: centre_id + mis_batch_id
        if clean_batch_id:
            batch = WWWIntegrationService.find_batch_by_mis_batch_id(
                db=db,
                centre_id=centre.centre_id,
                www_batch_id=clean_batch_id,
            )
            if batch is not None:
                return batch, False

        # If WWW omitted batch_name, try MIS source resolver or fallback to "Batch-<id>"
        if not clean_batch_name:
            resolved = _resolve_batch_name_from_mis(clean_batch_id)
            if resolved:
                _diag.info(
                    "[WWW-DIAG] BATCH name resolved from MIS source "
                    "batch_id=%r -> %r",
                    clean_batch_id, resolved,
                )
                clean_batch_name = resolved
            elif clean_batch_id:
                clean_batch_name = f"Batch-{clean_batch_id}"
                _diag.info(
                    "[WWW-DIAG] BATCH name fallback (no WWW/MIS name) "
                    "batch_id=%r -> %r",
                    clean_batch_id, clean_batch_name,
                )

        if not clean_batch_name:
            return None, False

        # Advisory lock for serialized creation per (centre, www_batch_id / batch_name)
        lock_token = (clean_batch_id or clean_batch_name).lower()
        lock_key = f"wwwbatch:{centre.centre_id}:{lock_token}"
        db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:k))"),
            {"k": lock_key},
        )

        # Re-check primary lookup inside lock
        if clean_batch_id:
            batch = WWWIntegrationService.find_batch_by_mis_batch_id(
                db=db,
                centre_id=centre.centre_id,
                www_batch_id=clean_batch_id,
            )
            if batch is not None:
                return batch, False

        # 2. Batch ID Not Found -> Batch Name Fallback:
        # Same LMS centre_id + same batch_name
        batch_by_name = WWWIntegrationService.find_batch_by_name(
            db=db,
            centre_id=centre.centre_id,
            batch_name=clean_batch_name,
        )

        if batch_by_name is not None:
            existing_mis = (
                str(batch_by_name.mis_batch_id).strip()
                if batch_by_name.mis_batch_id is not None
                else ""
            )
            # Case A: mis_batch_id is NULL / EMPTY -> safely reuse and backfill
            if not existing_mis:
                batch_by_name.mis_batch_id = clean_batch_id or None
                db.commit()
                db.refresh(batch_by_name)
                _diag.info(
                    "[WWW-DIAG] Backfilled existing batch_id=%s with mis_batch_id=%r",
                    batch_by_name.batch_id, clean_batch_id,
                )
                return batch_by_name, False

            # If existing mis_batch_id matches WWW batch_id: reuse
            if clean_batch_id and existing_mis.lower() == clean_batch_id.lower():
                return batch_by_name, False

            # Case B: existing mis_batch_id is DIFFERENT (e.g. 99 != 148)
            # DO NOT REUSE EXISTING BATCH -> Create a new LMS batch below
            _diag.info(
                "[WWW-DIAG] Existing batch_id=%s has different mis_batch_id=%r "
                "(!= incoming %r). Creating new batch.",
                batch_by_name.batch_id, existing_mis, clean_batch_id,
            )

        # 3. Batch Name Not Found OR Different mis_batch_id -> CREATE NEW LMS BATCH
        new_batch = BatchMaster(
            batch_name=clean_batch_name,
            centre_id=centre.centre_id,
            mis_batch_id=(clean_batch_id or None),
            status=1,
            created_by=0,
            fy_year=_current_financial_year(),
        )
        db.add(new_batch)
        db.commit()
        db.refresh(new_batch)
        return new_batch, True

    # ==========================================================
    # CREATE PARTICIPANT
    # ==========================================================

    @staticmethod
    def create_participant(
        db: Session,
        data: WWWTraineeCreateRequest,
    ):

        _diag.error("========== NEW WWW SERVICE CALLED ==========")

        # ======================================================
        # 0. PARTICIPANT PHOTO (OPTIONAL)
        # ======================================================
        #
        # photo_url is OPTIONAL. If missing/empty we normalize it to
        # None: the participant is still created, no empty string is
        # ever stored, and an existing image is never overwritten
        # with NULL (see the idempotent branch below).
        # ------------------------------------------------------

        image_url = (data.images or "").strip() or None

        _diag.info(
            "[WWW-DIAG] RECV enrollment=%r centre_id=%r batch_id=%r "
            "batch_name=%r photo=%s",
            data.enrollment_no, data.centre_code, data.batch_id,
            data.batch_name, bool(image_url),
        )

        # ======================================================
        # 1. FIND CENTRE  (WWW centre_id -> mis_centre_id)
        # ======================================================
        #
        # lms_participant_create == "YES" only when the WWW centre_id
        # resolves to an LMS centre via mis_centre_id. Otherwise we
        # return "NO" (HTTP 200) without creating anything.
        # ------------------------------------------------------

        centre = (
            WWWIntegrationService.find_centre(
                db=db,
                centre_code=data.centre_code,
            )
        )

        if not centre:

            _diag.info(
                "[WWW-DIAG] CENTRE not resolved for centre_id=%r -> NO",
                data.centre_code,
            )
            return {
                "lms_participant_create": "NO",
                "participant_id": None,
                "image": None,
                "url": LMS_LOGIN_URL,
                "message": (
                    "Centre mapping not found: "
                    f"{data.centre_code}"
                ),
            }

        _diag.info(
            "[WWW-DIAG] CENTRE resolved centre_id=%r -> lms_centre_id=%s "
            "mis_center_id=%r",
            data.centre_code, centre.centre_id, centre.mis_centre_id,
        )

        # ======================================================
        # 2. RESOLVE BATCH  (find existing, else auto-create)
        # ======================================================
        #
        # Authoritative mapping: WWW batch_id -> batch_masters.mis_batch_id
        # scoped to the centre. If not found, falls back to same-centre
        # batch_name. If batch does not exist or has a different mis_batch_id,
        # creates a new batch under this centre.
        # ------------------------------------------------------

        www_batch_id = (data.batch_id or "").strip()
        www_batch_name = (data.batch_name or "").strip()

        if not www_batch_id and not www_batch_name:
            _diag.info(
                "[WWW-DIAG] BATCH missing for enrollment=%r centre=%s -> NO",
                data.enrollment_no, centre.centre_id,
            )
            return {
                "lms_participant_create": "NO",
                "participant_id": None,
                "image": None,
                "url": LMS_LOGIN_URL,
                "message": (
                    "Batch is required to create a trainee in LMS. "
                    "Please assign a batch to this trainee in MIS."
                ),
            }

        batch, batch_created = WWWIntegrationService.resolve_or_create_batch(
            db=db,
            centre=centre,
            www_batch_id=www_batch_id,
            www_batch_name=www_batch_name,
        )

        if batch is None:
            # Only reached when the batch does not exist AND no batch_name
            # was supplied, so we cannot create a meaningful batch.
            _diag.info(
                "[WWW-DIAG] BATCH not resolved and no batch_name batch_id=%r "
                "centre=%s -> NO",
                data.batch_id, centre.centre_id,
            )
            return {
                "lms_participant_create": "NO",
                "participant_id": None,
                "image": None,
                "url": LMS_LOGIN_URL,
                "message": (
                    "Batch name is required to create a new batch for "
                    f"batch_id {data.batch_id} in centre {data.centre_code}."
                ),
            }

        _diag.info(
            "[WWW-DIAG] BATCH %s (mis_center_id=%r + mis_batch_id=%r) -> "
            "lms_batch_id=%s name=%r",
            "AUTO-CREATED" if batch_created else "FOUND/reused",
            centre.mis_centre_id, batch.mis_batch_id,
            batch.batch_id, batch.batch_name,
        )

        # ======================================================
        # 3. BUILD PARTICIPANT DATA
        # ======================================================

        # Age calculation: WWW sends DOB, not age.
        # If age is not sent, calculate it from date_of_birth.
        calculated_age = data.age
        if calculated_age is None and getattr(data, "date_of_birth", None):
            calculated_age = _calculate_age_from_dob(data.date_of_birth)

        normalized_gender = _normalize_gender(data.gender)

        participant_data = ParticipantCreateRequest(

            # --------------------------------------------------
            # LOCATION FROM CENTRE
            # --------------------------------------------------

            state_id=(centre.state_id or 1),

            district_id=(centre.district_id or 1),

            block_id=centre.block_id,

            centre_id=centre.centre_id,

            # --------------------------------------------------
            # RESOLVED LMS BATCH ID
            # --------------------------------------------------

            batch_id=batch.batch_id,

            # --------------------------------------------------
            # TRAINEE DATA
            # --------------------------------------------------

            participant_name=data.participant_name,

            enrollment_no=data.enrollment_no,

            username=data.username,

            password=data.password,

            # Normalize WWW gender to the LMS vocabulary
            # (e.g. "cis woman" -> "women"); other values unchanged.
            gender=normalized_gender,

            age=calculated_age,

            email=data.email,

            mobile_no=data.mobile_no,

            # --------------------------------------------------
            # PIN
            # --------------------------------------------------
            # Excel PIN if available,
            # otherwise centre PIN.
            # --------------------------------------------------

            pin=(
                data.pin
                if data.pin
                else (centre.pin or "110001")
            ),

            # WWW import does not provide Aadhaar.
            # Keep it NULL.
            # --------------------------------------------------

            aadhaar_number=None,

            # --------------------------------------------------
            # LOCATION
            # --------------------------------------------------

            location=(
                data.location
                if data.location
                else (centre.location or centre.centre_name or "Location")
            ),

            # --------------------------------------------------
            # ADDRESS
            # --------------------------------------------------

            address=(
                data.address
                if data.address
                else (centre.address or centre.centre_name or "Address")
            ),
        )

        # ======================================================
        # 4. CREATE PARTICIPANT (IDEMPOTENT)
        # ======================================================
        #
        # UserRepository.create_participant reuses the existing LMS
        # duplicate-detection logic and returns a sentinel string
        # instead of a participant when a duplicate is detected:
        #
        #   "duplicate_enrollment_no" -> same trainee already exists
        #   "duplicate_username"      -> username collision
        #
        # We must NOT create a duplicate participant for the same
        # trainee, so these sentinels are handled here.
        # ------------------------------------------------------

        participant = (
            UserRepository.create_participant(
                db=db,
                data=participant_data,
                image_name=image_url,
            )
        )

        # ------------------------------------------------------
        # SAME TRAINEE ALREADY IMPORTED -> idempotent success.
        # Return the existing participant instead of creating a
        # duplicate. If a NEW photo was provided, refresh the stored
        # image; we NEVER overwrite an existing image with NULL.
        # ------------------------------------------------------

        if participant == "duplicate_enrollment_no":

            existing = (
                db.query(ParticipantMaster)
                .filter(
                    ParticipantMaster.enrollment_no == data.enrollment_no,
                    ParticipantMaster.deleted_at.is_(None),
                )
                .first()
            )

            if existing:

                if image_url and existing.images != image_url:
                    existing.images = image_url
                    db.commit()
                    db.refresh(existing)

                return {
                    "lms_participant_create": "YES",
                    "participant_id": existing.participant_id,
                    "image": existing.images,
                    "url": LMS_LOGIN_URL,
                    "message": "Trainee already exists (idempotent).",
                }

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Duplicate enrollment number could not be resolved: "
                    f"{data.enrollment_no}"
                ),
            )

        # ------------------------------------------------------
        # USERNAME COLLISION (different trainee) -> conflict.
        # ------------------------------------------------------

        if participant == "duplicate_username":

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Username already exists: "
                    f"{data.username}"
                ),
            )

        # ------------------------------------------------------
        # MOBILE NUMBER COLLISION -> conflict.
        # ------------------------------------------------------

        if participant == "duplicate_mobile_no":

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Mobile number already exists: "
                    f"{data.mobile_no}"
                ),
            )

        # ------------------------------------------------------
        # EMAIL COLLISION -> conflict.
        # ------------------------------------------------------

        if participant == "duplicate_email":

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Email already exists: "
                    f"{data.email}"
                ),
            )

        # ------------------------------------------------------
        # AADHAAR COLLISION -> conflict.
        # ------------------------------------------------------

        if participant == "duplicate_aadhaar_number":

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Aadhaar number already exists.",
            )

        # ------------------------------------------------------
        # NEW PARTICIPANT CREATED.
        # ------------------------------------------------------

        _diag.info(
            "[WWW-DIAG] TRAINEE enrolled participant_id=%s -> lms_batch_id=%s "
            "name=%r mis_batch_id=%r",
            participant.participant_id, batch.batch_id,
            batch.batch_name, batch.mis_batch_id,
        )

        return {
            "lms_participant_create": "YES",
            "participant_id": participant.participant_id,
            "image": participant.images,
            "url": LMS_LOGIN_URL,
            "message": "Trainee created successfully",
        }
