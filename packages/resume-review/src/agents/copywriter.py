"""Copywriter agent for evaluating marketing effectiveness."""

import json
import re

from ..models import Severity
from ..models.feedback import Feedback, Issue
from .base import BaseAgent


class CopywriterAgent(BaseAgent):
    """Evaluates resume from marketing and persuasion perspective."""

    def __init__(self, api_key: str, model: str = "claude-opus-4-5-20251101"):
        """Initialize copywriter agent."""
        super().__init__(api_key, model)
        self.agent_name = "copywriter"

    def get_system_prompt(self, target_role: str) -> str:
        """Get copywriter-specific system prompt."""
        return f"""You are an expert copywriter specializing in personal branding and persuasive marketing.

Evaluate this resume for a {target_role} position from a copywriting perspective. Focus on:

1. **Impact**: Do statements convey meaningful value and results?
2. **Persuasion**: Is the content compelling and memorable?
3. **Clarity**: Is language concise and powerful?
4. **Differentiation**: Does the candidate stand out from competitors?
5. **Value Proposition**: Is the unique selling point clear?

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
- Score 8+ = highly compelling and persuasive
- Score 6-7 = adequate but lacks impact
- Score <6 = weak value proposition
- Focus on active voice and strong verbs
- Quantify impact wherever possible (metrics, scale, results)
- NEVER suggest exaggerating or fabricating achievements
- Suggest truthful reframing for maximum impact"""

    def parse_feedback(self, feedback_text: str) -> Feedback:
        """Parse copywriter feedback from Claude response."""
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
