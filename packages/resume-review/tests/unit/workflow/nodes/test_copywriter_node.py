"""Unit tests for copywriter_node."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from src.models.feedback import Feedback, Resume
from src.workflow.nodes.copywriter import copywriter_node


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
        agent_name="copywriter",
        score=9.0,
        strengths=["Compelling narrative"],
        issues=[],
        suggestions=["Add more impact statements"],
    )


@pytest.mark.asyncio
async def test_copywriter_node_success(mock_resume, mock_feedback):
    """Copywriter node returns feedback on success."""
    # Setup
    state = {
        "resume": mock_resume,
        "target_role": "Engineer",
        "anthropic_api_key": "test-key",
    }

    # Mock LLMClientFactory and CopywriterAgent
    with patch("src.workflow.nodes.copywriter.LLMClientFactory.create_client") as mock_factory:
        mock_client = Mock()
        mock_factory.return_value = mock_client

        with patch("src.workflow.nodes.copywriter.CopywriterAgent") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.evaluate_async = AsyncMock(return_value=mock_feedback)
            mock_agent_class.return_value = mock_agent

            # Execute
            result = await copywriter_node(state)

            # Verify
            assert "copywriter_feedback" in result
            assert result["copywriter_feedback"] == mock_feedback
            mock_agent.evaluate_async.assert_called_once_with(mock_resume, "Engineer")


@pytest.mark.asyncio
async def test_copywriter_node_handles_exception(mock_resume):
    """Copywriter node returns minimal feedback on exception."""
    # Setup
    state = {
        "resume": mock_resume,
        "target_role": "Engineer",
        "anthropic_api_key": "test-key",
    }

    # Mock LLMClientFactory to raise exception
    with patch("src.workflow.nodes.copywriter.LLMClientFactory.create_client") as mock_factory:
        mock_factory.side_effect = Exception("Network timeout")

        # Execute
        result = await copywriter_node(state)

        # Verify
        assert "copywriter_feedback" in result
        feedback = result["copywriter_feedback"]
        assert feedback.score == 5.0  # Neutral score
        assert "Evaluation failed" in feedback.strengths
        assert "Network timeout" in feedback.suggestions[0]
