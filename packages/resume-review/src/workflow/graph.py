"""LangGraph StateGraph builder for resume review workflow."""

from typing import Literal

from langgraph.graph import END, StateGraph

from .conditions import (
    should_continue_review,
    should_do_design_review,
    should_run_design_applier,
)
from .nodes import (
    aggregator_node,
    design_applier_node,
    design_supervisor_node,
    job_parser_node,
    personalizer_node,
    portfolio_analyzer_node,
    revisor_node,
    supervisor_node,
)
from .state import ReviewState


def route_after_job_parser(state: ReviewState) -> Literal["supervisor", "design"]:
    """Route after job parser based on design_only flag."""
    if state.get("design_only", False):
        return "design"
    return "supervisor"


def build_review_workflow() -> StateGraph:
    """
    Build and compile the LangGraph StateGraph for resume review.

    Returns:
        Compiled StateGraph ready for execution
    """
    # Create the state graph
    workflow = StateGraph(ReviewState)

    # Add nodes
    workflow.add_node("job_parser", job_parser_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("aggregator", aggregator_node)
    workflow.add_node("personalizer", personalizer_node)
    workflow.add_node("revisor", revisor_node)
    workflow.add_node("portfolio", portfolio_analyzer_node)
    workflow.add_node("design", design_supervisor_node)
    workflow.add_node("design_applier", design_applier_node)

    # Set entry point (job_parser will pass through if no job posting)
    workflow.set_entry_point("job_parser")

    # Job parser routes depending on design_only flag
    workflow.add_conditional_edges(
        "job_parser",
        route_after_job_parser,
        {
            "supervisor": "supervisor",
            "design": "design",
        },
    )

    # Add edges
    workflow.add_edge("supervisor", "aggregator")

    # After aggregator, run personalizer (no-op if no job posting)
    workflow.add_edge("aggregator", "personalizer")

    # Conditional edge after personalizer
    workflow.add_conditional_edges(
        "personalizer",
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

    # Conditional edge after design review
    workflow.add_conditional_edges(
        "design",
        should_run_design_applier,
        {
            "design_applier": "design_applier",
            "end": END,
        },
    )

    # Design applier goes back to design supervisor for re-evaluation
    workflow.add_edge("design_applier", "design")

    # Compile the workflow
    return workflow.compile()
