"""LangGraph StateGraph builder for resume review workflow."""

from langgraph.graph import END, StateGraph

from .conditions import should_continue_review, should_do_design_review
from .nodes import (
    aggregator_node,
    design_supervisor_node,
    portfolio_analyzer_node,
    revisor_node,
    supervisor_node,
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
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("aggregator", aggregator_node)
    workflow.add_node("revisor", revisor_node)
    workflow.add_node("portfolio", portfolio_analyzer_node)
    workflow.add_node("design", design_supervisor_node)

    # Set entry point
    workflow.set_entry_point("supervisor")

    # Add edges
    workflow.add_edge("supervisor", "aggregator")

    # Conditional edge after aggregator
    workflow.add_conditional_edges(
        "aggregator",
        should_continue_review,
        {
            "revisor": "revisor",
            "portfolio": "portfolio",
        },
    )

    # After revision, go back to supervisor for re-evaluation
    workflow.add_edge("revisor", "supervisor")

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
