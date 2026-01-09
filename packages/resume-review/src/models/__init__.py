"""Data models for the resume review system."""

from enum import Enum


class ActionType(str, Enum):
    """Action types for issue resolution."""

    ADD_CONTENT = "add_content"
    ADD_PORTFOLIO = "add_portfolio"
    RESTRUCTURE = "restructure"
    EMPHASIZE = "emphasize"
    REMOVE = "remove"
    QUANTIFY = "quantify"


class Severity(str, Enum):
    """Issue severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SessionStatus(str, Enum):
    """Review session workflow states."""

    INITIALIZED = "initialized"
    CONTENT_REVIEW = "content_review"
    PORTFOLIO_ANALYSIS = "portfolio_analysis"
    DESIGN_REVIEW = "design_review"
    COMPLETED = "completed"
    FAILED = "failed"


__all__ = ["ActionType", "Severity", "SessionStatus"]
