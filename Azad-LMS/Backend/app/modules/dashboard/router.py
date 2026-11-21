from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.dashboard.schema import (
    DashboardCentreDetail,
    DashboardDocumentDetail,
    DashboardLoginDetail,
    DashboardModuleDetail,
    DashboardParticipantDetail,
    DashboardResponse,
    MonthlyLoginTrendItem,
    MonthlyTrendingModuleItem,
    ModuleAssignmentUsageItem,
    TraineeStatusDetail,
    StateWiseTraineesItem,
    CentreWiseTraineesItem,
    StateWiseTraineeStatusItem,
    NeedAttentionSummaryResponse,
    NeedAttentionLearnersResponse,
    RecentLearnersResponse,
    LearnerDetailResponse,
    CentreLeaderboardResponse,
    TopLearnersResponse,
)

from app.modules.dashboard.service import DashboardService
from app.shared.dependencies.module_access import Module, require_module_access
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.model import User
from app.modules.users.service import UserService

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(require_module_access(Module.DASHBOARD))],
)


@router.get(
    "",
    response_model=DashboardResponse,
)
def get_dashboard(
    state_id: int | None = Query(None),
    district_id: int | None = Query(None),
    centre_id: int | None = Query(None),
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user, state_id, district_id, centre_id
    )
    return DashboardService.get_dashboard_summary(
        db=db,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get(
    "/trainee-status/details",
    response_model=list[TraineeStatusDetail],
)
def get_trainee_status_details(
    state_id: int | None = None,
    district_id: int | None = None,
    centre_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user, state_id, district_id, centre_id
    )
    return DashboardService.get_trainee_status_details(
        db=db,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
    )


@router.get(
    "/state-wise-trainee-status",
    response_model=list[StateWiseTraineeStatusItem],
)
def get_state_wise_trainee_status_route(
    state_id: int | None = None,
    district_id: int | None = None,
    centre_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user,
        state_id,
        district_id,
        centre_id,
    )

    return DashboardService.get_state_wise_trainee_status(
        db=db,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
    )


@router.get(
    "/state-wise-participants",
    response_model=list[DashboardParticipantDetail],
)
def get_state_wise_participants(
    clicked_value: int | None = None,
    state_id: int | None = None,
    district_id: int | None = None,
    centre_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user, state_id, district_id, centre_id
    )
    return DashboardService.get_state_wise_participants(
        db=db,
        clicked_value=clicked_value,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get(
    "/district-wise-participants",
    response_model=list[DashboardParticipantDetail],
)
def get_district_wise_participants(
    clicked_value: str | None = None,
    state_id: int | None = None,
    district_id: int | None = None,
    centre_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user, state_id, district_id, centre_id
    )
    return DashboardService.get_district_wise_participants(
        db=db,
        clicked_value=clicked_value,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get(
    "/gender-distribution",
    response_model=list[DashboardParticipantDetail],
)
def get_gender_distribution(
    clicked_value: str | None = None,
    state_id: int | None = None,
    district_id: int | None = None,
    centre_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user, state_id, district_id, centre_id
    )
    return DashboardService.get_gender_distribution(
        db=db,
        clicked_value=clicked_value,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get(
    "/age-group-distribution",
    response_model=list[DashboardParticipantDetail],
)
def get_age_group_distribution(
    clicked_value: str | None = None,
    state_id: int | None = None,
    district_id: int | None = None,
    centre_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user, state_id, district_id, centre_id
    )
    return DashboardService.get_age_group_distribution(
        db=db,
        clicked_value=clicked_value,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get(
    "/state-wise-centres",
    response_model=list[DashboardCentreDetail],
)
def get_state_wise_centres(
    clicked_value: str | None = None,
    state_id: int | None = None,
    district_id: int | None = None,
    centre_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user, state_id, district_id, centre_id
    )
    return DashboardService.get_state_wise_centres(
        db=db,
        clicked_value=clicked_value,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get(
    "/module-wise-performance",
    response_model=list[DashboardModuleDetail],
)
def get_module_wise_performance(
    clicked_value: str | None = None,
    state_id: int | None = None,
    district_id: int | None = None,
    centre_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user, state_id, district_id, centre_id
    )
    return DashboardService.get_module_wise_performance_details(
        db=db,
        clicked_value=clicked_value,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get(
    "/document-type-distribution",
    response_model=list[DashboardDocumentDetail],
)
def get_document_type_distribution(
    db: Session = Depends(get_db),
):
    return DashboardService.get_document_type_distribution(
        db=db,
    )


@router.get(
    "/monthly-trending-modules",
    response_model=list[MonthlyTrendingModuleItem],
)
def get_monthly_trending_modules(
    state_id: int | None = None,
    district_id: int | None = None,
    centre_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user,
        state_id,
        district_id,
        centre_id,
    )

    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="from_date cannot be later than to_date",
        )

    return DashboardService.get_monthly_trending_modules(
        db=db,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get(
    "/module-assignment-usage",
    response_model=list[ModuleAssignmentUsageItem],
)
def get_module_assignment_usage(
    state_id: int | None = None,
    district_id: int | None = None,
    centre_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user,
        state_id,
        district_id,
        centre_id,
    )

    return DashboardService.get_module_assignment_usage(
        db=db,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
    )


# @router.get(
#     "/monthly-logins",
#     response_model=list[MonthlyLoginTrendItem],
# )
# def get_monthly_logins(
#     clicked_value: str | None = None,
#     state_id: int | None = None,
#     district_id: int | None = None,
#     centre_id: int | None = None,
#     from_date: date | None = None,
#     to_date: date | None = None,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     state_id, district_id, centre_id = UserService.clamp_scope(
#         current_user, state_id, district_id, centre_id
#     )
#     return DashboardService.get_monthly_logins(
#         db=db,
#         clicked_value=clicked_value,
#         state_id=state_id,
#         district_id=district_id,
#         centre_id=centre_id,
#         from_date=from_date,
#         to_date=to_date,
#     )


@router.get(
    "/monthly-logins/details",
    response_model=list[DashboardLoginDetail],
)
def get_monthly_login_details(
    clicked_value: str,
    state_id: int | None = None,
    district_id: int | None = None,
    centre_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user, state_id, district_id, centre_id
    )
    return DashboardService.get_monthly_login_details(
        db=db,
        clicked_value=clicked_value,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get(
    "/centre-wise-trainees",
    response_model=list[CentreWiseTraineesItem],
)
def get_centre_wise_trainees(
    state_id: int | None = None,
    district_id: int | None = None,
    centre_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user,
        state_id,
        district_id,
        centre_id,
    )

    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="from_date cannot be later than to_date",
        )

    return DashboardService.get_centre_wise_trainees(
        db=db,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
        from_date=from_date,
        to_date=to_date,
    )


# state and center wise separate api for trainee details with pagination and search


@router.get(
    "/state-wise-trainees",
    response_model=list[StateWiseTraineesItem],
)
def get_state_wise_trainees(
    state_id: int | None = None,
    district_id: int | None = None,
    centre_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user,
        state_id,
        district_id,
        centre_id,
    )

    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="from_date cannot be later than to_date",
        )

    return DashboardService.get_state_wise_trainees(
        db=db,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get(
    "/need-attention",
    response_model=NeedAttentionSummaryResponse,
    summary="Get count of trainees requiring attention",
)
def get_need_attention_summary(
    state_id: int | None = Query(None),
    district_id: int | None = Query(None),
    centre_id: int | None = Query(None),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user, state_id, district_id, centre_id
    )

    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="from_date cannot be later than to_date",
        )

    return DashboardService.get_need_attention_summary(
        db=db,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get(
    "/need-attention/learners",
    response_model=NeedAttentionLearnersResponse,
    summary="Get paginated list of trainees requiring attention",
)
def get_need_attention_learners(
    type: str = Query(..., description="Filter type: 'never_logged_in' or 'inactive_30d'"),
    page: int = Query(1, ge=1, description="Page number (starting from 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Page size (1 to 100)"),
    state_id: int | None = Query(None),
    district_id: int | None = Query(None),
    centre_id: int | None = Query(None),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    search: str | None = Query(None, description="Search by name, enrollment no, or mobile"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if type not in ("never_logged_in", "inactive_30d"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid type '{type}'. Supported values are 'never_logged_in' and 'inactive_30d'.",
        )

    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user, state_id, district_id, centre_id
    )

    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="from_date cannot be later than to_date",
        )

    return DashboardService.get_need_attention_learners(
        db=db,
        learner_type=type,
        page=page,
        page_size=page_size,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
        from_date=from_date,
        to_date=to_date,
        search=search,
    )


@router.get(
    "/need-attention/export",
    summary="Export trainees requiring attention as CSV",
)
def export_need_attention_learners(
    type: str = Query(..., description="Filter type: 'never_logged_in' or 'inactive_30d'"),
    state_id: int | None = Query(None),
    district_id: int | None = Query(None),
    centre_id: int | None = Query(None),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if type not in ("never_logged_in", "inactive_30d"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid type '{type}'. Supported values are 'never_logged_in' and 'inactive_30d'.",
        )

    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user, state_id, district_id, centre_id
    )

    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="from_date cannot be later than to_date",
        )

    csv_data = DashboardService.export_need_attention_learners_csv(
        db=db,
        learner_type=type,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
        from_date=from_date,
        to_date=to_date,
    )

    filename = f"need_attention_{type}_{date.today().isoformat()}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get(
    "/recent-learners",
    response_model=RecentLearnersResponse,
    summary="Get recent active learners",
)
def get_recent_learners(
    limit: int = Query(5, ge=1, le=50, description="Limit between 1 and 50"),
    state_id: int | None = Query(None),
    district_id: int | None = Query(None),
    centre_id: int | None = Query(None),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user, state_id, district_id, centre_id
    )

    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="from_date cannot be later than to_date",
        )

    return DashboardService.get_recent_learners(
        db=db,
        limit=limit,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get(
    "/recent-learners/{participant_id}",
    response_model=LearnerDetailResponse,
    summary="Get learner activity and module completion details",
)
def get_learner_activity_detail(
    participant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return DashboardService.get_learner_activity_detail(
        db=db,
        participant_id=participant_id,
    )




@router.get(
    "/top-learners",
    response_model=TopLearnersResponse,
    summary="Get top learners ranked by combined assessment and learning time score",
)
def get_top_learners(
    limit: int = Query(10, ge=1, le=100),
    state_id: int | None = Query(None),
    district_id: int | None = Query(None),
    centre_id: int | None = Query(None),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user, state_id, district_id, centre_id
    )
    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="from_date cannot be later than to_date",
        )
    return DashboardService.get_top_learners(
        db=db,
        limit=limit,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
        from_date=from_date,
        to_date=to_date,
    )

@router.get(
    "/centre-leaderboard",
    response_model=CentreLeaderboardResponse,
    summary="Get top-performing centres ranking and performance",
)
def get_centre_leaderboard(
    limit: int | None = Query(None, ge=1, le=100, description="Optional limit"),
    state_id: int | None = Query(None),
    district_id: int | None = Query(None),
    centre_id: int | None = Query(None),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    state_id, district_id, centre_id = UserService.clamp_scope(
        current_user, state_id, district_id, centre_id
    )

    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="from_date cannot be later than to_date",
        )

    return DashboardService.get_centre_leaderboard(
        db=db,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
    )
