from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func, desc, asc
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel
from app.models.user import User
from app.models.log import QueryLog, UserSession
from app.database.dependencies import get_db
from app.auth.dependencies import get_current_user
from fastapi.exceptions import HTTPException

router = APIRouter()

class QueryResponse(BaseModel):
    question: str
    response: Optional[str]
    response_time: Optional[float]
    timestamp: datetime

class SessionResponse(BaseModel):
    id: int
    started_at: datetime
    query_count: int
    avg_response_time: Optional[float]
    total_response_time: Optional[float]
    queries: List[QueryResponse]

@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    date_from: Optional[date] = Query(None, description="Filter sessions from this date"),
    date_to: Optional[date] = Query(None, description="Filter sessions to this date"),
    min_queries: Optional[int] = Query(None, ge=0, description="Minimum number of queries per session"),
    sort_by: Optional[str] = Query("date_desc", regex="^(date_desc|date_asc|queries_desc|queries_asc)$"),
    limit: Optional[int] = Query(50, ge=1, le=100, description="Maximum number of sessions to return")
):
    """
    Get user sessions with optional filtering and sorting
    """
    
    # Base query for sessions with query statistics
    query = (
        db.query(
            UserSession.id,
            UserSession.started_at,
            func.count(QueryLog.id).label('query_count'),
            func.avg(QueryLog.response_time).label('avg_response_time'),
            func.sum(QueryLog.response_time).label('total_response_time')
        )
        .outerjoin(QueryLog, UserSession.id == QueryLog.session_id)
        .filter(UserSession.user_id == current_user.id)
        .group_by(UserSession.id, UserSession.started_at)
    )
    
    # Apply date filters
    if date_from:
        query = query.filter(UserSession.started_at >= datetime.combine(date_from, datetime.min.time()))
    
    if date_to:
        query = query.filter(UserSession.started_at <= datetime.combine(date_to, datetime.max.time()))
    
    # Apply minimum queries filter
    if min_queries is not None:
        query = query.having(func.count(QueryLog.id) >= min_queries)
    
    # Apply sorting
    if sort_by == "date_desc":
        query = query.order_by(desc(UserSession.started_at))
    elif sort_by == "date_asc":
        query = query.order_by(asc(UserSession.started_at))
    elif sort_by == "queries_desc":
        query = query.order_by(desc(func.count(QueryLog.id)))
    elif sort_by == "queries_asc":
        query = query.order_by(asc(func.count(QueryLog.id)))
    
    # Apply limit
    sessions_data = query.limit(limit).all()
    
    # Build response with queries for each session
    result = []
    
    for session_data in sessions_data:
        session_id = session_data.id
        
        # Get all queries for this session
        queries = (
            db.query(QueryLog)
            .filter(QueryLog.session_id == session_id)
            .order_by(QueryLog.timestamp)
            .all()
        )
        
        # Convert queries to response format
        query_responses = [
            QueryResponse(
                question=query.question,
                response=query.response,
                response_time=query.response_time,
                timestamp=query.timestamp
            )
            for query in queries
        ]
        
        # Create session response
        session_response = SessionResponse(
            id=session_data.id,
            started_at=session_data.started_at,
            query_count=session_data.query_count or 0,
            avg_response_time=float(session_data.avg_response_time) if session_data.avg_response_time else None,
            total_response_time=float(session_data.total_response_time) if session_data.total_response_time else None,
            queries=query_responses
        )
        
        result.append(session_response)
    
    return result

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session_by_id(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific session by ID
    """
    
    # Get session with statistics
    session_data = (
        db.query(
            UserSession.id,
            UserSession.started_at,
            func.count(QueryLog.id).label('query_count'),
            func.avg(QueryLog.response_time).label('avg_response_time'),
            func.sum(QueryLog.response_time).label('total_response_time')
        )
        .outerjoin(QueryLog, UserSession.id == QueryLog.session_id)
        .filter(
            UserSession.id == session_id,
            UserSession.user_id == current_user.id
        )
        .group_by(UserSession.id, UserSession.started_at)
        .first()
    )
    
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get all queries for this session
    queries = (
        db.query(QueryLog)
        .filter(QueryLog.session_id == session_id)
        .order_by(QueryLog.timestamp)
        .all()
    )
    
    # Convert queries to response format
    query_responses = [
        QueryResponse(
            question=query.question,
            response=query.response,
            response_time=query.response_time,
            timestamp=query.timestamp
        )
        for query in queries
    ]
    
    # Create session response
    return SessionResponse(
        id=session_data.id,
        started_at=session_data.started_at,
        query_count=session_data.query_count or 0,
        avg_response_time=float(session_data.avg_response_time) if session_data.avg_response_time else None,
        total_response_time=float(session_data.total_response_time) if session_data.total_response_time else None,
        queries=query_responses
    )

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a session and all its associated queries
    """
    
    # Check if session exists and belongs to current user
    session = (
        db.query(UserSession)
        .filter(
            UserSession.id == session_id,
            UserSession.user_id == current_user.id
        )
        .first()
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Delete associated queries first (due to foreign key constraint)
    db.query(QueryLog).filter(QueryLog.session_id == session_id).delete()
    
    # Delete the session
    db.delete(session)
    db.commit()
    
    return {"message": "Session deleted successfully"}

@router.get("/sessions/stats/summary")
async def get_sessions_summary(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None)
):
    """
    Get summary statistics for user sessions
    """
    
    # Base query for sessions
    query = db.query(UserSession).filter(UserSession.user_id == current_user.id)
    
    # Apply date filters
    if date_from:
        query = query.filter(UserSession.started_at >= datetime.combine(date_from, datetime.min.time()))
    
    if date_to:
        query = query.filter(UserSession.started_at <= datetime.combine(date_to, datetime.max.time()))
    
    # Get total sessions count
    total_sessions = query.count()
    
    # Get total queries and response time statistics
    stats_query = (
        db.query(
            func.count(QueryLog.id).label('total_queries'),
            func.avg(QueryLog.response_time).label('avg_response_time'),
            func.min(QueryLog.response_time).label('min_response_time'),
            func.max(QueryLog.response_time).label('max_response_time'),
            func.sum(QueryLog.response_time).label('total_response_time')
        )
        .join(UserSession, QueryLog.session_id == UserSession.id)
        .filter(UserSession.user_id == current_user.id)
    )
    
    # Apply same date filters to queries
    if date_from:
        stats_query = stats_query.filter(UserSession.started_at >= datetime.combine(date_from, datetime.min.time()))
    
    if date_to:
        stats_query = stats_query.filter(UserSession.started_at <= datetime.combine(date_to, datetime.max.time()))
    
    stats = stats_query.first()
    
    return {
        "total_sessions": total_sessions,
        "total_queries": stats.total_queries or 0,
        "avg_response_time": float(stats.avg_response_time) if stats.avg_response_time else None,
        "min_response_time": float(stats.min_response_time) if stats.min_response_time else None,
        "max_response_time": float(stats.max_response_time) if stats.max_response_time else None,
        "total_response_time": float(stats.total_response_time) if stats.total_response_time else None,
        "avg_queries_per_session": float(stats.total_queries / total_sessions) if total_sessions > 0 and stats.total_queries else 0
    }