"""Integration tests for LangGraph StateGraph workflow."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

from src.workflow import build_review_workflow, ReviewWorkflow
from src.workflow.state import ReviewState
from src.models.feedback import Resume, Feedback
from src.models import Severity, ActionType


class TestStateGraphCompilation:
    """Test that StateGraph compiles correctly."""

    def test_build_review_workflow_compiles(self):
        """Verify StateGraph compiles without errors."""
        workflow = build_review_workflow()
        assert workflow is not None

    def test_workflow_has_required_nodes(self):
        """Verify all required nodes are present."""
        workflow = build_review_workflow()
        # Check nodes exist
        node_names = list(workflow.nodes.keys())
        assert "supervisor" in node_names
        assert "aggregator" in node_names
        assert "revisor" in node_names
        assert "portfolio" in node_names
        assert "design" in node_names

    def test_workflow_entry_point(self):
        """Verify entry point is set correctly."""
        workflow = build_review_workflow()
        # Entry point should be supervisor
        assert "__start__" in workflow.nodes


class TestReviewWorkflowWrapper:
    """Test ReviewWorkflow CLI integration wrapper."""

    def test_wrapper_initializes_compiled_workflow(self):
        """Verify wrapper creates compiled workflow."""
        with patch("src.workflow.runner.build_review_workflow") as mock_build:
            mock_build.return_value = MagicMock()
            wrapper = ReviewWorkflow(api_key="test-key")
            assert wrapper.compiled_workflow is not None
            mock_build.assert_called_once()

    def test_wrapper_stores_api_key(self):
        """Verify API key is stored."""
        with patch("src.workflow.runner.build_review_workflow"):
            wrapper = ReviewWorkflow(api_key="test-key-123")
            assert wrapper.api_key == "test-key-123"

    def test_wrapper_stores_options(self):
        """Verify all options are stored."""
        with patch("src.workflow.runner.build_review_workflow"):
            wrapper = ReviewWorkflow(
                api_key="test-key",
                save_iterations=True,
                output_dir=Path("/tmp/test"),
            )
            assert wrapper.save_iterations is True
            assert wrapper.output_dir == Path("/tmp/test")


class TestStateSchema:
    """Test ReviewState TypedDict schema."""

    def test_review_state_can_be_created(self):
        """Verify ReviewState can be instantiated with required fields."""
        state: ReviewState = {
            "resume": MagicMock(spec=Resume),
            "resume_content": "test content",
            "target_role": "LLM Engineer",
            "score_threshold": 8.0,
            "max_iterations": 3,
            "api_key": "test-key",
            "dry_run": False,
            "screenshot_url": None,
            "save_iterations": False,
            "output_dir": None,
            "session_id": "test-session",
            "current_iteration": 0,
            "feedback_history": [],
            "current_feedback": [],
            "integrated_score": 0.0,
            "threshold_met": False,
            "skill_gaps": [],
            "portfolio_suggestions": [],
            "revised_content": "",
            "applied_revisions": [],
            "final_score": 0.0,
            "should_continue": True,
            "error": None,
        }
        assert state["target_role"] == "LLM Engineer"
        assert state["score_threshold"] == 8.0
        assert state["current_iteration"] == 0


class TestConditionalEdges:
    """Test conditional edge functions."""

    def test_should_continue_review_threshold_met(self):
        """When threshold is met, proceed to portfolio."""
        from src.workflow import should_continue_review

        state = {
            "threshold_met": True,
            "current_iteration": 1,
            "max_iterations": 3,
        }
        result = should_continue_review(state)
        assert result == "portfolio"

    def test_should_continue_review_max_iterations(self):
        """When max iterations reached, proceed to portfolio."""
        from src.workflow import should_continue_review

        state = {
            "threshold_met": False,
            "current_iteration": 2,
            "max_iterations": 3,
        }
        result = should_continue_review(state)
        assert result == "portfolio"

    def test_should_continue_review_continue(self):
        """When threshold not met and iterations remain, continue revision."""
        from src.workflow import should_continue_review

        state = {
            "threshold_met": False,
            "current_iteration": 0,
            "max_iterations": 3,
        }
        result = should_continue_review(state)
        assert result == "revisor"

    def test_should_do_design_review_with_url(self):
        """When screenshot URL provided, proceed to design review."""
        from src.workflow import should_do_design_review

        state = {"screenshot_url": "http://localhost:3000"}
        result = should_do_design_review(state)
        assert result == "design"

    def test_should_do_design_review_without_url(self):
        """When no screenshot URL, end workflow."""
        from src.workflow import should_do_design_review

        state = {"screenshot_url": None}
        result = should_do_design_review(state)
        assert result == "end"


class TestNodeFunctions:
    """Test individual node functions."""

    def test_aggregator_node_calculates_score(self):
        """Verify aggregator calculates integrated score."""
        from src.workflow import aggregator_node

        # Create mock feedback
        feedback1 = Feedback(
            agent_name="recruiter",
            score=8.0,
            strengths=["Good"],
            issues=[],
            suggestions=[],
        )
        feedback2 = Feedback(
            agent_name="technical_writer",
            score=7.0,
            strengths=["Good"],
            issues=[],
            suggestions=[],
        )

        state = {
            "current_feedback": [feedback1, feedback2],
            "score_threshold": 7.5,
        }

        result = aggregator_node(state)
        assert "integrated_score" in result
        assert "threshold_met" in result
        assert "feedback_history" in result
        assert result["integrated_score"] > 0

    def test_aggregator_node_handles_empty_feedback(self):
        """Verify aggregator handles empty feedback gracefully."""
        from src.workflow import aggregator_node

        state = {"current_feedback": [], "score_threshold": 8.0}
        result = aggregator_node(state)
        assert "error" in result


@pytest.mark.asyncio
class TestAsyncNodeFunctions:
    """Test async node functions."""

    async def test_supervisor_node_runs_agents_in_parallel(self):
        """Verify supervisor runs agents with asyncio.gather."""
        from src.workflow import supervisor_node

        # Create mock resume
        mock_resume = MagicMock(spec=Resume)
        mock_resume.content = "Test resume content"

        state = {
            "api_key": "test-key",
            "resume": mock_resume,
            "target_role": "LLM Engineer",
            "current_iteration": 0,
        }

        # Mock the LLM factory and agents to avoid actual API calls
        with patch("src.workflow.nodes.supervisor.LLMClientFactory") as mock_factory, \
             patch("src.workflow.nodes.supervisor.RecruiterAgent") as mock_recruiter, \
             patch("src.workflow.nodes.supervisor.TechnicalWriterAgent") as mock_tech, \
             patch("src.workflow.nodes.supervisor.CopywriterAgent") as mock_copy:

            # Mock factory to return a mock client
            mock_factory.create_client.return_value = MagicMock()

            # Setup mock feedback
            mock_feedback = Feedback(
                agent_name="test",
                score=7.0,
                strengths=["Test"],
                issues=[],
                suggestions=[],
            )

            mock_recruiter.return_value.evaluate_async = AsyncMock(return_value=mock_feedback)
            mock_tech.return_value.evaluate_async = AsyncMock(return_value=mock_feedback)
            mock_copy.return_value.evaluate_async = AsyncMock(return_value=mock_feedback)

            result = await supervisor_node(state)

            assert "current_feedback" in result
            assert len(result["current_feedback"]) == 3
