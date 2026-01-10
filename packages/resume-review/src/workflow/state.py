"""LangGraph state definitions for resume review workflow."""

from typing import Annotated, Any, Optional, TypedDict

from ..models.design import (
    CSSModification,
    DesignPreview,
    SectionReorder,
    ThemeRecommendation,
)
from ..models.feedback import Feedback, Resume
from ..models.job_posting import JobPosting, PersonalizationResult
from ..models.portfolio import PortfolioItem



from pydantic import BaseModel, Field, ConfigDict

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


class ReviewState(BaseModel):
    """
    State schema for LangGraph review workflow.

    This Pydantic model defines all fields that flow through the StateGraph.
    Fields use Annotated types with reducers for list accumulation.
    """

    # Input fields (set once at initialization)
    resume: Resume
    resume_content: str = ""
    target_role: str = "LLM/Multi-Agent Engineer"
    score_threshold: float = Field(default=8.0, ge=0, le=10)
    max_iterations: int = Field(default=3, ge=1)
    api_key: str = ""  # Legacy: kept for backward compatibility
    anthropic_api_key: Optional[str] = None  # New: Anthropic API key
    gemini_api_key: Optional[str] = None  # New: Gemini API key
    openai_api_key: Optional[str] = None  # New: OpenAI API key
    override_model: Optional[str] = None  # New: Override model for all agents (testing)
    dry_run: bool = False
    screenshot_url: Optional[str] = None
    save_iterations: bool = True
    output_dir: Optional[str] = None
    session_dir: Optional[str] = None  # New: Specific session directory (timestamped)
    session_id: str = Field(default_factory=lambda: "")

    # Iteration tracking
    current_iteration: int = 0

    # Feedback accumulation (uses reducer)
    feedback_history: Annotated[list[list[Feedback]], add_feedback] = Field(
        default_factory=list
    )
    current_feedback: list[Feedback] = Field(default_factory=list)

    # Per-agent feedback (NEW: for separate agent nodes)
    recruiter_feedback: Optional[Feedback] = None
    tech_writer_feedback: Optional[Feedback] = None
    copywriter_feedback: Optional[Feedback] = None

    # Score tracking
    integrated_score: float = 0.0
    threshold_met: bool = False

    # Portfolio analysis
    skill_gaps: list[str] = Field(default_factory=list)
    portfolio_suggestions: Annotated[list[PortfolioItem], add_portfolio] = Field(
        default_factory=list
    )

    # Revision tracking
    revised_content: str = ""
    applied_revisions: Annotated[list[str], add_revisions] = Field(default_factory=list)

    # Token usage tracking (New: for cost calculation)
    token_usage: dict[str, dict[str, Any]] = Field(
        default_factory=dict
    )  # {agent_name: {input_tokens, output_tokens, model, provider}}

    # Final output
    final_score: float = 0.0

    # Control flow
    should_continue: bool = True
    error: Optional[str] = None

    # Validation retry tracking
    validation_retry_count: int = 0
    max_validation_retries: int = 3
    strict_validation: bool = False
    current_retry_attempts: list[dict[str, Any]] = Field(
        default_factory=list
    )  # Serialized RetryAttempt records

    # Design modification flags (from CLI)
    auto_design_enabled: bool = False  # --auto-design flag
    design_preview_enabled: bool = False  # --design-preview flag
    css_output_path: Optional[str] = None  # --css-output override
    design_only: bool = False  # --design-only flag

    # Design modification outputs
    css_modification: Optional[CSSModification] = None
    section_reorder: Optional[SectionReorder] = None
    theme_recommendation: Optional[ThemeRecommendation] = None
    design_preview_paths: Optional[DesignPreview] = None

    # Design modification status
    design_changes_applied: bool = False  # Were modifications actually applied?
    design_changes_pending: bool = False  # Are modifications ready but not applied (preview mode)?
    design_changes_list: list[str] = Field(default_factory=list)  # Human-readable list of applied changes

    # Backup tracking
    design_backup_paths: dict[str, str] = Field(default_factory=dict)  # {original_path: backup_path} for rollback

    # Design Loop Control
    design_loop_active: bool = False
    design_iteration: int = 0
    max_design_iterations: int = 3
    design_score: float = 0.0  # Score from Design Supervisor

    # Job personalization (optional fields for job-specific review)
    job_posting_file: Optional[str] = None  # Path to job posting file
    job_url: Optional[str] = None  # Job posting URL
    job_posting: Optional[JobPosting] = None
    personalization_result: Optional[PersonalizationResult] = None
    job_source_type: Optional[str] = None  # 'file' or 'url'

    model_config = ConfigDict(arbitrary_types_allowed=True)

