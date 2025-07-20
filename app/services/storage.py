import json
from pathlib import Path
from app.models.session import InterviewSession

SESSIONS_DIR = Path("app/sessions")
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

def save_session_json(session: InterviewSession):
    path = SESSIONS_DIR / f"{session.session_id}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(session.model_dump(), f, indent=2, default=str)
    return str(path)
