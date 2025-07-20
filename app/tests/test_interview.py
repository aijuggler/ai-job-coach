from app.pipeline.interview import (
    start_session, get_current_question, record_answer,
    next_question, is_finished
)
from app.models.question import Question

def test_interview_loop_basic():
    questions = [
        Question(id="Q1", text="What is overfitting?", category="fundamentals", target_skills=["ml"], difficulty="easy"),
        Question(id="Q2", text="Describe a project you led.", category="behavioral", target_skills=[], difficulty="medium")
    ]
    session = start_session("cand1", questions, "sess_test")
    assert get_current_question(session).id == "Q1"
    record_answer(session, "Overfitting is ...")
    next_question(session)
    assert get_current_question(session).id == "Q2"
    record_answer(session, "I led ...")
    next_question(session)
    assert is_finished(session)
    assert len(session.answers) == 2

from app.pipeline.interview import start_session, next_question
from app.models.question import Question

def test_next_question():
    qs = [Question(id=f"Q{i}", text=f"q{i}", category="fundamentals") for i in range(1,4)]
    s = start_session("cand", qs, "sess")
    assert s.current_index == 0
    next_question(s)          # advance to Q2
    assert s.current_index == 1
    next_question(s)          # advance to Q3
    assert s.current_index == 2
    next_question(s)          # should finish
    assert s.is_finished()
