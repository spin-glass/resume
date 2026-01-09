"""Agent scoring weights configuration.

Weights are based on FR-004 and the data model specification.
These determine how each agent's score contributes to the final integrated score.
"""

# Agent weights for score integration
# Based on FR-004: Weighted average targeting 8.0+ for contract positions
AGENT_WEIGHTS = {
    "recruiter": 0.30,  # Most important for contract acquisition
    "technical_writer": 0.20,  # Technical depth and clarity
    "copywriter": 0.25,  # Marketing effectiveness and value proposition
    "ux_designer": 0.15,  # Scannability and information hierarchy
    "visual_designer": 0.10,  # Visual polish and presentation
}


def get_agent_weight(agent_name: str) -> float:
    """
    Get the weight for a specific agent.

    Args:
        agent_name: Name of the agent (e.g., "recruiter", "copywriter")

    Returns:
        Weight as a float (0.0 if agent not found)
    """
    return AGENT_WEIGHTS.get(agent_name, 0.0)


def validate_weights() -> bool:
    """Validate that weights sum to 1.0."""
    total = sum(AGENT_WEIGHTS.values())
    return abs(total - 1.0) < 0.001


# Score interpretation thresholds
SCORE_THRESHOLDS = {
    "premium": 8.0,  # Ready for 120万円+ positions
    "competitive": 7.0,  # Ready for standard premium rates
    "improvement_needed": 6.0,  # Needs work for premium positioning
}
