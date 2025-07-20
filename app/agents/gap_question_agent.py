# app/agents/gap_question_agent.py
from typing import List, Optional, Tuple

from app.models.resume import ResumeProfile
from app.models.job import JobProfile
from app.models.gap import GapAnalysis
from app.models.question import Question, QuestionPlan
from app.pipeline.gap import gap_analysis
from app.pipeline.questions import (
    plan_question_buckets,
    generate_questions_from_plan,
)
# Import your LLMs (adjust if you renamed)
from app.services.llm import llm_questions, llm_deterministic


class GapQuestionAgent:
    """
    Agent combining:
      - Gap Analysis (resume vs job)
      - Question Planning (bucket distribution)
      - Question Generation (LLM-based, per bucket)
    """

    def __init__(
        self,
        planning_llm=None,   # could keep deterministic
        question_llm=None,   # creative-ish
    ):
        self.planning_llm = planning_llm or llm_deterministic
        self.question_llm = question_llm or llm_questions

    # ---------------- GAP ANALYSIS ---------------- #
    def analyze(self, resume: ResumeProfile, job: JobProfile) -> GapAnalysis:
        """
        Produce a GapAnalysis object (matched, ambiguous, missing).
        """
        return gap_analysis(resume, job)

    # ---------------- PLANNING ---------------- #
    def plan(
        self,
        resume: ResumeProfile,
        job: JobProfile,
        gap: GapAnalysis,
        total: int = 18
    ) -> QuestionPlan:
        """
        Decide how many questions per bucket (fundamentals, strengths, gaps, behavioral, advanced).
        """
        return plan_question_buckets(gap, resume, job, total=total)

    # ---------------- GENERATION ---------------- #
    def generate(
        self,
        resume: ResumeProfile,
        job: JobProfile,
        gap: GapAnalysis,
        plan: QuestionPlan,
        llm=None
    ) -> List[Question]:
        """
        Generate actual question objects from a plan.
        llm: optional override (defaults to self.question_llm).
        """
        llm = llm or self.question_llm
        return generate_questions_from_plan(
            resume=resume,
            job=job,
            gap=gap,
            plan=plan,
            llm=llm
        )
    # ---------------- CONVENIENCE (ANALYZE + PLAN + GENERATE) ---------------- #
    def plan_and_generate(
        self,
        resume: ResumeProfile,
        job: JobProfile,
        gap: Optional[GapAnalysis] = None,
        total: int = 18,
        llm=None
    ) -> tuple[GapAnalysis, QuestionPlan, List[Question]]:
        if gap is None:
            gap = self.analyze(resume, job)
        plan = self.plan(resume, job, gap, total=total)
        questions = self.generate(resume, job, gap, plan, llm=llm)
        return gap, plan, questions
