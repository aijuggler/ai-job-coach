from __future__ import annotations
from typing import Dict
from app.models.question import Question
from app.models.answer import AnswerFeedback
from app.services.llm import llm_eval          # we’ll add this in services

_EVAL_SYSTEM_PROMPT = """
You are a rigorous technical interviewer scoring answers on a 1-5 scale.
Return ONLY valid JSON with keys:
score (int 1-5),
dimensions: {correctness:int,clarity:int,depth:int},
suggestions (max 30 words)
"""

def _build_user_prompt(question_text: str, answer_text: str) -> str:
    return f"""QUESTION:
{question_text}

CANDIDATE ANSWER:
{answer_text}

EVALUATE NOW:
"""

def evaluate_answer(question: Question, answer_text: str) -> AnswerFeedback:
    prompt = _build_user_prompt(question.text, answer_text)
    messages = [
        ("system", _EVAL_SYSTEM_PROMPT.strip()),
        ("user", prompt.strip()),
    ]
    resp = llm_eval.invoke(messages)
    content = resp.content
    # Fallback if model returns list-of-dict chunks
    if isinstance(content, list):
        content = "".join([c.get("text", "") for c in content if isinstance(c, dict)])

    import json, re
    match = re.search(r"{.*}", content, flags=re.S)
    data: Dict = json.loads(match.group(0)) if match else {"score":3,"dimensions":{"correctness":3,"clarity":3,"depth":3},"suggestions":"Work on concise structure."}

    # Defensive coercion
    score = int(data.get("score", 3))
    score = min(5, max(1, score))

    dims = {k:int(v) for k,v in data.get("dimensions", {}).items()}
    for key in ("correctness","clarity","depth"):
        dims.setdefault(key,3)

    return AnswerFeedback(
        question_id=question.id,
        score=score,
        dimensions=dims,
        suggestions=data.get("suggestions",""),
        raw_eval=content
    )
