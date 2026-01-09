"""Score aggregation and integration logic."""

from ..config.weights import AGENT_WEIGHTS
from ..models.feedback import Feedback


def calculate_integrated_score(feedback_list: list[Feedback]) -> float:
    """
    Calculate weighted average of agent scores.

    Weights based on FR-004 and assumptions section:
    - Recruiter: 30% (most important for contract acquisition)
    - Technical Writer: 20% (technical depth)
    - Copywriter: 25% (marketing effectiveness)
    - UX Designer: 15% (scannability)
    - Visual Designer: 10% (visual polish)

    Args:
        feedback_list: List of Feedback from different agents

    Returns:
        Integrated score (1.0-10.0)

    Raises:
        ValueError: If feedback_list is empty or contains no valid agents
    """
    if not feedback_list:
        raise ValueError("Cannot calculate score from empty feedback list")

    total_score = 0.0
    total_weight = 0.0

    for feedback in feedback_list:
        weight = AGENT_WEIGHTS.get(feedback.agent_name, 0.0)
        if weight > 0:
            total_score += feedback.score * weight
            total_weight += weight

    if total_weight == 0:
        raise ValueError("No valid agent feedback found for scoring")

    return total_score / total_weight


def get_agent_weight(agent_name: str) -> float:
    """Get the weight for a specific agent."""
    return AGENT_WEIGHTS.get(agent_name, 0.0)


def validate_score(score: float) -> bool:
    """Validate that a score is within valid range (1.0-10.0)."""
    return 1.0 <= score <= 10.0
