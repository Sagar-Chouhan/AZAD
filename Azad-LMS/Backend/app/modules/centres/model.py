from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Integer,
    String,
    text,
    literal,
)
from sqlalchemy.orm import synonym
from sqlalchemy.ext.hybrid import hybrid_property

from app.database.database import Base


class CentreMaster(Base):
    __tablename__ = "central_centres"
    __table_args__ = {"schema": "mis_azad"}

    centre_id = Column(
        "id",
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    id = synonym("centre_id")

    mis_center_id = Column("centre_code", String(100), nullable=True)
    mis_centre_id = synonym("mis_center_id")
    centre_code = synonym("mis_center_id")

    centre_name = Column(String(255), nullable=False)

    district_code = Column(String(50), nullable=True)
    district_id = synonym("district_code")

    state_code = Column(String(50), nullable=True)
    state_id = Column(Integer, nullable=True)
    status = Column(String(50), nullable=True, default="Active")

    created_by = Column(String(100), nullable=True)

    created_at = Column(
        DateTime,
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at = Column(
        DateTime,
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    deleted_at = Column(
        DateTime,
        nullable=True,
    )

    centre_name_hi = Column(String, nullable=True)
    centre_name_bn = Column(String, nullable=True)
    centre_name_ta = Column(String, nullable=True)

    # Safe compatibility hybrid properties for omitted database columns
    @hybrid_property
    def address(self):
        return None

    @address.expression
    def address(cls):
        return literal(None)

    @hybrid_property
    def location(self):
        return self.centre_name

    @location.expression
    def location(cls):
        return cls.centre_name

    @hybrid_property
    def latitude(self):
        return None

    @latitude.expression
    def latitude(cls):
        return literal(None)

    @hybrid_property
    def longitude(self):
        return None

    @longitude.expression
    def longitude(cls):
        return literal(None)

    @hybrid_property
    def pin(self):
        return ""

    @pin.expression
    def pin(cls):
        return literal("")

    @hybrid_property
    def phone_number(self):
        return ""

    @phone_number.expression
    def phone_number(cls):
        return literal("")

    @hybrid_property
    def email(self):
        return ""

    @email.expression
    def email(cls):
        return literal("")

    @hybrid_property
    def block_id(self):
        return None

    @block_id.expression
    def block_id(cls):
        return literal(None)


class BlockMaster(Base):
    __tablename__ = "block_master"
    __table_args__ = {"schema": "mis_azad"}

    id = Column(Integer, primary_key=True, index=True)
    block_lgd_code = Column(Integer, index=True)
    block_name = Column(String(100), nullable=False)
    state_lgd_code = Column(Integer, nullable=True)
    district_lgd_code = Column(Integer, nullable=False)
    status = Column(String(10), nullable=False)
