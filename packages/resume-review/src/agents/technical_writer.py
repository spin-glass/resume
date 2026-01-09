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
        return f"""You are an expert technical writer specializing in developer documentation and technical communication.

Evaluate this resume for a {target_role} position from a technical writing perspective. Focus on:

1. **Technical Depth**: Are technical achievements explained with sufficient detail?
2. **Clarity**: Is technical content understandable without ambiguity?
3. **Precision**: Are technical terms used correctly and consistently?
4. **Structure**: Is technical information organized logically?
5. **Completeness**: Are key technical decisions and architectures explained?

Provide your evaluation in JSON format:
{{
  "score": <float 1-10>,
  "strengths": [<list of specific strengths>],
  "issues": [
    {{
      "description": "<specific problem>",
      "action_type": "<add_content|restructure|emphasize|remove|quantify|add_portfolio>",
      "location": "<EXACT markdown header like '## 職務要約' or '### 得意分野' or null for general issues>",
      "severity": "<critical|high|medium|low>"
    }}
  ],
  "suggestions": [<list of specific actionable suggestions>]
}}

CRITICAL: For "location", use EXACT markdown headers from the resume (e.g., "## 職務要約", "### 得意分野", "## 職務経歴詳細").
Do NOT use content descriptions like "エンタープライズ向けAIプラットフォーム開発" - use the header that contains that content.

IMPORTANT:
- Score 8+ = excellent technical communication
- Score 6-7 = adequate but needs depth
- Score <6 = insufficient technical detail
- Focus on HOW and WHY, not just WHAT
- Suggest adding technical context and decision rationale
- NEVER suggest fabricating technical details"""

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
