with open("Backend/app/modules/dashboard/repository.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update get_state_wise_participants
old_state_part = """    @staticmethod
    def get_state_wise_participants(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ):

        query = (
            db.query(
                StateMaster.state_lgd_code.label("state_id"),
                StateMaster.state_name,
                func.count(distinct(ParticipantMaster.participant_id)).label(
                    "total"
                ),
            )
            .select_from(ParticipantMaster)
            .join(
                StateMaster,
                StateMaster.state_lgd_code == ParticipantMaster.state_id,
            )
            .filter(ParticipantMaster.deleted_at.is_(None))
        )"""

new_state_part = """    @staticmethod
    def get_state_wise_participants(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ):
        p_centre = DashboardRepository._build_distinct_participant_centre_subquery(db)
        query = (
            db.query(
                StateMaster.state_lgd_code.label("state_id"),
                StateMaster.state_name,
                func.count(distinct(ParticipantMaster.participant_id)).label(
                    "total"
                ),
            )
            .select_from(ParticipantMaster)
            .join(
                p_centre,
                p_centre.c.participant_id == ParticipantMaster.participant_id,
            )
            .join(
                CentreMaster,
                and_(
                    CentreMaster.centre_id == p_centre.c.centre_id,
                    CentreMaster.deleted_at.is_(None),
                ),
            )
            .join(
                StateMaster,
                StateMaster.state_lgd_code == CentreMaster.state_id,
            )
            .filter(ParticipantMaster.deleted_at.is_(None))
        )"""

code = code.replace(old_state_part.replace("\n", "\r\n"), new_state_part.replace("\n", "\r\n"))
code = code.replace(old_state_part, new_state_part)

# 2. Update get_state_wise_trainees
old_state_trainees = """    @staticmethod
    def get_state_wise_trainees(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ):
        query = (
            db.query(
                StateMaster.state_lgd_code.label("state_id"),
                StateMaster.state_name,
                func.count(distinct(ParticipantMaster.participant_id)).label(
                    "total_trainees"
                ),
            )
            .select_from(ParticipantMaster)
            .join(
                StateMaster,
                StateMaster.state_lgd_code == ParticipantMaster.state_id,
            )
            .filter(ParticipantMaster.deleted_at.is_(None))
        )

        if state_id is not None:
            query = query.filter(ParticipantMaster.state_id == state_id)

        if district_id is not None:
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
        )"""

new_state_trainees = """    @staticmethod
    def get_state_wise_trainees(
        db: Session,
        state_id=None,
        district_id=None,
        centre_id=None,
        from_date=None,
        to_date=None,
    ):
        p_centre = DashboardRepository._build_distinct_participant_centre_subquery(db)
        query = (
            db.query(
                StateMaster.state_lgd_code.label("state_id"),
                StateMaster.state_name,
                func.count(distinct(ParticipantMaster.participant_id)).label(
                    "total_trainees"
                ),
            )
            .select_from(ParticipantMaster)
            .join(
                p_centre,
                p_centre.c.participant_id == ParticipantMaster.participant_id,
            )
            .join(
                CentreMaster,
                and_(
                    CentreMaster.centre_id == p_centre.c.centre_id,
                    CentreMaster.deleted_at.is_(None),
                ),
            )
            .join(
                StateMaster,
                StateMaster.state_lgd_code == CentreMaster.state_id,
            )
            .filter(ParticipantMaster.deleted_at.is_(None))
        )

        if state_id is not None:
            query = query.filter(CentreMaster.state_id == state_id)

        if district_id is not None:
            query = query.filter(CentreMaster.district_id == district_id)

        if centre_id is not None:
            query = query.filter(CentreMaster.centre_id == centre_id)

        query = DashboardRepository._apply_date_filter(
            query,
            ParticipantMaster,
            from_date,
            to_date,
        )"""

code = code.replace(old_state_trainees.replace("\n", "\r\n"), new_state_trainees.replace("\n", "\r\n"))
code = code.replace(old_state_trainees, new_state_trainees)

with open("Backend/app/modules/dashboard/repository.py", "w", encoding="utf-8", newline="\r\n") as f:
    f.write(code)

print("repository.py updated state queries successfully")

