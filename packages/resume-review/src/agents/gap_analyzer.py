import json
import asyncio
from typing import Optional

from ..models.gap_analysis import GapAnalysisResult
from ..models.feedback import Feedback
from ..services import BaseLLMClient
from .base import BaseAgent

class GapAnalyzerAgent(BaseAgent):
    """Analyzes gaps between Resume and Job Description."""

    def __init__(self, llm_client: BaseLLMClient, agent_name: str | None = None) -> None:
        super().__init__(llm_client, agent_name)
        self.agent_name = "gap_analyzer"
        
    def parse_feedback(self, feedback_text: str) -> Feedback:
        """Required by BaseAgent, but not used by GapAnalyzer.
        
        GapAnalyzer uses parse_result() to return GapAnalysisResult instead of Feedback.
        """
        return Feedback(
            agent_name=self.agent_name,
            score=0.0,
            strengths=[],
            issues=[],
            suggestions=["GapAnalyzer does not use standard Feedback model."]
        )

    def get_system_prompt(self, target_role: str = "Candidate", job_posting: Optional[str] = None) -> str:
        """Get gap analyzer system prompt."""
        from ..config.prompts import get_system_prompt
        # Note: job_posting argument in get_system_prompt expects JobPosting object or None, 
        # but here we might just need the base prompt and pass JD in user message.
        # For simplicity, we stick to the pattern.
        return get_system_prompt("gap_analyzer", target_role)

    def analyze(self, resume_content: str, jd_text: str) -> GapAnalysisResult:
        """Run gap analysis."""
        
        system_prompt = self.get_system_prompt()
        
        user_message = f"""
# Job Description
{jd_text}

# Resume
{resume_content}

Perform the Gap Analysis now.
"""
        
        # Run async generation in sync context
        response = asyncio.run(self.llm_client.generate_async(
            system_prompt=system_prompt,
            user_prompt=user_message,
        ))

        return self.parse_result(response.content)

    def parse_result(self, response_text: str) -> GapAnalysisResult:
        """Parse LLM response into GapAnalysisResult."""
        try:
            # Clean up potential markdown code blocks
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            
            data = json.loads(clean_text.strip())
            return GapAnalysisResult(**data)
        except json.JSONDecodeError as e:
            # Fallback or error handling
            raise ValueError(f"Failed to parse Gap Analysis JSON: {e}\nResponse: {response_text}")
        except Exception as e:
            raise ValueError(f"Error validating Gap Analysis data: {e}")
