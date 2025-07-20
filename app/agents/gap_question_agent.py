# app/agents/gap_question_agent.py
from app.models.resume import ResumeProfile
from app.models.job import JobProfile
from app.models.gap import GapAnalysis
from app.pipeline.gap import gap_analysis

class GapQuestionAgent:
    """
    For M2 only uses gap_analysis.
    In M3 will add question planning/generation methods.
    """
    def analyze(self, resume: ResumeProfile, job: JobProfile) -> GapAnalysis:
        return gap_analysis(resume, job)
