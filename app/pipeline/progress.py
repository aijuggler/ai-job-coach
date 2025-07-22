# app/pipeline/progress.py

from __future__ import annotations
from typing import List, Optional
from statistics import mean
from app.models.progress import ProgressReport, SessionMetric
from app.models.session import InterviewSession # Import InterviewSession
from app.services.storage import load_sessions

def build_progress(candidate_id: str, current_session: Optional[InterviewSession] = None) -> ProgressReport:
    """
    Builds a progress report for a candidate.

    It loads all historical sessions from storage and can optionally include the
    current, in-memory session to ensure the most up-to-date data is used.
    """
    # Load historical sessions from disk
    raw_sessions = load_sessions(candidate_id)
    
    # Create a set of session IDs from disk to avoid duplicates
    disk_session_ids = {s.get("session_id") for s in raw_sessions}

    # If a current session is provided and not already on disk, add it to our list
    if current_session and current_session.session_id not in disk_session_ids:
        # Convert the Pydantic model to a dict to match the format of other sessions
        raw_sessions.append(current_session.dict())

    metrics: List[SessionMetric] = []

    for data in raw_sessions:
        # --- THE FIX ---
        # This check ensures we only process sessions that have been properly
        # completed and have an 'ended_at' timestamp. This prevents errors
        # from incomplete, historical session files.
        if data.get("ended_at") is None:
            continue # Skip this incomplete session

        scores = [fb["score"] for fb in data.get("feedback", []) if isinstance(fb, dict)]
        dims_acc = {"correctness": [], "clarity": [], "depth": []}
        for fb in data.get("feedback", []):
            if isinstance(fb, dict) and "dimensions" in fb:
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
