"""Technical Writer agent for evaluating technical depth and clarity."""

import json
import re

from ..models import Severity
from ..models.feedback import Feedback, Issue
from .base import BaseAgent


class TechnicalWriterAgent(BaseAgent):
    """Evaluates resume from technical depth and clarity perspective."""

    def __init__(self, llm_client, agent_name=None):
        """Initialize technical writer agent."""
        super().__init__(llm_client, agent_name)
        self.agent_name = "technical_writer"

    def get_system_prompt(self, target_role: str) -> str:
        """Get technical writer-specific system prompt."""
        from ..config.prompts import get_system_prompt

        return get_system_prompt("technical_writer", target_role)

    def parse_feedback(self, feedback_text: str) -> Feedback:
        """Parse technical writer feedback from Claude response."""
        try:
            # Extract JSON from response
            json_match = re.search(r"\{.*\}", feedback_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in feedback response")

            data = json.loads(json_match.group())

            # Parse issues
            issues = []
            for issue_data in data.get("issues", []):
                issues.append(
                    Issue(
                        description=issue_data["description"],
                        action_type=issue_data["action_type"],
                        location=issue_data.get("location"),
                        severity=Severity(issue_data["severity"]),
                    )
                )

            return Feedback(
                agent_name=self.agent_name,
                score=float(data["score"]),
                strengths=data.get("strengths", []),
                issues=issues,
                suggestions=data.get("suggestions", []),
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback: create basic feedback from text
            return Feedback(
                agent_name=self.agent_name,
                score=7.0,  # Default middle score
                strengths=["Resume reviewed"],
                issues=[],
                suggestions=[f"Error parsing feedback: {e}. Please review manually."],
            )
