from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Question(BaseModel):
    id: str
    text: str
    category: str  # fundamentals | strengths | gaps | behavioral | advanced
    target_skills: List[str] = []
    difficulty: str = "medium"  # easy | medium | hard
    rationale: Optional[str] = None

class QuestionPlan(BaseModel):
    total: int
    fundamentals: int
    strengths: int
    gaps: int
    behavioral: int
    advanced: int

    def as_bucket_counts(self) -> Dict[str, int]:
        return {
            "fundamentals": self.fundamentals,
            "strengths": self.strengths,
            "gaps": self.gaps,
            "behavioral": self.behavioral,
            "advanced": self.advanced,
        }
