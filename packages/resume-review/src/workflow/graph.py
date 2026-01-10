"""LangGraph StateGraph builder for resume review workflow."""

from langgraph.graph import END, StateGraph

from .conditions import should_continue_review, should_do_design_review
from .nodes import (
    aggregator_node,
    copywriter_node,
    design_supervisor_node,
    portfolio_analyzer_node,
    recruiter_node,
    revisor_node,
    router_node,
    tech_writer_node,
)
from .state import ReviewState


def build_review_workflow() -> StateGraph:
    """
    Build and compile the LangGraph StateGraph for resume review.

    Returns:
        Compiled StateGraph ready for execution
    """
    # Create the state graph
    workflow = StateGraph(ReviewState)

    # Add nodes
    workflow.add_node("router", router_node)  # NEW: Fan-out coordinator
    workflow.add_node("recruiter", recruiter_node)  # NEW: Separate agent node
    workflow.add_node("tech_writer", tech_writer_node)  # NEW: Separate agent node
    workflow.add_node("copywriter", copywriter_node)  # NEW: Separate agent node
    workflow.add_node("aggregator", aggregator_node)
    workflow.add_node("revisor", revisor_node)
    workflow.add_node("portfolio", portfolio_analyzer_node)
    workflow.add_node("design", design_supervisor_node)

    # Set entry point
    workflow.set_entry_point("router")  # CHANGED: From "supervisor" to "router"

    # Fan-out: router → three agents (parallel execution)
    workflow.add_edge("router", "recruiter")
    workflow.add_edge("router", "tech_writer")
    workflow.add_edge("router", "copywriter")

    # Fan-in: three agents → aggregator (waits for all)
    workflow.add_edge("recruiter", "aggregator")
    workflow.add_edge("tech_writer", "aggregator")
    workflow.add_edge("copywriter", "aggregator")

    # Conditional edge after aggregator
    workflow.add_conditional_edges(
        "aggregator",
        should_continue_review,
        {
            "revisor": "revisor",
            "portfolio": "portfolio",
        },
    )

    # After revision, go back to router for re-evaluation
    workflow.add_edge("revisor", "router")  # CHANGED: From "supervisor" to "router"

    # Conditional edge after portfolio
    workflow.add_conditional_edges(
        "portfolio",
        should_do_design_review,
        {
            "design": "design",
            "end": END,
        },
    )

    # Design review ends the workflow
    workflow.add_edge("design", END)

    # Compile the workflow
    return workflow.compile()
