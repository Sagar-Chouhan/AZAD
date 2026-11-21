import csv
import io
from fastapi import HTTPException, status
from datetime import date

from sqlalchemy.orm import Session
from app.modules.users.service import UserService
from app.modules.users.participant_images import deduplicate_participant_images

from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.constants import (
    AVERAGE_PERCENTAGE,
    GOOD_PERCENTAGE,
)


def _dashboard_image_url(stored_image, participant_id=None):
    """Return the public URL path for a participant's stored image."""
    if stored_image and isinstance(stored_image, str):
        image = stored_image.strip().lstrip("/")
        if image.lower().startswith(("http://", "https://", "blob:", "data:")):
            return image

        if image.lower().startswith("app/"):
            image = image[4:]
        if image.lower().startswith("uploads/participants/"):
            image = image[21:]
        elif image.lower().startswith("participants/"):
            image = image[13:]
        elif image.lower().startswith("uploads/"):
            image = image[8:]

        if image and not image.lower().startswith("img_"):
            return image

    return None


def _normalize_dashboard_images(items):
    for item in items:
        pid = item.get("participant_id") or item.get("id") or item.get("user_id")
        item["image"] = _dashboard_image_url(item.get("image"), pid)
    return deduplicate_participant_images(items)


# Trainee performance categories, in display order. Keys match the frontend
# donut colour map (DONUT_STATUS); labels come from get_participants.
_TRAINEE_STATUS_ORDER = [
    ("YetToStart", "Yet to Start"),
    ("Poor", "Poor"),
    ("Average", "Average"),
    ("Good", "Good"),
]


def _trainee_status_rows(db, state_id=None, district_id=None, centre_id=None):
    """Per-trainee list with the same performance category the participants
    list uses (Yet to Start / Poor / Average / Good). Imported locally to
    avoid a circular import with the users module."""

    return UserService.get_participants(
        db=db,
        state_id=state_id,
        district_id=district_id,
        centre_id=centre_id,
    )


_STATUS_LOOKUP = {
    "yet to start": "YetToStart",
    "yettostart": "YetToStart",
    "poor": "Poor",
    "average": "Average",
    "good": "Good",
}


def _trainee_status_summary(rows):
    """Return overall counts grouped by trainee performance status."""
    counts = {key: 0 for key, _ in _TRAINEE_STATUS_ORDER}

    for row in rows:
        raw_status = (
            str(row.get("performance_status") or "Yet to Start").strip().casefold()
        )
        status_key = _STATUS_LOOKUP.get(raw_status)

        if status_key:
            counts[status_key] += 1

    return [
        {"status": key, "label": label, "total": counts[key]}
        for key, label in _TRAINEE_STATUS_ORDER
    ]


def _state_wise_trainee_status_summary(rows):
    """Return trainee counts grouped by state and performance status."""
    grouped = {}

    for row in rows:
        state_name = str(row.get("state_name") or "").strip()
        if not state_name:
            continue

        raw_status = (
            str(row.get("performance_status") or "Yet to Start").strip().casefold()
        )
        status_key = _STATUS_LOOKUP.get(raw_status)

        if not status_key:
            continue

        key = (state_name, status_key)
        grouped[key] = grouped.get(key, 0) + 1

    status_order = {key: index for index, (key, _) in enumerate(_TRAINEE_STATUS_ORDER)}
    labels = dict(_TRAINEE_STATUS_ORDER)

    details = [
        {
            "state_name": state_name,
            "status": status_key,
            "label": labels[status_key],
            "total": total,
        }
        for (state_name, status_key), total in sorted(
            grouped.items(),
            key=lambda item: (
                item[0][0].casefold(),
                status_order[item[0][1]],
            ),
        )
    ]
    return details


class DashboardService:

    @staticmethod
    def get_state_wise_trainee_status(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
    ):
        """Return state-wise counts for the stacked Trainee Status chart."""
        rows = _trainee_status_rows(
            db=db,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
        )
        return _state_wise_trainee_status_summary(rows)

    @staticmethod
    def get_trainee_status_details(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
    ):
        """Individual trainees with their performance status (for the
        Trainee Status chart's detail modal)."""
        rows = _trainee_status_rows(db, state_id, district_id, centre_id)
        return [
            {
                "participant_id": r.get("participant_id"),
                "participant_name": r.get("participant_name"),
                "mobile_no": r.get("mobile_no"),
                "enrollment_no": r.get("enrollment_no"),
                "image": _dashboard_image_url(r.get("image")),
                "age": r.get("age"),
                "state_name": r.get("state_name"),
                "district_name": r.get("district_name"),
                "centre_name": r.get("centre_name"),
                "course_progress": r.get("course_progress"),
                "performance_status": r.get("performance_status"),
            }
            for r in rows
        ]
        return deduplicate_participant_images(details)

    @staticmethod
    def get_dashboard_summary(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ):

        total_centres = DashboardRepository.get_total_centres(
            db=db,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
        )

        total_participants = DashboardRepository.get_total_participants(
            db=db,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

        active_participants = DashboardRepository.get_active_participants(
            db=db,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

        total_courses = DashboardRepository.get_total_courses(db)

        total_modules = DashboardRepository.get_total_modules(db)

        total_batches = DashboardRepository.get_total_batches(
            db=db,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
        )

        gender_distribution = DashboardRepository.get_gender_distribution(
            db=db,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

        total_documents = DashboardRepository.get_total_documents(db)

        total_assessments = DashboardRepository.get_total_assessments(db)

        completion_rate = (
            round(
                (active_participants / total_participants) * 100,
                2,
            )
            if total_participants
            else 0
        )

        monthly_login_trend = DashboardRepository.get_monthly_login_trend(
            db=db,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

        age_group_distribution = DashboardRepository.get_age_group_distribution(
            db=db,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

        # -----------------------------
        # State-wise Participants
        # -----------------------------
        state_wise_participants = DashboardRepository.get_state_wise_participants(
            db=db,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

        district_wise_participants = DashboardRepository.get_district_wise_participants(
            db=db,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

        module_lock_status = DashboardRepository.get_module_lock_status(
            db=db,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

        module_wise_performance = (
            DashboardRepository.get_module_wise_performance_details(
                db=db,
                state_id=state_id,
                district_id=district_id,
                centre_id=centre_id,
                from_date=from_date,
                to_date=to_date,
            )
        )
        document_type_distribution = DashboardRepository.get_document_type_distribution(
            db
        )

        # -----------------------------
        # State-wise Centres
        # -----------------------------
        state_wise_centres = DashboardRepository.get_state_wise_centres(
            db=db,
        )

        trainee_status = _trainee_status_summary(
            _trainee_status_rows(db, state_id, district_id, centre_id)
        )

        return {
            "summary": {
                "total_centres": total_centres,
                "total_participants": total_participants,
                "active_participants": active_participants,
                "total_courses": total_courses,
                "total_modules": total_modules,
                "total_batches": total_batches,
                "total_documents": total_documents,
                "total_assessments": total_assessments,
                "completion_rate": completion_rate,
            },
            "trainee_status": trainee_status,
            "state_wise_participants": [
                {
                    "state_id": row.state_id,
                    "state_name": row.state_name,
                    "total": row.total,
                }
                for row in state_wise_participants
            ],
            "state_wise_centres": [
                {
                    "state_id": row.state_id,
                    "state_name": row.state_name,
                    "total": row.total,
                }
                for row in state_wise_centres
            ],
            "gender_distribution": [
                {
                    "gender": row.gender,
                    "total": row.total,
                }
                for row in gender_distribution
            ],
            "monthly_login_trend": [
                {
                    "month": row.month,
                    "total": row.total,
                }
                for row in monthly_login_trend
            ],
            "age_group_distribution": [
                {
                    "age_group": row.age_group,
                    "total": row.total,
                }
                for row in age_group_distribution
            ],
            "document_type_distribution": [
                {
                    "doc_type": row.doc_type,
                    "total": row.total,
                }
                for row in document_type_distribution
            ],
            "district_wise_participants": [  # ✅ Add it here
                {
                    "district_name": row.district_name,
                    "total": row.total,
                }
                for row in district_wise_participants
            ],
            "module_lock_status": [
                {
                    "lock_status": row.lock_status,
                    "total": row.total,
                }
                for row in module_lock_status
            ],
            "module_wise_performance": [
                {
                    "module_name": row.module_name,
                    "total": row.total,
                }
                for row in module_wise_performance
            ],
        }

    @staticmethod
    def get_state_wise_participants(
        db: Session,
        clicked_value=None,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ):
        return DashboardRepository.get_state_wise_participant_details(
            db=db,
            clicked_value=clicked_value,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

    @staticmethod
    def get_district_wise_participants(
        db: Session,
        clicked_value: str | None = None,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        return DashboardRepository.get_district_wise_participant_details(
            db=db,
            clicked_value=clicked_value,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

    @staticmethod
    def get_gender_distribution(
        db: Session,
        clicked_value: str | None = None,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        return DashboardRepository.get_gender_distribution_details(
            db=db,
            clicked_value=clicked_value,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

    @staticmethod
    def get_age_group_distribution(
        db: Session,
        clicked_value: str | None = None,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        return DashboardRepository.get_age_group_distribution_details(
            db=db,
            clicked_value=clicked_value,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

    @staticmethod
    def get_state_wise_centres(
        db: Session,
        clicked_value: str | None = None,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        return DashboardRepository.get_state_wise_centre_details(
            db=db,
            clicked_value=clicked_value,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

    @staticmethod
    def get_module_wise_performance_details(
        db: Session,
        clicked_value: str | None = None,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        return DashboardRepository.get_module_wise_performance_details(
            db=db,
            clicked_value=clicked_value,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

    @staticmethod
    def get_monthly_trending_modules(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ):
        rows = DashboardRepository.get_monthly_trending_modules(
            db=db,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

        return [
            {
                "month": row.month,
                "module_id": row.module_id,
                "module_name": row.module_name,
                "total": row.total,
            }
            for row in rows
        ]

    @staticmethod
    def get_module_assignment_usage(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
    ):
        rows = DashboardRepository.get_module_assignment_usage(
            db=db,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
        )

        return [
            {
                "module_id": row.module_id,
                "module_name": row.module_name,
                "total_assigned": row.total_assigned,
            }
            for row in rows
        ]

    @staticmethod
    def get_document_type_distribution(db: Session):
        return DashboardRepository.get_document_type_distribution_details(db=db)

    @staticmethod
    def get_monthly_logins(
        db: Session,
        clicked_value: str | None = None,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        return DashboardRepository.get_monthly_login_trend(
            db=db,
            clicked_value=clicked_value,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

    @staticmethod
    def get_monthly_login_details(
        db: Session,
        clicked_value: str,
        state_id: int | None = None,
        district_id: int | None = None,
        centre_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ):
        return DashboardRepository.get_monthly_login_details(
            db=db,
            clicked_value=clicked_value,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

    @staticmethod
    def get_centre_wise_trainees(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ):
        rows = DashboardRepository.get_centre_wise_trainees(
            db=db,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

        return [
            {
                "state_id": row.state_id,
                "state_name": row.state_name,
                "centre_id": row.centre_id,
                "centre_name": row.centre_name,
                "district_name": row.district_name,
                "total_trainees": row.total_trainees,
            }
            for row in rows
        ]

    @staticmethod
    def get_state_wise_trainees(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ):
        rows = DashboardRepository.get_state_wise_trainees(
            db=db,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

        return [
            {
                "state_id": row.state_id,
                "state_name": row.state_name,
                "total_trainees": row.total_trainees,
            }
            for row in rows
        ]

    @staticmethod
    def get_need_attention_summary(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ) -> dict:
        summary_data = DashboardRepository.get_need_attention_summary(
            db=db,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )
        return {
            "success": True,
            "data": summary_data,
        }

    @staticmethod
    def get_need_attention_learners(
        db: Session,
        learner_type: str,
        page: int = 1,
        page_size: int = 20,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
        search=None,
    ) -> dict:
        valid_types = ("never_logged_in", "inactive_30d")
        if learner_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid type '{learner_type}'. Supported types are 'never_logged_in' and 'inactive_30d'.",
            )

        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="page must be an integer greater than or equal to 1.",
            )

        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="page_size must be between 1 and 100.",
            )

        items, total = DashboardRepository.get_need_attention_learners(
            db=db,
            learner_type=learner_type,
            page=page,
            page_size=page_size,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
            search=search,
        )
        _normalize_dashboard_images(items)

        total_pages = (total + page_size - 1) // page_size if total else 0

        return {
            "success": True,
            "data": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
            },
        }

    @staticmethod
    def get_recent_learners(
        db: Session,
        limit: int = 5,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ) -> dict:
        if limit < 1 or limit > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="limit must be an integer between 1 and 50.",
            )

        items = DashboardRepository.get_recent_learners(
            db=db,
            limit=limit,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )
        _normalize_dashboard_images(items)

        return {
            "success": True,
            "data": items,
        }

    @staticmethod
    def get_learner_activity_detail(
        db: Session,
        participant_id: int,
    ) -> dict:
        detail = DashboardRepository.get_learner_activity_detail(
            db=db,
            participant_id=participant_id,
        )
        if not detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trainee with ID {participant_id} not found.",
            )
        detail["image"] = _dashboard_image_url(detail.get("image"))
        return {
            "success": True,
            "data": detail,
        }

    @staticmethod
    def export_need_attention_learners_csv(
        db: Session,
        learner_type: str,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ) -> str:
        valid_types = ("never_logged_in", "inactive_30d")
        if learner_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid type '{learner_type}'. Supported types are 'never_logged_in' and 'inactive_30d'.",
            )

        items, _ = DashboardRepository.get_need_attention_learners(
            db=db,
            learner_type=learner_type,
            page=1,
            page_size=100000,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Trainee ID",
                "Trainee Name",
                "Enrollment No",
                "Centre Name",
                "State",
                "District",
                "Registration Date",
                "Last Activity Time",
                "Days Inactive",
            ]
        )

        for item in items:
            reg_date = item.get("registration_date")
            act_date = item.get("last_activity_time")
            writer.writerow(
                [
                    item.get("participant_id"),
                    item.get("participant_name"),
                    item.get("enrollment_no") or "",
                    item.get("centre_name") or "",
                    item.get("state_name") or "",
                    item.get("district_name") or "",
                    reg_date.strftime("%Y-%m-%d %H:%M:%S") if reg_date else "",
                    act_date.strftime("%Y-%m-%d %H:%M:%S") if act_date else "",
                    (
                        item.get("days_inactive")
                        if item.get("days_inactive") is not None
                        else ""
                    ),
                ]
            )

        return output.getvalue()

    @staticmethod
    def get_top_learners(
        db: Session,
        limit: int = 10,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ) -> dict:
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="limit must be an integer between 1 and 100.",
            )
        items = DashboardRepository.get_top_learners(
            db=db,
            limit=limit,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
        )
        _normalize_dashboard_images(items)
        return {"success": True, "data": items}

    # @staticmethod
    # def get_centre_leaderboard(

    #     db: Session,
    #     state_id=None,
    #     district_id=None,
    #     centre_id=None,
    #     from_date=None,
    #     to_date=None,
    #     limit=None,
    # ) -> dict:
    #     items = DashboardRepository.get_centre_leaderboard(
    #         db=db,
    #         state_id=state_id,
    #         district_id=district_id,
    #         centre_id=centre_id,
    #         from_date=from_date,
    #         to_date=to_date,
    #         limit=limit,
    #     )
    #     return {
    #         "success": True,
    #         "data": items,
    #     }

    @staticmethod
    def get_centre_leaderboard(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
        limit=None,
    ) -> dict:
        items = DashboardRepository.get_centre_leaderboard(
            db=db,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
            from_date=from_date,
            to_date=to_date,
            limit=None,
        )

        # Fetch exact report-level trainee status (Good / Average / Poor / Yet to Start)
        participant_rows = _trainee_status_rows(
            db=db,
            state_id=state_id,
            district_id=district_id,
            centre_id=centre_id,
        )

        evaluated_pids = [
            int(r["participant_id"])
            for r in participant_rows
            if r.get("participant_id") is not None
            and _STATUS_LOOKUP.get(
                str(r.get("performance_status") or "Yet to Start").strip().casefold(),
                "YetToStart",
            )
            != "YetToStart"
        ]
        report_scores = DashboardRepository._compute_view_report_scores_batch(
            db, evaluated_pids
        )

        # Group participants by centre_id (fallback to centre_name)
        by_centre_id: dict[int, list[dict]] = {}
        by_centre_name: dict[str, list[dict]] = {}
        for r in participant_rows:
            cid = r.get("centre_id")
            if cid is not None:
                by_centre_id.setdefault(int(cid), []).append(r)
            cname = str(r.get("centre_name") or "").strip().casefold()
            if cname:
                by_centre_name.setdefault(cname, []).append(r)

        for item in items:
            cid = item.get("centre_id")
            cname = str(item.get("centre_name") or "").strip().casefold()
            trainees = (
                by_centre_id.get(int(cid))
                if cid is not None and int(cid) in by_centre_id
                else by_centre_name.get(cname, [])
            )

            good_cnt = 0
            avg_cnt = 0
            poor_cnt = 0
            yet_cnt = 0
            scores: list[float] = []

            for t in trainees:
                raw_status = (
                    str(t.get("performance_status") or "Yet to Start")
                    .strip()
                    .casefold()
                )
                status_key = _STATUS_LOOKUP.get(raw_status, "YetToStart")

                if status_key == "Good":
                    good_cnt += 1
                elif status_key == "Average":
                    avg_cnt += 1
                elif status_key == "Poor":
                    poor_cnt += 1
                else:
                    yet_cnt += 1
                    continue

                pid = t.get("participant_id")
                pct = (
                    report_scores.get(int(pid), {}).get("assessment_percentage")
                    if pid is not None
                    else None
                )
                if pct is None:
                    pct = float(t.get("course_progress") or 0.0)
                scores.append(float(pct))

            evaluated = good_cnt + avg_cnt + poor_cnt
            avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
            good_perf_rate = (
                round((good_cnt / evaluated) * 100.0, 2) if evaluated > 0 else 0.0
            )

            if evaluated == 0:
                perf_status = "Yet to Start"
            elif avg_score >= GOOD_PERCENTAGE:
                perf_status = "Good"
            elif avg_score >= AVERAGE_PERCENTAGE:
                perf_status = "Average"
            else:
                perf_status = "Poor"

            item["evaluated_trainees"] = evaluated
            item["good_trainees"] = good_cnt
            item["average_trainees"] = avg_cnt
            item["poor_trainees"] = poor_cnt
            item["yet_to_start_trainees"] = yet_cnt
            item["good_performance_rate"] = good_perf_rate
            item["average_trainee_score"] = avg_score
            item["assessment_percentage"] = avg_score
            item["completion_rate_pct"] = avg_score
            item["completion_rate"] = avg_score
            item["combined_score"] = avg_score
            item["total_score"] = good_cnt
            item["total_questions"] = evaluated
            item["performance_status"] = perf_status

        items.sort(
            key=lambda item: (
                item["average_trainee_score"],
                item["good_performance_rate"],
                item["evaluated_trainees"],
                item["active_trainees"],
            ),
            reverse=True,
        )

        for rank_idx, item in enumerate(items, 1):
            item["rank"] = rank_idx

        if limit is not None and limit > 0:
            items = items[:limit]

        return {
            "success": True,
            "data": items,
        }
