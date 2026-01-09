"""Portfolio item entity for skill gap recommendations."""

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class PortfolioItem(BaseModel):
    """A suggested project to demonstrate a skill."""

    repository_name: str = Field(min_length=1)
    skills: list[str] = Field(min_length=1)
    description: str = Field(min_length=1)
    github_url: str
    demo_url: Optional[str] = None
    priority: int = Field(ge=1)

    @field_validator("repository_name")
    @classmethod
    def validate_naming_pattern(cls, v: str) -> str:
        """Validate repository name follows {technology}-{type} pattern (FR-007, SC-004)."""
        pattern = r"^[a-z0-9]+-[a-z0-9-]+$"
        if not re.match(pattern, v):
            raise ValueError(
                f"Repository name must match pattern {pattern} (lowercase, alphanumeric, "
                f"hyphens, at least one hyphen), got: {v}"
            )
        return v

    @field_validator("github_url")
    @classmethod
    def validate_github_url_pattern(cls, v: str) -> str:
        """Validate GitHub URL follows consistent pattern (FR-007, SC-004)."""
        pattern = r"^https://github\.com/[a-zA-Z0-9_-]+/[a-z0-9-]+$"
        if not re.match(pattern, v):
            raise ValueError(
                f"GitHub URL must match pattern https://github.com/{{username}}/{{repo}}, got: {v}"
            )
        return v

    @field_validator("demo_url")
    @classmethod
    def validate_demo_url_pattern(cls, v: Optional[str]) -> Optional[str]:
        """Validate demo URL if provided."""
        if v is None:
            return v
        # Allow various demo URL patterns (Vercel, Netlify, etc.)
        if not v.startswith("https://"):
            raise ValueError(f"Demo URL must use HTTPS, got: {v}")
        return v

    @staticmethod
    def generate_github_url(username: str, repo_name: str) -> str:
        """Generate GitHub URL from username and repository name."""
        return f"https://github.com/{username}/{repo_name}"

    @staticmethod
    def generate_demo_url(repo_name: str, platform: str = "vercel") -> str:
        """Generate demo URL from repository name and platform."""
        if platform == "vercel":
            return f"https://{repo_name}.vercel.app"
        elif platform == "netlify":
            return f"https://{repo_name}.netlify.app"
        else:
            raise ValueError(f"Unsupported platform: {platform}")
