from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

class Answer(BaseModel):
    question_id: str
    question_text: str
    category: str
    answer_text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AnswerFeedback(BaseModel):
    question_id: str
    score: int                                 # 1‑5 overall
    dimensions: Dict[str, int]                 # e.g. {"correctness":3,"clarity":4,"depth":2}
    suggestions: str
    raw_eval: Optional[str] = None             # keep entire LLM response for traceability
