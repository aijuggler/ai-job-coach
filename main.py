# main.py

import sys
import os
import streamlit as st
import io
import base64

# --- The Correct Path Fix ---
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.state.build import app
from app.models import ResumeProfile, JobProfile, GapAnalysis, Question, ProgressReport, InterviewSession, AnswerFeedback
from app.agents import InterviewAgent, ProgressAgent

st.set_page_config(layout="wide")
st.title("LLM-Powered Job Interview Coach (LangGraph Edition)")

# --- 1. Session State Initialization for Multi-Step Flow ---
if "stage" not in st.session_state:
    st.session_state.stage = "analysis_pending"
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "interview_session" not in st.session_state:
    st.session_state.interview_session = None
if "current_feedback" not in st.session_state:
    st.session_state.current_feedback = None

# --- Instantiate Agents for Interactive Part ---
interview_agent = InterviewAgent()
progress_agent = ProgressAgent()

# --- 2. UI Layout ---
st.sidebar.header("Controls")

with st.sidebar:
    if st.session_state.stage == "analysis_pending":
        resume_file = st.file_uploader("Upload your Resume (PDF or DOCX)", type=["pdf", "docx"])
        st.sidebar.subheader("Provide Job Description")
        job_desc_file = st.file_uploader("Upload Job Description (PDF or DOCX)", type=["pdf", "docx"])
        job_desc_text = st.text_area("Or Paste the Job Description Here")

        if st.button("1. Analyze Resume & JD", type="primary"):
            if resume_file and (job_desc_file or job_desc_text):
                with st.spinner("The AI Coach is preparing your session..."):
                    initial_state = {
                        "resume_bytes": resume_file.getvalue(),
                        "job_bytes": job_desc_file.getvalue() if job_desc_file else None,
                        "job_text": job_desc_text if not job_desc_file and job_desc_text else None,
                    }
                    config = {"recursion_limit": 100, "interrupt_before": ["interview_setup"]}
                    analysis_result = app.invoke(initial_state, config=config)
                    st.session_state.analysis_results = analysis_result
                    st.session_state.stage = "analysis_complete"
                st.rerun()
            else:
                st.error("Please upload a resume and provide a job description.")
    
    with st.expander("View Agent Workflow"):
        try:
            graph_image = app.get_graph().draw_mermaid_png()
            b64_image = base64.b64encode(graph_image).decode("utf-8")
            st.image(f"data:image/png;base64,{b64_image}")
        except Exception as e:
            st.warning(f"Could not render graph visualization: {e}")


# --- 3. Display Analysis Results ---
if st.session_state.stage == "analysis_complete" and st.session_state.analysis_results:
    state = st.session_state.analysis_results
    
    st.header("Analysis & Interview Plan")
    st.info("The AI Coach has analyzed your resume against the job and prepared a set of interview questions.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Resume Profile")
        if state.get("resume_profile"): st.json(state["resume_profile"].model_dump(), expanded=False)
    with col2:
        st.subheader("Gap Analysis")
        if state.get("gap_analysis"): st.json(state["gap_analysis"].model_dump(), expanded=False)

    st.subheader("Generated Interview Questions")
    if state.get("question_list"):
        for i, q in enumerate(state["question_list"]):
            with st.expander(f"Question {i+1}: {q.text}"):
                st.write(f"**Category:** {q.category}")
                st.write(f"**Target Skills:** {', '.join(q.target_skills)}")

    st.success("Analysis complete. You are now ready to start the interview.")
    
    if st.button("2. Start Interactive Interview", type="primary"):
        questions = st.session_state.analysis_results.get("question_list", [])
        session = interview_agent.start(candidate_id="candidate_123", questions=questions)
        st.session_state.interview_session = session
        st.session_state.stage = "interviewing"
        st.rerun()

# --- 4. Interactive Interview Stage ---
elif st.session_state.stage == "interviewing":
    st.header("Interview in Progress...")
    
    session = st.session_state.interview_session
    if not session or session.current_index >= len(session.questions):
        st.session_state.stage = "report_pending"
        st.rerun()

    current_question = session.questions[session.current_index]
    
    st.subheader(f"Question {session.current_index + 1}/{len(session.questions)}")
    st.markdown(f"#### {current_question.text}")
    st.write(f"**Category:** {current_question.category}")

    if st.session_state.current_feedback:
        fb = st.session_state.current_feedback
        with st.expander("View Feedback on Your Last Answer", expanded=True):
            st.metric("Score", f"{fb.score}/5")
            st.write(f"**Suggestion:** {fb.suggestions}")
            # --- THE FIX: Use dictionary key access (.get()) for the dimensions dict ---
            st.write(f"**Correctness:** {fb.dimensions.get('correctness', 'N/A')}/5 | **Clarity:** {fb.dimensions.get('clarity', 'N/A')}/5 | **Depth:** {fb.dimensions.get('depth', 'N/A')}/5")
        st.divider()

    with st.form(key=f"answer_form_{session.current_index}"):
        answer_text = st.text_area("Your Answer (Chat Mode):", key=f"text_{session.current_index}")
        submitted = st.form_submit_button("Submit Answer")

        if submitted and answer_text:
            with st.spinner("Evaluating your answer..."):
                feedback = interview_agent.answer(session=session, answer_text=answer_text)
                interview_agent.next(session)
                st.session_state.current_feedback = feedback
            st.rerun()

    st.divider()
    if st.button("End Interview Early", type="secondary"):
        st.warning("Ending interview... generating final report.")
        st.session_state.stage = "report_pending"
        st.rerun()


# --- 5. Final Report Stage ---
elif st.session_state.stage == "report_pending":
    st.header("Interview Complete!")
    with st.spinner("Generating your final report..."):
        session = st.session_state.interview_session
        finished_session = interview_agent.finish(session=session)
        report = progress_agent.report(candidate_id=finished_session.candidate_id, current_session=finished_session)

        # --- NEW: Stylish, Text-Based Report for the Current Session ---
        st.subheader("Your Performance Summary")

        # Find the metric for the session we just finished
        current_session_metric = None
        for metric in report.sessions:
            if metric.session_id == finished_session.session_id:
                current_session_metric = metric
                break
        
        if current_session_metric:
            st.success("Here's how you did in this session:")
            
            # Key Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Overall Average Score", f"{current_session_metric.avg_score:.2f} / 5.0")
            col2.metric("Questions Answered", f"{current_session_metric.question_count} / {len(finished_session.questions)}")
            
            # Performance Dimensions
            st.markdown("---")
            st.markdown("##### Performance Across Dimensions:")
            
            dims = current_session_metric.dims_avg
            col1, col2, col3 = st.columns(3)
            col1.metric("Avg. Correctness", f"{dims.get('correctness', 0):.2f} / 5.0")
            col2.metric("Avg. Clarity", f"{dims.get('clarity', 0):.2f} / 5.0")
            col3.metric("Avg. Depth", f"{dims.get('depth', 0):.2f} / 5.0")

        else:
            st.warning("Could not retrieve the summary for the session you just completed.")

    st.markdown("---")
    if st.button("Start Over"):
        st.session_state.clear()
        st.rerun()

else:
    st.info("Upload your resume and a job description on the left, then click 'Analyze' to start.")
