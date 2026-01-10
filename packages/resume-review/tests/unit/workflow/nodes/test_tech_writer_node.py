"""Unit tests for tech_writer_node."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from src.models.feedback import Feedback, Resume
from src.workflow.nodes.tech_writer import tech_writer_node
from src.workflow.state import ReviewState


@pytest.fixture
def mock_resume():
    """Create a mock Resume object."""
    return Resume(
        file_path=Path("test.qmd"),
        yaml_frontmatter={"title": "Test Resume"},
        content="Test content",
        full_text="---\ntitle: Test Resume\n---\nTest content",
    )


@pytest.fixture
def mock_feedback():
    """Create a mock Feedback object."""
    return Feedback(
        agent_name="technical_writer",
        score=7.0,
        strengths=["Clear writing"],
        issues=[],
        suggestions=["Improve technical details"],
    )


@pytest.mark.asyncio
async def test_tech_writer_node_success(mock_resume, mock_feedback):
    """Tech writer node returns feedback on success."""
    # Setup
    # Setup
    state = ReviewState(
        resume=mock_resume,
        target_role="Engineer",
        openai_api_key="test-key",
    )

    # Mock LLMClientFactory and TechnicalWriterAgent
    with patch("src.workflow.nodes.tech_writer.LLMClientFactory.create_client") as mock_factory:
        mock_client = Mock()
        mock_factory.return_value = mock_client

        with patch("src.workflow.nodes.tech_writer.TechnicalWriterAgent") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.evaluate_async = AsyncMock(return_value=mock_feedback)
            mock_agent_class.return_value = mock_agent

            # Execute
            result = await tech_writer_node(state)

            # Verify
            assert "tech_writer_feedback" in result
            assert result["tech_writer_feedback"] == mock_feedback
            mock_agent.evaluate_async.assert_called_once_with(mock_resume, "Engineer")


@pytest.mark.asyncio
async def test_tech_writer_node_handles_exception(mock_resume):
    """Tech writer node returns minimal feedback on exception."""
    # Setup
    # Setup
    state = ReviewState(
        resume=mock_resume,
        target_role="Engineer",
        openai_api_key="test-key",
    )

    # Mock LLMClientFactory to raise exception
    with patch("src.workflow.nodes.tech_writer.LLMClientFactory.create_client") as mock_factory:
        mock_factory.side_effect = Exception("Rate limit exceeded")

        # Execute
        result = await tech_writer_node(state)

        # Verify
        assert "tech_writer_feedback" in result
        feedback = result["tech_writer_feedback"]
        assert feedback.score == 5.0  # Neutral score
        assert "Evaluation failed" in feedback.strengths
        assert "Rate limit exceeded" in feedback.suggestions[0]
