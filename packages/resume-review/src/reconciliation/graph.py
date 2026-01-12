from typing import Literal

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from .state import InterviewSessionState
from .nodes import interview_node, fact_check_node, star_generator_node

def should_continue(state: InterviewSessionState) -> Literal["end", "interview"]:
    if state.is_complete:
        return "end"
    return "interview"

def build_reconciliation_workflow() -> CompiledStateGraph:
    """
    Builds the Experience Reconciliation workflow.
    
    Flow:
    1. Check user input (Fact Check)
    2. Try to generate STAR (Star Gen)
    3. If complete -> End
    4. If not -> Ask next question (Interview) -> End (Wait for user)
    """
    workflow = StateGraph(InterviewSessionState)
    
    workflow.add_node("interview", interview_node)
    workflow.add_node("fact_check", fact_check_node)
    workflow.add_node("star_gen", star_generator_node)
    
    # Start by analyzing the current state (potentially with new user input)
    workflow.set_entry_point("fact_check")
    
    workflow.add_edge("fact_check", "star_gen")
    
    workflow.add_conditional_edges(
        "star_gen",
        should_continue,
        {
            "end": END,
            "interview": "interview"
        }
    )
    
    workflow.add_edge("interview", END)
    
    return workflow.compile()
