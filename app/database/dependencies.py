from app.database.session import SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy.orm import Session as DBSession
from app.models.log import UserSession, QueryLog

from typing import Generator

def get_db() -> Generator[DBSession, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def start_new_session(db: DBSession, user_id: int) -> int:
    session = UserSession(user_id=user_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session.id

def log_query(
    db: DBSession,
    user_id: int,
    session_id: int,
    question: str,
    response: str,
    response_time: float
):
    entry = QueryLog(
        user_id=user_id,
        session_id=session_id,
        question=question,
        response=response,
        response_time=response_time
    )
    db.add(entry)
    db.commit()
