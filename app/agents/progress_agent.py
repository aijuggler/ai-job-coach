from app.pipeline.progress import build_progress
from app.services.storage import save_session_json
from app.models.session import InterviewSession
from app.models.progress import ProgressReport

class ProgressAgent:
    def save(self, session: InterviewSession):
        return save_session_json(session)

    def report(self, candidate_id: str) -> ProgressReport:
        return build_progress(candidate_id)
