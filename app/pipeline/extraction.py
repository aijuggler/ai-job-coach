# app/pipeline/extraction.py
import json
from typing import Tuple, Optional
from app.config.settings import settings
from app.models.resume import ResumeProfile
from app.models.job import JobProfile

# ---- Prompt Templates ----
RESUME_SCHEMA = """
{
  "full_name": str|null,
  "headline": str|null,
  "summary": str|null,
  "skills":[{"name":str,"evidence":str|null,"confidence":float}],
  "experiences":[{"role":str,"company":str|null,"start":str|null,"end":str|null,"bullets":[str],"skills":[str]}],
  "education":[{"degree":str,"institution":str|null,"end":str|null}],
  "projects":[{"name":str,"description":str|null,"impact":str|null,"skills":[str]}],
  "certifications":[str],
  "inferred_skills":[{"name":str,"reason":str,"confidence":float}]
}
""".strip()

JOB_SCHEMA = """
{
  "title": str|null,
  "company": str|null,
  "must_have_skills":[{"name":str,"reason":str,"confidence":float}],
  "nice_to_have_skills":[{"name":str,"reason":str,"confidence":float}],
  "responsibilities":[str],
  "requirements_raw":[str],
  "domain_keywords":[str],
  "inferred_hidden_expectations":[{"expectation":str,"reason":str}]
}
""".strip()

RESUME_SYSTEM = "You are a precise resume extraction engine. Output ONLY raw JSON."
JOB_SYSTEM = "You are a precise job description extraction engine. Output ONLY raw JSON."

def _build_resume_user_prompt(resume_text: str) -> str:
    truncated = resume_text[:settings.max_chars]
    return f"""
Return ONLY valid JSON (no markdown, no extra text) matching this schema:
{RESUME_SCHEMA}

RULES:
- confidence between 0.50 and 0.99 (never 1.0)
- no hallucination; only strongly implied in 'inferred_skills'
- dates: 'YYYY-MM' if month present, else 'YYYY', else null
RESUME_TEXT:
\"\"\"{truncated}\"\"\"
""".strip()

def _build_job_user_prompt(job_text: str) -> str:
    truncated = job_text[:settings.max_chars]
    return f"""
Return ONLY valid JSON (no markdown) matching this schema:
{JOB_SCHEMA}

RULES:
- explicit required => must_have_skills
- words like 'preferred', 'nice', 'bonus' => nice_to_have
- responsibilities: imperative concise phrases
- hidden expectations only if clearly implied (e.g. 'stakeholder communication')
JOB_TEXT:
\"\"\"{truncated}\"\"\"
""".strip()

def _invoke_json(llm, system_prompt: str, user_prompt: str, retries: int = 2) -> str:
    """
    Uses llm.invoke(messages) (LangChain style).
    Retries if JSON parse fails.
    """
    last_err: Optional[Exception] = None
    messages = [
        ("system", system_prompt),
        ("user", user_prompt)
    ]
    for attempt in range(retries + 1):
        try:
            resp = llm.invoke(messages)   # returns AIMessage
            content = resp.content
            # Some Azure responses may return a list of message chunks; handle both
            if isinstance(content, list):
                # LangChain sometimes returns a list of content parts; join text parts
                text_parts = [c["text"] for c in content if isinstance(c, dict) and c.get("type") == "text"]
                content = "".join(text_parts)
            json.loads(content)  # validation
            return content
        except Exception as e:
            last_err = e
            if attempt == retries:
                raise
    raise last_err  # Shouldn’t reach

def extract_resume_text(resume_text: str, llm) -> ResumeProfile:
    raw_json = _invoke_json(
        llm=llm,
        system_prompt=RESUME_SYSTEM,
        user_prompt=_build_resume_user_prompt(resume_text),
        retries=settings.extraction_retries
    )
    data = json.loads(raw_json)
    data["raw_length"] = len(resume_text)
    return ResumeProfile(**data)

def extract_job_text(job_text: str, llm) -> JobProfile:
    raw_json = _invoke_json(
        llm=llm,
        system_prompt=JOB_SYSTEM,
        user_prompt=_build_job_user_prompt(job_text),
        retries=settings.extraction_retries
    )
    data = json.loads(raw_json)
    data["raw_length"] = len(job_text)
    return JobProfile(**data)

def extract_pipeline(resume_text: str, job_text: str, llm) -> Tuple[ResumeProfile, JobProfile]:
    return extract_resume_text(resume_text, llm), extract_job_text(job_text, llm)
