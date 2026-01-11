from typing import List, Optional
from pydantic import BaseModel, Field

class ActionItem(BaseModel):
    """Suggested action to address a skill gap."""
    description: str = Field(..., description="Description of the action to take")
    resource_url: Optional[str] = Field(None, description="URL to a learning resource or documentation")
    estimated_hours: Optional[str] = Field(None, description="Estimated time to complete (e.g., '2-4 hours')")

class MissingSkill(BaseModel):
    """Details of a missing or under-represented skill."""
    skill_name: str = Field(..., description="Name of the missing skill")
    urgency: str = Field(..., description="Urgency level: 'Critical', 'High', 'Medium', 'Low'")
    context: str = Field(..., description="Why this skill is important based on the JD")
    action_items: List[ActionItem] = Field(default_factory=list, description="List of suggested actions")

class GapAnalysisResult(BaseModel):
    """Result of the gap analysis between Resume and JD."""
    match_score: float = Field(..., description="Overall match score (0.0 - 10.0)")
    summary: str = Field(..., description="Executive summary of the fit")
    missing_skills: List[MissingSkill] = Field(default_factory=list, description="List of missing skills")
    strong_points: List[str] = Field(default_factory=list, description="List of matching strong points")
    overall_recommendation: str = Field(..., description="Strategic recommendation (e.g., 'Apply now', 'Study X first')")
