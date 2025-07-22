from app.pipeline.progress import build_progress
from app.services.storage import save_session_json
from app.models.session import InterviewSession
from app.models.progress import ProgressReport
from typing import Optional

class ProgressAgent:
    """
    Handles saving interview sessions and building progress reports.
    """

    def save(self, session: InterviewSession):
        """
        Saves the session to persistent storage.
        """
        save_session_json(session)

    def report(
        self,
        candidate_id: str,
        current_session: Optional[InterviewSession] = None,
    ) -> dict:
        """
        Builds a progress report for a candidate.

        This method can now accept the current, in-memory session to ensure
        the report is generated with the most up-to-date data, avoiding
        race conditions with file I/O.
        """
        progress = build_progress(
            candidate_id=candidate_id, current_session=current_session
        )
        return progress

