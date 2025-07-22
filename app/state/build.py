# app/state/build.py

from langgraph.graph import StateGraph, END
from .graph_state import GraphState
from .nodes import (
    extract_node,
    gap_and_questions_node,
    interview_setup_node,
    interview_loop_node,
    finish_interview_node,  # Import the new node
    progress_node
)

def should_continue(state: GraphState) -> str:
    """
    A conditional edge function that determines the next step after the
    interview setup or after a question has been answered.
    
    Args:
        state: The current graph state.
        
    Returns:
        "continue" if there are more questions in the list, otherwise "end".
    """
    if state["current_question_index"] < len(state["question_list"]):
        return "continue"
    else:
        return "end"

# Create a new StateGraph with our GraphState definition.
workflow = StateGraph(GraphState)

# Add all the nodes to the graph.
workflow.add_node("extract", extract_node)
workflow.add_node("gap_and_questions", gap_and_questions_node)
workflow.add_node("interview_setup", interview_setup_node)
workflow.add_node("interview_loop", interview_loop_node)
workflow.add_node("finish_interview", finish_interview_node) # Add the new node
workflow.add_node("generate_report", progress_node)

# Define the edges that determine the flow of the graph.
workflow.set_entry_point("extract")
workflow.add_edge("extract", "gap_and_questions")
workflow.add_edge("gap_and_questions", "interview_setup")
# This new edge connects the finish step to the report step.
workflow.add_edge("finish_interview", "generate_report")
workflow.add_edge("generate_report", END)

# Update the conditional edge for the interview loop.
# When the interview is over, it must now go to 'finish_interview'.
workflow.add_conditional_edges(
    "interview_setup",
    should_continue,
    {
        "continue": "interview_loop",
        "end": "finish_interview", # Go to finish, not report
    }
)
workflow.add_conditional_edges(
    "interview_loop",
    should_continue,
    {
        "continue": "interview_loop",
        "end": "finish_interview", # Go to finish, not report
    }
)

# Compile the graph into a runnable application.
app = workflow.compile()
