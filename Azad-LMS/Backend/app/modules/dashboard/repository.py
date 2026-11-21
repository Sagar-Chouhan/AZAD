from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    Integer,
    Numeric,
    and_,
    case,
    distinct,
    exists,
    func,
    or_,
    text,
    union_all,
    select,
)
from sqlalchemy.orm import aliased, Session
from sqlalchemy.orm import Query

from app.modules.assessment.model import (
    AssessmentMaster,
    DropBucket,
    DropBucketItem,
    DropBucketMaster,
    MatchCorrectAnswer,
    MatchMakingMaster,
    McqMaster,
    PostSessionAssessment,
    ScqMaster,
)
from app.modules.batch.model import BatchMaster, BatchParticipant
from app.modules.course.model import CourseMaster
from app.modules.dashboard.Login_Log import LoginLog
from app.modules.dashboard.constants import (
    LEADERBOARD_ASSESSMENT_WEIGHT,
    LEADERBOARD_LEARNING_TIME_WEIGHT,
)
from app.modules.dashboard.model import ParticipantModule
from app.modules.document.model import DocumentCategory, DocumentMaster

# This import is causing a ModuleNotFoundError. Assuming app.modules.users.model exists.
from app.modules.centres.model import CentreMaster
from app.modules.master.district.model import DistrictMaster
from app.modules.master.state.model import StateMaster
from app.modules.module.model import ModuleMaster
from app.modules.users.model import (
    ParticipantDb,
    ParticipantMaster,
    ParticipantMcq,
    ParticipantMm,
    ParticipantScq,
    TimeSpentModuleLog,
)

if not hasattr(TimeSpentModuleLog, "created_at"):
    TimeSpentModuleLog.created_at = Column("created_at", DateTime)


class DashboardRepository:

    @staticmethod
    def get_total_centres(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
    ):
        query = db.query(func.count(CentreMaster.centre_id)).filter(
            CentreMaster.deleted_at.is_(None)
        )

        if state_id:
            query = query.filter(CentreMaster.state_id == state_id)

        if district_id:
            query = query.filter(
                CentreMaster.district_code == select(DistrictMaster.district_code)
                .where(DistrictMaster.district_lgd_code == district_id)
                .scalar_subquery()
            )

        if centre_id:
            query = query.filter(CentreMaster.centre_id == centre_id)

        return query.scalar() or 0

    @staticmethod
    def _apply_date_filter(
        query: Query,
        model,
        from_date=None,
        to_date=None,
    ):
        if from_date:
            query = query.filter(model.created_at >= from_date)

        if to_date:
            query = query.filter(model.created_at <= to_date)

        return query

    @staticmethod
    def _apply_centre_filter(
        query: Query,
        centre_id=None,
    ):
        if centre_id:
            query = (
                query.join(
                    BatchParticipant,
                    BatchParticipant.participant_id == ParticipantMaster.participant_id,
                )
                .join(
                    BatchMaster,
                    BatchMaster.batch_id == BatchParticipant.batch_id,
                )
                .filter(
                    BatchMaster.deleted_at.is_(None),
                    BatchParticipant.deleted_at.is_(None),
                    BatchMaster.centre_id == centre_id,
                )
            )

        return query

    @staticmethod
    def get_total_participants(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ):

        query = db.query(func.count(ParticipantMaster.participant_id)).filter(
            ParticipantMaster.deleted_at.is_(None)
        )

        if state_id:
            query = query.filter(ParticipantMaster.state_id == state_id)

        if district_id:
            query = query.filter(ParticipantMaster.district_id == district_id)

        query = DashboardRepository._apply_centre_filter(
            query,
            centre_id,
        )

        query = DashboardRepository._apply_date_filter(
            query,
            ParticipantMaster,
            from_date,
            to_date,
        )

        return query.scalar() or 0

    @staticmethod
    def get_active_participants(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ):
        last_act = DashboardRepository._build_last_activity_subquery(db)

        query = (
            db.query(func.count(distinct(ParticipantMaster.participant_id)))
            .join(
                last_act,
                last_act.c.participant_id == ParticipantMaster.participant_id,
            )
            .filter(
                ParticipantMaster.deleted_at.is_(None),
                ParticipantMaster.status == "1",
            )
        )

        if state_id:
            query = query.filter(ParticipantMaster.state_id == state_id)

        if district_id:
            query = query.filter(ParticipantMaster.district_id == district_id)

        query = DashboardRepository._apply_centre_filter(
            query,
            centre_id,
        )

        query = DashboardRepository._apply_date_filter(
            query,
            ParticipantMaster,
            from_date,
            to_date,
        )

        return query.scalar() or 0

    @staticmethod
    def get_total_courses(db: Session):
        return (
            db.query(func.count(CourseMaster.course_id))
            .filter(
                CourseMaster.deleted_at.is_(None),
                CourseMaster.parent_id == CourseMaster.course_id,
            )
            .scalar()
            or 0
        )

    @staticmethod
    def get_total_modules(db: Session):
        return (
            db.query(func.count(ModuleMaster.module_id))
            .filter(
                ModuleMaster.deleted_at.is_(None),
                ModuleMaster.parent_id == ModuleMaster.module_id,
            )
            .scalar()
            or 0
        )

    @staticmethod
    def get_total_batches(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
    ):

        query = (
            db.query(func.count(BatchMaster.batch_id))
            .join(
                CentreMaster,
                BatchMaster.centre_id == CentreMaster.centre_id,
            )
            .filter(
                BatchMaster.deleted_at.is_(None),
                CentreMaster.deleted_at.is_(None),
            )
        )

        if state_id:
            query = query.filter(CentreMaster.state_id == state_id)

        if district_id:
            query = query.filter(
                CentreMaster.district_code == select(DistrictMaster.district_code)
                .where(DistrictMaster.district_lgd_code == district_id)
                .scalar_subquery()
            )

        if centre_id:
            query = query.filter(CentreMaster.centre_id == centre_id)

        return query.scalar() or 0

    @staticmethod
    def get_total_documents(db: Session):
        return (
            db.query(func.count(DocumentMaster.doc_id))
            .filter(
                DocumentMaster.parent_id == DocumentMaster.doc_id,
                DocumentMaster.deleted_at.is_(None),
            )
            .scalar()
            or 0
        )

    @staticmethod
    def get_total_assessments(db: Session):
        return (
            db.query(func.count(AssessmentMaster.assessment_id))
            .filter(AssessmentMaster.parent_id == AssessmentMaster.assessment_id)
            .scalar()
            or 0
        )

    @staticmethod
    def get_completion_rate(db: Session):
        total_assigned = (
            db.query(func.count(ParticipantModule.participant_module_id)).scalar() or 0
        )

        total_completed = (
            db.query(func.count(ParticipantModule.participant_module_id))
            .filter(ParticipantModule.status == "1")
            .scalar()
            or 0
        )

        if total_assigned == 0:
            return 0

        return round((total_completed / total_assigned) * 100)

    @staticmethod
    def get_state_wise_participants(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ):
        p_centre = DashboardRepository._build_distinct_participant_centre_subquery(db)
        state_col = func.coalesce(ParticipantMaster.state_id, CentreMaster.state_id)
        query = (
            db.query(
                StateMaster.state_lgd_code.label("state_id"),
                StateMaster.state_name,
                func.count(distinct(ParticipantMaster.participant_id)).label("total"),
            )
            .select_from(ParticipantMaster)
            .outerjoin(
                p_centre,
                p_centre.c.participant_id == ParticipantMaster.participant_id,
            )
            .outerjoin(
                CentreMaster,
                and_(
                    CentreMaster.centre_id == p_centre.c.centre_id,
                    CentreMaster.deleted_at.is_(None),
                ),
            )
            .join(
                StateMaster,
                StateMaster.state_lgd_code == state_col,
            )
            .outerjoin(
                DistrictMaster,
                DistrictMaster.district_code == CentreMaster.district_code,
            )
            .filter(ParticipantMaster.deleted_at.is_(None))
        )
        if state_id:
            query = query.filter(state_col == state_id)

        if district_id:
            query = query.filter(
                CentreMaster.district_code == select(DistrictMaster.district_code)
                .where(DistrictMaster.district_lgd_code == district_id)
                .scalar_subquery()
            )

        if centre_id:
            query = query.filter(CentreMaster.centre_id == centre_id)

        query = DashboardRepository._apply_date_filter(
            query,
            ParticipantMaster,
            from_date,
            to_date,
        )

        query = query.group_by(
            StateMaster.state_lgd_code,
            StateMaster.state_name,
        )

        query = query.order_by(
            func.count(distinct(ParticipantMaster.participant_id)).desc()
        )

        return query.all()

    @staticmethod
    def get_state_wise_centres(
        db: Session,
    ):
        query = (
            db.query(
                StateMaster.state_lgd_code.label("state_id"),
                StateMaster.state_name,
                func.count(CentreMaster.centre_id).label("total"),
            )
            .select_from(CentreMaster)
            .join(
                StateMaster,
                StateMaster.state_lgd_code == CentreMaster.state_id,
            )
            .filter(
                CentreMaster.deleted_at.is_(None),
            )
            .group_by(
                StateMaster.state_lgd_code,
                StateMaster.state_name,
            )
            .order_by(func.count(CentreMaster.centre_id).desc())
        )

        return query.all()

    @staticmethod
    def get_gender_distribution(
        db: Session,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        query = db.query(
            ParticipantMaster.gender,
            func.count(ParticipantMaster.participant_id).label("total"),
        ).filter(
            ParticipantMaster.deleted_at.is_(None),
        )

        if state_id:
            query = query.filter(ParticipantMaster.state_id == state_id)

        if district_id:
            query = query.filter(ParticipantMaster.district_id == district_id)

        query = DashboardRepository._apply_centre_filter(
            query,
            centre_id,
        )

        query = DashboardRepository._apply_date_filter(
            query=query,
            model=ParticipantMaster,
            from_date=from_date,
            to_date=to_date,
        )

        return query.group_by(ParticipantMaster.gender).all()

    @staticmethod
    def get_monthly_login_trend(
        db: Session,
        state_id: int | None = None,
        clicked_value=None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date=None,
        to_date=None,
    ):
        query = (
            db.query(
                func.to_char(LoginLog.login_time, "YYYY-MM").label("month"),
                func.count().label("total"),
            )
            .join(
                ParticipantMaster,
                ParticipantMaster.participant_id == LoginLog.user_id,
            )
            .filter(
                ParticipantMaster.deleted_at.is_(None),
                LoginLog.login_time >= func.now() - text("INTERVAL '12 months'"),
            )
        )

        if clicked_value:
            query = query.filter(
                func.to_char(LoginLog.login_time, "Mon YYYY") == clicked_value
            )

        if state_id:
            query = query.filter(ParticipantMaster.state_id == state_id)

        if district_id:
            query = query.filter(ParticipantMaster.district_id == district_id)

        query = DashboardRepository._apply_centre_filter(
            query,
            centre_id,
        )

        query = DashboardRepository._apply_date_filter(
            query,
            ParticipantMaster,
            from_date,
            to_date,
        )

        return (
            query.group_by(func.to_char(LoginLog.login_time, "YYYY-MM"))
            .order_by(func.to_char(LoginLog.login_time, "YYYY-MM"))
            .all()
        )

    @staticmethod
    def get_age_group_distribution(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ):
        age_group = case(
            (ParticipantMaster.age.between(18, 25), "18-25"),
            (ParticipantMaster.age.between(26, 35), "26-35"),
            (ParticipantMaster.age.between(36, 45), "36-45"),
            (ParticipantMaster.age.between(46, 55), "46-55"),
            (ParticipantMaster.age > 55, "55+"),
            else_="Under 18",
        ).label("age_group")

        query = db.query(
            age_group,
            func.count(ParticipantMaster.participant_id).label("total"),
        ).filter(
            ParticipantMaster.deleted_at.is_(None),
            ParticipantMaster.age.is_not(None),
            ParticipantMaster.age > 0,
        )

        if state_id:
            query = query.filter(ParticipantMaster.state_id == state_id)

        if district_id:
            query = query.filter(ParticipantMaster.district_id == district_id)

        query = DashboardRepository._apply_centre_filter(
            query,
            centre_id,
        )

        query = DashboardRepository._apply_date_filter(
            query,
            ParticipantMaster,
            from_date,
            to_date,
        )

        query = query.group_by(age_group)

        return query.all()

    @staticmethod
    def get_document_type_distribution(db: Session):
        return (
            db.query(
                DocumentCategory.doc_category_name.label("doc_type"),
                func.count(DocumentMaster.doc_id).label("total"),
            )
            .select_from(DocumentMaster)
            .join(
                DocumentCategory,
                DocumentCategory.doc_category_id == DocumentMaster.doc_category_id,
            )
            .filter(
                DocumentMaster.parent_id == DocumentMaster.doc_id,
                DocumentMaster.doc_category_id.is_not(None),
            )
            .group_by(DocumentCategory.doc_category_name)
            .order_by(func.count(DocumentMaster.doc_id).desc())
            .all()
        )

    @staticmethod
    def get_district_wise_participants(
        db: Session,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        query = (
            db.query(
                DistrictMaster.district_name,
                func.count(ParticipantMaster.participant_id).label("total"),
            )
            .select_from(ParticipantMaster)
            .join(
                DistrictMaster,
                DistrictMaster.district_lgd_code == ParticipantMaster.district_id,
            )
            .filter(
                ParticipantMaster.deleted_at.is_(None),
            )
        )

        if state_id:
            query = query.filter(ParticipantMaster.state_id == state_id)

        if district_id:
            query = query.filter(ParticipantMaster.district_id == district_id)

        query = DashboardRepository._apply_centre_filter(
            query,
            centre_id,
        )

        query = DashboardRepository._apply_date_filter(
            query,
            ParticipantMaster,
            from_date,
            to_date,
        )

        return (
            query.group_by(
                DistrictMaster.district_name,
            )
            .order_by(
                func.count(ParticipantMaster.participant_id).desc(),
            )
            .limit(10)
            .all()
        )

    @staticmethod
    def get_module_lock_status(
        db: Session,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        query = db.query(
            ParticipantModule.lock_status.label("lock_status"),
            func.count().label("total"),
        ).select_from(ParticipantModule)

        if state_id or district_id or centre_id or from_date or to_date:
            query = query.join(
                ParticipantMaster,
                ParticipantMaster.participant_id == ParticipantModule.participant_id,
            ).filter(ParticipantMaster.deleted_at.is_(None))

            if state_id:
                query = query.filter(ParticipantMaster.state_id == state_id)

            if district_id:
                query = query.filter(ParticipantMaster.district_id == district_id)

            query = DashboardRepository._apply_centre_filter(
                query,
                centre_id,
            )

            query = DashboardRepository._apply_date_filter(
                query,
                ParticipantMaster,
                from_date,
                to_date,
            )

        return query.group_by(
            ParticipantModule.lock_status,
        ).all()

    @staticmethod
    def get_module_wise_performance_details(
        db: Session,
        clicked_value=None,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ):
        ChildModule = aliased(ModuleMaster)
        ParentModule = aliased(ModuleMaster)

        query = (
            db.query(
                ParentModule.module_name.label("module_name"),
                func.count(distinct(ParticipantModule.participant_id)).label("total"),
            )
            .select_from(ParticipantModule)
            .join(
                ChildModule,
                ChildModule.module_id == ParticipantModule.module_id,
            )
            .join(
                ParentModule,
                and_(
                    ParentModule.module_id == ChildModule.parent_id,
                    ParentModule.parent_id == ParentModule.module_id,
                    ParentModule.deleted_at.is_(None),
                ),
            )
        )

        # ---------------------------------------------------
        # Module must have an active post-session assessment
        # ---------------------------------------------------
        query = query.filter(
            exists().where(
                and_(
                    PostSessionAssessment.module_id == ParticipantModule.module_id,
                    PostSessionAssessment.is_active == 1,
                    PostSessionAssessment.deleted_at.is_(None),
                )
            )
        )

        # ---------------------------------------------------
        # Participant must have attempted the assessment
        # ---------------------------------------------------
        query = query.filter(
            or_(
                exists().where(
                    and_(
                        ParticipantMcq.participant_id
                        == ParticipantModule.participant_id,
                        ParticipantMcq.module_id == ParticipantModule.module_id,
                    )
                ),
                exists().where(
                    and_(
                        ParticipantScq.participant_id
                        == ParticipantModule.participant_id,
                        ParticipantScq.module_id == ParticipantModule.module_id,
                    )
                ),
                exists().where(
                    and_(
                        ParticipantDb.participant_id
                        == ParticipantModule.participant_id,
                        ParticipantDb.module_id == ParticipantModule.module_id,
                    )
                ),
                exists().where(
                    and_(
                        ParticipantMm.participant_id
                        == ParticipantModule.participant_id,
                        ParticipantMm.module_id == ParticipantModule.module_id,
                    )
                ),
            )
        )

        if state_id or district_id or centre_id or from_date or to_date:

            query = query.join(
                ParticipantMaster,
                ParticipantMaster.participant_id == ParticipantModule.participant_id,
            ).filter(ParticipantMaster.deleted_at.is_(None))

        if state_id:
            query = query.filter(ParticipantMaster.state_id == state_id)

        if district_id:
            query = query.filter(ParticipantMaster.district_id == district_id)

        query = DashboardRepository._apply_centre_filter(
            query,
            centre_id,
        )

        query = DashboardRepository._apply_date_filter(
            query,
            ParticipantMaster,
            from_date,
            to_date,
        )

        query = (
            query.group_by(
                ParentModule.module_id,
                ParentModule.module_name,
            )
            .order_by(func.count(distinct(ParticipantModule.participant_id)).desc())
            .limit(10)
        )

        return query.all()

    @staticmethod
    def get_monthly_trending_modules(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ):
        module_activity = union_all(
            db.query(
                ParticipantMcq.participant_id.label("participant_id"),
                ParticipantMcq.module_id.label("module_id"),
                ParticipantMcq.created_date.label("activity_date"),
            ).filter(ParticipantMcq.created_date.isnot(None)),
            db.query(
                ParticipantScq.participant_id.label("participant_id"),
                ParticipantScq.module_id.label("module_id"),
                ParticipantScq.created_date.label("activity_date"),
            ).filter(ParticipantScq.created_date.isnot(None)),
            db.query(
                ParticipantDb.participant_id.label("participant_id"),
                ParticipantDb.module_id.label("module_id"),
                ParticipantDb.created_date.label("activity_date"),
            ).filter(ParticipantDb.created_date.isnot(None)),
            db.query(
                ParticipantMm.participant_id.label("participant_id"),
                ParticipantMm.module_id.label("module_id"),
                ParticipantMm.created_date.label("activity_date"),
            ).filter(ParticipantMm.created_date.isnot(None)),
        ).subquery("module_activity")

        child_module = aliased(ModuleMaster)
        parent_module = aliased(ModuleMaster)

        query = (
            db.query(
                func.to_char(module_activity.c.activity_date, "YYYY-MM").label("month"),
                parent_module.module_id.label("module_id"),
                parent_module.module_name.label("module_name"),
                func.count(distinct(module_activity.c.participant_id)).label("total"),
            )
            .select_from(module_activity)
            .join(
                child_module,
                child_module.module_id == module_activity.c.module_id,
            )
            .join(
                parent_module,
                and_(
                    parent_module.module_id == child_module.parent_id,
                    parent_module.parent_id == parent_module.module_id,
                    parent_module.deleted_at.is_(None),
                ),
            )
            .join(
                ParticipantMaster,
                ParticipantMaster.participant_id == module_activity.c.participant_id,
            )
            .filter(
                ParticipantMaster.deleted_at.is_(None),
            )
        )

        if state_id:
            query = query.filter(ParticipantMaster.state_id == state_id)

        if district_id:
            query = query.filter(ParticipantMaster.district_id == district_id)

        query = DashboardRepository._apply_centre_filter(query, centre_id)

        if from_date:
            query = query.filter(module_activity.c.activity_date >= from_date)

        if to_date:
            query = query.filter(module_activity.c.activity_date <= to_date)

        return (
            query.group_by(
                func.to_char(module_activity.c.activity_date, "YYYY-MM"),
                parent_module.module_id,
                parent_module.module_name,
            )
            .order_by(
                func.to_char(module_activity.c.activity_date, "YYYY-MM").desc(),
                func.count(distinct(module_activity.c.participant_id)).desc(),
                parent_module.module_name,
            )
            .all()
        )

    @staticmethod
    def get_module_assignment_usage(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
    ):
        child_module = aliased(ModuleMaster)
        parent_module = aliased(ModuleMaster)

        query = (
            db.query(
                parent_module.module_id.label("module_id"),
                parent_module.module_name.label("module_name"),
                func.count(distinct(ParticipantModule.participant_id)).label(
                    "total_assigned"
                ),
            )
            .select_from(ParticipantModule)
            .join(
                child_module,
                child_module.module_id == ParticipantModule.module_id,
            )
            .join(
                parent_module,
                and_(
                    parent_module.module_id == child_module.parent_id,
                    parent_module.parent_id == parent_module.module_id,
                    parent_module.deleted_at.is_(None),
                ),
            )
            .join(
                ParticipantMaster,
                ParticipantMaster.participant_id == ParticipantModule.participant_id,
            )
            .filter(ParticipantMaster.deleted_at.is_(None))
        )

        if state_id:
            query = query.filter(ParticipantMaster.state_id == state_id)

        if district_id:
            query = query.filter(ParticipantMaster.district_id == district_id)

        query = DashboardRepository._apply_centre_filter(query, centre_id)

        return (
            query.group_by(parent_module.module_id, parent_module.module_name)
            .order_by(
                func.count(distinct(ParticipantModule.participant_id)).desc(),
                parent_module.module_name,
            )
            .all()
        )

    @staticmethod
    def get_state_wise_participant_details(
        db: Session,
        clicked_value: int | None = None,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        query = (
            db.query(
                ParticipantMaster.participant_id,
                ParticipantMaster.participant_name,
                ParticipantMaster.mobile_no,
                ParticipantMaster.email,
                ParticipantMaster.enrollment_no,
                ParticipantMaster.gender,
                ParticipantMaster.age,
                StateMaster.state_name,
                DistrictMaster.district_name,
            )
            .outerjoin(
                StateMaster,
                StateMaster.state_lgd_code == ParticipantMaster.state_id,
            )
            .outerjoin(
                DistrictMaster,
                DistrictMaster.district_lgd_code == ParticipantMaster.district_id,
            )
            .filter(ParticipantMaster.deleted_at.is_(None))
        )

        if state_id:
            query = query.filter(ParticipantMaster.state_id == state_id)

        if district_id:
            query = query.filter(ParticipantMaster.district_id == district_id)

        query = DashboardRepository._apply_centre_filter(
            query,
            centre_id,
        )

        query = DashboardRepository._apply_date_filter(
            query,
            ParticipantMaster,
            from_date,
            to_date,
        )

        if clicked_value:
            query = query.filter(ParticipantMaster.state_id == clicked_value)

        return query.order_by(ParticipantMaster.participant_name).all()

    @staticmethod
    def get_district_wise_participant_details(
        db: Session,
        clicked_value: str | None = None,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        query = (
            db.query(
                ParticipantMaster.participant_id,
                ParticipantMaster.participant_name,
                ParticipantMaster.mobile_no,
                ParticipantMaster.email,
                ParticipantMaster.enrollment_no,
                ParticipantMaster.gender,
                ParticipantMaster.age,
                StateMaster.state_name,
                DistrictMaster.district_name,
            )
            .outerjoin(
                StateMaster,
                StateMaster.state_lgd_code == ParticipantMaster.state_id,
            )
            .outerjoin(
                DistrictMaster,
                DistrictMaster.district_lgd_code == ParticipantMaster.district_id,
            )
            .filter(ParticipantMaster.deleted_at.is_(None))
        )

        if state_id:
            query = query.filter(ParticipantMaster.state_id == state_id)

        if district_id:
            query = query.filter(ParticipantMaster.district_id == district_id)

        query = DashboardRepository._apply_centre_filter(query, centre_id)

        query = DashboardRepository._apply_date_filter(
            query,
            ParticipantMaster,
            from_date,
            to_date,
        )

        if clicked_value:
            query = query.filter(DistrictMaster.district_name == clicked_value)

        return query.order_by(ParticipantMaster.participant_name).all()

    @staticmethod
    def get_gender_distribution_details(
        db: Session,
        clicked_value: str | None = None,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        query = (
            db.query(
                ParticipantMaster.participant_id,
                ParticipantMaster.participant_name,
                ParticipantMaster.mobile_no,
                ParticipantMaster.email,
                ParticipantMaster.enrollment_no,
                ParticipantMaster.gender,
                ParticipantMaster.age,
                StateMaster.state_name,
                DistrictMaster.district_name,
            )
            .outerjoin(
                StateMaster,
                StateMaster.state_lgd_code == ParticipantMaster.state_id,
            )
            .outerjoin(
                DistrictMaster,
                DistrictMaster.district_lgd_code == ParticipantMaster.district_id,
            )
            .filter(ParticipantMaster.deleted_at.is_(None))
        )

        if state_id:
            query = query.filter(ParticipantMaster.state_id == state_id)

        if district_id:
            query = query.filter(ParticipantMaster.district_id == district_id)

        query = DashboardRepository._apply_centre_filter(query, centre_id)

        query = DashboardRepository._apply_date_filter(
            query,
            ParticipantMaster,
            from_date,
            to_date,
        )

        if clicked_value:
            query = query.filter(ParticipantMaster.gender == clicked_value)

        return query.order_by(ParticipantMaster.participant_name).all()

    @staticmethod
    def get_age_group_distribution_details(
        db: Session,
        clicked_value: str | None = None,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        query = (
            db.query(
                ParticipantMaster.participant_id,
                ParticipantMaster.participant_name,
                ParticipantMaster.mobile_no,
                ParticipantMaster.email,
                ParticipantMaster.enrollment_no,
                ParticipantMaster.gender,
                ParticipantMaster.age,
                StateMaster.state_name,
                DistrictMaster.district_name,
            )
            .outerjoin(
                StateMaster,
                StateMaster.state_lgd_code == ParticipantMaster.state_id,
            )
            .outerjoin(
                DistrictMaster,
                DistrictMaster.district_lgd_code == ParticipantMaster.district_id,
            )
            .filter(
                ParticipantMaster.deleted_at.is_(None),
                ParticipantMaster.age.is_not(None),
                ParticipantMaster.age > 0,
            )
        )

        if state_id:
            query = query.filter(ParticipantMaster.state_id == state_id)

        if district_id:
            query = query.filter(ParticipantMaster.district_id == district_id)

        query = DashboardRepository._apply_centre_filter(query, centre_id)

        query = DashboardRepository._apply_date_filter(
            query,
            ParticipantMaster,
            from_date,
            to_date,
        )

        if clicked_value == "Under 18":
            query = query.filter(ParticipantMaster.age.between(0, 17))
        elif clicked_value == "18-25":
            query = query.filter(ParticipantMaster.age.between(18, 25))
        elif clicked_value == "26-35":
            query = query.filter(ParticipantMaster.age.between(26, 35))
        elif clicked_value == "36-45":
            query = query.filter(ParticipantMaster.age.between(36, 45))
        elif clicked_value == "46-55":
            query = query.filter(ParticipantMaster.age.between(46, 55))
        elif clicked_value == "55+":
            query = query.filter(ParticipantMaster.age >= 56)

        return query.order_by(ParticipantMaster.participant_name).all()

    @staticmethod
    def get_state_wise_centre_details(
        db: Session,
        clicked_value: str | None = None,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        query = (
            db.query(
                CentreMaster.centre_name,
                CentreMaster.address,
                StateMaster.state_name,
                DistrictMaster.district_name,
                CentreMaster.status,
            )
            .outerjoin(
                StateMaster,
                StateMaster.state_lgd_code == CentreMaster.state_id,
            )
            .outerjoin(
                DistrictMaster,
                DistrictMaster.district_code == CentreMaster.district_code,
            )
            .filter(CentreMaster.deleted_at.is_(None))
        )

        if state_id:
            query = query.filter(CentreMaster.state_id == state_id)

        if district_id:
            query = query.filter(
                CentreMaster.district_code == select(DistrictMaster.district_code)
                .where(DistrictMaster.district_lgd_code == district_id)
                .scalar_subquery()
            )

        if centre_id:
            query = query.filter(CentreMaster.centre_id == centre_id)

        if clicked_value:
            query = query.filter(StateMaster.state_name == clicked_value)

        # Apply date filter only if CentreMaster has a created_at column
        if from_date or to_date:
            query = DashboardRepository._apply_date_filter(
                query,
                CentreMaster,
                from_date,
                to_date,
            )

        return query.order_by(CentreMaster.centre_name).all()

    @staticmethod
    def get_document_type_distribution_details(
        db: Session,
    ):
        return (
            db.query(
                DocumentMaster.doc_title,
                DocumentCategory.doc_category_name.label("doc_type"),
                DocumentMaster.doc_type.label("format"),
                ModuleMaster.module_name,
                DocumentMaster.status,
            )
            .select_from(DocumentMaster)
            .outerjoin(
                DocumentCategory,
                DocumentCategory.doc_category_id == DocumentMaster.doc_category_id,
            )
            .outerjoin(
                ModuleMaster,
                ModuleMaster.module_id == DocumentMaster.module_id,
            )
            .filter(
                DocumentMaster.parent_id == DocumentMaster.doc_id,
            )
            .order_by(
                DocumentCategory.doc_category_name,
                DocumentMaster.doc_title,
            )
            .all()
        )

    @staticmethod
    def get_monthly_login_details(
        db: Session,
        clicked_value: str | None = None,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        query = (
            db.query(
                ParticipantMaster.participant_name,
                ParticipantMaster.mobile_no,
                LoginLog.login_time,
                LoginLog.app_version,
            )
            .select_from(LoginLog)
            .join(
                ParticipantMaster,
                ParticipantMaster.participant_id == LoginLog.user_id,
            )
            .filter(
                ParticipantMaster.deleted_at.is_(None),
            )
        )

        if state_id:
            query = query.filter(ParticipantMaster.state_id == state_id)

        if district_id:
            query = query.filter(ParticipantMaster.district_id == district_id)

        query = DashboardRepository._apply_centre_filter(
            query,
            centre_id,
        )

        query = DashboardRepository._apply_date_filter(
            query,
            ParticipantMaster,
            from_date,
            to_date,
        )

        if clicked_value:
            query = query.filter(
                func.to_char(LoginLog.login_time, "YYYY-MM") == clicked_value
            )

        return query.order_by(LoginLog.login_time.desc()).all()

    # app/modules/dashboard/repository.py

    @staticmethod
    def get_centre_wise_trainees(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ):
        p_centre = DashboardRepository._build_distinct_participant_centre_subquery(db)
        state_col = func.coalesce(ParticipantMaster.state_id, CentreMaster.state_id)
        query = (
            db.query(
                StateMaster.state_lgd_code.label("state_id"),
                StateMaster.state_name,
                func.coalesce(CentreMaster.centre_id, 0).label("centre_id"),
                func.coalesce(CentreMaster.centre_name, "Unassigned").label("centre_name"),
                DistrictMaster.district_name,
                func.count(distinct(ParticipantMaster.participant_id)).label(
                    "total_trainees"
                ),
            )
            .select_from(ParticipantMaster)
            .outerjoin(
                p_centre,
                p_centre.c.participant_id == ParticipantMaster.participant_id,
            )
            .outerjoin(
                CentreMaster,
                and_(
                    CentreMaster.centre_id == p_centre.c.centre_id,
                    CentreMaster.deleted_at.is_(None),
                ),
            )
            .join(
                StateMaster,
                StateMaster.state_lgd_code == state_col,
            )
            .outerjoin(
                DistrictMaster,
                DistrictMaster.district_code == CentreMaster.district_code,
            )
            .filter(ParticipantMaster.deleted_at.is_(None))
        )

        if state_id is not None:
            query = query.filter(state_col == state_id)

        if district_id is not None:
            query = query.filter(DistrictMaster.district_lgd_code == district_id)

        if centre_id is not None:
            query = query.filter(CentreMaster.centre_id == centre_id)

        query = DashboardRepository._apply_date_filter(
            query,
            ParticipantMaster,
            from_date,
            to_date,
        )

        return (
            query.group_by(
                StateMaster.state_lgd_code,
                StateMaster.state_name,
                CentreMaster.centre_id,
                CentreMaster.centre_name,
                DistrictMaster.district_name,
            )
            .order_by(func.count(distinct(ParticipantMaster.participant_id)).desc())
            .all()
        )

    @staticmethod
    def get_state_wise_trainees(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ):
        p_centre = DashboardRepository._build_distinct_participant_centre_subquery(db)
        state_col = func.coalesce(ParticipantMaster.state_id, CentreMaster.state_id)
        query = (
            db.query(
                StateMaster.state_lgd_code.label("state_id"),
                StateMaster.state_name,
                func.count(distinct(ParticipantMaster.participant_id)).label(
                    "total_trainees"
                ),
            )
            .select_from(ParticipantMaster)
            .outerjoin(
                p_centre,
                p_centre.c.participant_id == ParticipantMaster.participant_id,
            )
            .outerjoin(
                CentreMaster,
                and_(
                    CentreMaster.centre_id == p_centre.c.centre_id,
                    CentreMaster.deleted_at.is_(None),
                ),
            )
            .join(
                StateMaster,
                StateMaster.state_lgd_code == state_col,
            )
            .outerjoin(
                DistrictMaster,
                DistrictMaster.district_code == CentreMaster.district_code,
            )
            .filter(ParticipantMaster.deleted_at.is_(None))
        )

        if state_id is not None:
            query = query.filter(state_col == state_id)

        if district_id is not None:
            query = query.filter(DistrictMaster.district_lgd_code == district_id)

        if centre_id is not None:
            query = query.filter(CentreMaster.centre_id == centre_id)

        query = DashboardRepository._apply_date_filter(
            query,
            ParticipantMaster,
            from_date,
            to_date,
        )

        return (
            query.group_by(
                StateMaster.state_lgd_code,
                StateMaster.state_name,
            )
            .order_by(func.count(distinct(ParticipantMaster.participant_id)).desc())
            .all()
        )

    @staticmethod
    def _build_last_activity_subquery(db: Session):
        login_sub = (
            db.query(
                LoginLog.user_id.label("user_id"),
                func.max(LoginLog.login_time).label("last_ts"),
            )
            .group_by(LoginLog.user_id)
            .subquery()
        )
        time_sub = (
            db.query(
                TimeSpentModuleLog.user_id.label("user_id"),
                func.max(TimeSpentModuleLog.created_at).label("last_ts"),
            )
            .group_by(TimeSpentModuleLog.user_id)
            .subquery()
        )
        union_act = union_all(
            db.query(
                login_sub.c.user_id.label("user_id"),
                login_sub.c.last_ts.label("last_ts"),
            ),
            db.query(
                time_sub.c.user_id.label("user_id"), time_sub.c.last_ts.label("last_ts")
            ),
        ).subquery()
        return (
            db.query(
                union_act.c.user_id.label("participant_id"),
                func.max(union_act.c.last_ts).label("latest_activity"),
            )
            .group_by(union_act.c.user_id)
            .subquery()
        )

    @staticmethod
    def _build_distinct_participant_centre_subquery(db: Session):
        return (
            db.query(
                BatchParticipant.participant_id.label("participant_id"),
                func.coalesce(
                    func.min(
                        case(
                            (
                                BatchMaster.deleted_at.is_(None),
                                BatchMaster.centre_id,
                            )
                        )
                    ),
                    func.min(BatchMaster.centre_id),
                ).label("centre_id"),
            )
            .join(
                BatchMaster,
                BatchMaster.batch_id == BatchParticipant.batch_id,
            )
            .filter(BatchParticipant.deleted_at.is_(None))
            .group_by(BatchParticipant.participant_id)
            .subquery()
        )

    @staticmethod
    def _build_participant_score_subquery(db: Session):
        score_sql = text(
            """
            SELECT p_id as participant_id, sum(score)::int as total_score
            FROM (
                SELECT pm.participant_id as p_id, count(*)::int as score
                FROM participant_mcqs pm
                JOIN mcq_question_options mo 
                  ON mo.mcq_option_id = CAST(NULLIF(regexp_replace(pm.option_selected, '[^0-9]', '', 'g'), '') AS BIGINT)
                WHERE mo.is_mcq_option_correct = 1
                GROUP BY pm.participant_id
                
                UNION ALL
                
                SELECT ps.participant_id as p_id, count(*)::int as score
                FROM participant_scs ps
                JOIN scq_question_options so 
                  ON so.scq_option_id = CAST(NULLIF(regexp_replace(ps.option_selected, '[^0-9]', '', 'g'), '') AS BIGINT)
                WHERE so.is_scq_option_correct = 1
                GROUP BY ps.participant_id
                
                UNION ALL
                
                SELECT pmm.participant_id as p_id, count(*)::int as score
                FROM participant_mm pmm
                WHERE pmm.is_correct = '1'
                GROUP BY pmm.participant_id
            ) all_scores
            GROUP BY p_id
        """
        )
        return score_sql.columns(
            Column("participant_id", BigInteger),
            Column("total_score", Integer),
        ).subquery("p_scores")

    @staticmethod
    def _build_centre_questions_subquery(db: Session):
        centre_q_sql = text(
            """
            WITH p_centre AS (
                SELECT DISTINCT ON (bp.participant_id) bp.participant_id, b.centre_id
                FROM batch_participant bp
                JOIN central_batches b ON b.batch_id = bp.batch_id
                ORDER BY bp.participant_id, bp.batch_id DESC
            ),
            q_stats AS (
                SELECT p_id, sum(is_corr)::int as correct_count, count(*)::int as total_attempts
                FROM (
                    SELECT pm.participant_id as p_id, 
                           CASE WHEN mo.is_mcq_option_correct = 1 THEN 1 ELSE 0 END as is_corr
                    FROM participant_mcqs pm
                    LEFT JOIN mcq_question_options mo 
                      ON mo.mcq_option_id = CAST(NULLIF(regexp_replace(pm.option_selected, '[^0-9]', '', 'g'), '') AS BIGINT)
                    
                    UNION ALL
                    
                    SELECT ps.participant_id as p_id,
                           CASE WHEN so.is_scq_option_correct = 1 THEN 1 ELSE 0 END as is_corr
                    FROM participant_scs ps
                    LEFT JOIN scq_question_options so 
                      ON so.scq_option_id = CAST(NULLIF(regexp_replace(ps.option_selected, '[^0-9]', '', 'g'), '') AS BIGINT)
                    
                    UNION ALL
                    
                    SELECT pmm.participant_id as p_id,
                           CASE WHEN pmm.is_correct = '1' THEN 1 ELSE 0 END as is_corr
                    FROM participant_mm pmm
                ) q
                GROUP BY p_id
            )
            SELECT pc.centre_id, 
                   sum(qs.correct_count)::int as total_correct, 
                   sum(qs.total_attempts)::int as total_questions
            FROM p_centre pc
            JOIN q_stats qs ON qs.p_id = pc.participant_id
            GROUP BY pc.centre_id
        """
        )
        return centre_q_sql.columns(
            Column("centre_id", BigInteger),
            Column("total_correct", Integer),
            Column("total_questions", Integer),
        ).subquery("centre_questions")

    @staticmethod
    def get_need_attention_summary(
        db: Session,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        reference_now: datetime | None = None,
    ) -> dict:
        if reference_now is None:
            reference_now = datetime.now(timezone.utc).replace(tzinfo=None)
        cutoff_30d = reference_now - timedelta(days=30)

        p_query = db.query(ParticipantMaster.participant_id).filter(
            ParticipantMaster.deleted_at.is_(None)
        )
        if state_id is not None:
            p_query = p_query.filter(ParticipantMaster.state_id == state_id)
        if district_id is not None:
            p_query = p_query.filter(ParticipantMaster.district_id == district_id)
        p_query = DashboardRepository._apply_centre_filter(p_query, centre_id)
        p_query = DashboardRepository._apply_date_filter(
            p_query, ParticipantMaster, from_date, to_date
        )
        p_sub = p_query.subquery()

        last_act = DashboardRepository._build_last_activity_subquery(db)

        agg = (
            db.query(
                func.count(case((last_act.c.participant_id.is_(None), 1))).label(
                    "never_logged_in"
                ),
                func.count(
                    case(
                        (
                            and_(
                                last_act.c.participant_id.isnot(None),
                                last_act.c.latest_activity < cutoff_30d,
                            ),
                            1,
                        )
                    )
                ).label("inactive_30d"),
            )
            .select_from(p_sub)
            .outerjoin(last_act, last_act.c.participant_id == p_sub.c.participant_id)
            .one()
        )

        return {
            "never_logged_in": int(agg.never_logged_in or 0),
            "inactive_30d": int(agg.inactive_30d or 0),
        }

    @staticmethod
    def get_need_attention_learners(
        db: Session,
        learner_type: str,
        page: int = 1,
        page_size: int = 20,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        search: str | None = None,
        reference_now: datetime | None = None,
    ) -> tuple[list[dict], int]:
        if reference_now is None:
            reference_now = datetime.now(timezone.utc).replace(tzinfo=None)
        cutoff_30d = reference_now - timedelta(days=30)

        last_act = DashboardRepository._build_last_activity_subquery(db)
        p_centre = DashboardRepository._build_distinct_participant_centre_subquery(db)

        query = (
            db.query(
                ParticipantMaster.participant_id,
                ParticipantMaster.participant_name,
                ParticipantMaster.images.label("image"),
                ParticipantMaster.enrollment_no,
                p_centre.c.centre_id,
                CentreMaster.centre_name,
                ParticipantMaster.state_id,
                StateMaster.state_name,
                ParticipantMaster.district_id,
                DistrictMaster.district_name,
                ParticipantMaster.created_at.label("registration_date"),
                last_act.c.latest_activity.label("last_activity_time"),
            )
            .outerjoin(
                last_act, last_act.c.participant_id == ParticipantMaster.participant_id
            )
            .outerjoin(
                p_centre, p_centre.c.participant_id == ParticipantMaster.participant_id
            )
            .outerjoin(
                CentreMaster,
                and_(
                    CentreMaster.centre_id == p_centre.c.centre_id,
                    CentreMaster.deleted_at.is_(None),
                ),
            )
            .outerjoin(
                StateMaster, StateMaster.state_lgd_code == ParticipantMaster.state_id
            )
            .outerjoin(
                DistrictMaster,
                DistrictMaster.district_lgd_code == ParticipantMaster.district_id,
            )
            .filter(ParticipantMaster.deleted_at.is_(None))
        )

        if state_id is not None:
            query = query.filter(ParticipantMaster.state_id == state_id)
        if district_id is not None:
            query = query.filter(ParticipantMaster.district_id == district_id)
        if centre_id is not None:
            query = query.filter(p_centre.c.centre_id == centre_id)
        if from_date is not None:
            query = query.filter(ParticipantMaster.created_at >= from_date)
        if to_date is not None:
            query = query.filter(ParticipantMaster.created_at <= to_date)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    ParticipantMaster.participant_name.ilike(search_pattern),
                    ParticipantMaster.enrollment_no.ilike(search_pattern),
                    ParticipantMaster.mobile_no.ilike(search_pattern),
                )
            )

        if learner_type == "never_logged_in":
            query = query.filter(last_act.c.participant_id.is_(None))
            query = query.order_by(
                ParticipantMaster.created_at.desc(),
                ParticipantMaster.participant_id.desc(),
            )
        elif learner_type == "inactive_30d":
            query = query.filter(
                and_(
                    last_act.c.participant_id.isnot(None),
                    last_act.c.latest_activity < cutoff_30d,
                )
            )
            query = query.order_by(
                last_act.c.latest_activity.desc(),
                ParticipantMaster.participant_id.desc(),
            )
        else:
            return [], 0

        total_count = query.count()
        offset = (page - 1) * page_size
        rows = query.offset(offset).limit(page_size).all()

        results = []
        for r in rows:
            days_inactive = None
            if r.last_activity_time is not None:
                days_inactive = max(
                    0, (reference_now.date() - r.last_activity_time.date()).days
                )
            results.append(
                {
                    "participant_id": r.participant_id,
                    "participant_name": r.participant_name,
                    "name": r.participant_name,
                    "image": r.image,
                    "name": r.participant_name,
                    "image": r.image,
                    "enrollment_no": r.enrollment_no,
                    "centre_id": r.centre_id,
                    "centre_name": r.centre_name,
                    "state_id": r.state_id,
                    "state_name": r.state_name,
                    "district_id": r.district_id,
                    "district_name": r.district_name,
                    "registration_date": r.registration_date,
                    "last_activity_time": r.last_activity_time,
                    "days_inactive": days_inactive,
                }
            )

        return results, total_count

    @staticmethod
    def get_recent_learners(
        db: Session,
        limit: int = 5,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[dict]:
        last_act = DashboardRepository._build_last_activity_subquery(db)
        p_centre = DashboardRepository._build_distinct_participant_centre_subquery(db)

        time_sum = (
            db.query(
                TimeSpentModuleLog.user_id.label("participant_id"),
                func.sum(TimeSpentModuleLog.time_taken).label("total_seconds"),
            )
            .group_by(TimeSpentModuleLog.user_id)
            .subquery()
        )

        mod_completed = (
            db.query(
                ParticipantModule.participant_id.label("participant_id"),
                func.count(distinct(ParticipantModule.module_id)).label(
                    "completed_count"
                ),
            )
            .filter(
                or_(
                    ParticipantModule.lock_status == 2,
                    ParticipantModule.status == "2",
                    ParticipantModule.status.ilike("completed"),
                )
            )
            .group_by(ParticipantModule.participant_id)
            .subquery()
        )

        mod_assigned = (
            db.query(
                ParticipantModule.participant_id.label("participant_id"),
                func.count(distinct(ParticipantModule.module_id)).label(
                    "assigned_count"
                ),
            )
            .group_by(ParticipantModule.participant_id)
            .subquery()
        )

        score_sub = DashboardRepository._build_participant_score_subquery(db)

        query = (
            db.query(
                ParticipantMaster.participant_id,
                ParticipantMaster.participant_name,
                ParticipantMaster.images.label("image"),
                ParticipantMaster.enrollment_no,
                p_centre.c.centre_id,
                CentreMaster.centre_name,
                ParticipantMaster.state_id,
                StateMaster.state_name,
                ParticipantMaster.district_id,
                DistrictMaster.district_name,
                last_act.c.latest_activity.label("latest_activity_time"),
                func.coalesce(score_sub.c.total_score, 0).label("total_score"),
                func.coalesce(time_sum.c.total_seconds, 0).label(
                    "session_duration_seconds"
                ),
                func.coalesce(mod_completed.c.completed_count, 0).label(
                    "completed_modules_count"
                ),
                func.coalesce(mod_assigned.c.assigned_count, 0).label(
                    "assigned_modules_count"
                ),
            )
            .outerjoin(
                last_act, last_act.c.participant_id == ParticipantMaster.participant_id
            )
            .outerjoin(
                score_sub,
                score_sub.c.participant_id == ParticipantMaster.participant_id,
            )
            .outerjoin(
                p_centre, p_centre.c.participant_id == ParticipantMaster.participant_id
            )
            .outerjoin(
                CentreMaster,
                and_(
                    CentreMaster.centre_id == p_centre.c.centre_id,
                    CentreMaster.deleted_at.is_(None),
                ),
            )
            .outerjoin(
                StateMaster, StateMaster.state_lgd_code == ParticipantMaster.state_id
            )
            .outerjoin(
                DistrictMaster,
                DistrictMaster.district_lgd_code == ParticipantMaster.district_id,
            )
            .outerjoin(
                time_sum, time_sum.c.participant_id == ParticipantMaster.participant_id
            )
            .outerjoin(
                mod_completed,
                mod_completed.c.participant_id == ParticipantMaster.participant_id,
            )
            .outerjoin(
                mod_assigned,
                mod_assigned.c.participant_id == ParticipantMaster.participant_id,
            )
            .filter(ParticipantMaster.deleted_at.is_(None))
        )

        if state_id is not None:
            query = query.filter(ParticipantMaster.state_id == state_id)
        if district_id is not None:
            query = query.filter(ParticipantMaster.district_id == district_id)
        if centre_id is not None:
            query = query.filter(p_centre.c.centre_id == centre_id)
        if from_date is not None:
            query = query.filter(
                or_(
                    last_act.c.latest_activity >= from_date,
                    ParticipantMaster.created_at >= from_date,
                )
            )
        if to_date is not None:
            query = query.filter(
                or_(
                    last_act.c.latest_activity <= to_date,
                    ParticipantMaster.created_at <= to_date,
                )
            )

        query = query.order_by(
            func.coalesce(score_sub.c.total_score, 0).desc(),
            func.coalesce(time_sum.c.total_seconds, 0).desc(),
            func.coalesce(mod_completed.c.completed_count, 0).desc(),
            last_act.c.latest_activity.desc().nullslast(),
            ParticipantMaster.participant_id.asc(),
        ).limit(limit)

        rows = query.all()
        results = []
        for rank_idx, r in enumerate(rows, 1):
            dur_sec = int(r.session_duration_seconds or 0)
            score = int(r.total_score or 0)
            c_cnt = int(r.completed_modules_count or 0)
            a_cnt = max(int(r.assigned_modules_count or 0), c_cnt)
            mod_pct = round((c_cnt / a_cnt) * 100, 2) if a_cnt > 0 else 0.0
            results.append(
                {
                    "rank": rank_idx,
                    "participant_id": r.participant_id,
                    "participant_name": r.participant_name,
                    "name": r.participant_name,
                    "image": r.image,
                    "enrollment_no": r.enrollment_no,
                    "centre_id": r.centre_id,
                    "centre_name": r.centre_name,
                    "state_id": r.state_id,
                    "state_name": r.state_name,
                    "district_id": r.district_id,
                    "district_name": r.district_name,
                    "latest_activity_time": r.latest_activity_time,
                    "total_score": score,
                    "score": score,
                    "session_duration_seconds": dur_sec,
                    "session_duration_minutes": round(dur_sec / 60.0, 1),
                    "completed_modules": c_cnt,
                    "completed_modules_count": c_cnt,
                    "total_assigned_modules": a_cnt,
                    "total_modules": a_cnt,
                    "total_modules_count": a_cnt,
                    "assigned_modules": a_cnt,
                    "assigned_modules_count": a_cnt,
                    "module_completion_percentage": mod_pct,
                    "course_progress": mod_pct,
                }
            )
        return results

    @staticmethod
    def get_learner_activity_detail(
        db: Session,
        participant_id: int,
    ) -> dict | None:
        p_centre = DashboardRepository._build_distinct_participant_centre_subquery(db)
        p = (
            db.query(
                ParticipantMaster.participant_id,
                ParticipantMaster.participant_name,
                ParticipantMaster.images.label("image"),
                ParticipantMaster.enrollment_no,
                p_centre.c.centre_id,
                CentreMaster.centre_name,
                ParticipantMaster.state_id,
                StateMaster.state_name,
                ParticipantMaster.district_id,
                DistrictMaster.district_name,
            )
            .outerjoin(
                p_centre, p_centre.c.participant_id == ParticipantMaster.participant_id
            )
            .outerjoin(
                CentreMaster,
                and_(
                    CentreMaster.centre_id == p_centre.c.centre_id,
                    CentreMaster.deleted_at.is_(None),
                ),
            )
            .outerjoin(
                StateMaster, StateMaster.state_lgd_code == ParticipantMaster.state_id
            )
            .outerjoin(
                DistrictMaster,
                DistrictMaster.district_lgd_code == ParticipantMaster.district_id,
            )
            .filter(
                ParticipantMaster.participant_id == participant_id,
                ParticipantMaster.deleted_at.is_(None),
            )
            .first()
        )
        if not p:
            return None

        total_logins = (
            db.query(func.count(LoginLog.id))
            .filter(LoginLog.user_id == participant_id)
            .scalar()
            or 0
        )
        last_login = (
            db.query(func.max(LoginLog.login_time))
            .filter(LoginLog.user_id == participant_id)
            .scalar()
        )

        time_stats = (
            db.query(
                func.coalesce(func.sum(TimeSpentModuleLog.time_taken), 0).label(
                    "total_seconds"
                ),
                func.max(TimeSpentModuleLog.created_at).label("last_module_time"),
            )
            .filter(TimeSpentModuleLog.user_id == participant_id)
            .first()
        )

        total_time_seconds = int(time_stats.total_seconds) if time_stats else 0
        last_module_time = time_stats.last_module_time if time_stats else None

        candidates = [ts for ts in (last_login, last_module_time) if ts is not None]
        last_activity = max(candidates) if candidates else None

        # ── Module completion & scores: parent-level logic matching View Report ──
        sc_info = {}
        try:
            scores = DashboardRepository._compute_view_report_scores_batch(
                db, [participant_id]
            )
            sc_info = scores.get(participant_id, {})
        except Exception:
            pass

        rep_sm = {}
        try:
            from app.modules.users.repository import UserRepository
            rep = UserRepository.get_module_report(db, participant_id)
            rep_sm = rep.get("assessment_summary") or {}
        except Exception:
            pass

        completed_count = int(
            rep_sm.get("completed_modules")
            if rep_sm.get("completed_modules") is not None
            else sc_info.get("completed_modules", 0)
        )
        total_assigned_count = int(
            rep_sm.get("total_assigned_modules")
            if rep_sm.get("total_assigned_modules") is not None
            else sc_info.get("total_assigned_modules", 0)
        )
        module_completion_percentage = float(
            rep_sm.get("module_completion_percentage")
            if rep_sm.get("module_completion_percentage") is not None
            else sc_info.get(
                "module_completion_percentage",
                round((completed_count / total_assigned_count) * 100.0, 2)
                if total_assigned_count > 0
                else 0.0,
            )
        )

        assessment_pct = float(
            rep_sm.get("percentage")
            if rep_sm.get("percentage") is not None and float(rep_sm.get("percentage") or 0.0) > 0
            else sc_info.get("assessment_percentage", 0.0)
        )
        obtained_marks = float(
            rep_sm.get("score")
            if rep_sm.get("score") is not None and float(rep_sm.get("score") or 0.0) > 0
            else sc_info.get("score", 0.0)
        )
        total_marks = float(
            rep_sm.get("total_marks")
            if rep_sm.get("total_marks") is not None and float(rep_sm.get("total_marks") or 0.0) > 0
            else sc_info.get("total_marks", 0.0)
        )
        total_q = int(rep_sm.get("total_questions") or sc_info.get("assigned_questions") or 0)
        correct_q = int(rep_sm.get("correct") or sc_info.get("correct_questions") or 0)
        completed_q = int(rep_sm.get("completed_questions") or sc_info.get("completed_questions") or 0)

        score_scalar_sql = text(
            """
            SELECT sum(score)::int as total_score
            FROM (
                SELECT count(*)::int as score
                FROM participant_mcqs pm
                JOIN mcq_question_options mo 
                  ON mo.mcq_option_id = CAST(NULLIF(regexp_replace(pm.option_selected, '[^0-9]', '', 'g'), '') AS BIGINT)
                WHERE pm.participant_id = :p_id AND mo.is_mcq_option_correct = 1
                
                UNION ALL
                
                SELECT count(*)::int as score
                FROM participant_scs ps
                JOIN scq_question_options so 
                  ON so.scq_option_id = CAST(NULLIF(regexp_replace(ps.option_selected, '[^0-9]', '', 'g'), '') AS BIGINT)
                WHERE ps.participant_id = :p_id AND so.is_scq_option_correct = 1
                
                UNION ALL
                
                SELECT count(*)::int as score
                FROM participant_mm pmm
                WHERE pmm.participant_id = :p_id AND pmm.is_correct = '1'
            ) s
        """
        )
        total_score_val = (
            db.execute(score_scalar_sql, {"p_id": participant_id}).scalar() or 0
        )

        recent_sessions_rows = (
            db.query(
                TimeSpentModuleLog.topic_id,
                TimeSpentModuleLog.module_id,
                TimeSpentModuleLog.document_id,
                TimeSpentModuleLog.time_taken,
                TimeSpentModuleLog.created_at,
            )
            .filter(TimeSpentModuleLog.user_id == participant_id)
            .order_by(TimeSpentModuleLog.created_at.desc())
            .limit(10)
            .all()
        )

        recent_sessions = [
            {
                "topic_id": r.topic_id,
                "module_id": r.module_id,
                "document_id": r.document_id,
                "time_taken_seconds": int(r.time_taken or 0),
                "created_at": r.created_at,
            }
            for r in recent_sessions_rows
        ]

        return {
            "participant_id": p.participant_id,
            "participant_name": p.participant_name,
            "name": p.participant_name,
            "image": p.image,
            "enrollment_no": p.enrollment_no,
            "centre_id": p.centre_id,
            "centre_name": p.centre_name,
            "state_id": p.state_id,
            "state_name": p.state_name,
            "district_id": p.district_id,
            "district_name": p.district_name,
            "total_logins": int(total_logins),
            "total_time_spent_seconds": total_time_seconds,
            "total_time_spent_minutes": round(total_time_seconds / 60.0, 1),
            "completed_modules": int(completed_count),
            "completed_modules_count": int(completed_count),
            "total_assigned_modules": int(total_assigned_count),
            "total_modules_count": int(total_assigned_count),
            "assigned_modules": int(total_assigned_count),
            "assigned_modules_count": int(total_assigned_count),
            "module_completion_percentage": float(module_completion_percentage),
            "course_progress": float(module_completion_percentage),
            "total_score": int(total_score_val),
            "score": float(obtained_marks),
            "obtained_marks": float(obtained_marks),
            "total_marks": float(total_marks),
            "assessment_percentage": float(assessment_pct),
            "total_questions": int(total_q),
            "correct_questions": int(correct_q),
            "completed_questions": int(completed_q),
            "last_login": last_login,
            "last_activity": last_activity,
            "recent_sessions": recent_sessions,
        }

    @staticmethod
    def _get_latest_assessment_score_map(
        db: Session,
        participant_ids: list[int],
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> dict[int, dict]:
        """
        Overall assessment score % per participant = the AVERAGE of every
        ASSIGNED module's score %, so each assigned module counts equally and a
        module with no answers (or none correct) contributes 0 %.

        Per module only the latest attempt is scored: MCQ/SCQ compare the
        selected option with the stored correct option, Match uses
        ParticipantMm.is_correct. Drop Bucket is excluded from scoring but may
        still decide which attempt is the latest.
        """
        if not participant_ids:
            return {}

        # 1) one latest attempt per participant/module across all answer types.
        attempt_sources = []
        for answer_model in (
            ParticipantMcq,
            ParticipantScq,
            ParticipantMm,
            ParticipantDb,
        ):
            attempt_query = db.query(
                answer_model.participant_id.label("participant_id"),
                answer_model.module_id.label("module_id"),
                answer_model.attempt_id.label("attempt_id"),
            ).filter(
                answer_model.participant_id.in_(participant_ids),
                answer_model.attempt_id.isnot(None),
            )
            if hasattr(answer_model, "is_active"):
                attempt_query = attempt_query.filter(answer_model.is_active == 1)
            if from_date is not None:
                attempt_query = attempt_query.filter(
                    answer_model.created_date >= from_date
                )
            if to_date is not None:
                attempt_query = attempt_query.filter(
                    answer_model.created_date < to_date + timedelta(days=1)
                )
            attempt_sources.append(attempt_query)

        all_attempts = union_all(*attempt_sources).subquery("all_assessment_attempts")
        latest = (
            db.query(
                all_attempts.c.participant_id,
                all_attempts.c.module_id,
                func.max(all_attempts.c.attempt_id).label("latest_attempt_id"),
            )
            .group_by(all_attempts.c.participant_id, all_attempts.c.module_id)
            .subquery("latest_assessment_attempt")
        )

        answer_models = (
            (ParticipantMcq, "option_selected", "correct_option", False),
            (ParticipantScq, "option_selected", "correct_option", False),
            (ParticipantMm, None, None, True),
        )

        # 2) attempted + correct on the latest attempt, PER (participant, module).
        per_mod: dict[tuple[int, int], list[int]] = {}
        for model, selected_attr, correct_attr, uses_is_correct in answer_models:
            if uses_is_correct:
                # is_correct is VARCHAR in PostgreSQL, not BOOLEAN.
                normalized_correct = func.lower(func.trim(model.is_correct))
                correct_expression = case(
                    (normalized_correct.in_(("1", "true", "t", "yes", "y")), 1),
                    else_=0,
                )
            else:
                correct_expression = case(
                    (
                        getattr(model, selected_attr) == getattr(model, correct_attr),
                        1,
                    ),
                    else_=0,
                )

            answer_query = db.query(
                model.participant_id.label("participant_id"),
                model.module_id.label("module_id"),
                func.count().label("attempted_count"),
                func.coalesce(func.sum(correct_expression), 0).label("correct_count"),
            ).join(
                latest,
                and_(
                    model.participant_id == latest.c.participant_id,
                    model.module_id == latest.c.module_id,
                    model.attempt_id == latest.c.latest_attempt_id,
                ),
            )
            if hasattr(model, "is_active"):
                answer_query = answer_query.filter(model.is_active == 1)
            rows = answer_query.group_by(model.participant_id, model.module_id).all()

            for row in rows:
                key = (int(row.participant_id), int(row.module_id))
                slot = per_mod.setdefault(key, [0, 0])
                slot[0] += int(row.attempted_count or 0)
                slot[1] += int(row.correct_count or 0)

        # 3) sum of per-module score %, pooled totals, and attempted-module count.
        sum_module_pct: dict[int, float] = {}
        pooled_attempted: dict[int, int] = {}
        pooled_correct: dict[int, int] = {}
        attempted_modules: dict[int, int] = {}
        for (pid, _mid), (attempted, correct) in per_mod.items():
            if attempted > 0:
                sum_module_pct[pid] = sum_module_pct.get(pid, 0.0) + (
                    correct * 100.0 / attempted
                )
            pooled_attempted[pid] = pooled_attempted.get(pid, 0) + attempted
            pooled_correct[pid] = pooled_correct.get(pid, 0) + correct
            attempted_modules[pid] = attempted_modules.get(pid, 0) + 1

        # 4) ASSIGNED module count per participant — the averaging denominator,
        #    so unattempted assigned modules pull the average toward 0 %.
        assigned_rows = (
            db.query(
                ParticipantModule.participant_id,
                func.count(distinct(ParticipantModule.module_id)),
            )
            .filter(ParticipantModule.participant_id.in_(participant_ids))
            .group_by(ParticipantModule.participant_id)
            .all()
        )
        assigned_count = {int(pid): int(cnt or 0) for pid, cnt in assigned_rows}

        # 5) average over assigned modules; every requested participant is
        #    returned so even a 0 % learner shows up.
        result: dict[int, dict] = {}
        for raw_pid in participant_ids:
            pid = int(raw_pid)
            # Prefer the assigned-module count; fall back to the number of
            # modules actually attempted when no assignment rows exist.
            denom = assigned_count.get(pid, 0) or attempted_modules.get(pid, 0)
            total_pct = sum_module_pct.get(pid, 0.0)
            result[pid] = {
                "assessment_percentage": round(total_pct / denom, 2) if denom else 0.0,
                "assessment_questions_attempted": pooled_attempted.get(pid, 0),
                "assessment_questions_correct": pooled_correct.get(pid, 0),
            }
        return result

    @staticmethod
    def _compute_view_report_scores_batch(db: Session, participant_ids: list[int]) -> dict[int, dict]:
        """
        Computes the EXACT View Report 'Overall Post Assessment Score (%)' for every
        participant in batch:
          Overall % = (overall_score / overall_total_marks) * 100
        Where:
          - Scored on latest attempt per parent module across MCQ, SCQ, MM, Drop Bucket.
          - Unattempted assigned modules have their configured question marks added to
            overall_total_marks, exactly matching UserRepository.get_assessment_summary().
        """
        if not participant_ids:
            return {}

        # 1. Configured marks per parent module when unattempted
        modules_raw = db.execute(
            text("SELECT module_id, COALESCE(parent_id, module_id) AS parent_id FROM module_masters WHERE deleted_at IS NULL")
        ).fetchall()
        mod_to_parent = {r[0]: r[1] for r in modules_raw}
        parent_to_children = defaultdict(set)
        for mid, pid in mod_to_parent.items():
            parent_to_children[pid].add(mid)

        configured_marks_by_parent = {}
        configured_questions_by_parent = {}
        for parent_id, child_ids in parent_to_children.items():
            post_a_ids = [
                r[0]
                for r in db.execute(
                    text(
                        "SELECT assessment_id FROM post_session_assessment "
                        "WHERE module_id = :mid AND is_active = 1 AND deleted_at IS NULL"
                    ),
                    {"mid": parent_id},
                ).fetchall()
            ]
            if not post_a_ids:
                for cid in child_ids:
                    post_a_ids = [
                        r[0]
                        for r in db.execute(
                            text(
                                "SELECT assessment_id FROM post_session_assessment "
                                "WHERE module_id = :mid AND is_active = 1 AND deleted_at IS NULL"
                            ),
                            {"mid": cid},
                        ).fetchall()
                    ]
                    if post_a_ids:
                        break

            tot = 0.0
            q_cnt = 0
            if post_a_ids:
                mcq_row = db.execute(
                    text(
                        "SELECT COUNT(DISTINCT mm.mcq_id), COALESCE(SUM(mm.marks), 0) FROM assessment_mapping am "
                        "JOIN mcq_master mm ON mm.mcq_id = am.assessment_ref_id "
                        "WHERE am.assessment_id = ANY(:aids) AND am.assessment_type = 'MCQ' AND am.is_active = 1 AND mm.deleted_at IS NULL"
                    ),
                    {"aids": post_a_ids},
                ).first()
                if mcq_row:
                    q_cnt += int(mcq_row[0] or 0)
                    tot += float(mcq_row[1] or 0.0)

                scq_row = db.execute(
                    text(
                        "SELECT COUNT(DISTINCT sm.scq_id), COALESCE(SUM(sm.marks), 0) FROM assessment_mapping am "
                        "JOIN scq_master sm ON sm.scq_id = am.assessment_ref_id "
                        "WHERE am.assessment_id = ANY(:aids) AND am.assessment_type = 'SCQ' AND am.is_active = 1 AND sm.deleted_at IS NULL"
                    ),
                    {"aids": post_a_ids},
                ).first()
                if scq_row:
                    q_cnt += int(scq_row[0] or 0)
                    tot += float(scq_row[1] or 0.0)

                db_row = db.execute(
                    text(
                        "SELECT COUNT(DISTINCT dm.drop_bucket_id), COALESCE(SUM(dm.marks), 0) FROM assessment_mapping am "
                        "JOIN drop_bucket_masters dm ON dm.drop_bucket_id = am.assessment_ref_id "
                        "WHERE am.assessment_id = ANY(:aids) AND am.assessment_type = 'DB' AND am.is_active = 1 AND dm.deleted_at IS NULL"
                    ),
                    {"aids": post_a_ids},
                ).first()
                if db_row:
                    q_cnt += int(db_row[0] or 0)
                    tot += float(db_row[1] or 0.0)

                mm_row = db.execute(
                    text(
                        "SELECT COUNT(DISTINCT mmm.match_making_id), COALESCE(SUM(mmm.marks), 0) FROM assessment_mapping am "
                        "JOIN match_making_masters mmm ON mmm.match_making_id = am.assessment_ref_id "
                        "WHERE am.assessment_id = ANY(:aids) AND am.assessment_type = 'MM' AND am.is_active = 1 AND mmm.deleted_at IS NULL"
                    ),
                    {"aids": post_a_ids},
                ).first()
                if mm_row:
                    q_cnt += int(mm_row[0] or 0)
                    tot += float(mm_row[1] or 0.0)

            configured_marks_by_parent[parent_id] = round(tot, 2)
            configured_questions_by_parent[parent_id] = q_cnt

        # 2. Attempted score, marks, and correct question counts on latest attempts per (participant_id, parent_id)
        attempted_sql = text(
            """
            WITH mod_parent AS (
                SELECT module_id, COALESCE(parent_id, module_id) AS parent_id FROM module_masters
            ),
            all_att AS (
                SELECT participant_id, module_id, attempt_id FROM participant_mcqs WHERE is_active=1 AND attempt_id IS NOT NULL AND participant_id = ANY(:pids)
                UNION ALL SELECT participant_id, module_id, attempt_id FROM participant_scs WHERE is_active=1 AND attempt_id IS NOT NULL AND participant_id = ANY(:pids)
                UNION ALL SELECT participant_id, module_id, attempt_id FROM participant_mm WHERE is_active=1 AND attempt_id IS NOT NULL AND participant_id = ANY(:pids)
                UNION ALL SELECT participant_id, module_id, attempt_id FROM participant_dbs WHERE is_active=1 AND attempt_id IS NOT NULL AND participant_id = ANY(:pids)
            ),
            latest AS (
                SELECT a.participant_id, mp.parent_id, MAX(a.attempt_id) AS latest_attempt_id
                FROM all_att a
                JOIN mod_parent mp ON mp.module_id = a.module_id
                GROUP BY a.participant_id, mp.parent_id
            ),
            scq_ans AS (
                SELECT ps.participant_id, mp.parent_id, ps.single_choice_id,
                       MAX(CASE WHEN so.is_scq_option_correct = 1 THEN 1 ELSE 0 END) AS is_correct
                FROM participant_scs ps
                JOIN mod_parent mp ON mp.module_id = ps.module_id
                JOIN latest l ON l.participant_id = ps.participant_id AND l.parent_id = mp.parent_id AND l.latest_attempt_id = ps.attempt_id
                LEFT JOIN scq_question_options so ON so.scq_option_id = CAST(NULLIF(regexp_replace(ps.option_selected, '[^0-9]', '', 'g'), '') AS BIGINT) AND so.deleted_at IS NULL
                WHERE ps.is_active = 1 AND ps.participant_id = ANY(:pids)
                GROUP BY ps.participant_id, mp.parent_id, ps.single_choice_id
            ),
            scq AS (
                SELECT a.participant_id, a.parent_id,
                       COALESCE(sm.marks, 1) AS q_marks,
                       CASE WHEN a.is_correct = 1 THEN COALESCE(sm.marks, 1) ELSE 0 END AS q_score,
                       CASE WHEN a.is_correct = 1 THEN 1 ELSE 0 END AS q_correct,
                       1 AS q_attempted
                FROM scq_ans a
                LEFT JOIN scq_master sm ON sm.scq_id = a.single_choice_id
            ),
            mcq_ans AS (
                SELECT pm.participant_id, mp.parent_id, pm.mcq_id,
                       COUNT(DISTINCT pm.option_selected) AS n_sel,
                       COUNT(DISTINCT CASE WHEN mo.is_mcq_option_correct = 1 THEN pm.option_selected END) AS n_sel_correct
                FROM participant_mcqs pm
                JOIN mod_parent mp ON mp.module_id = pm.module_id
                JOIN latest l ON l.participant_id = pm.participant_id AND l.parent_id = mp.parent_id AND l.latest_attempt_id = pm.attempt_id
                LEFT JOIN mcq_question_options mo ON mo.mcq_option_id = CAST(NULLIF(regexp_replace(pm.option_selected, '[^0-9]', '', 'g'), '') AS BIGINT) AND mo.deleted_at IS NULL
                WHERE pm.is_active = 1 AND pm.participant_id = ANY(:pids)
                GROUP BY pm.participant_id, mp.parent_id, pm.mcq_id
            ),
            mcq_cc AS (
                SELECT mcq_id, COUNT(*) AS n_correct
                FROM mcq_question_options
                WHERE is_mcq_option_correct = 1 AND deleted_at IS NULL AND status = 1
                GROUP BY mcq_id
            ),
            mcq AS (
                SELECT a.participant_id, a.parent_id,
                       COALESCE(mm2.marks, 1) AS q_marks,
                       CASE WHEN cc.n_correct IS NOT NULL AND a.n_sel = cc.n_correct AND a.n_sel_correct = cc.n_correct THEN COALESCE(mm2.marks, 1) ELSE 0 END AS q_score,
                       CASE WHEN cc.n_correct IS NOT NULL AND a.n_sel = cc.n_correct AND a.n_sel_correct = cc.n_correct THEN 1 ELSE 0 END AS q_correct,
                       1 AS q_attempted
                FROM mcq_ans a
                JOIN mcq_master mm2 ON mm2.mcq_id = a.mcq_id
                LEFT JOIN mcq_cc cc ON cc.mcq_id = a.mcq_id
            ),
            mm_totals AS (
                SELECT match_making_id, COUNT(*) AS total_pairs
                FROM match_left_items
                WHERE deleted_at IS NULL
                GROUP BY match_making_id
            ),
            mm_ans AS (
                SELECT pmm.participant_id, mp.parent_id, pmm.question_id,
                       COUNT(*) AS n_pairs,
                       SUM(CASE WHEN pmm.is_correct = '1' THEN 1 ELSE 0 END) AS n_correct
                FROM participant_mm pmm
                JOIN mod_parent mp ON mp.module_id = pmm.module_id
                JOIN latest l ON l.participant_id = pmm.participant_id AND l.parent_id = mp.parent_id AND l.latest_attempt_id = pmm.attempt_id
                WHERE pmm.is_active = 1 AND pmm.participant_id = ANY(:pids)
                GROUP BY pmm.participant_id, mp.parent_id, pmm.question_id
            ),
            mm AS (
                SELECT a.participant_id, a.parent_id,
                       COALESCE(mmm.marks, 1) AS q_marks,
                       CASE WHEN tot.total_pairs IS NOT NULL AND a.n_pairs = tot.total_pairs AND a.n_correct = tot.total_pairs THEN COALESCE(mmm.marks, 1) ELSE 0 END AS q_score,
                       CASE WHEN tot.total_pairs IS NOT NULL AND a.n_pairs = tot.total_pairs AND a.n_correct = tot.total_pairs THEN 1 ELSE 0 END AS q_correct,
                       1 AS q_attempted
                FROM mm_ans a
                JOIN match_making_masters mmm ON mmm.match_making_id = a.question_id
                LEFT JOIN mm_totals tot ON tot.match_making_id = a.question_id
            ),
            db_totals AS (
                SELECT dbk.drop_bucket_id, COUNT(*) AS total_items
                FROM drop_buckets dbk
                JOIN drop_bucket_items dbi ON dbi.bucket_id = dbk.bucket_id AND dbi.deleted_at IS NULL AND dbi.status = 1
                WHERE dbk.deleted_at IS NULL
                GROUP BY dbk.drop_bucket_id
            ),
            db_ans AS (
                SELECT pd.participant_id, mp.parent_id, dbk.drop_bucket_id,
                       COUNT(*) AS n_items,
                       SUM(CASE WHEN pd.bucket_id = dbi.bucket_id THEN 1 ELSE 0 END) AS n_correct
                FROM participant_dbs pd
                JOIN mod_parent mp ON mp.module_id = pd.module_id
                JOIN latest l ON l.participant_id = pd.participant_id AND l.parent_id = mp.parent_id AND l.latest_attempt_id = pd.attempt_id
                JOIN drop_bucket_items dbi ON dbi.drop_bucket_item_id = pd.item_id AND dbi.deleted_at IS NULL
                JOIN drop_buckets dbk ON dbk.bucket_id = dbi.bucket_id AND dbk.deleted_at IS NULL
                WHERE pd.is_active = 1 AND pd.participant_id = ANY(:pids)
                GROUP BY pd.participant_id, mp.parent_id, dbk.drop_bucket_id
            ),
            dbm AS (
                SELECT a.participant_id, a.parent_id,
                       COALESCE(dm.marks, 1) AS q_marks,
                       CASE WHEN tot.total_items IS NOT NULL AND a.n_items = tot.total_items AND a.n_correct = tot.total_items THEN COALESCE(dm.marks, 1) ELSE 0 END AS q_score,
                       CASE WHEN tot.total_items IS NOT NULL AND a.n_items = tot.total_items AND a.n_correct = tot.total_items THEN 1 ELSE 0 END AS q_correct,
                       1 AS q_attempted
                FROM db_ans a
                JOIN drop_bucket_masters dm ON dm.drop_bucket_id = a.drop_bucket_id
                LEFT JOIN db_totals tot ON tot.drop_bucket_id = a.drop_bucket_id
            ),
            allq AS (
                SELECT participant_id, parent_id, q_marks, q_score, q_correct, q_attempted FROM scq
                UNION ALL SELECT participant_id, parent_id, q_marks, q_score, q_correct, q_attempted FROM mcq
                UNION ALL SELECT participant_id, parent_id, q_marks, q_score, q_correct, q_attempted FROM mm
                UNION ALL SELECT participant_id, parent_id, q_marks, q_score, q_correct, q_attempted FROM dbm
            )
            SELECT participant_id, parent_id,
                   SUM(q_score) AS mod_score,
                   SUM(q_marks) AS mod_marks,
                   SUM(q_correct) AS mod_correct,
                   SUM(q_attempted) AS mod_attempted
            FROM allq
            GROUP BY participant_id, parent_id
        """
        )

        rows = db.execute(attempted_sql, {"pids": list(participant_ids)}).fetchall()
        attempted_mods = defaultdict(dict)
        for r in rows:
            attempted_mods[int(r.participant_id)][int(r.parent_id)] = {
                "score": float(r.mod_score or 0),
                "marks": float(r.mod_marks or 0),
                "correct": int(r.mod_correct or 0),
                "attempted": int(r.mod_attempted or 0),
            }

        # Assigned parent modules
        assigned_raw = db.execute(
            text(
                """
            SELECT pm.participant_id, COALESCE(mm.parent_id, mm.module_id) AS parent_id
            FROM participant_module pm
            JOIN module_masters mm ON mm.module_id = pm.module_id
            WHERE (pm.status IN ('1', '2') OR pm.status ILIKE 'completed' OR pm.lock_status IS NOT NULL)
              AND mm.deleted_at IS NULL
              AND pm.participant_id = ANY(:pids)
            GROUP BY pm.participant_id, COALESCE(mm.parent_id, mm.module_id)
        """
            ),
            {"pids": list(participant_ids)},
        ).fetchall()
        if not assigned_raw:
            assigned_raw = db.execute(
                text(
                    """
                SELECT pm.participant_id, COALESCE(mm.parent_id, mm.module_id) AS parent_id
                FROM participant_module pm
                JOIN module_masters mm ON mm.module_id = pm.module_id
                WHERE mm.deleted_at IS NULL AND pm.participant_id = ANY(:pids)
                GROUP BY pm.participant_id, COALESCE(mm.parent_id, mm.module_id)
            """
                ),
                {"pids": list(participant_ids)},
            ).fetchall()

        assigned_parents_by_pid = defaultdict(set)
        for r in assigned_raw:
            assigned_parents_by_pid[int(r.participant_id)].add(int(r.parent_id))

        out: dict[int, dict] = {}
        for pid in participant_ids:
            assigned_parents = assigned_parents_by_pid.get(pid, set())
            assigned_q = sum(configured_questions_by_parent.get(parent_id, 0) for parent_id in assigned_parents)
            correct_q = 0
            completed_q = 0
            ov_score = 0.0
            ov_total = 0.0
            att_map = attempted_mods.get(pid, {})
            completed_parents_cnt = 0
            for parent_id in assigned_parents:
                conf_q = configured_questions_by_parent.get(parent_id, 0)
                if parent_id in att_map:
                    st = att_map[parent_id]
                    ov_score += st["score"]
                    ov_total += max(float(st["marks"]), float(configured_marks_by_parent.get(parent_id, 0.0)))
                    correct_q += st["correct"]
                    completed_q += st["attempted"]
                    # Parent module is Completed strictly when all configured questions are completed
                    effective_conf_q = max(conf_q, st["attempted"])
                    if effective_conf_q > 0 and st["attempted"] >= effective_conf_q:
                        completed_parents_cnt += 1
                else:
                    ov_total += configured_marks_by_parent.get(parent_id, 0.0)

            assigned_q = max(assigned_q, completed_q)

            # Performance percentage = (correct_questions / assigned_questions) * 100
            performance_pct = (
                round((correct_q / assigned_q) * 100.0, 2)
                if assigned_q > 0
                else 0.0
            )

            marks_pct = round((ov_score / ov_total) * 100.0, 2) if ov_total > 0 else 0.0
            # Canonical View Report percentage = (score / total_marks) * 100
            report_pct = marks_pct if ov_total > 0 else performance_pct
            total_parents_cnt = len(assigned_parents)
            mod_comp_pct = (
                round((completed_parents_cnt / total_parents_cnt) * 100.0, 2)
                if total_parents_cnt > 0
                else 0.0
            )

            out[pid] = {
                "performance_percentage": report_pct,
                "assessment_percentage": report_pct,
                "score": round(ov_score, 2),
                "total_marks": round(ov_total, 2),
                "assigned_questions": assigned_q,
                "total_questions": assigned_q,
                "correct_questions": correct_q,
                "correct": correct_q,
                "completed_questions": completed_q,
                "marks_percentage": marks_pct,
                "completed_modules": completed_parents_cnt,
                "total_assigned_modules": total_parents_cnt,
                "module_completion_percentage": mod_comp_pct,
            }
        return out

    @staticmethod
    def _batch_report_pct(db: Session, participant_ids: list[int]) -> dict[int, dict]:
        """Backward-compatible alias pointing to exact View Report calculation."""
        return DashboardRepository._compute_view_report_scores_batch(db, participant_ids)

    @staticmethod
    def get_top_learners(
        db: Session,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """
        Rank learners by Overall Post Assessment Score (%) DESC, matching View Report exactly:
          Percentage = (overall_score / overall_total_marks) * 100
        Where:
          - Marks-weighted sum of correct answers on latest attempt per assigned module.
          - Unattempted assigned modules contribute to the denominator total_marks.
          - Tie-breaker: overall_score (obtained marks) DESC.
          - Top candidates refined directly with UserRepository.get_module_report().
        """
        from app.modules.users.repository import UserRepository

        participants = UserRepository.get_participants(
            db=db,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
        )
        if not participants:
            return []

        p_map = {int(p.participant_id): p for p in participants}
        p_ids = list(p_map.keys())

        # Exact View Report scores in fast batch
        score_map = DashboardRepository._compute_view_report_scores_batch(db, p_ids)

        ranked_candidates = []
        for pid in p_ids:
            p = p_map[pid]
            s_info = score_map.get(
                pid,
                {
                    "performance_percentage": 0.0,
                    "assigned_questions": 0,
                    "correct_questions": 0,
                    "completed_questions": 0,
                    "score": 0.0,
                    "total_marks": 0.0,
                },
            )
            ranked_candidates.append({
                "participant": p,
                "pid": pid,
                "performance_percentage": s_info.get("performance_percentage", 0.0),
                "assigned_questions": s_info.get("assigned_questions", 0),
                "correct_questions": s_info.get("correct_questions", 0),
                "completed_questions": s_info.get("completed_questions", 0),
                "score": s_info.get("score", 0.0),
                "total_marks": s_info.get("total_marks", 0.0),
            })

        # Filter to learners who have attempted assessments (correct > 0 or percentage > 0)
        scored = [
            c
            for c in ranked_candidates
            if c["performance_percentage"] > 0 or c["correct_questions"] > 0
        ]
        ranking_list = scored if scored else ranked_candidates

        # Ranking rules:
        # 1. performance_percentage DESC
        # 2. assigned_questions DESC
        # 3. Deterministic: correct_questions DESC, then pid ASC (-pid in reverse)
        # Time is strictly NOT included in ranking formula!
        ranking_list.sort(
            key=lambda c: (
                c["performance_percentage"],
                c["assigned_questions"],
                c["correct_questions"],
                -c["pid"],
            ),
            reverse=True,
        )

        top_slice = ranking_list[: max(1, limit)]
        top_ids = [c["pid"] for c in top_slice]

        # Refine top slice with exact assessment_summary from UserRepository.get_module_report
        refined_summaries = {}
        for pid in top_ids:
            try:
                rep = UserRepository.get_module_report(db, pid)
                refined_summaries[pid] = rep.get("assessment_summary") or {}
            except Exception:
                refined_summaries[pid] = {}

        # Fetch learning time for top learners from TimeSpentModuleLog (for dashboard display only)
        time_map = {}
        mod_map = {}
        if top_ids:
            time_rows = (
                db.query(
                    TimeSpentModuleLog.user_id.label("participant_id"),
                    func.coalesce(func.sum(TimeSpentModuleLog.time_taken), 0).label(
                        "learning_time_seconds"
                    ),
                )
                .filter(TimeSpentModuleLog.user_id.in_(top_ids))
                .group_by(TimeSpentModuleLog.user_id)
                .all()
            )
            time_map = {
                int(row.participant_id): int(row.learning_time_seconds or 0)
                for row in time_rows
            }

        results = []
        for item in top_slice:
            p = item["participant"]
            pid = item["pid"]
            sm = refined_summaries.get(pid, {})
            s_info = score_map.get(pid, {})

            score_val = float(sm.get("score") if sm.get("score") is not None else item["score"])
            total_marks = float(sm.get("total_marks") if sm.get("total_marks") is not None else item["total_marks"])
            assigned_q = int(sm.get("total_questions") if sm.get("total_questions") is not None else item["assigned_questions"])
            correct_q = int(sm.get("correct") if sm.get("correct") is not None else item["correct_questions"])
            completed_q = int(sm.get("completed_questions") if sm.get("completed_questions") is not None else item["completed_questions"])
            assigned_q = max(assigned_q, completed_q)

            # Canonical View Report percentage = (score / total_marks) * 100
            pct = float(
                sm.get("percentage")
                if sm.get("percentage") is not None
                else (
                    round((score_val / total_marks) * 100.0, 2)
                    if total_marks > 0
                    else (
                        round((correct_q / assigned_q) * 100.0, 2)
                        if assigned_q > 0
                        else float(item.get("performance_percentage") or 0.0)
                    )
                )
            )

            seconds = time_map.get(pid, 0)

            # ── Parent-level module completion counts matching View Report exactly ──
            c_mods = int(
                sm.get("completed_modules")
                if sm.get("completed_modules") is not None
                else s_info.get("completed_modules", 0)
            )
            a_mods = int(
                sm.get("total_assigned_modules")
                if sm.get("total_assigned_modules") is not None
                else s_info.get("total_assigned_modules", 0)
            )
            mod_pct = float(
                sm.get("module_completion_percentage")
                if sm.get("module_completion_percentage") is not None
                else s_info.get(
                    "module_completion_percentage",
                    round((c_mods / a_mods) * 100.0, 2) if a_mods > 0 else 0.0,
                )
            )

            results.append({
                "participant_id": pid,
                "participant_name": p.participant_name or "-",
                "name": p.participant_name or "-",
                "image": getattr(p, "image", None),
                "enrollment_no": p.enrollment_no or "-",
                "centre_id": getattr(p, "centre_id", None),
                "centre_name": getattr(p, "centre_name", None) or "-",
                "state_id": getattr(p, "state_id", None),
                "state_name": getattr(p, "state_name", None) or "-",
                "district_id": getattr(p, "district_id", None),
                "district_name": getattr(p, "district_name", None) or "-",
                # ── Performance percentage = (correct / assigned) * 100 ──
                "assessment_percentage": pct,
                "score": pct,
                "performance_score": pct,
                # ── Question counts ──
                "assigned_questions": assigned_q,
                "total_questions": assigned_q,
                "correct_questions": correct_q,
                "correct": correct_q,
                "total_correct": correct_q,
                "assessment_questions_correct": correct_q,
                "assessment_questions_attempted": completed_q,
                "completed_questions": completed_q,
                # ── Marks and counts ──
                "obtained_marks": score_val,
                "total_marks": total_marks,
                "total_score": score_val,
                # ── Module completion ──
                "completed_modules": c_mods,
                "completed_modules_count": c_mods,
                "total_assigned_modules": a_mods,
                "total_modules": a_mods,
                "total_modules_count": a_mods,
                "assigned_modules": a_mods,
                "assigned_modules_count": a_mods,
                "module_completion_percentage": mod_pct,
                "course_progress": mod_pct,
                # ── Learning time (displayed on dashboard, NOT used in ranking) ──
                "learning_time_seconds": seconds,
                "learning_time_minutes": round(seconds / 60.0, 1),
                "combined_score": pct,
                "normalized_learning_time_score": 0.0,
            })

        # Final sort by:
        # 1. assessment_percentage DESC
        # 2. assigned_questions DESC
        # 3. correct_questions DESC, then pid ASC
        results.sort(
            key=lambda r: (
                r["assessment_percentage"],
                r["assigned_questions"],
                r["correct_questions"],
                -r["participant_id"],
            ),
            reverse=True,
        )

        for rank, r in enumerate(results, start=1):
            r["rank"] = rank

        return results

    @staticmethod
    def _build_centre_trainee_performance_subquery(db: Session):
        sql = text(
            """
            WITH p_centre AS (
                SELECT bp.participant_id, min(b.centre_id) AS centre_id
                FROM batch_participant bp
                JOIN central_batches b ON b.batch_id = bp.batch_id AND b.deleted_at IS NULL
                WHERE bp.deleted_at IS NULL
                GROUP BY bp.participant_id
            ),
            mcq_perf AS (
                SELECT pm.participant_id,
                       COUNT(CASE WHEN pm.option_selected IS NOT NULL THEN 1 END) AS attempted,
                       COUNT(CASE WHEN mo.is_mcq_option_correct = 1 THEN 1 END) AS correct
                FROM participant_mcqs pm
                LEFT JOIN mcq_question_options mo 
                  ON mo.mcq_option_id = CAST(NULLIF(regexp_replace(pm.option_selected, '[^0-9]', '', 'g'), '') AS BIGINT)
                     AND mo.deleted_at IS NULL
                GROUP BY pm.participant_id
            ),
            scq_perf AS (
                SELECT ps.participant_id,
                       COUNT(CASE WHEN ps.option_selected IS NOT NULL THEN 1 END) AS attempted,
                       COUNT(CASE WHEN so.is_scq_option_correct = 1 THEN 1 END) AS correct
                FROM participant_scs ps
                LEFT JOIN scq_question_options so 
                  ON so.scq_option_id = CAST(NULLIF(regexp_replace(ps.option_selected, '[^0-9]', '', 'g'), '') AS BIGINT)
                     AND so.deleted_at IS NULL
                GROUP BY ps.participant_id
            ),
            trainee_scores AS (
                SELECT p.participant_id,
                       pc.centre_id,
                       (COALESCE(m.attempted, 0) + COALESCE(s.attempted, 0)) AS attempted,
                       (COALESCE(m.correct, 0) + COALESCE(s.correct, 0)) AS correct,
                       CASE 
                           WHEN (COALESCE(m.attempted, 0) + COALESCE(s.attempted, 0)) > 0 
                           THEN ((COALESCE(m.correct, 0) + COALESCE(s.correct, 0))::float / (COALESCE(m.attempted, 0) + COALESCE(s.attempted, 0)) * 100.0)
                           ELSE NULL 
                       END AS score_pct
                FROM participantmasters p
                JOIN p_centre pc ON pc.participant_id = p.participant_id
                LEFT JOIN mcq_perf m ON m.participant_id = p.participant_id
                LEFT JOIN scq_perf s ON s.participant_id = p.participant_id
                WHERE p.deleted_at IS NULL
            )
            SELECT centre_id,
                   COUNT(CASE WHEN attempted > 0 THEN 1 END)::int AS evaluated_trainees,
                   COUNT(CASE WHEN attempted > 0 AND score_pct >= 70.0 THEN 1 END)::int AS good_trainees,
                   COUNT(CASE WHEN attempted > 0 AND score_pct >= 40.0 AND score_pct < 70.0 THEN 1 END)::int AS avg_trainees,
                   COUNT(CASE WHEN attempted > 0 AND score_pct < 40.0 THEN 1 END)::int AS poor_trainees,
                   COALESCE(ROUND(AVG(CASE WHEN attempted > 0 THEN score_pct END)::numeric, 2), 0.0)::float AS avg_trainee_score
            FROM trainee_scores
            GROUP BY centre_id
        """
        )
        return sql.columns(
            Column("centre_id", BigInteger),
            Column("evaluated_trainees", Integer),
            Column("good_trainees", Integer),
            Column("avg_trainees", Integer),
            Column("poor_trainees", Integer),
            Column("avg_trainee_score", Float),
        ).subquery("centre_perf")

    @staticmethod
    def get_centre_leaderboard(
        db: Session,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        last_act = DashboardRepository._build_last_activity_subquery(db)
        p_centre = DashboardRepository._build_distinct_participant_centre_subquery(db)

        # Base active trainees count per centre
        trainee_agg = (
            db.query(
                p_centre.c.centre_id.label("centre_id"),
                func.count(distinct(ParticipantMaster.participant_id)).label(
                    "total_trainees"
                ),
                func.count(distinct(last_act.c.participant_id)).label(
                    "active_trainees"
                ),
            )
            .join(
                ParticipantMaster,
                ParticipantMaster.participant_id == p_centre.c.participant_id,
            )
            .outerjoin(
                last_act, last_act.c.participant_id == ParticipantMaster.participant_id
            )
            .filter(ParticipantMaster.deleted_at.is_(None))
            .group_by(p_centre.c.centre_id)
            .subquery()
        )

        # Time spent per centre
        time_agg = (
            db.query(
                p_centre.c.centre_id.label("centre_id"),
                func.sum(TimeSpentModuleLog.time_taken).label("total_seconds"),
            )
            .join(
                TimeSpentModuleLog,
                TimeSpentModuleLog.user_id == p_centre.c.participant_id,
            )
            .group_by(p_centre.c.centre_id)
            .subquery()
        )

        centre_perf = DashboardRepository._build_centre_trainee_performance_subquery(db)

        query = (
            db.query(
                CentreMaster.centre_id,
                CentreMaster.centre_name,
                CentreMaster.state_id,
                StateMaster.state_name,
                CentreMaster.district_id,
                DistrictMaster.district_name,
                func.coalesce(trainee_agg.c.total_trainees, 0).label("total_trainees"),
                func.coalesce(trainee_agg.c.active_trainees, 0).label(
                    "active_trainees"
                ),
                func.coalesce(centre_perf.c.evaluated_trainees, 0).label(
                    "evaluated_trainees"
                ),
                func.coalesce(centre_perf.c.good_trainees, 0).label("good_trainees"),
                func.coalesce(centre_perf.c.avg_trainees, 0).label("avg_trainees"),
                func.coalesce(centre_perf.c.poor_trainees, 0).label("poor_trainees"),
                func.coalesce(centre_perf.c.avg_trainee_score, 0.0).label(
                    "avg_trainee_score"
                ),
                func.coalesce(time_agg.c.total_seconds, 0).label("total_seconds"),
            )
            .outerjoin(trainee_agg, trainee_agg.c.centre_id == CentreMaster.centre_id)
            .outerjoin(centre_perf, centre_perf.c.centre_id == CentreMaster.centre_id)
            .outerjoin(time_agg, time_agg.c.centre_id == CentreMaster.centre_id)
            .outerjoin(StateMaster, StateMaster.state_lgd_code == CentreMaster.state_id)
            .outerjoin(
                DistrictMaster,
                DistrictMaster.district_code == CentreMaster.district_code,
            )
            .filter(CentreMaster.deleted_at.is_(None))
        )

        if state_id is not None:
            query = query.filter(CentreMaster.state_id == state_id)
        if district_id is not None:
            query = query.filter(DistrictMaster.district_lgd_code == district_id)
        if centre_id is not None:
            query = query.filter(CentreMaster.centre_id == centre_id)

        rows = query.all()

        results = []
        for r in rows:
            eval_trainees = int(r.evaluated_trainees or 0)
            good_cnt = int(r.good_trainees or 0)
            avg_cnt = int(r.avg_trainees or 0)
            poor_cnt = int(r.poor_trainees or 0)
            avg_score = round(float(r.avg_trainee_score or 0.0), 2)

            # Good Performance Rate = (Number of Good-performing trainees / Total evaluated trainees) * 100
            good_perf_rate = (
                round((good_cnt / eval_trainees * 100.0), 2)
                if eval_trainees > 0
                else 0.0
            )
            tot_sec = int(r.total_seconds or 0)

            results.append(
                {
                    "centre_id": r.centre_id,
                    "centre_name": r.centre_name,
                    "state_id": r.state_id,
                    "state_name": r.state_name,
                    "district_id": r.district_id,
                    "district_name": r.district_name,
                    "total_trainees": int(r.total_trainees or 0),
                    "active_trainees": int(r.active_trainees or 0),
                    "evaluated_trainees": eval_trainees,
                    "good_trainees": good_cnt,
                    "average_trainees": avg_cnt,
                    "poor_trainees": poor_cnt,
                    "good_performance_rate": good_perf_rate,
                    "average_trainee_score": avg_score,
                    "completion_rate_pct": avg_score,
                    "completion_rate": avg_score,
                    "total_time_spent_seconds": tot_sec,
                    "total_time_spent_minutes": round(tot_sec / 60.0, 1),
                    "total_score": good_cnt,
                    "total_questions": eval_trainees,
                    "assessment_percentage": avg_score,
                    "combined_score": avg_score,
                }
            )

        # Rank centres by:
        # 1. Average trainee score DESC
        # 2. Good Performance Rate DESC
        # 3. Total evaluated trainees DESC
        # 4. Total active trainees DESC
        results.sort(
            key=lambda item: (
                item["average_trainee_score"],
                item["good_performance_rate"],
                item["evaluated_trainees"],
                item["active_trainees"],
            ),
            reverse=True,
        )

        for rank_idx, item in enumerate(results, 1):
            item["rank"] = rank_idx

        if limit is not None and limit > 0:
            results = results[:limit]

        return results
