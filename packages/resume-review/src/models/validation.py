"""Validation entities for Quarto retry loop."""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class ValidationResult(BaseModel):
    """Outcome of a Quarto validation attempt."""

    is_valid: bool
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    attempt_number: int

    @field_validator("error_message")
    @classmethod
    def validate_error_message(cls, v: Optional[str], info: Any) -> Optional[str]:
        """Ensure error_message is non-empty when is_valid=False."""
        is_valid = info.data.get("is_valid", True)
        if not is_valid and not v:
            raise ValueError("error_message required when is_valid=False")
        return v

    @field_validator("attempt_number")
    @classmethod
    def validate_attempt_number(cls, v: int) -> int:
        """Ensure attempt_number is >= 0."""
        if v < 0:
            raise ValueError(f"attempt_number must be >= 0, got {v}")
        return v


class RetryAttempt(BaseModel):
    """Record of a single retry iteration."""

    attempt_number: int
    timestamp: datetime = Field(default_factory=datetime.now)
    error_detected: str
    correction_applied: str
    validation_result: ValidationResult
    qmd_snapshot_path: Optional[Path] = None

    @field_validator("attempt_number")
    @classmethod
    def validate_attempt_number(cls, v: int) -> int:
        """Ensure attempt_number > 0 (initial attempt is not a retry)."""
        if v <= 0:
            raise ValueError(f"attempt_number must be > 0 for retries, got {v}")
        return v

    @field_validator("error_detected")
    @classmethod
    def validate_error_detected(cls, v: str) -> str:
        """Ensure error_detected is non-empty."""
        if not v or not v.strip():
            raise ValueError("error_detected must be non-empty")
        return v
