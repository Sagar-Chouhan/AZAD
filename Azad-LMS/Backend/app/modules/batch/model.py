from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Integer,
    String,
    ForeignKey,
    text,
)
from sqlalchemy.orm import relationship, synonym

from app.database.database import Base


class BatchMaster(Base):
    __tablename__ = "central_batches"
    __table_args__ = {"schema": "mis_azad"}

    batch_id = Column(BigInteger, primary_key=True, index=True)
    batch_name = Column(String(255), nullable=False)

    mis_batch_id = Column("www_batch_id", BigInteger, nullable=True)
    www_batch_id = synonym("mis_batch_id")
    lms_batch_id = Column("lms_batch_id", Integer, nullable=True)

    centre_id = Column(
        BigInteger, ForeignKey("mis_azad.central_centres.id"), nullable=False
    )
    status = Column(Integer, nullable=False)

    created_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    deleted_at = Column(DateTime)

    created_by = Column(BigInteger, nullable=False)

    fy_year = Column("financial_year", String(20), nullable=False)
    financial_year = synonym("fy_year")

    participants = relationship("BatchParticipant", back_populates="batch")


class BatchParticipant(Base):
    __tablename__ = "batch_participant"
    __table_args__ = {"schema": "mis_azad"}

    batch_participant_id = Column(
        BigInteger,
        primary_key=True,
        index=True,
    )

    batch_id = Column(
        BigInteger, ForeignKey("mis_azad.central_batches.batch_id"), nullable=False
    )
    participant_id = Column(
        BigInteger, ForeignKey("mis_azad.participantmasters.participant_id"), nullable=False
    )

    created_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    deleted_at = Column(DateTime)

    # Relationships
    batch = relationship("BatchMaster", back_populates="participants")
    participant = relationship("ParticipantMaster", back_populates="batches")
