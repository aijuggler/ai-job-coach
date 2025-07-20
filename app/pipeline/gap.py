# app/pipeline/gap.py
import numpy as np
from typing import Tuple
from app.models.resume import ResumeProfile
from app.models.job import JobProfile
from app.models.gap import GapAnalysis, SkillMatch, GapSummary
from app.services.embeddings import embed_texts

# Thresholds (tune later)
MATCH_THRESHOLD = 0.83
AMBIGUOUS_THRESHOLD = 0.70   # >= this and < MATCH_THRESHOLD is ambiguous

def _normalize_skill(name: str) -> str:
    return name.strip().lower()

def _collect_resume_skills(resume: ResumeProfile) -> list[str]:
    base = [_normalize_skill(s.name) for s in resume.skills]
    inferred = [_normalize_skill(s.name) for s in resume.inferred_skills]
    # Also optional: gather skills listed inside experiences/projects
    nested = []
    for exp in resume.experiences:
        nested.extend([_normalize_skill(s) for s in exp.skills])
    for proj in resume.projects:
        nested.extend([_normalize_skill(s) for s in proj.skills])
    # Deduplicate preserving first order
    seen = set()
    ordered = []
    for skill in base + inferred + nested:
        if skill and skill not in seen:
            seen.add(skill)
            ordered.append(skill)
    return ordered

def _collect_job_skills(job: JobProfile) -> list[str]:
    job_skills = []
    for s in job.must_have_skills:
        job_skills.append(_normalize_skill(s.name))
    for s in job.nice_to_have_skills:
        job_skills.append(_normalize_skill(s.name))
    # Dedup
    seen = set()
    uniq = []
    for s in job_skills:
        if s and s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq

def _cosine_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-12)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-12)
    return a_norm @ b_norm.T

def gap_analysis(resume: ResumeProfile, job: JobProfile) -> GapAnalysis:
    resume_skills = _collect_resume_skills(resume)
    job_skills = _collect_job_skills(job)

    if not job_skills:
        raise ValueError("No job skills extracted to analyze.")

    # Edge: if resume has no skills at all
    if not resume_skills:
        matches = [
            SkillMatch(job_skill=js, resume_skill=None, similarity=0.0, category="missing")
            for js in job_skills
        ]
        return GapAnalysis(
            matched=[],
            ambiguous=[],
            missing=job_skills,
            matches=matches,
            summary=GapSummary(
                total_job_skills=len(job_skills),
                matched_count=0,
                ambiguous_count=0,
                missing_count=len(job_skills)
            )
        )

    # Embed: combine lists so we do two batches
    resume_vecs = embed_texts(resume_skills)
    job_vecs = embed_texts(job_skills)

    R = np.array(resume_vecs)
    J = np.array(job_vecs)
    sim_matrix = _cosine_matrix(R, J)  # shape: (len(resume_skills), len(job_skills))

    matched_list = []
    ambiguous_list = []
    missing_list = []
    matches_detail = []

    for j_idx, job_skill in enumerate(job_skills):
        column = sim_matrix[:, j_idx]
        best_idx = int(np.argmax(column))
        best_score = float(column[best_idx])
        resume_skill = resume_skills[best_idx]

        if best_score >= MATCH_THRESHOLD:
            category = "matched"
            matched_list.append(job_skill)
        elif best_score >= AMBIGUOUS_THRESHOLD:
            category = "ambiguous"
            ambiguous_list.append(job_skill)
        else:
            category = "missing"
            resume_skill = None
            missing_list.append(job_skill)

        matches_detail.append(
            SkillMatch(
                job_skill=job_skill,
                resume_skill=resume_skill,
                similarity=round(best_score, 4),
                category=category
            )
        )

    summary = GapSummary(
        total_job_skills=len(job_skills),
        matched_count=len(matched_list),
        ambiguous_count=len(ambiguous_list),
        missing_count=len(missing_list)
    )

    return GapAnalysis(
        matched=matched_list,
        ambiguous=ambiguous_list,
        missing=missing_list,
        matches=matches_detail,
        summary=summary
    )
