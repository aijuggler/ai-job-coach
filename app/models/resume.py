from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional, Union

class SkillItem(BaseModel):
    name: str
    evidence: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)

class ExperienceItem(BaseModel):
    role: str = Field(alias="job_title")
    company: Optional[str] = None
    start: Optional[str] = None   # "YYYY" or "YYYY-MM" or None
    end: Optional[str] = None
    bullets: List[str] = []
    skills: List[str] = []
    model_config = {
        "populate_by_name": True,            # allow alias when constructing
        "extra": "ignore",                   # ignore unexpected keys if any
    }

class EducationItem(BaseModel):
    degree: str
    institution: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None

class ProjectItem(BaseModel):
    name: str
    description: Optional[str] = None
    impact: Optional[str] = None
    skills: List[str] = []

class InferredSkill(BaseModel):
    name: str
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)

class ResumeProfile(BaseModel):
    full_name: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    skills: List[Union[str, SkillItem]] = []
    experiences: List[ExperienceItem] = []
    education: List[EducationItem] = []
    projects: List[ProjectItem] = []
    certifications: List[str] = []
    inferred_skills: List[Union[str, InferredSkill]] = []
    raw_length: Optional[int] = None