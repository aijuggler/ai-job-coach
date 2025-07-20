from app.models.question import QuestionPlan
from app.models.gap import GapAnalysis, GapSummary, SkillMatch
from app.models.resume import ResumeProfile, SkillItem
from app.models.job import JobProfile, JobSkill
from app.pipeline.questions import generate_questions_from_plan
from app.pipeline.questions import plan_question_buckets

class DummyLLM:
    def invoke(self, messages):
        # Always returns 2 trivial JSON questions per category request,
        # Replace with dynamic logic if needed.
        import json
        user_prompt = messages[-1][1]
        # crude detect count (fallback to 2)
        count = 2
        if "Generate" in user_prompt:
            # try to parse number after "Generate "
            try:
                count = int(user_prompt.split("Generate")[1].split(" ")[1])
            except Exception:
                pass
        arr = []
        for i in range(count):
            arr.append({
                "text": f"Dummy question {i}",
                "category": user_prompt.split("CATEGORY:")[1].splitlines()[0].strip().lower(),
                "target_skills": ["python"],
                "difficulty": "medium",
                "rationale": "test"
            })
        class Msg:
            def __init__(self, c): self.content = json.dumps(arr)
        return Msg(json.dumps(arr))

def test_question_generation_monkeypatch(monkeypatch):
    resume = ResumeProfile(
        full_name="Test",
        headline=None,
        summary=None,
        skills=[SkillItem(name="python", evidence=None, confidence=0.9)],
        experiences=[], education=[], projects=[], certifications=[], inferred_skills=[],
        raw_length=10
    )
    job = JobProfile(
        title="Data Scientist",
        company="Co",
        must_have_skills=[JobSkill(name="python", reason="explicit", confidence=0.95)],
        nice_to_have_skills=[JobSkill(name="aws", reason="optional", confidence=0.6)],
        responsibilities=[], requirements_raw=[], domain_keywords=[],
        inferred_hidden_expectations=[], raw_length=20
    )
    gap = GapAnalysis(
        matched=["python"],
        ambiguous=["aws"],
        missing=["mlops"],
        matches=[
            SkillMatch(job_skill="python", resume_skill="python", similarity=0.95, category="matched"),
            SkillMatch(job_skill="aws", resume_skill=None, similarity=0.6, category="ambiguous"),
            SkillMatch(job_skill="mlops", resume_skill=None, similarity=0.4, category="missing"),
        ],
        summary=GapSummary(total_job_skills=3, matched_count=1, ambiguous_count=1, missing_count=1)
    )

    plan = plan_question_buckets(gap, resume, job, total=15)
    from app.pipeline import questions as qmod
    monkeypatch.setattr(qmod, "_invoke_questions_batch", lambda llm, prompt: DummyLLM().invoke([("user", prompt)]).content)

    qs = generate_questions_from_plan(resume, job, gap, plan, llm=DummyLLM())
    assert len(qs) <= plan.total
    assert all(q.id.startswith("Q") for q in qs)
