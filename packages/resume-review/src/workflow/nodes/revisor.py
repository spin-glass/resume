"""Revisor node for applying content revisions."""

import asyncio
import logging
from typing import Any

from ...agents.revisor import RevisorAgent
from ...config.model_config import AgentName
from ...services.llm_factory import LLMClientFactory
from ..state import ReviewState

logger = logging.getLogger("resume_review")


async def revisor_node(state: ReviewState) -> dict[str, Any]:
    """
    Revisor node that applies content revisions based on feedback.

    Uses RevisorAgent with full-rewrite approach to eliminate fuzzy replacement errors.
    """
    logger.info("Revisor: Applying content revisions using full-rewrite approach")

    resume = state.resume
    current_feedback = state.current_feedback
    dry_run = state.dry_run
    target_role = state.target_role

    # Get API keys
    gemini_api_key = state.gemini_api_key
    openai_api_key = state.openai_api_key
    anthropic_api_key = state.anthropic_api_key or state.api_key
    override_model = state.override_model

    # Create LLM client for Revisor (uses Gemini for cost-effectiveness)
    revisor_client = LLMClientFactory.create_client(
        agent_name=AgentName.REVISOR,
        gemini_api_key=gemini_api_key,
        openai_api_key=openai_api_key,
        anthropic_api_key=anthropic_api_key,
        override_model=override_model,
    )

    # Initialize RevisorAgent with injected LLM client
    revisor = RevisorAgent(llm_client=revisor_client)

    try:
        revised_resume, revisions = await revisor.apply_revisions_async(
            resume, current_feedback, target_role=target_role, dry_run=dry_run
        )

        # Update state with revisions
        result = {
            "applied_revisions": revisions,
            "current_iteration": state.current_iteration + 1,
        }

        if not dry_run:
            result["resume"] = revised_resume
            result["resume_content"] = revised_resume.content
            result["revised_content"] = revised_resume.content

        logger.info(f"Revisor: Applied {len(revisions)} revisions")
        return result

    except Exception as e:
        logger.error(f"Revisor node failed: {e}")
        return {"error": str(e), "applied_revisions": [f"Error: {str(e)}"]}
