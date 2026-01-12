from pydantic import BaseModel, Field
from typing import Optional

class StarStory(BaseModel):
    """
    Represents a behavioral interview story in STAR format.
    """
    situation: str = Field(..., description="The context or situation.")
    task: str = Field(..., description="The specific challenge or task.")
    action: str = Field(..., description="The actions taken to address the task.")
    result: str = Field(..., description="The outcome or result, preferably quantitative.")
    
    tech_stack: list[str] = Field(default_factory=list, description="Technologies used in this story.")
    year: Optional[int] = Field(None, description="Year this took place.")
    project_name: Optional[str] = Field(None, description="Name of the project.")
