"""Supervisor nodes for coordinating agent execution."""

import asyncio
import logging
from typing import Any

from ...agents.copywriter import CopywriterAgent
from ...agents.recruiter import RecruiterAgent
from ...agents.technical_writer import TechnicalWriterAgent
from ...config.model_config import AgentName, calculate_cost
from ...models.feedback import Feedback
from ...services.llm_factory import LLMClientFactory
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

    resume = state["resume"]
    target_role = state["target_role"]
    job_posting = state.get("job_posting")

    # Get API keys (new multi-provider support)
    gemini_api_key = state.get("gemini_api_key")
    openai_api_key = state.get("openai_api_key")
    anthropic_api_key = state.get("anthropic_api_key") or state.get("api_key")
    override_model = state.get("override_model")

    # Initialize token usage tracking
    if "token_usage" not in state:
        state["token_usage"] = {}

    # Create LLM clients for each agent using factory
    recruiter_client = LLMClientFactory.create_client(
        agent_name=AgentName.RECRUITER,
        gemini_api_key=gemini_api_key,
        openai_api_key=openai_api_key,
        anthropic_api_key=anthropic_api_key,
        override_model=override_model,
    )
    tech_writer_client = LLMClientFactory.create_client(
        agent_name=AgentName.TECHNICAL_WRITER,
        gemini_api_key=gemini_api_key,
        openai_api_key=openai_api_key,
        anthropic_api_key=anthropic_api_key,
        override_model=override_model,
    )
    copywriter_client = LLMClientFactory.create_client(
        agent_name=AgentName.COPYWRITER,
        gemini_api_key=gemini_api_key,
        openai_api_key=openai_api_key,
        anthropic_api_key=anthropic_api_key,
        override_model=override_model,
    )

    # Initialize agents with injected LLM clients
    recruiter = RecruiterAgent(llm_client=recruiter_client)
    tech_writer = TechnicalWriterAgent(llm_client=tech_writer_client)
    copywriter = CopywriterAgent(llm_client=copywriter_client)

    # Run all agents in parallel using asyncio.gather
    try:
        results = await asyncio.gather(
            recruiter.evaluate_async(resume, target_role, job_posting=job_posting),
            tech_writer.evaluate_async(resume, target_role, job_posting=job_posting),
            copywriter.evaluate_async(resume, target_role, job_posting=job_posting),
            return_exceptions=True,
        )

        # Process results, handling any exceptions
        feedback_list = []
        token_usage = state.get("token_usage", {})

        for i, result in enumerate(results):
            agent_name = ["recruiter", "technical_writer", "copywriter"][i]
            client = [recruiter_client, tech_writer_client, copywriter_client][i]

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

                # Log token usage for cost tracking
                # Note: In real implementation, we'd capture this from LLMResponse
                # For now, we track the model used
                token_usage[agent_name] = {
                    "model": client.model,
                    "provider": client.provider,
                }

        return {
            "current_feedback": feedback_list,
            "token_usage": token_usage,
        }

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

    target_role = state["target_role"]

    # Get API keys
    gemini_api_key = state.get("gemini_api_key")
    openai_api_key = state.get("openai_api_key")
    anthropic_api_key = state.get("anthropic_api_key") or state.get("api_key")
    override_model = state.get("override_model")

    # Import design agents and screenshot service
    from ...agents.ux_designer import UXDesignerAgent
    from ...agents.visual_designer import VisualDesignerAgent
    from ...services.screenshot import ScreenshotService

    try:
        # Capture screenshot
        screenshot_service = ScreenshotService()
        screenshot_path = await screenshot_service.capture(screenshot_url)

        if not screenshot_path:
            logger.warning("Design Supervisor: Failed to capture screenshot")
            return {}

        # Create LLM clients for design agents
        ux_client = LLMClientFactory.create_client(
            agent_name=AgentName.UX_DESIGNER,
            gemini_api_key=gemini_api_key,
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            override_model=override_model,
        )
        visual_client = LLMClientFactory.create_client(
            agent_name=AgentName.VISUAL_DESIGNER,
            gemini_api_key=gemini_api_key,
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            override_model=override_model,
        )

        # Initialize design agents with injected clients
        ux_designer = UXDesignerAgent(llm_client=ux_client)
        visual_designer = VisualDesignerAgent(llm_client=visual_client)

        # Run design agents in parallel (both are now async)
        ux_feedback, visual_feedback = await asyncio.gather(
            ux_designer.evaluate_from_screenshot(str(screenshot_path), target_role),
            visual_designer.evaluate_from_screenshot(str(screenshot_path), target_role),
        )

        design_feedback = [ux_feedback, visual_feedback]

        # Recalculate score with design feedback
        all_feedback = state.get("current_feedback", []) + design_feedback
        final_score = calculate_integrated_score(all_feedback)

        # Calculate design-specific score (average of design agents)
        design_scores = [f.score for f in design_feedback]
        design_score = sum(design_scores) / len(design_scores) if design_scores else 0.0
        
        logger.info(f"Design Score: {design_score:.1f}/10.0")

        # Save feedback to design_iter folder if session_dir exists
        session_dir_raw = state.get("session_dir")
        if session_dir_raw:
            from pathlib import Path
            design_iteration = state.get("design_iteration", 0)
            session_dir = Path(session_dir_raw)
            design_dir = session_dir / f"design_iter{design_iteration + 1}"
            design_dir.mkdir(parents=True, exist_ok=True)
            
            feedback_path = design_dir / "feedback.md"
            with open(feedback_path, "w") as f:
                f.write(f"# Design Feedback (Score: {design_score:.1f}/10.0)\n\n")
                
                for fb in design_feedback:
                    f.write(f"## {fb.agent_name} (Score: {fb.score}/10.0)\n\n")
                    
                    if fb.strengths:
                        f.write("### Strengths\n")
                        for s in fb.strengths:
                            f.write(f"- {s}\n")
                        f.write("\n")
                    
                    if fb.issues:
                        f.write("### Issues\n")
                        for issue in fb.issues:
                            f.write(f"- {issue.description}\n")
                        f.write("\n")
                    
                    if fb.suggestions:
                        f.write("### Suggestions\n")
                        for s in fb.suggestions:
                            f.write(f"- {s}\n")
                        f.write("\n")
        else:
            logger.info("Skipping design feedback file save (no session_dir provided)")

        return {
            "current_feedback": all_feedback,
            "feedback_history": [design_feedback],
            "final_score": final_score,
            "design_score": design_score,
            "design_loop_active": True,
        }

    except Exception as e:
        logger.warning(f"Design Supervisor: Design review failed: {e}")
        return {}
