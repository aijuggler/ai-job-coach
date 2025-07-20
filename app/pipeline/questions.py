import json
import re
from typing import List, Dict, Tuple
from app.models.resume import ResumeProfile
from app.models.job import JobProfile
from app.models.gap import GapAnalysis
from app.models.question import Question, QuestionPlan

# ---------------- Planning ---------------- #

def plan_question_buckets(
    gap: GapAnalysis,
    resume: ResumeProfile,
    job: JobProfile,
    total: int = 18,
    min_total: int = 15,
    max_total: int = 20
) -> QuestionPlan:
    """
    Heuristic distribution. Adjust later if needed.
    """
    total = max(min_total, min(max_total, total))

    missing_count = len(gap.missing)
    ambiguous_count = len(gap.ambiguous)
    matched_count = len(gap.matched)

    # Base seeds
    fundamentals = 3
    behavioral = 2
    advanced = 3

    # Gaps: proportional
    gap_target = max(5, min(8, (missing_count // 2) + (ambiguous_count // 2) + 3))

    # Strengths: proportional to matched
    strengths = max(2, min(4, matched_count // 3 if matched_count else 2))

    allocated = fundamentals + behavioral + advanced + gap_target + strengths

    # Adjust to total
    if allocated < total:
        remaining = total - allocated
        # Preference order to add
        for bucket in ("gaps", "advanced", "strengths", "fundamentals"):
            if remaining <= 0:
                break
            if bucket == "gaps" and gap_target < 8:
                add = min(remaining, 8 - gap_target)
                gap_target += add
                remaining -= add
            elif bucket == "advanced":
                add = min(remaining, 2)
                advanced += add
                remaining -= add
            elif bucket == "strengths":
                add = min(remaining, 2)
                strengths += add
                remaining -= add
            elif bucket == "fundamentals":
                add = min(remaining, 2)
                fundamentals += add
                remaining -= add
    elif allocated > total:
        # Trim from strengths then advanced
        over = allocated - total
        for bucket_name in ("strengths", "advanced", "behavioral"):
            if over <= 0:
                break
            if bucket_name == "strengths" and strengths > 2:
                reducible = strengths - 2
                cut = min(over, reducible)
                strengths -= cut
                over -= cut
            elif bucket_name == "advanced" and advanced > 2:
                reducible = advanced - 2
                cut = min(over, reducible)
                advanced -= cut
                over -= cut
            elif bucket_name == "behavioral" and behavioral > 1:
                reducible = behavioral - 1
                cut = min(over, reducible)
                behavioral -= cut
                over -= cut

    return QuestionPlan(
        total=fundamentals + strengths + gap_target + behavioral + advanced,
        fundamentals=fundamentals,
        strengths=strengths,
        gaps=gap_target,
        behavioral=behavioral,
        advanced=advanced,
    )

# ---------------- Generation ---------------- #

def _batch_question_prompt(
    category: str,
    count: int,
    resume: ResumeProfile,
    job: JobProfile,
    gap: GapAnalysis
) -> str:
    """
    Build a user prompt for a specific bucket.
    """
    missing = ", ".join(gap.missing[:10]) or "none"
    ambiguous = ", ".join(gap.ambiguous[:10]) or "none"
    strengths = ", ".join(gap.matched[:10]) or "none"

    instructions_map = {
        "fundamentals": "Cover core theoretical or foundational concepts relevant to the role.",
        "strengths": "Deep-dive into areas where the candidate is already strong to assess depth & nuance.",
        "gaps": "Probe missing or ambiguous skills to uncover weak areas; ask open-ended, diagnostic questions.",
        "behavioral": "Use STAR-aligned prompts focusing on collaboration, ownership, conflict resolution.",
        "advanced": "Focus on architectural, scalability, system design, optimization, or MLOps depth.",
    }

    instruction = instructions_map[category]

    return f"""
ROLE CONTEXT:
Title: {job.title or "Unknown"}
Company: {job.company or "Unknown"}

GAP SNAPSHOT:
Missing skills: {missing}
Ambiguous skills: {ambiguous}
Strength (matched) skills: {strengths}

CATEGORY: {category.upper()}
CATEGORY INSTRUCTION: {instruction}

TASK:
Generate {count} interview questions for this category.
For each question return JSON object with keys:
- text (string) concise, no numbering
- category (exact: {category})
- target_skills (list of relevant skills, lowercase)
- difficulty (easy|medium|hard)
- rationale (short reason)

Rules:
- Avoid duplicate or near-duplicate wording.
- Do NOT prefix with Q1, numbers, bullets.
- Keep each question under 180 characters.
- Use open-ended phrasing unless a direct comparison is more diagnostic.
- Avoid overlap with other categories' typical focus.

Return a JSON array ONLY. No markdown.
""".strip()

def _invoke_questions_batch(llm, prompt: str):
    """
    A thin wrapper so tests can monkeypatch this function.
    """
    messages = [
        ("system", "You generate only valid JSON arrays of interview question objects."),
        ("user", prompt),
    ]
    response = llm.invoke(messages)
    content = response.content
    if isinstance(content, list):
        # LangChain may return list-of-chunks
        text_parts = [c.get("text", "") for c in content if isinstance(c, dict)]
        content = "".join(text_parts)
    return content

def _parse_questions_json(raw: str) -> List[dict]:
    # Extract first JSON array found
    # Safe approach: find first '[' and last ']'
    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("No JSON array brackets found in LLM response.")
    snippet = raw[start : end + 1]
    data = json.loads(snippet)
    if not isinstance(data, list):
        raise ValueError("Top-level JSON is not a list.")
    return data

def generate_questions_from_plan(
    resume: ResumeProfile,
    job: JobProfile,
    gap: GapAnalysis,
    plan: QuestionPlan,
    llm,
    max_retries: int = 2
) -> List[Question]:
    bucket_counts = plan.as_bucket_counts()
    all_questions: List[Question] = []
    seen_texts = set()

    for category, count in bucket_counts.items():
        if count <= 0:
            continue
        prompt = _batch_question_prompt(category, count, resume, job, gap)

        raw = None
        for attempt in range(max_retries + 1):
            try:
                raw = _invoke_questions_batch(llm, prompt)
                parsed = _parse_questions_json(raw)
                break
            except Exception:
                if attempt == max_retries:
                    # fallback simple templated questions
                    parsed = _fallback_bucket(category, count, gap)
                else:
                    continue

        for q_obj in parsed:
            # Defensive extraction
            text = (q_obj.get("text") or "").strip()
            if not text:
                continue
            normalized = re.sub(r"\s+", " ", text.lower())
            if normalized in seen_texts:
                continue
            seen_texts.add(normalized)

            all_questions.append(
                Question(
                    id="TEMP",  # assign final IDs later
                    text=text,
                    category=category,
                    target_skills=[s.lower() for s in q_obj.get("target_skills", [])][:5],
                    difficulty=q_obj.get("difficulty", "medium"),
                    rationale=q_obj.get("rationale"),
                )
            )

    # Trim or pad if off target
    if len(all_questions) > plan.total:
        all_questions = all_questions[: plan.total]

    # Assign IDs sequentially
    for i, q in enumerate(all_questions, start=1):
        q.id = f"Q{i}"

    return all_questions

def _fallback_bucket(category: str, count: int, gap: GapAnalysis) -> List[dict]:
    base_texts = []
    if category == "gaps":
        src = gap.missing + gap.ambiguous
        for s in src[:count]:
            base_texts.append(
                {
                    "text": f"Describe your experience (if any) with {s}. What would be your next step to improve?",
                    "category": category,
                    "target_skills": [s],
                    "difficulty": "medium",
                    "rationale": "Probe skill gap."
                }
            )
    elif category == "strengths":
        src = gap.matched or ["problem solving"]
        for s in src[:count]:
            base_texts.append(
                {
                    "text": f"Walk me through a significant challenge where {s} was critical to success.",
                    "category": category,
                    "target_skills": [s],
                    "difficulty": "medium",
                    "rationale": "Depth on strength."
                }
            )
    elif category == "fundamentals":
        fundamentals_seed = [
            "Explain overfitting and how to mitigate it.",
            "How do you evaluate model performance beyond accuracy?",
            "What is the bias-variance tradeoff?",
        ]
        for t in fundamentals_seed[:count]:
            base_texts.append(
                {
                    "text": t,
                    "category": category,
                    "target_skills": ["fundamentals"],
                    "difficulty": "easy",
                    "rationale": "Core concept."
                }
            )
        while len(base_texts) < count:
            base_texts.append(
                {
                    "text": "Explain cross-validation and why it is used.",
                    "category": category,
                    "target_skills": ["fundamentals"],
                    "difficulty": "easy",
                    "rationale": "Core concept.",
                }
            )
    elif category == "behavioral":
        seeds = [
            "Tell me about a time you resolved a team conflict.",
            "Describe a situation where you had to influence without authority.",
        ]
        for t in seeds[:count]:
            base_texts.append(
                {
                    "text": t,
                    "category": category,
                    "target_skills": [],
                    "difficulty": "medium",
                    "rationale": "Behavioral insight."
                }
            )
        while len(base_texts) < count:
            base_texts.append(
                {
                    "text": "Describe a failure and what you learned.",
                    "category": category,
                    "target_skills": [],
                    "difficulty": "medium",
                    "rationale": "Reflection.",
                }
            )
    elif category == "advanced":
        seeds = [
            "Design a scalable feature store architecture.",
            "How would you monitor model drift in production?",
        ]
        for t in seeds[:count]:
            base_texts.append(
                {
                    "text": t,
                    "category": category,
                    "target_skills": ["architecture"],
                    "difficulty": "hard",
                    "rationale": "Advanced reasoning."
                }
            )
        while len(base_texts) < count:
            base_texts.append(
                {
                    "text": "Explain how you would design an end-to-end ML pipeline for real-time inference.",
                    "category": category,
                    "target_skills": ["mlops"],
                    "difficulty": "hard",
                    "rationale": "System depth."
                }
            )
    return base_texts
