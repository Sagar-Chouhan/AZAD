from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# =========================================================
# DASHBOARD FILTERS
# =========================================================


class DashboardFilterRequest(BaseModel):
    state_id: Optional[int] = None
    district_id: Optional[int] = None
    centre_id: Optional[int] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None


# =========================================================
# DASHBOARD SUMMARY
# =========================================================


class DashboardSummaryResponse(BaseModel):
    total_centres: int
    total_participants: int
    active_participants: int
    total_courses: int
    total_modules: int
    total_batches: int
    total_documents: int
    total_assessments: int
    completion_rate: float


# =========================================================
# CHART SCHEMAS
# =========================================================


class StateWiseParticipant(BaseModel):
    state_id: int
    state_name: str
    total: int


class ChartItem(BaseModel):
    state_id: int
    state_name: str
    total: int


class GenderDistributionItem(BaseModel):
    gender: Optional[str] = None
    total: int


class MonthlyLoginTrendItem(BaseModel):
    month: str
    total: int


class AgeGroupDistributionItem(BaseModel):
    age_group: str
    total: int


class DocumentTypeDistributionItem(BaseModel):
    doc_type: str
    total: int


class DistrictWiseParticipantItem(BaseModel):
    district_name: str
    total: int


class ModuleLockStatusItem(BaseModel):
    lock_status: int
    total: int


class ModuleWisePerformanceItem(BaseModel):
    module_name: str
    total: int


class MonthlyTrendingModuleItem(BaseModel):
    month: str
    module_id: int
    module_name: str
    total: int


class ModuleAssignmentUsageItem(BaseModel):
    module_id: int
    module_name: str
    total_assigned: int


# =========================================================
# TRAINEE STATUS
# =========================================================


class TraineeStatusItem(BaseModel):
    status: str
    label: str
    total: int


class StateWiseTraineeStatusItem(BaseModel):
    state_name: str
    status: str
    label: str
    total: int


class TraineeStatusDetail(BaseModel):
    participant_id: Optional[int] = None
    participant_name: Optional[str] = None
    mobile_no: Optional[str] = None
    enrollment_no: Optional[str] = None
    image: Optional[str] = None
    age: Optional[int] = None
    state_name: Optional[str] = None
    district_name: Optional[str] = None
    centre_name: Optional[str] = None
    course_progress: Optional[float | int] = None
    performance_status: Optional[str] = None


# =========================================================
# DASHBOARD DETAILS
# =========================================================


class DashboardParticipantDetail(BaseModel):
    participant_id: int
    participant_name: str
    mobile_no: Optional[str] = None
    email: Optional[str] = None
    enrollment_no: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    state_name: Optional[str] = None
    district_name: Optional[str] = None


class DashboardCentreDetail(BaseModel):
    centre_name: str
    address: Optional[str] = None
    state_name: Optional[str] = None
    district_name: Optional[str] = None
    status: Optional[int] = None


class DashboardModuleDetail(BaseModel):
    module_name: str
    total: int


class DashboardDocumentDetail(BaseModel):
    doc_title: str
    doc_type: Optional[str] = None
    format: Optional[str] = None
    module_name: Optional[str] = None
    status: Optional[int] = None


class DashboardLoginDetail(BaseModel):
    participant_name: str
    mobile_no: Optional[str] = None
    login_time: datetime
    app_version: Optional[str] = None


# =========================================================
# NEED ATTENTION
# IMPORTANT: Define this BEFORE DashboardResponse
# =========================================================


class NeedAttentionSummaryData(BaseModel):
    never_logged_in: int
    inactive_30d: int


class NeedAttentionSummaryResponse(BaseModel):
    success: bool = True
    data: NeedAttentionSummaryData


class NeedAttentionLearnerItem(BaseModel):
    participant_id: int
    participant_name: str
    enrollment_no: Optional[str] = None
    image: Optional[str] = None
    centre_id: Optional[int] = None
    centre_name: Optional[str] = None
    state_id: Optional[int] = None
    state_name: Optional[str] = None
    district_id: Optional[int] = None
    district_name: Optional[str] = None
    registration_date: Optional[datetime] = None
    last_activity_time: Optional[datetime] = None
    days_inactive: Optional[int] = None


class PaginationMetadata(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class NeedAttentionLearnersResponse(BaseModel):
    success: bool = True
    data: list[NeedAttentionLearnerItem]
    pagination: PaginationMetadata


# =========================================================
# MAIN DASHBOARD RESPONSE
# =========================================================


class DashboardResponse(BaseModel):
    summary: DashboardSummaryResponse
    trainee_status: list[TraineeStatusItem] = Field(default_factory=list)
    state_wise_participants: list[StateWiseParticipant] = Field(default_factory=list)
    state_wise_centres: list[ChartItem] = Field(default_factory=list)
    gender_distribution: list[GenderDistributionItem] = Field(default_factory=list)
    monthly_login_trend: list[MonthlyLoginTrendItem] = Field(default_factory=list)
    document_type_distribution: list[DocumentTypeDistributionItem] = Field(
        default_factory=list
    )
    district_wise_participants: list[DistrictWiseParticipantItem] = Field(
        default_factory=list
    )
    age_group_distribution: list[AgeGroupDistributionItem] = Field(default_factory=list)
    module_lock_status: list[ModuleLockStatusItem] = Field(default_factory=list)
    module_wise_performance: list[ModuleWisePerformanceItem] = Field(
        default_factory=list
    )
    need_attention: Optional[NeedAttentionSummaryData] = None

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# CENTRE / STATE-WISE TRAINEES
# =========================================================


class CentreWiseTraineesItem(BaseModel):
    state_id: int
    state_name: str
    centre_id: int
    centre_name: str
    district_name: Optional[str] = None
    total_trainees: int


class StateWiseTraineesItem(BaseModel):
    state_id: int
    state_name: str
    total_trainees: int


# =========================================================
# RECENT LEARNERS
# =========================================================


class RecentLearnerItem(BaseModel):
    participant_id: int
    participant_name: str
    name: Optional[str] = None
    enrollment_no: Optional[str] = None
    centre_id: Optional[int] = None
    centre_name: Optional[str] = None
    state_id: Optional[int] = None
    state_name: Optional[str] = None
    district_id: Optional[int] = None
    district_name: Optional[str] = None
    latest_activity_time: Optional[datetime] = None
    session_duration_seconds: int = 0
    session_duration_minutes: float = 0.0
    completed_modules_count: int = 0
    total_modules_count: int = 0
    image: Optional[str] = None
    rank: Optional[int] = None
    total_score: Optional[int] = 0
    score: Optional[float] = 0.0
    obtained_marks: Optional[float] = 0.0
    total_marks: Optional[float] = 0.0
    assigned_modules: Optional[int] = 0
    assigned_modules_count: Optional[int] = 0
    completed_modules: Optional[int] = 0
    total_assigned_modules: Optional[int] = 0
    module_completion_percentage: Optional[float] = 0.0


class RecentLearnersResponse(BaseModel):
    success: bool = True
    data: list[RecentLearnerItem]


# =========================================================
# LEARNER ACTIVITY
# =========================================================


class LearnerRecentSession(BaseModel):
    topic_id: Optional[int] = None
    module_id: Optional[int] = None
    document_id: Optional[int] = None
    time_taken_seconds: int = 0
    created_at: Optional[datetime] = None


class LearnerActivityDetail(BaseModel):
    participant_id: int
    participant_name: str
    enrollment_no: Optional[str] = None
    centre_id: Optional[int] = None
    centre_name: Optional[str] = None
    state_id: Optional[int] = None
    state_name: Optional[str] = None
    district_id: Optional[int] = None
    district_name: Optional[str] = None
    total_logins: int = 0
    total_time_spent_seconds: int = 0
    total_time_spent_minutes: float = 0.0
    total_score: Optional[int] = 0
    total_questions: Optional[int] = 0
    assessment_percentage: Optional[float] = 0.0
    completed_modules_count: int = 0
    total_modules_count: int = 0
    course_progress: float = 0.0
    last_login: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    recent_sessions: list[LearnerRecentSession] = Field(default_factory=list)
    image: Optional[str] = None
    rank: Optional[int] = None
    score: Optional[float] = 0.0
    obtained_marks: Optional[float] = 0.0
    total_marks: Optional[float] = 0.0
    assigned_modules: Optional[int] = 0
    assigned_modules_count: Optional[int] = 0
    completed_modules: Optional[int] = 0
    total_assigned_modules: Optional[int] = 0
    module_completion_percentage: Optional[float] = 0.0


class LearnerDetailResponse(BaseModel):
    success: bool = True
    data: LearnerActivityDetail


# =========================================================
# CENTRE LEADERBOARD
# =========================================================


class CentreLeaderboardItem(BaseModel):
    rank: int
    centre_id: int
    centre_name: str
    state_id: Optional[int] = None
    state_name: Optional[str] = None
    district_id: Optional[str] = None
    district_name: Optional[str] = None
    total_trainees: int = 0
    active_trainees: int = 0
    completed_modules: int = 0
    assigned_modules: int = 0
    completion_rate_pct: float = 0.0
    total_time_spent_seconds: int = 0
    total_time_spent_minutes: float = 0.0
    total_score: Optional[int] = 0
    total_questions: Optional[int] = 0
    assessment_percentage: float = 0.0
    combined_score: float = 0.0
    good_performance_rate: Optional[float] = 0.0
    average_trainee_score: Optional[float] = 0.0
    evaluated_trainees: Optional[int] = 0
    good_trainees: Optional[int] = 0
    average_trainees: Optional[int] = 0
    poor_trainees: Optional[int] = 0
    yet_to_start_trainees: Optional[int] = 0
    performance_status: str = "Yet to Start"


class CentreLeaderboardResponse(BaseModel):
    success: bool = True
    data: list[CentreLeaderboardItem]


# =========================================================
# TOP LEARNERS
# =========================================================


class TopLearnerItem(BaseModel):
    rank: int
    participant_id: int
    participant_name: str
    name: Optional[str] = None
    image: Optional[str] = None
    enrollment_no: Optional[str] = None
    centre_id: Optional[int] = None
    centre_name: Optional[str] = None
    state_id: Optional[int] = None
    state_name: Optional[str] = None
    district_id: Optional[int] = None
    district_name: Optional[str] = None
    assessment_percentage: float = 0.0
    assessment_questions_attempted: int = 0
    assessment_questions_correct: int = 0
    learning_time_seconds: int = 0
    learning_time_minutes: float = 0.0
    normalized_learning_time_score: float = 0.0
    combined_score: float = 0.0
    score: Optional[float] = 0.0
    obtained_marks: Optional[float] = 0.0
    total_marks: Optional[float] = 0.0
    assigned_modules: Optional[int] = 0
    assigned_modules_count: Optional[int] = 0
    completed_modules: Optional[int] = 0
    completed_modules_count: Optional[int] = 0
    total_assigned_modules: Optional[int] = 0
    total_modules: Optional[int] = 0
    total_modules_count: Optional[int] = 0
    module_completion_percentage: Optional[float] = 0.0
    correct: Optional[int] = 0
    correct_questions: Optional[int] = 0
    assigned_questions: Optional[int] = 0
    total_questions: Optional[int] = 0
    completed_questions: Optional[int] = 0
    performance_score: Optional[float] = 0.0


class TopLearnersResponse(BaseModel):
    success: bool = True
    data: list[TopLearnerItem]
