# app/models/__init__.py

"""
This file makes the 'models' directory a Python package and exposes
the primary data models for convenient importing from other parts of
the application.
"""

from .answer import Answer, AnswerFeedback
from .gap import GapAnalysis
from .job import JobProfile
from .progress import ProgressReport
from .question import Question, QuestionPlan
from .resume import ResumeProfile
from .session import InterviewSession

# You can define __all__ to specify what gets imported with 'from app.models import *'
__all__ = [
    "Answer",
    "AnswerFeedback",
    "GapAnalysis",
    "SkillGap",
    "JobProfile",
    "ProgressReport",
    "SessionSummary",
    "Question",
    "QuestionPlan",
    "ResumeProfile",
    "InterviewSession",
]
