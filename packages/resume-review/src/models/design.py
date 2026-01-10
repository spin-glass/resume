"""Data models for design modification feature.

This module defines the domain entities for automated design modifications,
including CSS generation, section reordering, theme recommendations, and preview generation.
"""

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class DesignIssueType(str, Enum):
    """Types of design issues that can be automatically addressed."""

    SPACING = "spacing"  # Margin, padding, gaps between elements
    TYPOGRAPHY = "typography"  # Font size, weight, line height, hierarchy
    COLOR = "color"  # Color contrast, accessibility, consistency
    HIERARCHY = "hierarchy"  # Visual information hierarchy, emphasis
    LAYOUT = "layout"  # Section arrangement, alignment, balance


class CSSModification(BaseModel):
    """CSS modification generated from design feedback."""

    css_content: str = Field(
        ..., description="Generated CSS rules as string", min_length=1
    )

    target_file: Path = Field(
        default=Path("styles/resume-custom.css"), description="Output file path for CSS"
    )

    changes: list[str] = Field(
        default_factory=list,
        description="Human-readable list of changes made (e.g., 'Increased heading font size')",
    )

    issue_types: list[DesignIssueType] = Field(
        default_factory=list, description="Types of issues this CSS addresses"
    )

    validation_passed: bool = Field(
        default=False, description="Whether CSS passed cssutils validation"
    )

    validation_errors: list[str] = Field(
        default_factory=list, description="CSS validation errors (if any)"
    )

    backup_path: Path | None = Field(
        default=None,
        description="Path to backup of previous CSS file (if existed)",
    )

    @field_validator("css_content")
    @classmethod
    def validate_css_content(cls, v: str) -> str:
        """Ensure CSS content is not empty or just comments."""
        stripped = "\n".join(
            line
            for line in v.split("\n")
            if line.strip() and not line.strip().startswith("//")
        )
        if not stripped:
            raise ValueError("CSS content is empty or contains only comments")
        return v

    @field_validator("target_file")
    @classmethod
    def validate_target_file(cls, v: Path) -> Path:
        """Ensure target file has .css extension."""
        if v.suffix != ".css":
            raise ValueError(f"Target file must have .css extension, got {v.suffix}")
        return v

    def get_summary(self) -> str:
        """Get human-readable summary of modifications."""
        issue_types_str = ", ".join(t.value for t in self.issue_types)
        return f"CSS modifications for {issue_types_str} ({len(self.changes)} changes)"


class SectionReorder(BaseModel):
    """Section reordering operation for QMD content."""

    original_order: list[str] = Field(
        ..., description="Original section headings in order", min_length=1
    )

    new_order: list[str] = Field(
        ..., description="New section headings in desired order", min_length=1
    )

    rationale: str = Field(
        ...,
        description="Explanation for why sections were reordered",
        min_length=10,
    )

    content_hash_before: str | None = Field(
        default=None, description="SHA256 hash of all content (for verification)"
    )

    content_hash_after: str | None = Field(
        default=None,
        description="SHA256 hash after reordering (should match before)",
    )

    @field_validator("new_order")
    @classmethod
    def validate_new_order(cls, v: list[str], info) -> list[str]:
        """Ensure new_order contains same sections as original_order."""
        if "original_order" in info.data:
            original_set = set(info.data["original_order"])
            new_set = set(v)
            if original_set != new_set:
                raise ValueError(
                    f"New order must contain same sections as original. "
                    f"Missing: {original_set - new_set}, "
                    f"Extra: {new_set - original_set}"
                )
        return v

    @field_validator("content_hash_after")
    @classmethod
    def validate_content_preservation(cls, v: str | None, info) -> str | None:
        """Ensure content was preserved (hashes match)."""
        if v and "content_hash_before" in info.data:
            if v != info.data["content_hash_before"]:
                raise ValueError(
                    "Content hash mismatch - content was modified during reordering. "
                    "Only order should change, not content."
                )
        return v

    def is_changed(self) -> bool:
        """Check if order actually changed."""
        return self.original_order != self.new_order

    def get_movements(self) -> list[tuple[str, int, int]]:
        """Get list of (section, old_index, new_index) for moved sections."""
        movements = []
        for section in self.original_order:
            old_idx = self.original_order.index(section)
            new_idx = self.new_order.index(section)
            if old_idx != new_idx:
                movements.append((section, old_idx, new_idx))
        return movements


class ThemeRecommendation(BaseModel):
    """Quarto theme recommendation with configuration."""

    theme_name: str = Field(
        ..., description="Name of recommended Quarto theme", min_length=1
    )

    rationale: str = Field(
        ...,
        description="Explanation of why this theme is recommended",
        min_length=20,
    )

    quarto_config: dict[str, Any] = Field(
        ..., description="_quarto.yml configuration snippet for this theme"
    )

    installation_command: str = Field(
        ...,
        description="Command to install/apply theme (e.g., 'quarto use theme cosmo')",
    )

    preview_url: str | None = Field(
        default=None, description="URL to theme preview/demo (if available)"
    )

    addresses_issues: list[DesignIssueType] = Field(
        default_factory=list,
        description="Design issue types this theme addresses",
    )

    def get_config_yaml(self) -> str:
        """Generate YAML string for _quarto.yml."""
        import yaml

        return yaml.dump(self.quarto_config, default_flow_style=False, sort_keys=False)

    def get_summary(self) -> str:
        """Get human-readable summary."""
        issues_str = ", ".join(t.value for t in self.addresses_issues)
        return f"Theme '{self.theme_name}' recommended for {issues_str}"


class DesignPreview(BaseModel):
    """Visual preview of design modifications."""

    before_screenshot: Path = Field(
        ..., description="Path to screenshot before modifications"
    )

    after_screenshot: Path = Field(
        ..., description="Path to screenshot after modifications"
    )

    diff_screenshot: Path | None = Field(
        default=None, description="Path to diff image highlighting changes"
    )

    composite_screenshot: Path | None = Field(
        default=None,
        description="Path to side-by-side comparison (before|diff|after)",
    )

    diff_pixel_count: int | None = Field(
        default=None, description="Number of pixels that differ between before/after"
    )

    diff_percentage: float | None = Field(
        default=None,
        description="Percentage of pixels that differ (0-100)",
        ge=0.0,
        le=100.0,
    )

    metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted design metrics (spacing measurements, contrast ratios, etc.)",
    )

    def get_summary(self) -> str:
        """Get human-readable summary of changes."""
        if self.diff_percentage is not None:
            return (
                f"{self.diff_percentage:.2f}% of pixels changed "
                f"({self.diff_pixel_count} pixels)"
            )
        return "Preview generated"

    def has_significant_changes(self, threshold: float = 1.0) -> bool:
        """Check if changes exceed threshold percentage."""
        if self.diff_percentage is None:
            return True  # Assume significant if not measured
        return self.diff_percentage >= threshold
