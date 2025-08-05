from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from datetime import datetime, timedelta
import time

from app.schemas.query import AskRequest, AskResponse
from app.database.dependencies import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.log import QueryLog, UserSession
from app.vectore_store.retriever import get_relevant_chunks
from fastapi.responses import StreamingResponse
from app.utils.agent_responder import stream_llm_response
from app.utils.orchestrator import chat_history_analyzer

router = APIRouter()


SESSION_TIMEOUT_MINUTES = 5  # Define session lifetime

@router.post("/ask")
async def ask_question(
    request: AskRequest,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    start_time = time.time()

    original_user_input=request.question

    updated_user_input = await chat_history_analyzer(original_user_input, request.chat_history)
    print(updated_user_input)

    relevant_chunks = await get_relevant_chunks(current_user.id, updated_user_input)
    
    # Step 1: Find or create session
    timeout_threshold = datetime.utcnow() - timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    session = (
        db.query(UserSession)
        .filter(
            UserSession.user_id == current_user.id,
            UserSession.started_at >= timeout_threshold
        )
        .order_by(UserSession.started_at.desc())
        .first()
    )

    if not session:
        session = UserSession(user_id=current_user.id, started_at=datetime.utcnow())
        db.add(session)
        db.commit()  # Commit the session immediately
        db.refresh(session)  # Refresh to get the generated ID

    # Store session_id to avoid detached instance issues
    session_id = session.id
    user_id = session.user_id

    # Step 2: Define generator to stream response and log at the same time
    async def stream_and_log():
        full_response = ""
        try:
            async for chunk in stream_llm_response(
                context_str=relevant_chunks,
                question=updated_user_input
            ):
                full_response += chunk
                yield chunk
        except Exception as e:
            yield f"\n[Error generating answer: {str(e)}]"
            return

        print(full_response)
        # After full stream, log to database
        response_time = round(time.time() - start_time, 3)
        log = QueryLog(
            user_id=user_id,
            question=original_user_input,
            response=full_response,
            response_time=response_time,
            timestamp=datetime.utcnow(),
            session_id=session_id  # Use the stored session_id
        )
        db.add(log)
        db.commit()

    return StreamingResponse(stream_and_log(), media_type="text/plain")
