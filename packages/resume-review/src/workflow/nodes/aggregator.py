"""Aggregator node for calculating integrated scores."""

import logging
from typing import Any

from ..scoring import calculate_integrated_score
from ..state import ReviewState

logger = logging.getLogger("resume_review")


def aggregator_node(state: ReviewState) -> dict[str, Any]:
    """
    Aggregator node that calculates integrated score from feedback.

    Combines individual agent scores using weighted averaging.
    """
    logger.info("Aggregator: Calculating integrated score")

    current_feedback = state.get("current_feedback", [])
    if not current_feedback:
        return {"error": "No feedback to aggregate"}

    # Calculate integrated score
    integrated_score = calculate_integrated_score(current_feedback)

    # Check threshold
    threshold = state.get("score_threshold", 8.0)
    threshold_met = integrated_score >= threshold

    logger.info(
        f"Aggregator: Integrated score = {integrated_score:.2f}/10.0 "
        f"(threshold: {threshold}, met: {threshold_met})"
    )

    # Update feedback history - wrap current_feedback as a single-element list
    # The reducer will append this to existing history: existing + [current_feedback]
    feedback_history = [current_feedback]

    return {
        "integrated_score": integrated_score,
        "threshold_met": threshold_met,
        "feedback_history": feedback_history,
        "final_score": integrated_score,
    }
