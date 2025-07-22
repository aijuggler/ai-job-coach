# app/state/graph_state.py

from typing import TypedDict, List
# Reverting to an absolute import from the 'app' package root.
from app.models import (
    ResumeProfile,
    JobProfile,
    GapAnalysis,
    Question,
    AnswerFeedback,
    InterviewSession,
    ProgressReport
)

class GraphState(TypedDict):
    """
    Represents the state of our graph, acting as a centralized data container.

    This state object is passed between all nodes in the graph, carrying the
    payload of the entire interview process from start to finish. Each key
    corresponds to a piece of data generated or used by one of the agents.
    """
    # Initial inputs from the user
    resume_bytes: bytes | None
    job_bytes: bytes | None
    job_text: str | None
    
    # Outputs from the ExtractionAgent
    resume_profile: ResumeProfile | None
    job_profile: JobProfile | None
    
    # Outputs from the GapQuestionAgent
    gap_analysis: GapAnalysis | None
    question_list: List[Question] | None
    
    # State for the InterviewAgent
    interview_session: InterviewSession | None
    current_question_index: int | None
    # We add a list to store all feedback items as the interview progresses
    all_feedback: List[AnswerFeedback]

    # Output from the ProgressAgent
    progress_report: ProgressReport | None
