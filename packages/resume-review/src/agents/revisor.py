"""Revisor agent for applying full-rewrite revisions to resume."""

import logging
from typing import Optional

import frontmatter

from ..models.feedback import Feedback, Resume
from ..services.llm_client import BaseLLMClient
from .base import BaseAgent

logger = logging.getLogger("resume_review")


class RevisorAgent(BaseAgent):
    """Agent responsible for applying revisions using full-rewrite approach."""

    def __init__(self, llm_client: BaseLLMClient, agent_name: Optional[str] = None):
        """
        Initialize Revisor agent with LLM client.

        Args:
            llm_client: Pre-configured LLM client (Gemini for cost-effectiveness)
            agent_name: Optional agent name override
        """
        super().__init__(llm_client, agent_name or "revisor")

    def get_system_prompt(self, target_role: str) -> str:
        """Get system prompt for Revisor agent."""
        from ..config.prompts import REVISOR_SYSTEM_PROMPT

        return REVISOR_SYSTEM_PROMPT.format(target_role=target_role)

    def parse_feedback(self, feedback_text: str) -> Feedback:
        """Not used by Revisor - this agent doesn't produce feedback."""
        raise NotImplementedError("RevisorAgent does not produce feedback")

    async def apply_revisions_async(
        self,
        resume: Resume,
        feedback_list: list[Feedback],
        target_role: str = "LLM/Multi-Agent Engineer",
        dry_run: bool = False,
    ) -> tuple[Resume, list[str]]:
        """
        Apply revisions using full-rewrite approach.

        Args:
            resume: Current resume
            feedback_list: List of feedback from agents
            target_role: Target position
            dry_run: If True, don't modify content, just return proposed changes

        Returns:
            Tuple of (revised_resume, list of applied revision descriptions)
        """
        logger.info("RevisorAgent: Starting full-rewrite revision")

        # Extract YAML frontmatter
        yaml_frontmatter = resume.yaml_frontmatter
        content_only = resume.content

        # Collect all issues from feedback
        issues_summary = self._summarize_issues(feedback_list)

        if not issues_summary:
            logger.info("RevisorAgent: No issues to address")
            return resume, []

        if dry_run:
            logger.info(f"RevisorAgent: DRY RUN - Would apply {len(issues_summary)} revisions")
            return resume, [f"[DRY RUN] Would apply: {issue}" for issue in issues_summary]

        # Build prompt for full rewrite
        system_prompt = self.get_system_prompt(target_role)
        user_prompt = self._build_rewrite_prompt(content_only, feedback_list, issues_summary)

        # Call LLM for full rewrite (max_tokens=8000 for full resume)
        logger.info("RevisorAgent: Requesting full resume rewrite from LLM")
        response = await self.llm_client.generate_async(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=8000,
            temperature=0.7,
        )

        revised_content = response.content.strip()

        # Validate output length
        original_length = len(content_only)
        revised_length = len(revised_content)
        length_ratio = revised_length / original_length if original_length > 0 else 0

        if length_ratio < 0.5:
            logger.error(
                f"RevisorAgent: Output too short ({revised_length}/{original_length} chars, "
                f"ratio={length_ratio:.2f}). Possible truncation!"
            )
            return resume, [
                f"ERROR: Revised content too short ({revised_length}/{original_length} chars). "
                "Possible truncation. Revision aborted."
            ]

        if length_ratio > 1.5:
            logger.warning(
                f"RevisorAgent: Output unexpectedly long ({revised_length}/{original_length} chars, "
                f"ratio={length_ratio:.2f})"
            )

        logger.info(f"RevisorAgent: Full rewrite completed ({revised_length} chars)")

        # Validate YAML frontmatter unchanged
        try:
            post = frontmatter.Post(revised_content, **yaml_frontmatter)
            full_text = frontmatter.dumps(post)
        except Exception as e:
            logger.error(f"RevisorAgent: YAML frontmatter validation failed: {e}")
            return resume, [
                f"ERROR: YAML frontmatter validation failed: {e}. Revision aborted."
            ]

        # Create new Resume with revised content
        revised_resume = Resume.model_construct(
            file_path=resume.file_path,
            yaml_frontmatter=yaml_frontmatter.copy(),
            content=revised_content,
            full_text=full_text,
        )

        revisions_applied = [
            f"Applied full-rewrite revision ({len(issues_summary)} issues addressed)",
            f"Content length: {original_length} → {revised_length} chars (ratio: {length_ratio:.2f})",
        ]

        return revised_resume, revisions_applied

    def _summarize_issues(self, feedback_list: list[Feedback]) -> list[str]:
        """
        Summarize all high/critical issues from feedback.

        Args:
            feedback_list: List of feedback from agents

        Returns:
            List of issue descriptions to address
        """
        from ..models import Severity

        issues_summary = []
        for feedback in feedback_list:
            for issue in feedback.issues:
                if issue.severity in [Severity.CRITICAL, Severity.HIGH]:
                    location_str = f" (Location: {issue.location})" if issue.location else ""
                    issues_summary.append(
                        f"[{feedback.agent_name}] {issue.severity.value.upper()}: "
                        f"{issue.description}{location_str}"
                    )

        return issues_summary

    def _build_rewrite_prompt(
        self, content: str, feedback_list: list[Feedback], issues_summary: list[str]
    ) -> str:
        """
        Build prompt for full resume rewrite.

        Args:
            content: Current resume content (without YAML)
            feedback_list: List of feedback from agents
            issues_summary: Summarized issues to address

        Returns:
            User prompt for LLM
        """
        issues_text = "\n".join(f"{i+1}. {issue}" for i, issue in enumerate(issues_summary))

        return f"""## Task
You are rewriting a resume to address the following issues identified by multiple expert reviewers.

## Current Resume Content:
```
{content}
```

## Issues to Address:
{issues_text}

## Instructions:
Please rewrite THE ENTIRE resume content, addressing all the issues listed above.

CRITICAL REQUIREMENTS:
1. Return THE COMPLETE resume content - do not truncate or abbreviate
2. Address ALL issues listed above with appropriate revisions
3. Maintain the same overall structure (sections, headers, formatting)
4. Keep all existing content, but improve/enhance based on feedback
5. Do NOT add any YAML frontmatter (title, format, etc.) - only the markdown content
6. Do NOT fabricate experience or credentials - only enhance truthful presentation
7. Keep the same language (Japanese) as the original
8. Ensure all sections are complete and no content is cut off

Return ONLY the revised resume content, nothing else."""
