"""Integration tests for dry-run mode (T047)."""

import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models import ActionType, SessionStatus, Severity
from src.models.feedback import Feedback, Issue, Resume
from src.models.session import ReviewSession
from src.models.portfolio import PortfolioItem
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
def mock_feedback():
    """Create mock feedback for testing."""
    return Feedback(
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


def create_mock_final_state(session: ReviewSession, feedback: Feedback) -> dict:
    """Create a mock final state that the workflow would return."""
    return {
        "resume": session.resume,
        "resume_content": session.resume.content,
        "target_role": session.target_role,
        "score_threshold": session.score_threshold,
        "max_iterations": session.max_iterations,
        "dry_run": session.dry_run,
        "current_iteration": 1,
        "feedback_history": [[feedback]],  # List of iterations, each with list of feedbacks
        "current_feedback": [feedback],
        "integrated_score": 7.5,
        "final_score": 7.5,
        "threshold_met": False,
        "skill_gaps": ["LLM experience"],
        "portfolio_suggestions": [
            PortfolioItem(
                repository_name="llm-project",
                skills=["LLM", "Python"],
                description="End-to-end LLM application",
                github_url="https://github.com/user/llm-project",
                priority=1
            )
        ],
        "revised_content": "",
        "applied_revisions": ["[DRY RUN] Would add metrics to achievements"],
        "token_usage": {},
        "should_continue": False,
        "error": None,
        "validation_retry_count": 0,
        "current_retry_attempts": [],
    }


@pytest.mark.integration
def test_dry_run_does_not_modify_file(temp_resume, mock_feedback):
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
        score_threshold=9.0,
        max_iterations=1,
        dry_run=True,
    )

    # Create mock final state
    mock_state = create_mock_final_state(session, mock_feedback)

    # Mock the async workflow execution to return our mock state
    with patch.object(ReviewWorkflow, '_run_workflow_async', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_state

        workflow = ReviewWorkflow(api_key="test-key")
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
def test_dry_run_preserves_yaml_frontmatter(temp_resume, mock_feedback):
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

    # Create mock final state
    mock_state = create_mock_final_state(session, mock_feedback)

    with patch.object(ReviewWorkflow, '_run_workflow_async', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_state

        workflow = ReviewWorkflow(api_key="test-key")
        result_session = workflow.run_review(session)

    # Verify YAML frontmatter is unchanged in session
    assert result_session.resume.yaml_frontmatter == original_yaml


@pytest.mark.integration
def test_dry_run_logs_proposed_changes(temp_resume, mock_feedback):
    """
    Test that dry-run mode logs what changes would be made.
    """
    # Load resume
    parser = QMDParser()
    resume = parser.load_resume(temp_resume)

    # Create session with dry-run
    session = ReviewSession(
        resume=resume,
        target_role="LLM/Multi-Agent Engineer",
        score_threshold=9.0,
        max_iterations=2,
        dry_run=True,
    )

    # Create mock final state with multiple revisions
    mock_state = create_mock_final_state(session, mock_feedback)
    mock_state["applied_revisions"] = [
        "[DRY RUN] Would add metrics to experience section",
        "[DRY RUN] Would quantify project impact",
    ]

    with patch.object(ReviewWorkflow, '_run_workflow_async', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_state

        workflow = ReviewWorkflow(api_key="test-key")
        result_session = workflow.run_review(session)

    # Verify revisions are logged
    assert len(result_session.applied_revisions) == 2
    for revision in result_session.applied_revisions:
        assert "[DRY RUN]" in revision or "Would" in revision


@pytest.mark.integration
def test_dry_run_vs_normal_mode_session_directory(temp_resume, mock_feedback, tmp_path):
    """
    Test that dry-run mode does not create session directory when save_iterations is True.
    """
    parser = QMDParser()
    resume = parser.load_resume(temp_resume)

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create session with dry-run
    session = ReviewSession(
        resume=resume,
        target_role="LLM/Multi-Agent Engineer",
        score_threshold=9.0,
        max_iterations=1,
        dry_run=True,
    )

    mock_state = create_mock_final_state(session, mock_feedback)

    with patch.object(ReviewWorkflow, '_run_workflow_async', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_state

        # save_iterations=True but dry_run=True should NOT create session directory
        workflow = ReviewWorkflow(
            api_key="test-key",
            save_iterations=True,
            output_dir=output_dir
        )
        workflow.run_review(session)

    # In dry_run mode, no session directory should be created
    # (The actual logic in runner.py line 67-70 skips session directory creation for dry_run)
    session_dirs = list(output_dir.glob("review_*"))
    assert len(session_dirs) == 0, "No session directory should be created in dry-run mode"


@pytest.mark.integration
def test_dry_run_status_completed_on_success(temp_resume, mock_feedback):
    """
    Test that session status is COMPLETED even in dry-run mode.
    """
    parser = QMDParser()
    resume = parser.load_resume(temp_resume)

    session = ReviewSession(
        resume=resume,
        target_role="LLM/Multi-Agent Engineer",
        score_threshold=9.0,
        max_iterations=1,
        dry_run=True,
    )

    mock_state = create_mock_final_state(session, mock_feedback)

    with patch.object(ReviewWorkflow, '_run_workflow_async', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_state

        workflow = ReviewWorkflow(api_key="test-key")
        result_session = workflow.run_review(session)

    assert result_session.status == SessionStatus.COMPLETED


@pytest.mark.integration
def test_dry_run_handles_workflow_error_gracefully(temp_resume):
    """
    Test that workflow errors are handled gracefully in dry-run mode.
    """
    parser = QMDParser()
    resume = parser.load_resume(temp_resume)

    session = ReviewSession(
        resume=resume,
        target_role="LLM/Multi-Agent Engineer",
        score_threshold=9.0,
        max_iterations=1,
        dry_run=True,
    )

    with patch.object(ReviewWorkflow, '_run_workflow_async', new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = Exception("Simulated workflow error")

        workflow = ReviewWorkflow(api_key="test-key")
        result_session = workflow.run_review(session)

    # Session should be marked as FAILED
    assert result_session.status == SessionStatus.FAILED
