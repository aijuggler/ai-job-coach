import json, os
from pathlib import Path
from typing import List
from app.models.session import InterviewSession

SESSIONS_DIR = Path("app/sessions")
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

def save_session_json(session: InterviewSession) -> str:
    path = SESSIONS_DIR / f"{session.session_id}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(session.model_dump(), f, indent=2, default=str)
    return str(path)

def load_sessions(candidate_id: str) -> List[dict]:
    """Return a list of saved session‑dicts for the given candidate_id."""
    data: List[dict] = []
    for f in SESSIONS_DIR.glob("*.json"):        # look at every file
        try:
            obj = json.loads(f.read_text())
            if obj.get("candidate_id") == candidate_id:
                data.append(obj)
        except Exception:
            continue
    # sort by start time
    data.sort(key=lambda d: d.get("started_at", ""))
    return data