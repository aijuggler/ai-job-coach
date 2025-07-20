# app/agents/extraction_agent.py
from typing import Optional, Tuple
from app.utils.pdf_loader import pdf_bytes_to_text
from app.utils.docx_loader import docx_bytes_to_text
from app.pipeline.extraction import extract_pipeline
from app.models.resume import ResumeProfile
from app.models.job import JobProfile
from app.services.llm import llm_deterministic  # shared instance

class ExtractionAgent:
    """
    Converts uploaded files to text and calls extraction pipeline using the shared LLM.
    """

    def __init__(self, llm_instance=None):
        self.llm = llm_instance or llm_deterministic

    def run(
        self,
        resume_bytes: bytes,
        jd_bytes: Optional[bytes] = None,
        jd_free_text: Optional[str] = None,
        jd_mime: Optional[str] = None
    ) -> Tuple[ResumeProfile, JobProfile]:

        resume_text = pdf_bytes_to_text(resume_bytes)

        if jd_bytes:
            if jd_mime and "pdf" in jd_mime.lower():
                job_text = pdf_bytes_to_text(jd_bytes)
            else:
                job_text = docx_bytes_to_text(jd_bytes)
        else:
            job_text = jd_free_text or ""

        return extract_pipeline(resume_text, job_text, self.llm)
