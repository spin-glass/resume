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
    threshold_met = state.get("threshold_met", False)
    current_iteration = state.get("current_iteration", 0)
    max_iterations = state.get("max_iterations", 3)

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
    if state.get("screenshot_url"):
        logger.info("Condition: Screenshot URL provided, proceeding to design review")
        return "design"

    logger.info("Condition: No screenshot URL, ending workflow")
    return "end"
