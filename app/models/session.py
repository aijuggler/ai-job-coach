from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.question import Question
from app.models.answer import Answer, AnswerFeedback

class InterviewSession(BaseModel):
    session_id: str
    candidate_id: str
    questions: List[Question]
    answers: List[Answer] = []
    feedback: List[AnswerFeedback] = []
    current_index: int = 0
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

    def is_finished(self) -> bool:
        return self.current_index >= len(self.questions) or self.ended_at is not None
