from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db

from .schema import WWWTraineeCreateRequest
from .service import WWWIntegrationService


router = APIRouter(
    tags=["WWW Integration"],
)


def _create_www_trainee(
    data: WWWTraineeCreateRequest,
    db: Session = Depends(get_db),
):
    return WWWIntegrationService.create_participant(
        db=db,
        data=data,
    )


@router.post(
    "/integrations/www/trainee",
    response_model=dict,
)
def create_www_trainee(
    data: WWWTraineeCreateRequest,
    db: Session = Depends(get_db),
):
    return _create_www_trainee(
        data=data,
        db=db,
    )


@router.post(
    "/api/add-trainee",
    response_model=dict,
)
def create_www_trainee_legacy(
    data: WWWTraineeCreateRequest,
    db: Session = Depends(get_db),
):
    # Existing WWW Create LMS Login flow.
    # Uses the exact same service and batch mapping logic.
    return _create_www_trainee(
        data=data,
        db=db,
    )


@router.post(
    "/add-trainee",
    response_model=dict,
)
def create_www_trainee_legacy_root(
    data: WWWTraineeCreateRequest,
    db: Session = Depends(get_db),
):
    return _create_www_trainee(
        data=data,
        db=db,
    )
