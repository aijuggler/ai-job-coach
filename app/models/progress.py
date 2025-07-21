from __future__ import annotations
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

class SessionMetric(BaseModel):
    session_id: str
    started_at: datetime
    ended_at: datetime
    avg_score: float
    dims_avg: Dict[str, float]   # e.g. {"correctness":3.5,"clarity":3.8,"depth":3.2}
    question_count: int

class ProgressReport(BaseModel):
    candidate_id: str
    sessions: List[SessionMetric]
    overall_avg: float
