from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")  # 'user' or 'admin'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))