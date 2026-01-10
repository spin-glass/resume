"""Conditional edge functions for LangGraph workflow routing."""

import logging
from typing import Literal

from .state import ReviewState

logger = logging.getLogger("resume_review")


def should_continue_review(state: ReviewState) -> Literal["revisor", "portfolio"]:
    """
    Determine whether to continue revision or move to portfolio analysis.

    Returns:
        "revisor" if more iterations needed, "portfolio" if threshold met or max iterations reached
    """
    threshold_met = state.threshold_met
    current_iteration = state.current_iteration
    max_iterations = state.max_iterations

    if threshold_met:
        logger.info("Condition: Threshold met, proceeding to portfolio analysis")
        return "portfolio"

    if current_iteration >= max_iterations - 1:
        logger.info("Condition: Max iterations reached, proceeding to portfolio analysis")
        return "portfolio"

    logger.info("Condition: Continuing to revision")
    return "revisor"


def should_do_design_review(state: ReviewState) -> Literal["design", "end"]:
    """
    Determine whether to run design review.

    Returns:
        "design" if screenshot_url provided, "end" otherwise
    """
    if state.screenshot_url:
        logger.info("Condition: Screenshot URL provided, proceeding to design review")
        return "design"

    logger.info("Condition: No screenshot URL, ending workflow")
    return "end"


def should_run_design_applier(state: ReviewState) -> Literal["design_applier", "end"]:
    """
    Determine whether to run design applier node.

    Returns:
        "design_applier" if design modifications enabled and feedback exists
        "end" otherwise
    """
    auto_design = state.get("auto_design_enabled", False)
    preview = state.get("design_preview_enabled", False)

    if not (auto_design or preview):
        logger.info("Condition: Design modifications disabled, ending workflow")
        return "end"

    design_iteration = state.get("design_iteration", 0)
    max_design_iterations = state.get("max_design_iterations", 3)

    if design_iteration >= max_design_iterations:
        logger.info(f"Condition: Max design iterations ({max_design_iterations}) reached, ending workflow")
        return "end"

    # Get design-related feedback
    current_feedback = state.get("current_feedback", [])
    design_feedback = [
        f for f in current_feedback if f.agent_name in ["ux_designer", "visual_designer"]
    ]

    if len(design_feedback) > 0:
        design_score = state.get("design_score", 0.0)
        threshold = state.get("score_threshold", 8.0)

        if design_score >= threshold:
            logger.info(
                f"Condition: Design threshold met ({design_score:.2f} >= {threshold}), ending workflow"
            )
            return "end"

        logger.info("Condition: Proceeding to design applier")
        return "design_applier"

    logger.info("Condition: No design feedback, ending workflow")
    return "end"
