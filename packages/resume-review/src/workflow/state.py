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
    api_key: str  # Legacy: kept for backward compatibility
    anthropic_api_key: Optional[str]  # New: Anthropic API key
    gemini_api_key: Optional[str]  # New: Gemini API key
    openai_api_key: Optional[str]  # New: OpenAI API key
    override_model: Optional[str]  # New: Override model for all agents (testing)
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

    # Per-agent feedback (NEW: for separate agent nodes)
    recruiter_feedback: Optional[Feedback]
    tech_writer_feedback: Optional[Feedback]
    copywriter_feedback: Optional[Feedback]

    # Score tracking
    integrated_score: float
    threshold_met: bool

    # Portfolio analysis
    skill_gaps: list[str]
    portfolio_suggestions: Annotated[list[PortfolioItem], add_portfolio]

    # Revision tracking
    revised_content: str
    applied_revisions: Annotated[list[str], add_revisions]

    # Token usage tracking (New: for cost calculation)
    token_usage: dict[str, dict[str, int]]  # {agent_name: {input_tokens, output_tokens, model}}

    # Final output
    final_score: float

    # Control flow
    should_continue: bool
    error: Optional[str]

    # Validation retry tracking
    validation_retry_count: int
    max_validation_retries: int
    strict_validation: bool
    current_retry_attempts: list[dict]  # Serialized RetryAttempt records
