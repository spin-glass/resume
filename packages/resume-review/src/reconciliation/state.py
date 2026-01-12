from typing import Annotated, Optional, List
from pydantic import BaseModel, Field, ConfigDict
import operator

from ..models.star_story import StarStory

def add_messages(existing: list[str], new: list[str]) -> list[str]:
    return existing + new

class InterviewSessionState(BaseModel):
    """
    State for the Experience Reconciliation Interview.
    """
    # Context
    resume_context: str = "" # The project description from resume
    target_year: Optional[int] = None

    # LLM keys
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    override_model: Optional[str] = None

    # Conversation
    messages: Annotated[list[str], add_messages] = Field(default_factory=list)
    current_question: Optional[str] = None
    user_answer: Optional[str] = None
    turn_count: int = 0
    
    # Fact Checking
    anachronisms_detected: list[str] = Field(default_factory=list)
    force_terminate: bool = False
    
    # Outcome
    generated_star: Optional[StarStory] = None
    is_complete: bool = False
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
