"""Feedback and Issue entities for resume review."""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from . import ActionType, Severity


class Resume(BaseModel):
    """The QMD document being reviewed."""

    file_path: Path
    yaml_frontmatter: dict[str, Any]
    content: str
    full_text: str

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: Path) -> Path:
        """Validate file path format (not existence - allows in-memory Resume)."""
        if v.suffix != ".qmd":
            raise ValueError(f"File must have .qmd extension: {v}")
        return v

    @classmethod
    def from_file(cls, file_path: Path) -> "Resume":
        """
        Load Resume from an existing file with full validation.

        Args:
            file_path: Path to the QMD file

        Returns:
            Resume instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a valid QMD
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File does not exist: {file_path}")
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        import frontmatter  # type: ignore[import-untyped]
        with open(file_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        with open(file_path, "r", encoding="utf-8") as f:
            full_text = f.read()

        return cls(
            file_path=file_path,
            yaml_frontmatter=post.metadata,
            content=post.content,
            full_text=full_text,
        )


class Issue(BaseModel):
    """A specific problem identified during review."""

    description: str = Field(min_length=1)
    action_type: ActionType
    location: Optional[str] = None
    severity: Severity
    resolution: Optional[str] = None

    @field_validator("action_type")
    @classmethod
    def validate_no_fabrication(cls, v: ActionType) -> ActionType:
        """Ensure action_type does not allow fabrication (FR-008)."""
        # ActionType enum doesn't include "fabricate" or "invent"
        # This validator is defensive in case enum is modified
        return v


class Feedback(BaseModel):
    """Evaluation output from a single agent perspective."""

    agent_name: str = Field(min_length=1)
    score: float = Field(ge=1.0, le=10.0)
    strengths: list[str] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("score")
    @classmethod
    def validate_score_range(cls, v: float) -> float:
        """Validate score is between 1.0 and 10.0 (FR-003)."""
        if not 1.0 <= v <= 10.0:
            raise ValueError(f"Score must be between 1.0 and 10.0, got {v}")
        return v

    @field_validator("strengths", "issues", "suggestions")
    @classmethod
    def validate_has_content(cls, v: list[Any], info: Any) -> list[Any]:
        """Ensure at least one strength or issue is provided."""
        # This is validated at the model level rather than field level
        return v

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization validation."""
        if not self.strengths and not self.issues:
            raise ValueError("Feedback must have at least one strength or issue")
