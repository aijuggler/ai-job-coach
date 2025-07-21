from typing import List, Optional
from app.models.question import Question
from app.models.session import InterviewSession
from app.pipeline import interview
from app.services.id_gen import new_session_id
from app.services.storage import save_session_json
from app.pipeline import interview, evaluation
from app.models.answer import AnswerFeedback
from app.services.audio import transcribe_audio, AudioTranscriptionError

class InterviewAgent:
    """
    Handles starting and progressing through an interview session.
    (Evaluation comes in M5.)
    """

    def start(self, candidate_id: str, questions: List[Question]) -> InterviewSession:
        sess_id = new_session_id()
        session = interview.start_session(candidate_id, questions, sess_id)
        return session

    def answer(
        self,
        session: InterviewSession,
        answer_text: str | None = None,
        audio_bytes: bytes | None = None,
        language: str = "en-US",
    ):
        # Determine input mode
        if audio_bytes and not answer_text:
            try:
                answer_text = transcribe_audio(audio_bytes, language=language)
            except AudioTranscriptionError as e:
                raise RuntimeError(f"Audio transcription error: {e}")
        if not answer_text:
            raise ValueError("No answer text provided.")

        # record + evaluate (unchanged)
        ans = interview.record_answer(session, answer_text)
        q = interview.get_current_question(session)
        feedback = evaluation.evaluate_answer(q, answer_text)
        session.feedback.append(feedback)
        return feedback
    
    def next(self, session: InterviewSession):
        return interview.next_question(session)

    def current_question(self, session: InterviewSession):
        return interview.get_current_question(session)

    def finish(self, session: InterviewSession):
        interview.finish_session(session)
        save_session_json(session)
        return session

    def save(self, session: InterviewSession):
        return save_session_json(session)
