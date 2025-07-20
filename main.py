import streamlit as st
from app.config.settings import settings
from app.config.logging import setup_logging

# Agents
from app.agents.extraction_agent import ExtractionAgent
from app.agents.gap_question_agent import GapQuestionAgent

# ---------- Init ----------
setup_logging(settings.log_level)
st.set_page_config(page_title="Interview Coach – M1 + M2", layout="wide")

st.title("🧠 LLM Interview Coach – M1 Extraction & M2 Gap Analysis")

# # Resolve deployment names gracefully (some versions used different field names)
# deployment_name = getattr(settings, "azure_chat_deployment", None) or getattr(
#     settings, "azure_openai_chat_deployment", None
# )
# embedding_deployment = getattr(settings, "azure_openai_embedding_deployment", None) or getattr(
#     settings, "azure_openai_embedding_deployment", None
# )

with st.expander("Environment / Deployment Status"):
    st.json(
        {
            "app_env": settings.app_env,
            "log_level": settings.log_level,
            "azure_endpoint_set": bool(settings.azure_openai_endpoint),
            "azure_api_key_set": bool(settings.azure_openai_api_key),
            "chat_deployment": settings.azure_openai_chat_deployment,
            "embedding_deployment": settings.azure_openai_embedding_deployment,
            "max_chars_truncate": settings.max_chars,
        }
    )

# Warning if Azure creds missing
if not (
    settings.azure_openai_endpoint
    and settings.azure_openai_api_key
    and settings.azure_openai_chat_deployment
    and settings.azure_openai_embedding_deployment
):
    st.warning(
        "Azure OpenAI environment variables not fully set. "
        "Extraction will fail until endpoint, api key, and deployment are configured."
    )

# ------------------------------------------------------------------------------
# SECTION 1: Extraction Form
# ------------------------------------------------------------------------------
st.markdown("### 1. Extraction Inputs")

with st.form("extraction_form"):
    resume_file = st.file_uploader("Resume (PDF only)", type=["pdf"])
    jd_file = st.file_uploader("Job Description (PDF or DOCX)", type=["pdf", "docx", "doc"])
    jd_free_text = st.text_area(
        "OR Paste Job / Role Description (leave blank if uploading JD file)",
        height=180,
        placeholder="Paste JD or role summary here if no file..."
    )
    run_extract = st.form_submit_button("➡ Run Extraction")

if run_extract:
    if not resume_file:
        st.error("Please upload a resume PDF.")
    elif not jd_file and not jd_free_text.strip():
        st.error("Provide either a JD file OR free-text job description.")
    else:
        try:
            st.markdown("### 2. Extraction Result")
            with st.spinner("Extracting structured profiles via LLM..."):
                extraction_agent = ExtractionAgent()
                resume_bytes = resume_file.read()
                jd_bytes = jd_file.read() if jd_file else None

                resume_profile, job_profile = extraction_agent.run(
                    resume_bytes=resume_bytes,
                    jd_bytes=jd_bytes,
                    jd_free_text=jd_free_text if jd_bytes is None else None,
                    jd_mime=jd_file.type if jd_file else None,
                )

            # Store in session state
            st.session_state.resume_profile = resume_profile
            st.session_state.job_profile = job_profile
            # Clear previous gap if any
            if "gap_analysis" in st.session_state:
                del st.session_state["gap_analysis"]

            st.success("✅ Extraction complete.")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Resume Profile JSON")
                st.json(resume_profile.model_dump())
            with col2:
                st.subheader("Job Profile JSON")
                st.json(job_profile.model_dump())

            st.markdown("### 3. Quick Summary")
            st.write(f"- **Resume chars:** {resume_profile.raw_length}")
            st.write(
                f"- **Resume skills:** {len(resume_profile.skills)} | Experiences: {len(resume_profile.experiences)}"
            )
            st.write(
                f"- **JD must-have skills:** {len(job_profile.must_have_skills)} | Nice-to-have: {len(job_profile.nice_to_have_skills)}"
            )
            st.info("You can now proceed to run Gap Analysis (M2).")

        except Exception as e:
            st.error(f"Extraction failed: {e}")

# ------------------------------------------------------------------------------
# SECTION 2: Show previously extracted profiles if available
# ------------------------------------------------------------------------------
if "resume_profile" in st.session_state and "job_profile" in st.session_state and not run_extract:
    with st.expander("Latest Extracted Profiles (from session)", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Resume Profile")
            st.json(st.session_state.resume_profile.model_dump())
        with col2:
            st.subheader("Job Profile")
            st.json(st.session_state.job_profile.model_dump())

# ------------------------------------------------------------------------------
# SECTION 3: Gap Analysis (M2)
# ------------------------------------------------------------------------------
st.markdown("### 4. Gap Analysis (M2)")

gap_disabled_reason = None
if "resume_profile" not in st.session_state:
    gap_disabled_reason = "Run extraction first."
elif not settings.azure_openai_embedding_deployment:
    gap_disabled_reason = "Embedding deployment not configured in .env."

run_gap = st.button(
    "⚙️ Run Gap Analysis",
    disabled=gap_disabled_reason is not None
)

if gap_disabled_reason:
    st.caption(f"ℹ️ {gap_disabled_reason}")

if run_gap:
    try:
        gap_agent = GapQuestionAgent()
        with st.spinner("Computing semantic skill gaps..."):
            gap = gap_agent.analyze(
                st.session_state.resume_profile,
                st.session_state.job_profile
            )
        st.session_state.gap_analysis = gap
        st.success("✅ Gap analysis complete.")
    except Exception as e:
        st.error(f"Gap analysis failed: {e}")

# Display gap results if present
if "gap_analysis" in st.session_state:
    gap = st.session_state.gap_analysis
    st.subheader("Gap Summary")
    st.json(gap.summary.model_dump())

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Matched Skills**")
        st.write(gap.matched if gap.matched else "—")
    with c2:
        st.markdown("**Ambiguous Skills**")
        st.write(gap.ambiguous if gap.ambiguous else "—")
    with c3:
        st.markdown("**Missing Skills**")
        st.write(gap.missing if gap.missing else "—")

    with st.expander("Detailed Skill Similarities"):
        for m in gap.matches:
            st.write(
                f"- **Job:** `{m.job_skill}` → "
                f"{'**Resume:** `' + m.resume_skill + '`' if m.resume_skill else '*No close match*'} "
                f"(sim={m.similarity}, {m.category})"
            )

    st.info("Next (M3): Use this gap profile to generate targeted questions.")

# ------------------------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------------------------
st.markdown("---")
st.caption("M1: Extraction | M2: Gap Analysis. Next: M3 Question Generation.")
