from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey,TEXT
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base

class UserSession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="sessions")
    query_logs = relationship("QueryLog", back_populates="session")


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)

    question = Column(String(1000), nullable=False)
    response = Column(TEXT(50000), nullable=False)
    response_time = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="query_logs")
    session = relationship("UserSession", back_populates="query_logs")
