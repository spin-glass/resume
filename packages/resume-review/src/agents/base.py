"""Base agent interface for resume evaluation."""

import asyncio
from abc import ABC, abstractmethod
from functools import partial
from typing import Optional

from anthropic import Anthropic, AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models.feedback import Feedback, Resume


class BaseAgent(ABC):
    """Base class for all resume review agents."""

    def __init__(self, api_key: str, model: str = "claude-opus-4-5-20251101"):
        """
        Initialize agent with API credentials.

        Args:
            api_key: Anthropic API key
            model: Claude model to use (default: Claude Opus 4.5)
        """
        self.client = Anthropic(api_key=api_key)
        self.async_client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.agent_name = self.__class__.__name__.replace("Agent", "").lower()

    @abstractmethod
    def get_system_prompt(self, target_role: str) -> str:
        """
        Get system prompt for this agent.

        Args:
            target_role: Target position the resume is being tailored for

        Returns:
            System prompt string
        """
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def evaluate(
        self, resume: Resume, target_role: str = "LLM/Multi-Agent Engineer"
    ) -> Feedback:
        """
        Evaluate resume and return structured feedback.

        Args:
            resume: Resume entity to evaluate
            target_role: Target position

        Returns:
            Feedback entity with score, strengths, issues, suggestions

        Raises:
            Exception: If API call fails after retries
        """
        system_prompt = self.get_system_prompt(target_role)

        # Call Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Please evaluate this resume for a {target_role} position:\n\n{resume.content}",
                }
            ],
        )

        # Parse response and create Feedback
        # For now, we'll implement basic parsing
        # In production, we'd use structured outputs or JSON parsing
        feedback_text = response.content[0].text

        # This is a simplified implementation
        # In the actual implementation, we'll parse the structured output
        return self.parse_feedback(feedback_text)

    async def evaluate_async(
        self, resume: Resume, target_role: str = "LLM/Multi-Agent Engineer"
    ) -> Feedback:
        """
        Async version of evaluate for parallel execution in LangGraph.

        Args:
            resume: Resume entity to evaluate
            target_role: Target position

        Returns:
            Feedback entity with score, strengths, issues, suggestions
        """
        system_prompt = self.get_system_prompt(target_role)

        # Call Claude API asynchronously
        response = await self.async_client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Please evaluate this resume for a {target_role} position:\n\n{resume.content}",
                }
            ],
        )

        # Parse response and create Feedback
        feedback_text = response.content[0].text
        return self.parse_feedback(feedback_text)

    @abstractmethod
    def parse_feedback(self, feedback_text: str) -> Feedback:
        """
        Parse agent response into structured Feedback.

        Args:
            feedback_text: Raw text response from Claude

        Returns:
            Parsed Feedback entity
        """
        pass

    def format_feedback(self, feedback: Feedback) -> str:
        """
        Format feedback for display to user.

        Args:
            feedback: Feedback entity

        Returns:
            Formatted string
        """
        output = [
            f"\n{feedback.agent_name.upper()} FEEDBACK",
            f"Score: {feedback.score}/10.0",
            "",
        ]

        if feedback.strengths:
            output.append("Strengths:")
            for strength in feedback.strengths:
                output.append(f"  • {strength}")
            output.append("")

        if feedback.issues:
            output.append("Issues:")
            for issue in feedback.issues:
                severity_icon = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢",
                }
                icon = severity_icon.get(issue.severity.value, "⚪")
                output.append(f"  {icon} [{issue.action_type.value}] {issue.description}")
                if issue.location:
                    output.append(f"     Location: {issue.location}")
            output.append("")

        if feedback.suggestions:
            output.append("Suggestions:")
            for suggestion in feedback.suggestions:
                output.append(f"  • {suggestion}")
            output.append("")

        return "\n".join(output)
