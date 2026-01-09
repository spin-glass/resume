"""LangGraph state definitions for resume review workflow."""

from typing import Annotated, Optional, TypedDict

from ..models.feedback import Feedback, Resume
from ..models.portfolio import PortfolioItem


def add_feedback(
    existing: list[list[Feedback]], new: list[list[Feedback]]
) -> list[list[Feedback]]:
    """Reducer to append new feedback iterations."""
    return existing + new


def add_revisions(existing: list[str], new: list[str]) -> list[str]:
    """Reducer to append new revision descriptions."""
    return existing + new


def add_portfolio(
    existing: list[PortfolioItem], new: list[PortfolioItem]
) -> list[PortfolioItem]:
    """Reducer to append new portfolio suggestions (deduplicated)."""
    existing_names = {p.repository_name for p in existing}
    unique_new = [p for p in new if p.repository_name not in existing_names]
    return existing + unique_new


class ReviewState(TypedDict, total=False):
    """
    State schema for LangGraph review workflow.

    This TypedDict defines all fields that flow through the StateGraph.
    Fields use Annotated types with reducers for list accumulation.
    """

    # Input fields (set once at initialization)
    resume: Resume
    resume_content: str
    target_role: str
    score_threshold: float
    max_iterations: int
    api_key: str
    dry_run: bool
    screenshot_url: Optional[str]
    save_iterations: bool
    output_dir: Optional[str]
    session_id: str

    # Iteration tracking
    current_iteration: int

    # Feedback accumulation (uses reducer)
    feedback_history: Annotated[list[list[Feedback]], add_feedback]
    current_feedback: list[Feedback]

    # Score tracking
    integrated_score: float
    threshold_met: bool

    # Portfolio analysis
    skill_gaps: list[str]
    portfolio_suggestions: Annotated[list[PortfolioItem], add_portfolio]

    # Revision tracking
    revised_content: str
    applied_revisions: Annotated[list[str], add_revisions]

    # Final output
    final_score: float

    # Control flow
    should_continue: bool
    error: Optional[str]
