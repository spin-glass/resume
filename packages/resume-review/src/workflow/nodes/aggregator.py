"""Aggregator node for calculating integrated scores."""

import logging
from typing import Any

from ..scoring import calculate_integrated_score
from ..state import ReviewState

logger = logging.getLogger("resume_review")


def aggregator_node(state: ReviewState) -> dict[str, Any]:
    """
    Aggregator node that calculates integrated score from feedback.

    Collects feedback from three parallel agent nodes (recruiter, tech_writer,
    copywriter) and merges them into the canonical current_feedback list.
    Combines individual agent scores using weighted averaging.
    """
    logger.info("Aggregator: Collecting feedback from agent nodes")

    # Collect feedback from separate per-agent fields (NEW: for separate agent nodes)
    # NOTE: This per-agent feedback collection enables future per-agent retry logic (US4).
    # If one agent fails, we can retry only that agent while keeping others' feedback.
    current_feedback = []
    if "recruiter_feedback" in state:
        current_feedback.append(state["recruiter_feedback"])
    if "tech_writer_feedback" in state:
        current_feedback.append(state["tech_writer_feedback"])
    if "copywriter_feedback" in state:
        current_feedback.append(state["copywriter_feedback"])

    if not current_feedback:
        logger.warning("Aggregator: No feedback collected from agent nodes")
        return {"error": "All agents failed"}

    # Log feedback collection
    logger.debug(f"Received feedback from {len(current_feedback)} agents")

    # Calculate integrated score
    integrated_score = calculate_integrated_score(current_feedback)

    # Check threshold
    threshold = state.get("score_threshold", 8.0)
    threshold_met = integrated_score >= threshold

    logger.info(
        f"Integrated score: {integrated_score:.2f} (threshold: {threshold})"
    )

    # Update feedback history - wrap current_feedback as a single-element list
    # The reducer will append this to existing history: existing + [current_feedback]
    feedback_history = [current_feedback]

    return {
        "current_feedback": current_feedback,  # NEW: Set merged feedback
        "integrated_score": integrated_score,
        "threshold_met": threshold_met,
        "feedback_history": feedback_history,
        "final_score": integrated_score,
    }
