from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from app.database.database import Base
from app.modules.master.state.model import StateMaster


class DistrictMaster(Base):
    __tablename__ = "central_districts"
    __table_args__ = {"schema": "mis_azad"}

    id: Mapped[int] = mapped_column(
        "id",
        Integer,
        primary_key=True,
        index=True,
    )
    district_id = synonym("id")
    district_lgd_code = synonym("id")

    district_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    district_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    state_lgd_code: Mapped[int] = mapped_column(
        "state_id",
        Integer,
        ForeignKey("mis_azad.central_states.id"),
        nullable=False,
        index=True,
    )
    state_id = synonym("state_lgd_code")

    state_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    short_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Active",
    )

    state: Mapped["StateMaster"] = relationship(
        "StateMaster",
        back_populates="districts",
    )
