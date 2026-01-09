"""Recruiter agent for evaluating contract acquisition potential."""

import json
import re

from ..models import Severity
from ..models.feedback import Feedback, Issue
from .base import BaseAgent


class RecruiterAgent(BaseAgent):
    """Evaluates resume from recruiter/contract acquisition perspective."""

    def __init__(self, llm_client, agent_name=None):
        """Initialize recruiter agent."""
        super().__init__(llm_client, agent_name)
        self.agent_name = "recruiter"

    def get_system_prompt(self, target_role: str) -> str:
        """Get recruiter-specific system prompt."""
        return f"""You are an expert recruiter specializing in placing freelance engineers in high-value Japanese contract positions (110-140万円/month).

Evaluate this resume for a {target_role} position from a recruiter's perspective. Focus on:

1. **Market Competitiveness**: Does this candidate stand out for premium contracts?
2. **Skill Relevance**: Are the skills aligned with high-paying market demands?
3. **Project Impact**: Are achievements quantified and business-value focused?
4. **Client Appeal**: Will this resume attract hiring managers at top companies?
5. **Rate Justification**: Can this candidate justify 120万円+/month rates?

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
- Score 8+ = ready for 120万円+ positions
- Score 6-7 = needs improvement for premium rates
- Score <6 = significant gaps for target rate
- NEVER suggest fabricating experience or credentials
- Focus on truthful enhancements and strategic presentation"""

    def parse_feedback(self, feedback_text: str) -> Feedback:
        """Parse recruiter feedback from Claude response."""
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
