"""Unit tests for aggregator_node."""

import pytest

from src.models.feedback import Feedback
from src.workflow.nodes.aggregator import aggregator_node


@pytest.fixture
def recruiter_feedback():
    """Create recruiter feedback."""
    return Feedback(
        agent_name="recruiter",
        score=8.5,
        strengths=["Strong experience"],
        issues=[],
        suggestions=[],
    )


@pytest.fixture
def tech_writer_feedback():
    """Create tech writer feedback."""
    return Feedback(
        agent_name="technical_writer",
        score=7.0,
        strengths=["Clear writing"],
        issues=[],
        suggestions=[],
    )


@pytest.fixture
def copywriter_feedback():
    """Create copywriter feedback."""
    return Feedback(
        agent_name="copywriter",
        score=9.0,
        strengths=["Compelling narrative"],
        issues=[],
        suggestions=[],
    )


def test_aggregator_collects_from_separate_fields(
    recruiter_feedback, tech_writer_feedback, copywriter_feedback
):
    """Aggregator merges feedback from three separate state fields."""
    # Setup
    state = {
        "recruiter_feedback": recruiter_feedback,
        "tech_writer_feedback": tech_writer_feedback,
        "copywriter_feedback": copywriter_feedback,
        "score_threshold": 8.0,
    }

    # Execute
    result = aggregator_node(state)

    # Verify
    assert "current_feedback" in result
    assert len(result["current_feedback"]) == 3
    assert result["current_feedback"][0] == recruiter_feedback
    assert result["current_feedback"][1] == tech_writer_feedback
    assert result["current_feedback"][2] == copywriter_feedback
    assert "integrated_score" in result
    assert result["integrated_score"] > 0
    assert "threshold_met" in result


def test_aggregator_handles_missing_feedback(recruiter_feedback, copywriter_feedback):
    """Aggregator proceeds with partial feedback if one agent failed."""
    # Setup (tech_writer_feedback missing)
    state = {
        "recruiter_feedback": recruiter_feedback,
        # tech_writer_feedback missing (agent failed)
        "copywriter_feedback": copywriter_feedback,
        "score_threshold": 8.0,
    }

    # Execute
    result = aggregator_node(state)

    # Verify - should have only 2 feedbacks
    assert "current_feedback" in result
    assert len(result["current_feedback"]) == 2
    assert "integrated_score" in result
    assert result["integrated_score"] > 0


def test_aggregator_returns_error_if_no_feedback():
    """Aggregator returns error if all agents failed."""
    # Setup (no feedback fields)
    state = {
        "score_threshold": 8.0,
    }

    # Execute
    result = aggregator_node(state)

    # Verify
    assert "error" in result
    assert result["error"] == "All agents failed"


def test_aggregator_calculates_threshold_met(
    recruiter_feedback, tech_writer_feedback, copywriter_feedback
):
    """Aggregator correctly determines threshold_met status."""
    # Setup with low threshold
    state = {
        "recruiter_feedback": recruiter_feedback,  # 8.5
        "tech_writer_feedback": tech_writer_feedback,  # 7.0
        "copywriter_feedback": copywriter_feedback,  # 9.0
        "score_threshold": 7.0,  # Should be met
    }

    # Execute
    result = aggregator_node(state)

    # Verify
    assert result["threshold_met"] is True
    assert result["integrated_score"] >= 7.0


def test_aggregator_calculates_threshold_not_met(
    recruiter_feedback, tech_writer_feedback, copywriter_feedback
):
    """Aggregator correctly determines threshold not met."""
    # Setup with high threshold
    state = {
        "recruiter_feedback": recruiter_feedback,  # 8.5
        "tech_writer_feedback": tech_writer_feedback,  # 7.0
        "copywriter_feedback": copywriter_feedback,  # 9.0
        "score_threshold": 10.0,  # Cannot be met
    }

    # Execute
    result = aggregator_node(state)

    # Verify
    assert result["threshold_met"] is False
    assert result["integrated_score"] < 10.0
