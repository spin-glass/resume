"""Technical writer agent node for evaluating resume."""

import logging
import time
from typing import Any

from ...agents.technical_writer import TechnicalWriterAgent
from ...config.model_config import AgentName
from ...models.feedback import Feedback
from ...services.llm_factory import LLMClientFactory
from ..state import ReviewState

logger = logging.getLogger("resume_review")


async def tech_writer_node(state: ReviewState) -> dict[str, Any]:
    """
    Technical writer agent node for evaluating resume.

    Args:
        state: Workflow state with resume and configuration

    Returns:
        Partial state update with tech_writer_feedback field
    """
    start_time = time.perf_counter()
    logger.info("Starting tech_writer node")

    try:
        # Extract required fields
        resume = state.resume
        target_role = state.target_role

        # Create LLM client for this agent
        client = LLMClientFactory.create_client(
            agent_name=AgentName.TECHNICAL_WRITER,
            gemini_api_key=state.gemini_api_key,
            openai_api_key=state.openai_api_key,
            anthropic_api_key=state.anthropic_api_key,
            override_model=state.override_model,
        )

        # Initialize agent with client
        agent = TechnicalWriterAgent(llm_client=client)

        # Evaluate resume
        feedback = await agent.evaluate_async(resume, target_role)

        # Log success
        duration = time.perf_counter() - start_time
        logger.debug(f"Tech writer score: {feedback.score}/10.0")
        logger.info(f"Tech writer node completed in {duration:.2f}s")

        return {"tech_writer_feedback": feedback}

    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.error(f"Error in tech_writer node after {duration:.2f}s: {e}")

        # Return minimal feedback to allow workflow to continue
        return {
            "tech_writer_feedback": Feedback(
                agent_name="technical_writer",
                score=5.0,
                strengths=["Evaluation failed"],
                issues=[],
                suggestions=[f"Error: {str(e)}"],
            )
        }
