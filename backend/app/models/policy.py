from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime, timezone
from app.core.database import Base

class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    insurer = Column(String, index=True, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, json, txt
    file_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    uploaded_by = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)