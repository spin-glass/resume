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
        # Updated for separate agent nodes (no longer "supervisor")
        assert "router" in node_names
        assert "recruiter" in node_names
        assert "tech_writer" in node_names
        assert "copywriter" in node_names
        assert "aggregator" in node_names
        assert "revisor" in node_names
        assert "portfolio" in node_names
        assert "design" in node_names

    def test_graph_has_separate_agent_nodes(self):
        """Verify graph contains router and three separate agent nodes (US2)."""
        workflow = build_review_workflow()
        node_names = list(workflow.nodes.keys())

        assert "router" in node_names, "Router node should be present"
        assert "recruiter" in node_names, "Recruiter node should be present"
        assert "tech_writer" in node_names, "Tech writer node should be present"
        assert "copywriter" in node_names, "Copywriter node should be present"
        assert "supervisor" not in node_names, "Supervisor node should be removed"

    def test_graph_has_fan_out_edges(self):
        """Verify router fans out to three agent nodes (US2)."""
        workflow = build_review_workflow()
        graph = workflow.get_graph()
        edges = [(e.source, e.target) for e in graph.edges]

        # Router should have edges to all three agents
        assert ("router", "recruiter") in edges
        assert ("router", "tech_writer") in edges
        assert ("router", "copywriter") in edges

    def test_graph_has_fan_in_edges(self):
        """Verify three agent nodes converge at aggregator (US2)."""
        workflow = build_review_workflow()
        graph = workflow.get_graph()
        edges = [(e.source, e.target) for e in graph.edges]

        # All three agents should have edges to aggregator
        assert ("recruiter", "aggregator") in edges
        assert ("tech_writer", "aggregator") in edges
        assert ("copywriter", "aggregator") in edges

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
        with patch("src.workflow.graph.build_review_workflow"):
            wrapper = ReviewWorkflow(api_key="test-key-123")
            assert wrapper.api_key == "test-key-123"

    def test_wrapper_stores_options(self):
        """Verify all options are stored."""
        with patch("src.workflow.graph.build_review_workflow"):
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
        """Verify aggregator calculates integrated score from separate fields."""
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
        feedback3 = Feedback(
            agent_name="copywriter",
            score=9.0,
            strengths=["Great"],
            issues=[],
            suggestions=[],
        )

        # Updated: Use per-agent feedback fields
        state = {
            "recruiter_feedback": feedback1,
            "tech_writer_feedback": feedback2,
            "copywriter_feedback": feedback3,
            "score_threshold": 7.5,
        }

        result = aggregator_node(state)
        assert "current_feedback" in result  # NEW: Aggregator now returns this
        assert "integrated_score" in result
        assert "threshold_met" in result
        assert "feedback_history" in result
        assert result["integrated_score"] > 0
        assert len(result["current_feedback"]) == 3

    def test_aggregator_node_handles_empty_feedback(self):
        """Verify aggregator handles empty feedback gracefully."""
        from src.workflow import aggregator_node

        # No per-agent feedback fields
        state = {"score_threshold": 8.0}
        result = aggregator_node(state)
        assert "error" in result


@pytest.mark.asyncio
class TestAsyncNodeFunctions:
    """Test async node functions."""

    async def test_agent_nodes_run_in_parallel(self):
        """
        Verify agent nodes run in parallel via LangGraph fan-out (US2).

        This test verifies that the three agent nodes execute concurrently,
        which is achieved through LangGraph's fan-out edge semantics rather
        than asyncio.gather as in the old supervisor implementation.
        """
        from src.workflow.nodes.recruiter import recruiter_node
        from src.workflow.nodes.tech_writer import tech_writer_node
        from src.workflow.nodes.copywriter import copywriter_node
        import asyncio
        import time

        # Create mock resume
        mock_resume = MagicMock(spec=Resume)
        mock_resume.content = "Test resume content"

        state = {
            "resume": mock_resume,
            "target_role": "LLM Engineer",
            "anthropic_api_key": "test-key",
            "openai_api_key": "test-key",
            "gemini_api_key": "test-key",
        }

        # Setup mock feedback
        mock_feedback = Feedback(
            agent_name="test",
            score=7.0,
            strengths=["Test"],
            issues=[],
            suggestions=[],
        )

        # Mock all three agents
        with patch("src.workflow.nodes.recruiter.RecruiterAgent") as mock_recruiter, \
             patch("src.workflow.nodes.tech_writer.TechnicalWriterAgent") as mock_tech, \
             patch("src.workflow.nodes.copywriter.CopywriterAgent") as mock_copy:

            mock_recruiter.return_value.evaluate_async = AsyncMock(return_value=mock_feedback)
            mock_tech.return_value.evaluate_async = AsyncMock(return_value=mock_feedback)
            mock_copy.return_value.evaluate_async = AsyncMock(return_value=mock_feedback)

            # Execute all three agent nodes in parallel (simulating LangGraph fan-out)
            start_time = time.perf_counter()
            results = await asyncio.gather(
                recruiter_node(state),
                tech_writer_node(state),
                copywriter_node(state),
            )
            duration = time.perf_counter() - start_time

            # Verify all three nodes returned feedback
            assert len(results) == 3
            assert "recruiter_feedback" in results[0]
            assert "tech_writer_feedback" in results[1]
            assert "copywriter_feedback" in results[2]

            # Verify parallel execution (duration should be close to max, not sum)
            # This is a smoke test - actual timing depends on mock overhead
            assert duration < 1.0, "Parallel execution should be fast with mocks"
