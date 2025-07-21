from app.models.progress import ProgressReport
from app.pipeline.progress import build_progress
from app.services.storage import save_session_json
from app.models.session import InterviewSession
from datetime import datetime

def _fake_session(sess_id, scores):
    return {
        "session_id": sess_id,
        "candidate_id": "candidate_001",
        "started_at": datetime.utcnow().isoformat(),
        "ended_at": datetime.utcnow().isoformat(),
        "feedback": [
            {"question_id":"Q1","score":s,"dimensions":{"correctness":s,"clarity":s,"depth":s}} for s in scores
        ]
    }

def test_progress_build(tmp_path, monkeypatch):
    from app.services import storage
    monkeypatch.setattr(storage, "SESSIONS_DIR", tmp_path)

    # create two fake sessions
    import json, uuid
    for i, scores in enumerate([[3,4,4],[4,5,5]]):
        data = _fake_session(f"sess{i}", scores)
        (tmp_path / f"sess{i}_candidate_001.json").write_text(json.dumps(data))

    report = build_progress("candidate_001")
    assert isinstance(report, ProgressReport)
    assert len(report.sessions) == 2
    assert report.overall_avg > 0
