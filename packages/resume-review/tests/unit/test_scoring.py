"""Unit tests for scoring system."""

import pytest

from src.models.feedback import Feedback, Issue
from src.models import ActionType, Severity
from src.workflow.scoring import (
    calculate_integrated_score,
    get_agent_weight,
    validate_score,
    AGENT_WEIGHTS,
)


def test_calculate_integrated_score_basic():
    """Test basic score integration."""
    feedback_list = [
        Feedback(
            agent_name="recruiter",
            score=8.0,
            strengths=["Good experience"],
            issues=[],
            suggestions=[],
        ),
        Feedback(
            agent_name="technical_writer",
            score=7.0,
            strengths=["Clear writing"],
            issues=[],
            suggestions=[],
        ),
        Feedback(
            agent_name="copywriter",
            score=9.0,
            strengths=["Compelling"],
            issues=[],
            suggestions=[],
        ),
    ]

    score = calculate_integrated_score(feedback_list)

    # Manual calculation:
    # recruiter: 8.0 * 0.30 = 2.4
    # technical_writer: 7.0 * 0.20 = 1.4
    # copywriter: 9.0 * 0.25 = 2.25
    # Total: 6.05 / 0.75 = 8.067
    expected = (8.0 * 0.30 + 7.0 * 0.20 + 9.0 * 0.25) / (0.30 + 0.20 + 0.25)

    assert abs(score - expected) < 0.01


def test_calculate_integrated_score_all_agents():
    """Test score integration with all 5 agents."""
    feedback_list = [
        Feedback(agent_name="recruiter", score=8.0, strengths=["test"], issues=[], suggestions=[]),
        Feedback(agent_name="technical_writer", score=7.5, strengths=["test"], issues=[], suggestions=[]),
        Feedback(agent_name="copywriter", score=8.5, strengths=["test"], issues=[], suggestions=[]),
        Feedback(agent_name="ux_designer", score=7.0, strengths=["test"], issues=[], suggestions=[]),
        Feedback(agent_name="visual_designer", score=9.0, strengths=["test"], issues=[], suggestions=[]),
    ]

    score = calculate_integrated_score(feedback_list)

    # Should be weighted average
    expected = (
        8.0 * 0.30
        + 7.5 * 0.20
        + 8.5 * 0.25
        + 7.0 * 0.15
        + 9.0 * 0.10
    ) / 1.0  # Total weight = 1.0

    assert abs(score - expected) < 0.01


def test_calculate_integrated_score_empty_list():
    """Test error handling for empty feedback list."""
    with pytest.raises(ValueError, match="Cannot calculate score from empty feedback list"):
        calculate_integrated_score([])


def test_calculate_integrated_score_unknown_agent():
    """Test handling of unknown agent (should be ignored)."""
    feedback_list = [
        Feedback(agent_name="recruiter", score=8.0, strengths=["test"], issues=[], suggestions=[]),
        Feedback(agent_name="unknown_agent", score=10.0, strengths=["test"], issues=[], suggestions=[]),
    ]

    score = calculate_integrated_score(feedback_list)

    # Unknown agent should be ignored (weight 0)
    expected = 8.0  # Only recruiter with weight 0.30, normalized to 8.0

    assert abs(score - expected) < 0.01


def test_calculate_integrated_score_only_unknown_agents():
    """Test error when only unknown agents present."""
    feedback_list = [
        Feedback(agent_name="unknown1", score=8.0, strengths=["test"], issues=[], suggestions=[]),
        Feedback(agent_name="unknown2", score=9.0, strengths=["test"], issues=[], suggestions=[]),
    ]

    with pytest.raises(ValueError, match="No valid agent feedback found"):
        calculate_integrated_score(feedback_list)


def test_get_agent_weight():
    """Test getting agent weights."""
    assert get_agent_weight("recruiter") == 0.30
    assert get_agent_weight("technical_writer") == 0.20
    assert get_agent_weight("copywriter") == 0.25
    assert get_agent_weight("ux_designer") == 0.15
    assert get_agent_weight("visual_designer") == 0.10
    assert get_agent_weight("unknown") == 0.0


def test_agent_weights_sum_to_one():
    """Test that all agent weights sum to 1.0."""
    total = sum(AGENT_WEIGHTS.values())
    assert abs(total - 1.0) < 0.01


def test_validate_score():
    """Test score validation."""
    assert validate_score(1.0) is True
    assert validate_score(5.5) is True
    assert validate_score(10.0) is True

    assert validate_score(0.9) is False
    assert validate_score(10.1) is False
    assert validate_score(-1.0) is False


def test_score_range_boundary():
    """Test boundary values for scores."""
    # Exactly at boundaries
    feedback_min = [
        Feedback(agent_name="recruiter", score=1.0, strengths=["test"], issues=[], suggestions=[])
    ]
    score_min = calculate_integrated_score(feedback_min)
    assert score_min == 1.0

    feedback_max = [
        Feedback(agent_name="recruiter", score=10.0, strengths=["test"], issues=[], suggestions=[])
    ]
    score_max = calculate_integrated_score(feedback_max)
    assert score_max == 10.0


def test_weighted_average_property():
    """Test that weighted average is between min and max."""
    feedback_list = [
        Feedback(agent_name="recruiter", score=5.0, strengths=["test"], issues=[], suggestions=[]),
        Feedback(agent_name="copywriter", score=9.0, strengths=["test"], issues=[], suggestions=[]),
    ]

    score = calculate_integrated_score(feedback_list)

    # Weighted average should be between min and max
    assert 5.0 <= score <= 9.0
