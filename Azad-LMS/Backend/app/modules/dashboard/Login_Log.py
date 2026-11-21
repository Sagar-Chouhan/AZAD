from sqlalchemy import BigInteger, Column, DateTime, String
from app.database.database import Base


class LoginLog(Base):
    __tablename__ = "login_logs"
    __table_args__ = {"schema": "mis_azad"}

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False)
    login_time = Column(DateTime)
    app_version = Column(String(100))
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)

    @property
    def created_at(self):
        return self.login_time

    @property
    def updated_at(self):
        return self.login_time
