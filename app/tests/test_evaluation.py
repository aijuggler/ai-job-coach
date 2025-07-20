from app.pipeline.evaluation import evaluate_answer
from app.models.question import Question

class DummyLLM:
    def invoke(self, msgs):
        class Msg:
            content = '{"score":4,"dimensions":{"correctness":4,"clarity":4,"depth":3},"suggestions":"Good but expand depth."}'
        return Msg()

def test_eval_monkeypatch(monkeypatch):
    from app import services
    monkeypatch.setattr(services.llm, "llm_eval", DummyLLM())
    q = Question(id="Q1", text="Explain overfitting.", category="fundamentals")
    fb = evaluate_answer(q, "It happens when…")
    assert fb.score == 4
    assert fb.dimensions["correctness"] == 4
