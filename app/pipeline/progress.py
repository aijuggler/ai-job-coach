from __future__ import annotations
from typing import List
from statistics import mean
from app.models.progress import ProgressReport, SessionMetric
from app.services.storage import load_sessions

def build_progress(candidate_id: str) -> ProgressReport:
    raw_sessions = load_sessions(candidate_id)
    metrics: List[SessionMetric] = []

    for data in raw_sessions:
        scores = [fb["score"] for fb in data.get("feedback", []) if isinstance(fb, dict)]
        dims_acc = {"correctness": [], "clarity": [], "depth": []}
        for fb in data.get("feedback", []):
            for k in dims_acc:
                dims_acc[k].append(fb["dimensions"].get(k, 3))

        metric = SessionMetric(
            session_id=data["session_id"],
            started_at=data["started_at"],
            ended_at=data["ended_at"],
            question_count=len(scores),
            avg_score= round(mean(scores), 2) if scores else 0.0,
            dims_avg={k: round(mean(v), 2) if v else 0.0 for k, v in dims_acc.items()},
        )
        metrics.append(metric)

    overall = round(mean([m.avg_score for m in metrics]), 2) if metrics else 0.0
    return ProgressReport(candidate_id=candidate_id, sessions=metrics, overall_avg=overall)
