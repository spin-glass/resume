"""
Job posting data models for resume personalization.

This module contains Pydantic models for structured job posting data,
skill matching results, and personalization analysis.
"""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator


class JobPosting(BaseModel):
    """Structured representation of a job posting."""

    title: str = Field(..., description="Job title", min_length=1)
    company: Optional[str] = Field(default=None, description="Company name")
    required_skills: list[str] = Field(
        default_factory=list,
        description="Must-have technical and soft skills"
    )
    preferred_skills: list[str] = Field(
        default_factory=list,
        description="Nice-to-have skills"
    )
    responsibilities: list[str] = Field(
        default_factory=list,
        description="Key responsibilities and duties"
    )
    qualifications: list[str] = Field(
        default_factory=list,
        description="Experience level, education, certifications"
    )
    salary_range: Optional[str] = Field(
        default=None,
        description="Salary or rate information if mentioned"
    )
    contract_type: Optional[str] = Field(
        default=None,
        description="Full-time, contract, freelance, etc."
    )
    raw_text: str = Field(..., description="Original job posting text", min_length=10)
    source: str = Field(..., description="File path or URL")

    @field_validator("required_skills", "preferred_skills", "responsibilities", "qualifications")
    @classmethod
    def remove_empty_strings(cls, v: list[str]) -> list[str]:
        """Remove empty strings and strip whitespace from list fields."""
        return [item.strip() for item in v if item and item.strip()]

    @model_validator(mode="after")
    def validate_has_content(self) -> "JobPosting":
        """Ensure at least one of the key fields has content."""
        has_content = (
            len(self.required_skills) > 0
            or len(self.responsibilities) > 0
            or len(self.preferred_skills) > 0
        )
        if not has_content:
            raise ValueError(
                "Job posting must have at least one of: required_skills, "
                "responsibilities, or preferred_skills"
            )
        return self

    def get_all_skills(self) -> list[str]:
        """Return combined list of required and preferred skills."""
        all_skills = set(self.required_skills) | set(self.preferred_skills)
        return sorted(all_skills)

    def get_skill_count(self) -> dict[str, int]:
        """Return counts of required, preferred, and total skills."""
        return {
            "required": len(self.required_skills),
            "preferred": len(self.preferred_skills),
            "total": len(self.get_all_skills()),
        }


class SkillMatch(BaseModel):
    """Represents a single skill match between resume and job posting."""

    skill: str = Field(..., description="Skill from job posting")
    matched: bool = Field(..., description="Whether skill was found in resume")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score 0.0-1.0"
    )
    explanation: str = Field(..., description="Why this is/isn't a match")


class PersonalizationResult(BaseModel):
    """Complete personalization analysis results."""

    required_match_score: float = Field(..., ge=0.0, le=100.0)
    preferred_match_score: float = Field(..., ge=0.0, le=100.0)
    matched_required_skills: list[SkillMatch] = Field(default_factory=list)
    matched_preferred_skills: list[SkillMatch] = Field(default_factory=list)
    missing_required_skills: list[str] = Field(default_factory=list)
    missing_preferred_skills: list[str] = Field(default_factory=list)
    emphasis_suggestions: list[str] = Field(
        default_factory=list,
        description="Actionable suggestions for emphasizing relevant experience"
    )
    keyword_additions: list[str] = Field(
        default_factory=list,
        description="Keywords from job posting to incorporate into resume"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def match_score(self) -> float:
        """
        Overall match score using weighted average.

        Formula: (required * 0.7) + (preferred * 0.3)
        """
        return round((self.required_match_score * 0.7) + (self.preferred_match_score * 0.3), 1)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def match_level(self) -> Literal["Excellent", "Good", "Moderate", "Weak"]:
        """
        Categorize match score into levels.

        - Excellent: 80-100
        - Good: 60-79
        - Moderate: 40-59
        - Weak: 0-39
        """
        score = self.match_score
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Moderate"
        else:
            return "Weak"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_critical_gaps(self) -> bool:
        """Check if there are missing required skills."""
        return len(self.missing_required_skills) > 0

    def get_match_summary(self) -> dict[str, Any]:
        """
        Return summary dict with match statistics.

        Returns:
            Dict with overall_score, match_level, required_match,
            preferred_match, and critical_gaps count
        """
        return {
            "overall_score": self.match_score,
            "match_level": self.match_level,
            "required_match": self.required_match_score,
            "preferred_match": self.preferred_match_score,
            "critical_gaps": len(self.missing_required_skills),
            "has_critical_gaps": self.has_critical_gaps,
        }
