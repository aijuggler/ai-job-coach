from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional

class JobSkill(BaseModel):
    name: str
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)

class HiddenExpectation(BaseModel):
    expectation: str
    reason: str

class JobProfile(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    must_have_skills: List[JobSkill] = []
    nice_to_have_skills: List[JobSkill] = []
    responsibilities: List[str] = []
    requirements_raw: List[str] = []
    domain_keywords: List[str] = []
    inferred_hidden_expectations: List[HiddenExpectation] = []
    raw_length: int
