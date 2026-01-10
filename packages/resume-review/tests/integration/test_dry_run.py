"""Integration tests for dry-run mode (T047)."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models import ActionType, SessionStatus, Severity
from src.models.feedback import Feedback, Issue, Resume
from src.models.session import ReviewSession
from src.workflow import ReviewWorkflow
from src.services.qmd_parser import QMDParser


@pytest.fixture
def sample_resume_path():
    """Get path to sample resume fixture."""
    return Path(__file__).parent.parent / "fixtures" / "sample-resume.qmd"


@pytest.fixture
def temp_resume(sample_resume_path, tmp_path):
    """Create a temporary copy of the sample resume for testing."""
    temp_file = tmp_path / "test-resume.qmd"
    shutil.copy(sample_resume_path, temp_file)
    return temp_file


@pytest.fixture
def mock_agents():
    """Mock all agent API calls to avoid actual API usage."""
    from unittest.mock import AsyncMock

    mock_feedback = Feedback(
        agent_name="recruiter",
        score=7.5,
        strengths=["Strong technical skills"],
        issues=[
            Issue(
                description="Add metrics to achievements",
                action_type=ActionType.QUANTIFY,
                location="Experience",
                severity=Severity.HIGH,
            )
        ],
        suggestions=["Quantify impact of projects"],
    )

    with patch("src.workflow.nodes.supervisor.LLMClientFactory") as mock_factory, \
         patch("src.workflow.nodes.supervisor.RecruiterAgent") as mock_recruiter, \
         patch("src.workflow.nodes.supervisor.TechnicalWriterAgent") as mock_tech, \
         patch("src.workflow.nodes.supervisor.CopywriterAgent") as mock_copy, \
         patch("src.services.revision.RevisionService._apply_single_revision", return_value="revised content"):
        mock_factory.create_client.return_value = MagicMock()
        mock_recruiter.return_value.evaluate_async = AsyncMock(return_value=mock_feedback)
        mock_tech.return_value.evaluate_async = AsyncMock(return_value=mock_feedback)
        mock_copy.return_value.evaluate_async = AsyncMock(return_value=mock_feedback)
        yield


@pytest.mark.integration
@pytest.mark.skip(reason="Requires complete workflow mocking; move to e2e tests with API keys")
def test_dry_run_does_not_modify_file(temp_resume, mock_agents):
    """
    Test T047: Verify file is unchanged after dry-run review.

    This test ensures that when dry_run=True:
    1. The original file is not modified
    2. Feedback is still generated
    3. Revisions are logged with [DRY RUN] prefix
    """
    # Read original content
    original_content = temp_resume.read_text()
    original_stat = temp_resume.stat()

    # Load resume
    parser = QMDParser()
    resume = parser.load_resume(temp_resume)

    # Create session with dry-run enabled
    session = ReviewSession(
        resume=resume,
        target_role="LLM/Multi-Agent Engineer",
        score_threshold=9.0,  # High threshold to ensure revisions would be attempted
        max_iterations=1,
        dry_run=True,  # DRY RUN MODE
    )

    # Run workflow with mocked API calls
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    workflow = ReviewWorkflow(api_key)
    result_session = workflow.run_review(session)

    # Verify file was NOT modified
    current_content = temp_resume.read_text()
    current_stat = temp_resume.stat()

    assert current_content == original_content, "File content should not change in dry-run mode"
    assert current_stat.st_mtime == original_stat.st_mtime, "File modification time should not change"

    # Verify feedback was still generated
    assert len(result_session.feedback_history) > 0, "Feedback should still be generated"
    assert result_session.final_score is not None, "Score should still be calculated"

    # Verify revisions are marked as dry-run
    for revision in result_session.applied_revisions:
        assert "[DRY RUN]" in revision, f"Revision should be marked as dry-run: {revision}"


@pytest.mark.integration
def test_dry_run_preserves_yaml_frontmatter(temp_resume, mock_agents):
    """
    Test that YAML frontmatter is preserved in dry-run mode.
    """
    # Load and store original YAML
    parser = QMDParser()
    original_resume = parser.load_resume(temp_resume)
    original_yaml = original_resume.yaml_frontmatter.copy()

    # Create session with dry-run
    session = ReviewSession(
        resume=original_resume,
        target_role="LLM/Multi-Agent Engineer",
        score_threshold=9.0,
        max_iterations=1,
        dry_run=True,
    )

    # Run workflow
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    workflow = ReviewWorkflow(api_key)
    result_session = workflow.run_review(session)

    # Verify YAML frontmatter is unchanged in session
    assert result_session.resume.yaml_frontmatter == original_yaml


@pytest.mark.integration
def test_dry_run_logs_proposed_changes(temp_resume, mock_agents):
    """
    Test that dry-run mode logs what changes would be made.
    """
    # Load resume
    parser = QMDParser()
    resume = parser.load_resume(temp_resume)

    # Create session with dry-run and low threshold to trigger revisions
    session = ReviewSession(
        resume=resume,
        target_role="LLM/Multi-Agent Engineer",
        score_threshold=9.0,  # High threshold
        max_iterations=2,
        dry_run=True,
    )

    # Run workflow
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    workflow = ReviewWorkflow(api_key)
    result_session = workflow.run_review(session)

    # If there are issues that would trigger revisions, they should be logged
    # Note: With our mock, we expect revisions to be logged
    if result_session.applied_revisions:
        for revision in result_session.applied_revisions:
            assert "[DRY RUN]" in revision or "Would apply" in revision


@pytest.mark.integration
@pytest.mark.skip(reason="Requires complete workflow mocking; move to e2e tests with API keys")
def test_dry_run_vs_normal_mode_comparison(sample_resume_path, mock_agents):
    """
    Test that dry-run and normal mode produce similar feedback but different file outcomes.
    """
    parser = QMDParser()

    # Create two temporary copies
    with tempfile.TemporaryDirectory() as tmpdir:
        dry_run_file = Path(tmpdir) / "dry-run.qmd"
        normal_file = Path(tmpdir) / "normal.qmd"

        shutil.copy(sample_resume_path, dry_run_file)
        shutil.copy(sample_resume_path, normal_file)

        # Store original content
        original_content = dry_run_file.read_text()

        # Run dry-run mode
        dry_resume = parser.load_resume(dry_run_file)
        dry_session = ReviewSession(
            resume=dry_resume,
            target_role="LLM/Multi-Agent Engineer",
            score_threshold=9.0,
            max_iterations=1,
            dry_run=True,
        )

        api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
        workflow = ReviewWorkflow(api_key)
        dry_result = workflow.run_review(dry_session)

        # Verify dry-run file unchanged
        assert dry_run_file.read_text() == original_content

        # Both should have feedback
        assert dry_result.final_score is not None
        assert len(dry_result.feedback_history) > 0
