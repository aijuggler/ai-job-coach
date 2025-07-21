import streamlit as st
from collections import defaultdict
import io, numpy as np, soundfile as sf

from app.config.settings import settings
from app.config.logging import setup_logging

# Agents
from app.agents.extraction_agent import ExtractionAgent
from app.agents.gap_question_agent import GapQuestionAgent
from app.agents.interview_agent import InterviewAgent

# Models
from app.models.question import Question

# ---------- Init ----------
setup_logging(settings.log_level)
st.set_page_config(page_title="Interview Coach – M1‑M4", layout="wide")
st.title("🧠 LLM Interview Coach – Extraction ▶ Gap ▶ Questions ▶ Interview")

# ------------------------------------------------------------------
# Environment
# ------------------------------------------------------------------
with st.expander("Environment / Deployment Status"):
    st.json(
        {
            "app_env": settings.app_env,
            "log_level": settings.log_level,
            "azure_endpoint_set": bool(settings.azure_openai_endpoint),
            "azure_api_key_set": bool(settings.azure_openai_api_key),
            "chat_deployment": settings.azure_openai_chat_deployment,
            "embedding_deployment": settings.azure_openai_embedding_deployment,
        }
    )

# ------------------------------------------------------------------
# 1. Extraction
# ------------------------------------------------------------------
st.markdown("### 1. Extraction Inputs")

with st.form("extraction_form"):
    resume_file = st.file_uploader("Resume (PDF only)", type=["pdf"])
    jd_file = st.file_uploader("Job Description (PDF/DOCX)", type=["pdf", "docx", "doc"])
    jd_free_text = st.text_area(
        "OR Paste Job / Role Description (leave blank if uploading JD file)",
        height=180,
    )
    run_extract = st.form_submit_button("➡ Run Extraction")

if run_extract:
    if not resume_file:
        st.error("Please upload a resume PDF.")
    elif not jd_file and not jd_free_text.strip():
        st.error("Provide either a JD file OR free‑text job description.")
    else:
        try:
            with st.spinner("Extracting via LLM…"):
                agent = ExtractionAgent()
                resume_profile, job_profile = agent.run(
                    resume_bytes=resume_file.read(),
                    jd_bytes=jd_file.read() if jd_file else None,
                    jd_free_text=jd_free_text if jd_file is None else None,
                    jd_mime=jd_file.type if jd_file else None,
                )
            st.success("✅ Extraction complete.")
            st.session_state.resume_profile = resume_profile
            st.session_state.job_profile = job_profile
            for k in ("gap_analysis", "question_plan", "questions", "interview_session"):
                st.session_state.pop(k, None)
        except Exception as e:
            st.error(f"Extraction failed: {e}")

if "resume_profile" in st.session_state and "job_profile" in st.session_state and not run_extract:
    with st.expander("Extracted Profiles", expanded=False):
        c1, c2 = st.columns(2)
        c1.json(st.session_state.resume_profile.model_dump())
        c2.json(st.session_state.job_profile.model_dump())

# ------------------------------------------------------------------
# 2. Gap Analysis
# ------------------------------------------------------------------
st.markdown("### 2. Gap Analysis (M2)")

if "resume_profile" not in st.session_state:
    st.caption("ℹ️ Run extraction first.")
else:
    if st.button("⚙️ Run Gap Analysis"):
        try:
            gap_agent = GapQuestionAgent()
            with st.spinner("Computing semantic gaps…"):
                gap = gap_agent.analyze(
                    st.session_state.resume_profile,
                    st.session_state.job_profile
                )
            st.session_state.gap_analysis = gap
            for k in ("question_plan", "questions", "interview_session"):
                st.session_state.pop(k, None)
            st.success("Gap analysis complete.")
        except Exception as e:
            st.error(f"Gap analysis failed: {e}")

if "gap_analysis" in st.session_state:
    gap = st.session_state.gap_analysis
    st.subheader("Gap Summary JSON")
    st.json(gap.summary.model_dump())

    c1, c2, c3 = st.columns(3)
    c1.markdown("**Matched Skills**")
    c1.write(gap.matched if gap.matched else "—")
    c2.markdown("**Ambiguous Skills**")
    c2.write(gap.ambiguous if gap.ambiguous else "—")
    c3.markdown("**Missing Skills**")
    c3.write(gap.missing if gap.missing else "—")

    with st.expander("Detailed Skill Similarities", expanded=False):
        for m in gap.matches:
            st.write(
                f"- **Job:** `{m.job_skill}` → "
                f"{'`' + m.resume_skill + '`' if m.resume_skill else '*No close match*'} "
                f"(sim={m.similarity}, {m.category})"
            )

# ------------------------------------------------------------------
# 3. Question Generation
# ------------------------------------------------------------------
st.markdown("### 3. Question Generation (M3)")

if "gap_analysis" not in st.session_state:
    st.caption("ℹ️ Run gap analysis first.")
else:
    if st.button("🧩 Generate Questions (M3)"):
        try:
            gap_agent = GapQuestionAgent()
            with st.spinner("Generating questions…"):
                _, plan, q_models = gap_agent.plan_and_generate(
                    resume=st.session_state.resume_profile,
                    job=st.session_state.job_profile,
                    gap=st.session_state.gap_analysis,
                    total=18
                )
            st.session_state.question_plan = plan
            # 🔑 store as dicts
            st.session_state.questions = [q.model_dump() for q in q_models]
            st.session_state.pop("interview_session", None)
            st.success("Questions ready.")
        except Exception as e:
            st.error(f"Question generation failed: {e}")

if "questions" in st.session_state:
    plan = st.session_state.question_plan
    q_dicts = st.session_state.questions
    q_models = [Question(**d) for d in q_dicts]

    st.subheader("Plan")
    st.json(plan.as_bucket_counts())

    grouped = defaultdict(list)
    for q in q_models:
        grouped[q.category].append(q)

    for cat in ["fundamentals", "strengths", "gaps", "behavioral", "advanced"]:
        if cat in grouped:
            with st.expander(f"{cat.capitalize()} ({len(grouped[cat])})", expanded=False):
                for q in grouped[cat]:
                    st.markdown(f"**{q.id}**: {q.text}")
                    if q.target_skills:
                        st.caption(f"Skills: {', '.join(q.target_skills)} · Diff: {q.difficulty}")
                    if q.rationale:
                        st.write(f"*Rationale:* {q.rationale}")

    # download
    if st.download_button(
        "Download Questions JSON",
        data=str(q_dicts).encode(),
        file_name="questions.json",
        mime="application/json"
    ):
        pass

# ------------------------------------------------------------------
# 4. Interview Loop
# ------------------------------------------------------------------
st.markdown("### 4. Mock Interview (M4 + M5 Evaluation)")

interview_agent = InterviewAgent()
if "interview_session" not in st.session_state:
    st.session_state.interview_session = None

def _rerun():
    st.rerun()

cols = st.columns(3)
start = cols[0].button("🎬 Start Interview", disabled="questions" not in st.session_state)
finish = cols[1].button("🛑 Finish", disabled=st.session_state.interview_session is None or st.session_state.interview_session.is_finished())
reset  = cols[2].button("♻️ Reset",  disabled=st.session_state.interview_session is None)

# ---------- start ----------
if start:
    qs_models = [Question(**d) for d in st.session_state.questions]
    sess = interview_agent.start("candidate_001", qs_models)
    st.session_state.interview_session = sess
    _rerun()

# ---------- finish ----------
if finish and st.session_state.interview_session:
    sess = st.session_state.interview_session
    interview_agent.finish(sess)
    from app.agents import ProgressAgent
    ProgressAgent().save(sess)
    st.success("Session saved.")
    _rerun()

# ---------- reset ----------
if reset:
    st.session_state.interview_session = None
    st.success("Session reset.")
    _rerun()

# ---------- feedback helper ----------
def show_feedback(fb):
    st.success(f"Score: **{fb.score}/5**")
    st.caption(f"Correct {fb.dimensions['correctness']} · "
               f"Clarity {fb.dimensions['clarity']} · "
               f"Depth {fb.dimensions['depth']}")
    st.write(f"**Suggestion:** {fb.suggestions}")

# ---------- live session ----------
sess = st.session_state.interview_session
if sess:
    if sess.is_finished():
        st.success("Interview complete.")
    else:
        q = interview_agent.current_question(sess)
        st.markdown(f"**Q{sess.current_index+1}/{len(sess.questions)}** – {q.text}")

        # --- choose input mode ---
        audio_mode = st.checkbox(
            "🎙️ Answer with microphone or audio file", key=f"audio_mode_{q.id}", value=False
        )

        if audio_mode:
    # ------------- recorder -------------
            try:
                from st_audiorec import st_audiorec
                wav_data = st_audiorec()
            except ModuleNotFoundError:
                wav_data = None
                st.warning("Recorder component not installed.")

            rec_key = f"rec_bytes_{q.id}"
            if wav_data is not None:
                # convert bytes OR numpy → raw wav bytes once, persist
                if isinstance(wav_data, (bytes, bytearray)):
                    st.session_state[rec_key] = wav_data
                elif isinstance(wav_data, np.ndarray):
                    buf = io.BytesIO()
                    sf.write(buf, wav_data, samplerate=16000, format="WAV")
                    st.session_state[rec_key] = buf.getvalue()

            # optional upload
            audio_file = st.file_uploader("…or upload WAV/MP3", type=["wav", "mp3"], key=f"aud_{q.id}")

            # ---- debounce flag ----
            proc_flag = f"processing_{q.id}"
            if proc_flag not in st.session_state:
                st.session_state[proc_flag] = False

            btn_disabled = st.session_state[proc_flag]
            if st.button("Submit Audio", key=f"submit_audio_{q.id}", disabled=btn_disabled):
                audio_bytes = st.session_state.get(rec_key) or (audio_file.read() if audio_file else None)

                if not audio_bytes:
                    st.warning("Record or upload audio first.")
                else:
                    st.session_state[proc_flag] = True   # lock UI
                    with st.spinner("Transcribing & scoring…"):
                        try:
                            fb = interview_agent.answer(sess, audio_bytes=audio_bytes)
                            show_feedback(fb)
                            interview_agent.next(sess)
                            # clean up
                            for k in (rec_key, proc_flag):
                                st.session_state.pop(k, None)
                            st.session_state.interview_session = sess
                            _rerun()
                        except Exception as e:
                            st.error(f"Audio processing failed: {e}")
                            st.session_state[proc_flag] = False  # unlock

            if audio_file:
                st.session_state[rec_key] = audio_file.read()

    # -------- history panels --------
    if sess.answers:
        with st.expander("Answers so far", expanded=False):
            for a in sess.answers:
                st.markdown(f"**{a.question_id}** – {a.answer_text}")

    if sess.feedback:
        with st.expander("Feedback so far", expanded=False):
            for fb in sess.feedback:
                st.markdown(
                    f"**{fb.question_id}** → score **{fb.score}** /5  \n"
                    f"Correctness {fb.dimensions['correctness']}, "
                    f"Clarity {fb.dimensions['clarity']}, "
                    f"Depth {fb.dimensions['depth']}  \n"
                    f"*Suggestion:* {fb.suggestions}"
                )

# ------------------------------------------------------------------
st.markdown("---")

# ------------------------------------------------------------------
# 5. Progress Tracker (M6)
# ------------------------------------------------------------------
st.markdown("### 5. Progress (M6)")

if st.button("🔄 Refresh Progress"):
    from app.agents import ProgressAgent
    pr_agent = ProgressAgent()
    report = pr_agent.report("candidate_001")
    st.session_state.progress_report = report

if "progress_report" in st.session_state:
    report = st.session_state.progress_report
    st.subheader(f"Overall Avg Score: {report.overall_avg}")

    import pandas as pd
    df = pd.DataFrame([m.model_dump() for m in report.sessions])

    if df.empty:
        st.info("No finished interview sessions yet – complete one and refresh.")
    else:
        cols_show = ["session_id", "started_at", "ended_at", "question_count", "avg_score"]
        st.dataframe(df[cols_show], hide_index=True)
        st.line_chart(df.set_index("session_id")["avg_score"])
else:
    st.caption("Run and finish at least one interview, then refresh.")
