"""UX Designer agent for evaluating information hierarchy and scannability."""

import json
import re

from ..models import Severity
from ..models.feedback import Feedback, Issue
from ..models.job_posting import JobPosting
from ..services import BaseLLMClient
from .base import BaseAgent


class UXDesignerAgent(BaseAgent):
    """Evaluates resume from UX/information hierarchy perspective."""

    def __init__(self, llm_client: BaseLLMClient, agent_name: str | None = None) -> None:
        """Initialize UX designer agent."""
        super().__init__(llm_client, agent_name)
        self.agent_name = "ux_designer"

    def get_system_prompt(self, target_role: str, job_posting: JobPosting | None = None) -> str:
        """Get UX designer-specific system prompt."""
        return f"""You are an expert UX designer specializing in information architecture and document design.

Evaluate this resume for a {target_role} position from a UX perspective. Focus on:

1. **Information Hierarchy**: Is the most important information prominent?
2. **Scannability**: Can key qualifications be identified in 6-10 seconds?
3. **Visual Flow**: Does the layout guide the eye naturally?
4. **Readability**: Are sections clearly delineated and easy to navigate?
5. **White Space**: Is spacing used effectively to reduce cognitive load?

Provide your evaluation in JSON format:
{{
  "score": <float 1-10>,
  "strengths": [<list of specific strengths>],
  "issues": [
    {{
      "description": "<specific problem>",
      "action_type": "<add_content|restructure|emphasize|remove|quantify>",
      "location": "<section name or null>",
      "severity": "<critical|high|medium|low>"
    }}
  ],
  "suggestions": [<list of specific actionable suggestions>]
}}

IMPORTANT:
- Score 8+ = excellent UX, highly scannable
- Score 6-7 = adequate but improvements needed
- Score <6 = poor information hierarchy
- Focus on structure and organization, not visual styling
- Suggest improvements to layout and content grouping"""

    def parse_feedback(self, feedback_text: str) -> Feedback:
        """Parse UX designer feedback from Claude response."""
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

    async def evaluate_from_screenshot(self, screenshot_path: str, target_role: str = "LLM/Multi-Agent Engineer") -> Feedback:
        """
        Evaluate resume from screenshot instead of text content.

        Args:
            screenshot_path: Path to screenshot image
            target_role: Target position

        Returns:
            Feedback with UX evaluation
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

        if not self.async_client:
            raise RuntimeError("Vision evaluation requires AsyncAnthropic client")

        # Call Claude with vision
        response = await self.async_client.messages.create(
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
                            "text": f"Please evaluate the UX and information hierarchy of this resume for a {target_role} position.",
                        },
                    ],
                }
            ],
        )

        from anthropic.types import TextBlock
        feedback_text = ""
        for block in response.content:
            if isinstance(block, TextBlock):
                feedback_text += block.text
        return self.parse_feedback(feedback_text)
