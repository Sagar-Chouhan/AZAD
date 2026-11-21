import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from app.database.database import Base


class AuditLog(Base):
    __tablename__ = "system_activity_log"
    __table_args__ = {"schema": "mis_azad"}

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("mis_azad.lms_user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    user_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    role_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    entity = synonym("resource_type")

    resource_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    entity_id = synonym("resource_id")

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    details = synonym("description")

    source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default="web",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User")

    @property
    def user_email(self) -> str:
        if self.user and getattr(self.user, "email", None):
            return self.user.email
        return self.user_name or ""

    @user_email.setter
    def user_email(self, value: str):
        if not self.user_name:
            self.user_name = value
