import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.mobile.auth.repository import MobileAuthRepository
from app.modules.mobile.auth.schema import (
    LoginResponse,
    ParticipantResponse,
)
from app.modules.mobile.core.utils import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

from app.modules.users.model import ParticipantMaster


# ==========================================================
# TEMPORARY DIAGNOSTIC LOGGER for the mobile login 401.
# Remove together with the [MOBILE-DIAG] lines once the cause
# is confirmed. Never logs password/PIN — only safe fields:
# username, user found/inactive/not-found, password-hash
# presence, and which step failed.
# ==========================================================
_diag = logging.getLogger("uvicorn.error")


class MobileAuthService:

    @staticmethod
    def login(
        db: Session,
        username: str,
        password: str,
    ) -> LoginResponse:

        # -----------------------------
        # Find participant
        # -----------------------------
        _diag.info("[MOBILE-DIAG] LOGIN attempt username=%r", username)

        participant = MobileAuthRepository.get_active_participant_by_username(
            db=db,
            username=username,
        )

        if participant is None:
            # Distinguish "no such username" from "exists but inactive/deleted"
            # (the active lookup requires status=='1' and deleted_at IS NULL).
            raw = (
                db.query(ParticipantMaster)
                .filter(ParticipantMaster.username == username)
                .first()
            )
            if raw is None:
                _diag.info(
                    "[MOBILE-DIAG] STEP user-lookup -> NO ROW with username=%r -> 401",
                    username,
                )
            else:
                _diag.info(
                    "[MOBILE-DIAG] STEP user-lookup -> row exists but INACTIVE "
                    "participant_id=%s status=%r deleted=%s -> 401",
                    raw.participant_id, raw.status, raw.deleted_at is not None,
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )

        _diag.info(
            "[MOBILE-DIAG] STEP user-lookup -> FOUND participant_id=%s status=%r has_password=%s",
            participant.participant_id, participant.status, bool(participant.password),
        )

        # -----------------------------
        # Verify password
        # -----------------------------
        if not verify_password(
            password,
            participant.password,
        ):
            _diag.info(
                "[MOBILE-DIAG] STEP verify-password -> FAILED participant_id=%s -> 401",
                participant.participant_id,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )

        _diag.info(
            "[MOBILE-DIAG] STEP verify-password -> OK participant_id=%s -> SUCCESS",
            participant.participant_id,
        )

        # -----------------------------
        # Generate Tokens
        # -----------------------------
        access_token = create_access_token(
            participant_id=participant.participant_id,
            username=participant.username,
        )

        refresh_token = create_refresh_token(
            participant_id=participant.participant_id,
            username=participant.username,
        )

        # -----------------------------
        # Record Login Activity
        # -----------------------------
        MobileAuthRepository.update_last_login(db=db, participant=participant)

        # -----------------------------
        # Response
        # -----------------------------
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            participant=ParticipantResponse(
                participant_id=participant.participant_id,
                enrollment_no=participant.enrollment_no,
                participant_name=participant.participant_name,
                username=participant.username,
                email=participant.email,
                mobile_no=participant.mobile_no,
                images=participant.images,
                progress_status=participant.progress_status,
                course_progress=participant.course_progress,
            ),
        )

    @staticmethod
    def refresh_token(
        db: Session,
        refresh_token: str,
    ):

        payload = decode_token(refresh_token)

        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
            )

        if payload.get("token_type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
            )

        participant = MobileAuthRepository.get_by_participant_id(
            db=db,
            participant_id=payload["participant_id"],
        )

        if participant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participant not found.",
            )

        access_token = create_access_token(
            participant_id=participant.participant_id,
            username=participant.username,
        )

        new_refresh_token = create_refresh_token(
            participant_id=participant.participant_id,
            username=participant.username,
        )

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
        }

    @staticmethod
    def logout():
        """
        JWT logout is handled on the client side.

        The Flutter app should delete:
        - access token
        - refresh token

        This endpoint exists for API consistency.
        """

        return {
            "message": "Logged out successfully."
        }

    @staticmethod
    def get_current_participant(
        db: Session,
        participant_id: int,
    ):

        participant = MobileAuthRepository.get_by_participant_id(
            db=db,
            participant_id=participant_id,
        )

        if participant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participant not found.",
            )

        return ParticipantResponse(
            participant_id=participant.participant_id,
            enrollment_no=participant.enrollment_no,
            participant_name=participant.participant_name,
            username=participant.username,
            email=participant.email,
            mobile_no=participant.mobile_no,
            images=participant.images,
            progress_status=participant.progress_status,
            course_progress=participant.course_progress,
        )