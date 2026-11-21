from types import SimpleNamespace
from typing import Optional

from sqlalchemy import String, and_, case, cast, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.modules.assessment.model import AssessmentMapping
from app.modules.mobile.module.constants import (
    DOC_TYPE_PDF,
    DOC_TYPE_PPT,
    DOC_TYPE_VIDEO,
    MAPPING_ACTIVE_STATUS,
)
from app.modules.mobile.module.model import (
    DocumentMaster,
    ModuleMaster,
    PdfMaster,
    PptMaster,
    PreSessionAssessment,
    SelfPacedLearning,
    TopicMapping,
    TopicMaster,
    VideoMaster,
)


class TopicRepository:
    """
    Database access for the topics and documents that sit inside a module.
    """

    @staticmethod
    def get_parent_module_id(
        db: Session,
        module_id: int,
    ) -> Optional[int]:
        """
        topic_mapping is only populated for the canonical module of each
        language group, which is module_masters.parent_id.
        """

        return (
            db.query(ModuleMaster.parent_id)
            .filter(
                ModuleMaster.module_id == module_id,
                ModuleMaster.deleted_at.is_(None),
            )
            .scalar()
        )

    @staticmethod
    def get_module_overview(db: Session, module_id: int):
        """
        The module's own content — what the LMS calls the main content of the
        module — shown above its topic list.
        """

        parent_id = TopicRepository.get_parent_module_id(db, module_id) or module_id

        row = (
            db.query(
                ModuleMaster.module_id,
                ModuleMaster.module_name,
                ModuleMaster.module_description,
                ModuleMaster.module_overview,
                ModuleMaster.module_objective,
                cast(ModuleMaster.module_duration, String).label("duration"),
                cast(ModuleMaster.module_type, String).label("module_type"),
                ModuleMaster.module_icon,
                ModuleMaster.icon_images,
                ModuleMaster.main_content_of_the_module,
                ModuleMaster.post_session_assessment,
                ModuleMaster.self_paced_learning,
                ModuleMaster.pre_session_assessment,
            )
            .filter(
                ModuleMaster.module_id == module_id,
                ModuleMaster.deleted_at.is_(None),
            )
            .first()
        )

        if row is None:
            return None

        # Dynamically check if self_paced_learning has active items
        has_spl = (
            row.self_paced_learning == 1
            or db.query(SelfPacedLearning.self_paced_learning_id)
            .filter(
                SelfPacedLearning.module_id == parent_id,
                SelfPacedLearning.listing_type == "self",
                SelfPacedLearning.is_active == 1,
            )
            .first()
            is not None
        )

        # Dynamically check if pre_session_assessment has active questions mapped
        has_pre = (
            row.pre_session_assessment == 1
            or db.query(PreSessionAssessment.assessment_id)
            .join(
                AssessmentMapping,
                AssessmentMapping.assessment_id == PreSessionAssessment.assessment_id,
            )
            .filter(
                PreSessionAssessment.module_id == parent_id,
                PreSessionAssessment.is_active == 1,
                AssessmentMapping.is_active == 1,
            )
            .first()
            is not None
        )

        return SimpleNamespace(
            module_id=row.module_id,
            module_name=row.module_name,
            module_description=row.module_description,
            module_overview=row.module_overview,
            module_objective=row.module_objective,
            duration=row.duration,
            module_type=row.module_type,
            module_icon=row.module_icon,
            icon_images=row.icon_images,
            main_content_of_the_module=row.main_content_of_the_module,
            post_session_assessment=row.post_session_assessment,
            has_self_paced_learning=has_spl,
            has_pre_assessment=has_pre,
        )

    @staticmethod
    def list_module_topics(
        db: Session,
        parent_module_id: int,
        language_id: int,
    ):
        """
        Compulsory topics of a module with the document attached to each one.
        Filters out optional self-paced learning items.
        """

        base_doc = aliased(DocumentMaster)

        base_ref_id = (
            select(base_doc.doc_ref_id)
            .where(base_doc.doc_id == TopicMapping.doc_id)
            .limit(1)
            .scalar_subquery()
        )

        video_id = case(
            (
                DocumentMaster.doc_type == DOC_TYPE_VIDEO,
                func.coalesce(DocumentMaster.doc_ref_id, base_ref_id),
            ),
            else_=None,
        ).label("video_id")

        return (
            db.query(
                TopicMaster.topic_id,
                TopicMaster.topic_name,
                DocumentMaster.doc_id,
                DocumentMaster.doc_title,
                DocumentMaster.doc_type,
                cast(
                    DocumentMaster.doc_duration,
                    String,
                ).label("doc_duration"),
                DocumentMaster.doc_image,
                DocumentMaster.doc_file,
                PdfMaster.pdf_url,
                PptMaster.ppt_url,
                video_id,
                VideoMaster.video_url,
                VideoMaster.youtube_url,
            )
            .select_from(TopicMapping)
            .join(
                TopicMaster,
                and_(
                    TopicMaster.parent_id == TopicMapping.topic_id,
                    TopicMaster.language_id == language_id,
                    TopicMaster.is_active == "1",
                ),
            )
            .outerjoin(
                DocumentMaster,
                and_(
                    DocumentMaster.parent_id == TopicMapping.doc_id,
                    DocumentMaster.language_id == language_id,
                    DocumentMaster.deleted_at.is_(None),
                ),
            )
            .outerjoin(
                PdfMaster,
                and_(
                    DocumentMaster.doc_type == DOC_TYPE_PDF,
                    PdfMaster.pdf_id == DocumentMaster.doc_ref_id,
                ),
            )
            .outerjoin(
                PptMaster,
                and_(
                    DocumentMaster.doc_type == DOC_TYPE_PPT,
                    PptMaster.ppt_id == DocumentMaster.doc_ref_id,
                ),
            )
            .outerjoin(
                VideoMaster,
                and_(
                    DocumentMaster.doc_type == DOC_TYPE_VIDEO,
                    VideoMaster.video_id == DocumentMaster.doc_ref_id,
                ),
            )
            .outerjoin(
                SelfPacedLearning,
                and_(
                    SelfPacedLearning.module_id == TopicMapping.module_id,
                    SelfPacedLearning.topic_id == TopicMapping.topic_id,
                    SelfPacedLearning.doc_id == TopicMapping.doc_id,
                ),
            )
            .filter(
                TopicMapping.module_id == parent_module_id,
                TopicMapping.status == MAPPING_ACTIVE_STATUS,
                or_(
                    SelfPacedLearning.self_paced_learning_id.is_(None),
                    SelfPacedLearning.is_active == 1,
                ),
                or_(
                    SelfPacedLearning.listing_type.is_(None),
                    SelfPacedLearning.listing_type != "self",
                ),
            )
            .order_by(TopicMapping.topic_mapping_id)
            .all()
        )

    @staticmethod
    def list_self_paced_topics(
        db: Session,
        parent_module_id: int,
        language_id: int,
    ):
        """
        Optional self-paced learning topics of a module.
        """

        base_doc = aliased(DocumentMaster)

        base_ref_id = (
            select(base_doc.doc_ref_id)
            .where(base_doc.doc_id == TopicMapping.doc_id)
            .limit(1)
            .scalar_subquery()
        )

        video_id = case(
            (
                DocumentMaster.doc_type == DOC_TYPE_VIDEO,
                func.coalesce(DocumentMaster.doc_ref_id, base_ref_id),
            ),
            else_=None,
        ).label("video_id")

        return (
            db.query(
                TopicMaster.topic_id,
                TopicMaster.topic_name,
                DocumentMaster.doc_id,
                DocumentMaster.doc_title,
                DocumentMaster.doc_type,
                cast(
                    DocumentMaster.doc_duration,
                    String,
                ).label("doc_duration"),
                DocumentMaster.doc_image,
                DocumentMaster.doc_file,
                PdfMaster.pdf_url,
                PptMaster.ppt_url,
                video_id,
                VideoMaster.video_url,
                VideoMaster.youtube_url,
            )
            .select_from(TopicMapping)
            .join(
                TopicMaster,
                and_(
                    TopicMaster.parent_id == TopicMapping.topic_id,
                    TopicMaster.language_id == language_id,
                    TopicMaster.is_active == "1",
                ),
            )
            .outerjoin(
                DocumentMaster,
                and_(
                    DocumentMaster.parent_id == TopicMapping.doc_id,
                    DocumentMaster.language_id == language_id,
                    DocumentMaster.deleted_at.is_(None),
                ),
            )
            .outerjoin(
                PdfMaster,
                and_(
                    DocumentMaster.doc_type == DOC_TYPE_PDF,
                    PdfMaster.pdf_id == DocumentMaster.doc_ref_id,
                ),
            )
            .outerjoin(
                PptMaster,
                and_(
                    DocumentMaster.doc_type == DOC_TYPE_PPT,
                    PptMaster.ppt_id == DocumentMaster.doc_ref_id,
                ),
            )
            .outerjoin(
                VideoMaster,
                and_(
                    DocumentMaster.doc_type == DOC_TYPE_VIDEO,
                    VideoMaster.video_id == DocumentMaster.doc_ref_id,
                ),
            )
            .join(
                SelfPacedLearning,
                and_(
                    SelfPacedLearning.module_id == TopicMapping.module_id,
                    SelfPacedLearning.topic_id == TopicMapping.topic_id,
                    SelfPacedLearning.doc_id == TopicMapping.doc_id,
                    SelfPacedLearning.listing_type == "self",
                    SelfPacedLearning.is_active == 1,
                ),
            )
            .filter(
                TopicMapping.module_id == parent_module_id,
                TopicMapping.status == MAPPING_ACTIVE_STATUS,
            )
            .order_by(TopicMapping.topic_mapping_id)
            .all()
        )
