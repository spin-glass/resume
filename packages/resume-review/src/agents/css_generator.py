"""CSS Generator Agent for design auto-fix feature.

This agent uses LLM to translate design feedback into CSS rules that address
specific design issues (spacing, typography, color, hierarchy, layout).
"""

import logging
import re
from pathlib import Path

from ..config.prompts import CSS_GENERATOR_SYSTEM_PROMPT
from ..models.design import CSSModification, DesignIssueType
from ..models.feedback import Feedback
from ..services.css_service import CSSService
from ..services.llm_client import BaseLLMClient
from .base import BaseAgent

logger = logging.getLogger(__name__)


class CSSGeneratorAgent(BaseAgent):
    """Agent that generates CSS modifications from design feedback."""

    def __init__(self, llm_client: BaseLLMClient):
        """Initialize CSS generator agent.

        Args:
            llm_client: Pre-configured LLM client (provider-agnostic)
        """
        super().__init__(llm_client, agent_name="css_generator")
        self.css_service = CSSService()

    def parse_feedback(self, feedback_text: str) -> Feedback:
        """Parse feedback - not used by CSS generator.

        This agent generates CSS, not Feedback objects.
        Implemented to satisfy abstract base class requirement.

        Args:
            feedback_text: Raw response text

        Returns:
            Empty Feedback (not used)
        """
        # CSS generator doesn't parse feedback in the traditional sense
        # It generates CSS from design feedback, not evaluates resumes
        from ..models.feedback import Feedback

        return Feedback(
            agent_name=self.agent_name,
            score=0.0,
            strengths=["CSS generation agent - does not provide feedback"],
            issues=[],
            suggestions=[],
        )

    def get_system_prompt(self, target_role: str = "") -> str:
        """Get system prompt for CSS generation.

        Args:
            target_role: Target role (not used for CSS generation)

        Returns:
            CSS generator system prompt
        """
        return CSS_GENERATOR_SYSTEM_PROMPT

    def _classify_issue(self, description: str) -> DesignIssueType:
        """Classify design issue based on description.

        Args:
            description: Issue description text

        Returns:
            DesignIssueType enum value
        """
        description_lower = description.lower()

        # Spacing keywords
        if any(
            word in description_lower
            for word in [
                "spacing",
                "margin",
                "padding",
                "gap",
                "cramped",
                "crowded",
                "breathing room",
                "whitespace",
            ]
        ):
            return DesignIssueType.SPACING

        # Typography keywords
        if any(
            word in description_lower
            for word in [
                "font",
                "typography",
                "size",
                "weight",
                "line height",
                "leading",
                "readable",
                "readability",
            ]
        ):
            return DesignIssueType.TYPOGRAPHY

        # Hierarchy keywords
        if any(
            word in description_lower
            for word in [
                "hierarchy",
                "emphasis",
                "prominent",
                "heading",
                "priority",
                "structure",
                "visual hierarchy",
            ]
        ):
            return DesignIssueType.HIERARCHY

        # Color keywords
        if any(
            word in description_lower
            for word in [
                "color",
                "contrast",
                "accessibility",
                "readability",
                "wcag",
                "visibility",
            ]
        ):
            return DesignIssueType.COLOR

        # Layout keywords
        if any(
            word in description_lower
            for word in [
                "layout",
                "alignment",
                "balance",
                "arrangement",
                "order",
                "placement",
            ]
        ):
            return DesignIssueType.LAYOUT

        # Default to spacing if unclear
        return DesignIssueType.SPACING

    def _format_issues_for_prompt(self, design_feedback: list[Feedback]) -> str:
        """Format design feedback issues into structured prompt.

        Args:
            design_feedback: List of feedback from design agents

        Returns:
            Formatted string for LLM prompt
        """
        formatted_lines = []

        for feedback in design_feedback:
            agent_name = feedback.agent_name or "unknown"
            formatted_lines.append(f"\n## Feedback from {agent_name}:")

            for issue in feedback.issues:
                issue_type = self._classify_issue(issue.description)
                formatted_lines.append(
                    f"- **{issue_type.value.upper()}**: {issue.description} "
                    f"(severity: {issue.severity})"
                )

        return "\n".join(formatted_lines)

    def _extract_css_from_response(self, response_content: str) -> str:
        """Extract CSS code from LLM response.

        Args:
            response_content: Full LLM response text

        Returns:
            Extracted CSS content

        Raises:
            ValueError: If no CSS code found in response
        """
        # 1. Try to extract CSS from specific css code blocks (```css ... ```)
        css_pattern = r"```css\s*\n?(.*?)\n?```"
        match = re.search(css_pattern, response_content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # 2. Try generic code blocks (``` ... ```)
        generic_pattern = r"```\s*\n?(.*?)\n?```"
        match = re.search(generic_pattern, response_content, re.DOTALL)
        if match:
            content = match.group(1).strip()
            # Basic heuristic: if it has { and }, it's probably CSS
            if "{" in content and "}" in content:
                return content

        # 3. Fallback: find the first { and last } (riskier for CSS, but better than failing)
        # We look for a pattern that looks like a selector { property: value; }
        braced_pattern = r"([^{]+\s*\{.*?\})"
        matches = re.findall(braced_pattern, response_content, re.DOTALL)
        if matches:
            # Join all matched blocks
            return "\n\n".join([m.strip() for m in matches])

        raise ValueError("No CSS code found in response")

    def _extract_changes_from_css(self, css_content: str) -> list[str]:
        """Extract human-readable changes from CSS content.

        Args:
            css_content: CSS code

        Returns:
            List of change descriptions
        """
        changes = []

        # Extract comments as change descriptions
        comment_pattern = r"/\*\s*(.*?)\s*\*/"
        comments = re.findall(comment_pattern, css_content, re.DOTALL)
        changes.extend([c.strip() for c in comments if c.strip()])

        # If no comments, extract some basic info
        if not changes:
            # Count custom properties
            custom_props = re.findall(r"--[\w-]+:", css_content)
            if custom_props:
                changes.append(f"Added {len(custom_props)} CSS custom properties")

            # Count rules
            rules = re.findall(r"[^}]+\{[^}]+\}", css_content)
            if rules:
                changes.append(f"Generated {len(rules)} CSS rules")

        return changes or ["CSS modifications applied"]

    async def generate_css(
        self,
        design_feedback: list[Feedback],
        current_css: str = "",
        target_role: str = "LLM Engineer",
    ) -> CSSModification | None:
        """Generate CSS modifications from design feedback.

        Args:
            design_feedback: List of feedback from design agents
            current_css: Current CSS content (if any)
            target_role: Target role for context

        Returns:
            CSSModification model with validation results
        """
        try:
            # Format issues for prompt
            issues_text = self._format_issues_for_prompt(design_feedback)

            # Classify issues
            issue_types = []
            for feedback in design_feedback:
                for issue in feedback.issues:
                    issue_type = self._classify_issue(issue.description)
                    if issue_type not in issue_types:
                        issue_types.append(issue_type)

            # Build prompt
            user_prompt = f"""Based on the following design feedback, generate CSS modifications \
to address the identified issues.

{issues_text}

Current CSS (if any):
```css
{current_css or "/* No existing CSS */"}
```

Please generate CSS rules that address these specific issues. Focus on minimal, targeted changes."""

            # Get system prompt
            system_prompt = self.get_system_prompt(target_role)

            # Call LLM
            logger.info(f"Generating CSS for {len(issue_types)} issue types: {issue_types}")
            response = await self.llm_client.generate_async(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

            # Extract CSS from response
            css_content = self._extract_css_from_response(response.content)

            # Extract changes
            changes = self._extract_changes_from_css(css_content)

            # Validate CSS
            passed, errors = self.css_service.validate_css(css_content)

            logger.info(
                f"CSS generation complete. Validation: {'PASSED' if passed else 'FAILED'}"
            )
            if errors:
                logger.warning(f"Validation errors: {errors}")

            return CSSModification(
                css_content=css_content,
                target_file=Path("styles/resume-custom.css"),
                changes=changes,
                issue_types=issue_types,
                validation_passed=passed,
                validation_errors=errors,
            )

        except Exception as e:
            logger.error(f"CSS generation failed: {e}", exc_info=True)
            # Return None on generation failure - caller must handle this
            return None
