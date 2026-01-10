"""Copywriter agent node for evaluating resume."""

import logging
import time
from typing import Any

from ...agents.copywriter import CopywriterAgent
from ...config.model_config import AgentName
from ...models.feedback import Feedback
from ...services.llm_factory import LLMClientFactory
from ..state import ReviewState

logger = logging.getLogger("resume_review")


async def copywriter_node(state: ReviewState) -> dict[str, Any]:
    """
    Copywriter agent node for evaluating resume.

    Args:
        state: Workflow state with resume and configuration

    Returns:
        Partial state update with copywriter_feedback field
    """
    start_time = time.perf_counter()
    logger.info("Starting copywriter node")

    try:
        # Extract required fields
        resume = state["resume"]
        target_role = state["target_role"]

        # Create LLM client for this agent
        client = LLMClientFactory.create_client(
            agent_name=AgentName.COPYWRITER,
            gemini_api_key=state.get("gemini_api_key"),
            openai_api_key=state.get("openai_api_key"),
            anthropic_api_key=state.get("anthropic_api_key"),
            override_model=state.get("override_model"),
        )

        # Initialize agent with client
        agent = CopywriterAgent(llm_client=client)

        # Evaluate resume
        feedback = await agent.evaluate_async(resume, target_role)

        # Log success
        duration = time.perf_counter() - start_time
        logger.debug(f"Copywriter score: {feedback.score}/10.0")
        logger.info(f"Copywriter node completed in {duration:.2f}s")

        return {"copywriter_feedback": feedback}

    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.error(f"Error in copywriter node after {duration:.2f}s: {e}")

        # Return minimal feedback to allow workflow to continue
        return {
            "copywriter_feedback": Feedback(
                agent_name="copywriter",
                score=5.0,
                strengths=["Evaluation failed"],
                issues=[],
                suggestions=[f"Error: {str(e)}"],
            )
        }
