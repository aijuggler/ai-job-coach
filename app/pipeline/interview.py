from __future__ import annotations
from typing import Optional
from datetime import datetime
from app.models.session import InterviewSession
from app.models.question import Question
from app.models.answer import Answer

def start_session(candidate_id: str, questions: list[Question], session_id: str) -> InterviewSession:
    return InterviewSession(
        session_id=session_id,
        candidate_id=candidate_id,
        questions=questions,
        current_index=0
    )

def get_current_question(session: InterviewSession) -> Optional[Question]:
    if session.current_index < len(session.questions):
        return session.questions[session.current_index]
    return None

def record_answer(session: InterviewSession, answer_text: str) -> Answer:
    q = get_current_question(session)
    if q is None:
        raise RuntimeError("No active question to answer.")
    ans = Answer(
        question_id=q.id,
        question_text=q.text,
        category=q.category,
        answer_text=answer_text
    )
    session.answers.append(ans)
    return ans

def next_question(session: InterviewSession) -> Optional[Question]:
    # advance index
    if session.current_index < len(session.questions):
        session.current_index += 1      # <‑‑ this increments
    if session.current_index >= len(session.questions):
        session.ended_at = datetime.utcnow()
        return None
    return get_current_question(session)


def is_finished(session: InterviewSession) -> bool:
    return session.is_finished()

def remaining_count(session: InterviewSession) -> int:
    return max(0, len(session.questions) - session.current_index)

def finish_session(session: InterviewSession):
    if session.ended_at is None:
        session.ended_at = datetime.utcnow()

def session_summary(session: InterviewSession) -> dict:
    return {
        "session_id": session.session_id,
        "candidate_id": session.candidate_id,
        "total_questions": len(session.questions),
        "answered": len(session.answers),
        "remaining": remaining_count(session),
        "finished": session.is_finished(),
        "started_at": session.started_at.isoformat(),
        "ended_at": session.ended_at.isoformat() if session.ended_at else None
    }
