"""Review session entity for tracking workflow state."""

from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from . import SessionStatus
from .feedback import Feedback, Resume
from .portfolio import PortfolioItem


class ReviewSession(BaseModel):
    """The complete workflow from input to output."""

    session_id: str = Field(default_factory=lambda: str(uuid4()))
    resume: Resume
    target_role: str = "LLM/Multi-Agent Engineer"
    score_threshold: float = 8.0
    max_iterations: int = 3
    current_iteration: int = 0
    feedback_history: list[list[Feedback]] = Field(default_factory=list)
    portfolio_suggestions: list[PortfolioItem] = Field(default_factory=list)
    applied_revisions: list[str] = Field(default_factory=list)
    final_score: Optional[float] = None
    status: SessionStatus = SessionStatus.INITIALIZED
    dry_run: bool = False
    screenshot_url: Optional[str] = None
    max_validation_retries: int = 3
    strict_validation: bool = False
    # Design auto-fix flags (013-design-auto-fix)
    auto_design_enabled: bool = False
    design_preview_enabled: bool = False
    css_output_path: Optional[str] = None

    # Design auto-fix output (013-design-auto-fix)
    design_changes_applied: bool = False
    design_changes_pending: bool = False
    design_changes_list: list[str] = Field(default_factory=list)
    design_backup_paths: dict[str, str] = Field(default_factory=dict)
    css_modification: Optional[dict] = None  # Serialized CSSModification
    section_reorder: Optional[dict] = None  # Serialized SectionReorder
    theme_recommendation: Optional[dict] = None  # Serialized ThemeRecommendation
    design_preview_paths: Optional[dict] = None  # Preview screenshot paths
    design_preview: Optional[dict] = None  # Serialized DesignPreview with stats

    @field_validator("score_threshold")
    @classmethod
    def validate_threshold_range(cls, v: float) -> float:
        """Validate score threshold is between 1.0 and 10.0 (FR-005)."""
        if not 1.0 <= v <= 10.0:
            raise ValueError(f"Score threshold must be between 1.0 and 10.0, got {v}")
        return v

    @field_validator("max_iterations")
    @classmethod
    def validate_max_iterations(cls, v: int) -> int:
        """Validate max iterations is at least 1 (FR-005)."""
        if v < 1:
            raise ValueError(f"Max iterations must be >= 1, got {v}")
        return v

    @field_validator("current_iteration")
    @classmethod
    def validate_current_iteration(cls, v: int, info) -> int:
        """Validate current iteration doesn't exceed max iterations."""
        # Note: We can't access max_iterations here during initial validation
        # This will be checked in business logic
        return v

    @field_validator("final_score")
    @classmethod
    def validate_final_score_range(cls, v: Optional[float]) -> Optional[float]:
        """Validate final score if provided."""
        if v is not None and not 1.0 <= v <= 10.0:
            raise ValueError(f"Final score must be between 1.0 and 10.0, got {v}")
        return v

    def should_continue_iteration(self) -> bool:
        """Check if iteration should continue based on score and max iterations."""
        if self.final_score is None:
            return True  # No score yet, continue
        if self.final_score >= self.score_threshold:
            return False  # Met threshold, stop
        if self.current_iteration >= self.max_iterations:
            return False  # Reached max iterations, stop
        return True

    def add_feedback(self, feedback_list: list[Feedback]) -> None:
        """Add feedback for current iteration."""
        self.feedback_history.append(feedback_list)

    def add_portfolio_suggestion(self, item: PortfolioItem) -> None:
        """Add portfolio suggestion with deduplication."""
        # Check if this repo name already exists
        existing_repos = {p.repository_name for p in self.portfolio_suggestions}
        if item.repository_name not in existing_repos:
            self.portfolio_suggestions.append(item)

    def add_revision(self, description: str) -> None:
        """Log an applied revision."""
        self.applied_revisions.append(description)

    def increment_iteration(self) -> None:
        """Increment current iteration counter."""
        self.current_iteration += 1
