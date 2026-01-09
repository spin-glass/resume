"""Integration tests for CLI."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.cli import cli
from src.models import SessionStatus
from src.models.feedback import Feedback


@pytest.fixture
def runner():
    """Create Click CLI runner."""
    return CliRunner()


@pytest.fixture
def sample_resume_path():
    """Get path to sample resume fixture."""
    return Path(__file__).parent.parent / "fixtures" / "sample-resume.qmd"


@pytest.fixture
def mock_workflow():
    """Create a mock workflow that doesn't call API."""
    def _create_mock_session(session):
        """Simulate a completed review session."""
        # Create mock feedback
        mock_feedback = Feedback(
            agent_name="recruiter",
            score=8.5,
            strengths=["Strong technical background"],
            issues=[],
            suggestions=["Add more metrics"],
        )

        # Update session state
        session.status = SessionStatus.COMPLETED
        session.final_score = 8.5
        session.add_feedback([mock_feedback])

        if session.dry_run:
            session.add_revision("[DRY RUN] Would apply quantify: Add metrics")

        return session

    with patch("src.cli.ReviewWorkflow") as mock_class:
        mock_instance = MagicMock()
        mock_instance.run_review.side_effect = _create_mock_session
        mock_class.return_value = mock_instance
        yield mock_class


@pytest.mark.integration
def test_cli_basic_review_command(runner, sample_resume_path, mock_workflow):
    """
    Test T056: CLI integration test using Click CliRunner for basic review command.
    """
    result = runner.invoke(
        cli,
        ["review", "--input", str(sample_resume_path), "--dry-run", "--max-iterations", "1"],
        catch_exceptions=False,
    )

    # Should succeed or threshold not met (with mock, should succeed)
    assert result.exit_code in [0, 4]  # Success or threshold not met
    assert mock_workflow.called


@pytest.mark.integration
def test_cli_dry_run_mode(runner, sample_resume_path, mock_workflow):
    """
    Test T057: CLI integration test for dry-run mode.
    """
    result = runner.invoke(
        cli,
        ["review", "--input", str(sample_resume_path), "--dry-run", "--max-iterations", "1"],
        catch_exceptions=False
    )

    # Check output contains DRY RUN indicator
    assert "DRY RUN" in result.output or "dry" in result.output.lower()


@pytest.mark.integration
def test_cli_verbose_mode(runner, sample_resume_path, mock_workflow):
    """
    Test T058: CLI integration test for verbose mode output.
    """
    result = runner.invoke(
        cli,
        [
            "review",
            "--input",
            str(sample_resume_path),
            "--dry-run",
            "--verbose",
            "--max-iterations",
            "1",
        ],
        catch_exceptions=False,
    )

    # Verbose mode should produce more output
    assert len(result.output) > 100  # Should have substantial output


@pytest.mark.integration
def test_cli_error_handling_invalid_file(runner):
    """
    Test T059: CLI integration test for error handling (invalid file).
    """
    result = runner.invoke(cli, ["review", "--input", "/nonexistent/file.qmd"])

    # Should fail with validation error (Click checks file existence before calling function)
    assert result.exit_code == 2
    assert "Error" in result.output or "not found" in result.output.lower() or "does not exist" in result.output.lower()


@pytest.mark.integration
def test_cli_error_handling_invalid_extension(runner, tmp_path):
    """
    Test error handling for non-QMD file.
    """
    # Create a temporary non-QMD file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test content")

    result = runner.invoke(cli, ["review", "--input", str(test_file)])

    # Should fail with validation error
    assert result.exit_code in [1, 2]


@pytest.mark.integration
def test_cli_error_handling_missing_api_key(runner, sample_resume_path, monkeypatch):
    """
    Test T059: CLI integration test for error handling (missing API key).
    """
    # Remove API key from environment and prevent dotenv from reloading it
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    # Clear singleton cache to force reloading config
    from src.utils.config import get_config
    if hasattr(get_config, "_instance"):
        delattr(get_config, "_instance")

    # Mock load_dotenv to prevent it from loading the .env file
    with patch("src.utils.config.load_dotenv", return_value=None):
        result = runner.invoke(cli, ["review", "--input", str(sample_resume_path)])

    # Should fail with config/API error (exit code 3)
    assert result.exit_code == 3
    assert "API" in result.output or "key" in result.output.lower() or "Error" in result.output


@pytest.mark.integration
def test_cli_threshold_validation(runner, sample_resume_path):
    """
    Test threshold validation in CLI.
    """
    # Invalid threshold (too high)
    result = runner.invoke(
        cli, ["review", "--input", str(sample_resume_path), "--threshold", "11.0"]
    )

    assert result.exit_code == 2
    assert "threshold" in result.output.lower() or "error" in result.output.lower()


@pytest.mark.integration
def test_cli_max_iterations_validation(runner, sample_resume_path):
    """
    Test max iterations validation in CLI.
    """
    # Invalid max iterations (zero)
    result = runner.invoke(
        cli, ["review", "--input", str(sample_resume_path), "--max-iterations", "0"]
    )

    assert result.exit_code == 2
    assert "iteration" in result.output.lower() or "error" in result.output.lower()


@pytest.mark.integration
def test_cli_version_command(runner):
    """
    Test version command.
    """
    result = runner.invoke(cli, ["version"])

    assert result.exit_code == 0
    assert "0.1.0" in result.output
    assert "Claude" in result.output


@pytest.mark.integration
def test_cli_help(runner):
    """
    Test help command.
    """
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "review" in result.output.lower()


@pytest.mark.integration
def test_cli_review_help(runner):
    """
    Test review command help.
    """
    result = runner.invoke(cli, ["review", "--help"])

    assert result.exit_code == 0
    assert "--input" in result.output
    assert "--dry-run" in result.output
    assert "--verbose" in result.output
