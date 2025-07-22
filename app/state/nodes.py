# app/state/nodes.py

from app.agents import GapQuestionAgent, InterviewAgent, ProgressAgent
from app.pipeline.extraction import extract_pipeline
from app.state.graph_state import GraphState
from app.utils.pdf_loader import pdf_bytes_to_text
from app.utils.docx_loader import docx_bytes_to_text
# Import the specific, deterministic LLM for the extraction task
from app.services.llm import llm_deterministic
# Import the Answer model to construct the answer object
from app.models import Answer, InterviewSession, AnswerFeedback

# The other agents will internally call the correct LLM service as needed.
gap_question_agent = GapQuestionAgent()
interview_agent = InterviewAgent()
progress_agent = ProgressAgent()


def extract_node(state: GraphState) -> dict:
    """
    Processes resume and JD inputs and calls the extraction pipeline directly.
    """
    print("---NODE: EXTRACTING RESUME AND JOB DESCRIPTION---")
    resume_text = pdf_bytes_to_text(state["resume_bytes"])
    job_description_text = ""
    if state.get("job_bytes"):
        job_description_text = pdf_bytes_to_text(state["job_bytes"])
    elif state.get("job_text"):
        job_description_text = state["job_text"]
    else:
        raise ValueError("Either job description file or text must be provided.")
    resume_profile, job_profile = extract_pipeline(
        resume_text=resume_text, 
        job_text=job_description_text, 
        llm=llm_deterministic
    )
    return {
        "resume_profile": resume_profile,
        "job_profile": job_profile,
    }


def gap_and_questions_node(state: GraphState) -> dict:
    """
    Invokes the GapQuestionAgent by calling its methods in sequence.
    """
    print("---NODE: ANALYZING GAPS AND GENERATING QUESTIONS---")
    gap_analysis = gap_question_agent.analyze(
        resume=state["resume_profile"], job=state["job_profile"]
    )
    question_plan = gap_question_agent.plan(
        resume=state["resume_profile"],
        job=state["job_profile"],
        gap=gap_analysis
    )
    questions = gap_question_agent.generate(
        resume=state["resume_profile"],
        job=state["job_profile"],
        gap=gap_analysis,
        plan=question_plan
    )
    return {"gap_analysis": gap_analysis, "question_list": questions}


def interview_setup_node(state: GraphState) -> dict:
    """
    Invokes the InterviewAgent to initialize the interview session.
    """
    print("---NODE: SETTING UP INTERVIEW---")
    session = interview_agent.start(
        candidate_id="candidate_123", questions=state["question_list"]
    )
    return {
        "interview_session": session,
        "current_question_index": 0,
        "all_feedback": [],
    }


def interview_loop_node(state: GraphState) -> dict:
    """
    Calls the agent's 'answer' method with the exact signature it expects.
    """
    print(f"---NODE: INTERVIEW LOOP (Question #{state['current_question_index'] + 1})---")
    simulated_answer_text = "This is a simulated answer to demonstrate the graph flow."
    feedback = interview_agent.answer(
        session=state["interview_session"],
        answer_text=simulated_answer_text
    )
    updated_feedback_list = state["all_feedback"] + [feedback]
    return {
        "all_feedback": updated_feedback_list,
        "current_question_index": state["current_question_index"] + 1,
    }

def finish_interview_node(state: GraphState) -> dict:
    """
    This new node formally finishes the interview session by calling the
    InterviewAgent's finish method. This sets the 'ended_at' timestamp
    and returns the completed session object.
    """
    print("---NODE: FINISHING INTERVIEW SESSION---")
    finished_session = interview_agent.finish(session=state["interview_session"])
    return {"interview_session": finished_session}


def progress_node(state: GraphState) -> dict:
    """
    This node now passes the completed, in-memory interview session
    directly to the progress agent, ensuring the report is generated
    with the final, correct data.
    """
    print("---NODE: GENERATING PROGRESS REPORT---")
    report = progress_agent.report(
        candidate_id=state["interview_session"].candidate_id,
        current_session=state["interview_session"]
    )
    return {"progress_report": report}
