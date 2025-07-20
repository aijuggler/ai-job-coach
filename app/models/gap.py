# app/models/gap.py
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional

class SkillMatch(BaseModel):
    job_skill: str
    resume_skill: Optional[str] = None       # None if not matched
    similarity: float = Field(ge=0.0, le=1.0)
    category: str                             # "matched" | "ambiguous" | "missing"

class GapSummary(BaseModel):
    total_job_skills: int
    matched_count: int
    ambiguous_count: int
    missing_count: int

class GapAnalysis(BaseModel):
    matched: List[str] = []
    ambiguous: List[str] = []
    missing: List[str] = []
    matches: List[SkillMatch] = []            # detailed rows
    summary: GapSummary
