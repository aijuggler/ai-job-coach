from app.models.resume import ResumeProfile, SkillItem
from app.models.job import JobProfile, JobSkill
from app.pipeline.gap import gap_analysis

class DummyResume(ResumeProfile):
    pass

def test_gap_simple(monkeypatch):
    resume = ResumeProfile(
        full_name="Test",
        skills=[SkillItem(name="python", confidence=0.9)],
        experiences=[], education=[], projects=[], certifications=[], inferred_skills=[],
        raw_length=10
    )
    job = JobProfile(
        title="DS", company=None,
        must_have_skills=[JobSkill(name="Python", reason="explicit", confidence=0.95)],
        nice_to_have_skills=[JobSkill(name="aws", reason="cloud", confidence=0.6)],
        responsibilities=[], requirements_raw=[], domain_keywords=[],
        inferred_hidden_expectations=[], raw_length=5
    )

    # Monkeypatch embeddings to deterministic similarity
    import app.pipeline.gap as gap_mod

    def fake_embed(texts):
        # Very naive: python vector larger than aws
        vecs = []
        for t in texts:
            if "python" in t:
                vecs.append([1.0, 0.0])
            else:
                vecs.append([0.3, 0.1])
        return vecs

    monkeypatch.setattr(gap_mod, "embed_texts", fake_embed)

    analysis = gap_analysis(resume, job)
    assert "python" in analysis.matched
    assert "aws" in analysis.missing or "aws" in analysis.ambiguous
    assert analysis.summary.total_job_skills == 2
