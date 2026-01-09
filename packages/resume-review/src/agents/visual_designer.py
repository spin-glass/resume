"""Visual Designer agent for evaluating visual presentation."""

import json
import re

from ..models import Severity
from ..models.feedback import Feedback, Issue
from .base import BaseAgent


class VisualDesignerAgent(BaseAgent):
    """Evaluates resume from visual design perspective."""

    def __init__(self, llm_client, agent_name=None):
        """Initialize visual designer agent."""
        super().__init__(llm_client, agent_name)
        self.agent_name = "visual_designer"

    def get_system_prompt(self, target_role: str) -> str:
        """Get visual designer-specific system prompt."""
        return f"""You are an expert visual designer specializing in professional documents and typography.

Evaluate this resume for a {target_role} position from a visual design perspective. Focus on:

1. **Typography**: Font choices, sizes, and hierarchy
2. **Spacing**: Margins, padding, line height
3. **Consistency**: Visual elements aligned and uniform
4. **Professionalism**: Overall polish and attention to detail
5. **Balance**: Visual weight distribution across the page

Provide your evaluation in JSON format:
{{
  "score": <float 1-10>,
  "strengths": [<list of specific strengths>],
  "issues": [
    {{
      "description": "<specific problem>",
      "action_type": "<restructure|emphasize|remove>",
      "location": "<section name or null>",
      "severity": "<critical|high|medium|low>"
    }}
  ],
  "suggestions": [<list of specific actionable suggestions>]
}}

IMPORTANT:
- Score 8+ = professional, polished design
- Score 6-7 = adequate but lacks refinement
- Score <6 = unprofessional appearance
- Focus on visual presentation, not content
- Suggest design improvements, not content changes"""

    def parse_feedback(self, feedback_text: str) -> Feedback:
        """Parse visual designer feedback from Claude response."""
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

    def evaluate_from_screenshot(self, screenshot_path: str, target_role: str = "LLM/Multi-Agent Engineer") -> Feedback:
        """
        Evaluate resume from screenshot instead of text content.

        Args:
            screenshot_path: Path to screenshot image
            target_role: Target position

        Returns:
            Feedback with visual design evaluation
        """
        import base64
        from pathlib import Path

        # Read and encode screenshot
        screenshot_file = Path(screenshot_path)
        if not screenshot_file.exists():
            return Feedback(
                agent_name=self.agent_name,
                score=5.0,
                strengths=[],
                issues=[],
                suggestions=[f"Screenshot not found: {screenshot_path}"],
            )

        with open(screenshot_file, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        system_prompt = self.get_system_prompt(target_role)

        # Call Claude with vision
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": f"Please evaluate the visual design and presentation of this resume for a {target_role} position.",
                        },
                    ],
                }
            ],
        )

        feedback_text = response.content[0].text
        return self.parse_feedback(feedback_text)
