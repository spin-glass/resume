"""Supervisor nodes for coordinating agent execution."""

import asyncio
import logging
from typing import Any

from ...agents.copywriter import CopywriterAgent
from ...agents.recruiter import RecruiterAgent
from ...agents.technical_writer import TechnicalWriterAgent
from ...models.feedback import Feedback
from ..scoring import calculate_integrated_score
from ..state import ReviewState

logger = logging.getLogger("resume_review")


async def supervisor_node(state: ReviewState) -> dict[str, Any]:
    """
    Supervisor node that coordinates parallel agent execution.

    Runs recruiter, technical_writer, and copywriter agents in parallel
    using asyncio.gather for efficiency.
    """
    logger.info(
        f"Supervisor: Starting parallel agent evaluation (iteration {state.get('current_iteration', 0) + 1})"
    )

    api_key = state["api_key"]
    resume = state["resume"]
    target_role = state["target_role"]

    # Initialize agents
    recruiter = RecruiterAgent(api_key)
    tech_writer = TechnicalWriterAgent(api_key)
    copywriter = CopywriterAgent(api_key)

    # Run all agents in parallel using asyncio.gather
    try:
        results = await asyncio.gather(
            recruiter.evaluate_async(resume, target_role),
            tech_writer.evaluate_async(resume, target_role),
            copywriter.evaluate_async(resume, target_role),
            return_exceptions=True,
        )

        # Process results, handling any exceptions
        feedback_list = []
        for i, result in enumerate(results):
            agent_name = ["recruiter", "technical_writer", "copywriter"][i]
            if isinstance(result, Exception):
                logger.error(f"Agent {agent_name} failed: {result}")
                # Create minimal feedback for failed agent
                feedback_list.append(
                    Feedback(
                        agent_name=agent_name,
                        score=5.0,  # Neutral score
                        strengths=["Evaluation failed"],
                        issues=[],
                        suggestions=[f"Error: {str(result)}"],
                    )
                )
            else:
                feedback_list.append(result)
                logger.debug(f"Agent {agent_name} score: {result.score}/10.0")

        return {"current_feedback": feedback_list}

    except Exception as e:
        logger.error(f"Supervisor node failed: {e}")
        return {"error": str(e)}


async def design_supervisor_node(state: ReviewState) -> dict[str, Any]:
    """
    Design supervisor node that coordinates UX and Visual designer agents.

    Only runs if screenshot_url is provided.
    """
    screenshot_url = state.get("screenshot_url")
    if not screenshot_url:
        logger.info("Design Supervisor: No screenshot URL, skipping design review")
        return {}

    logger.info(f"Design Supervisor: Starting design review for {screenshot_url}")

    api_key = state["api_key"]
    target_role = state["target_role"]

    # Import design agents and screenshot service
    from ...agents.ux_designer import UXDesignerAgent
    from ...agents.visual_designer import VisualDesignerAgent
    from ...services.screenshot import ScreenshotService

    try:
        # Capture screenshot
        screenshot_service = ScreenshotService()
        screenshot_path = screenshot_service.capture(screenshot_url)

        if not screenshot_path:
            logger.warning("Design Supervisor: Failed to capture screenshot")
            return {}

        # Initialize design agents
        ux_designer = UXDesignerAgent(api_key)
        visual_designer = VisualDesignerAgent(api_key)

        # Run design agents in parallel
        ux_feedback, visual_feedback = await asyncio.gather(
            asyncio.get_event_loop().run_in_executor(
                None, ux_designer.evaluate_from_screenshot, str(screenshot_path), target_role
            ),
            asyncio.get_event_loop().run_in_executor(
                None,
                visual_designer.evaluate_from_screenshot,
                str(screenshot_path),
                target_role,
            ),
        )

        design_feedback = [ux_feedback, visual_feedback]

        # Recalculate score with design feedback
        all_feedback = state.get("current_feedback", []) + design_feedback
        final_score = calculate_integrated_score(all_feedback)

        return {
            "current_feedback": all_feedback,
            "feedback_history": [design_feedback],
            "final_score": final_score,
        }

    except Exception as e:
        logger.warning(f"Design Supervisor: Design review failed: {e}")
        return {}
