from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional, Union

class JobSkill(BaseModel):
    name: str
    confidence: Optional[float] = None            # optional if LLM adds it
    source: Optional[str] = None   

class HiddenExpectation(BaseModel):
    expectation: str
    reason: Optional[str] = None

class JobProfile(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    must_have_skills: List[Union[str, JobSkill]] = Field(default_factory=list)
    nice_to_have_skills: List[Union[str, JobSkill]] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    requirements_raw: List[str] = []
    domain_keywords: List[str] = []
    inferred_hidden_expectations: List[Union[str, HiddenExpectation]] = Field(default_factory=list)
    raw_length: Optional[int] = None
