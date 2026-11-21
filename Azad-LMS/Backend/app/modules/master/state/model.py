from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from app.database.database import Base


class StateMaster(Base):
    __tablename__ = "central_states"
    __table_args__ = {"schema": "mis_azad"}

    id: Mapped[int] = mapped_column(
        "id",
        Integer,
        primary_key=True,
        index=True,
    )
    state_lgd_code = synonym("id")
    state_id = synonym("id")

    state_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    state_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
    )

    short_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    districts = relationship(
        "DistrictMaster",
        back_populates="state",
    )
