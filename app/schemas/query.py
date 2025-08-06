from pydantic import BaseModel
from datetime import datetime

class AskRequest(BaseModel):
    question: str
    chat_history: list

class AskResponse(BaseModel):
    answer: str

class QueryLog(BaseModel):
    id: int
    user_id: int
    question: str
    response: str
    response_time: float
    timestamp: datetime

    class Config:
        orm_mode = True
