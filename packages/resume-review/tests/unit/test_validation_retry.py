"""Unit tests for validation retry configuration (T039-T042)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from src.workflow.runner import ReviewWorkflow
from src.models.session import ReviewSession
from src.models.feedback import Resume


@pytest.fixture
def mock_session():
    """Create a mock review session for testing."""
    return ReviewSession(
        resume=Resume(
            file_path=Path("test_resume.qmd"),
            yaml_frontmatter={},
            content="# Test Resume",
            full_text="# Test Resume",
        ),
        target_role="Test Engineer",
        score_threshold=8.0,
        max_iterations=1,
        dry_run=False,
        max_validation_retries=3,
        strict_validation=False,
    )


@pytest.fixture
def mock_workflow():
    """Create a workflow instance with mocked dependencies."""
    workflow = ReviewWorkflow(
        api_key="test-key",
        save_iterations=True,
        output_dir=None,
    )
    return workflow


@pytest.mark.asyncio
async def test_max_validation_retries_zero_skips_retry_loop(mock_session):
    """T039: Test that max_validation_retries=0 skips retry loop entirely."""
    mock_session.max_validation_retries = 0

    workflow = ReviewWorkflow(api_key="test-key", save_iterations=False)

    # Mock state with revised content
    state = {
        "revised_content": "# Test Content",
        "max_validation_retries": 0,
        "strict_validation": False,
        "current_iteration": 1,
    }

    # Mock validator to always fail
    with patch("src.services.quarto_validator.QuartoValidator") as mock_validator_class:
        mock_validator = MagicMock()
        mock_validator.validate.return_value = (False, "Validation error")
        mock_validator_class.return_value = mock_validator

        # Should not raise error and not retry
        await workflow._validate_and_retry(state)

        # Validator should be called exactly once (initial validation, no retries)
        assert mock_validator.validate.call_count == 1
        assert state.get("validation_retry_count", 0) == 0


@pytest.mark.asyncio
async def test_custom_max_validation_retries_respected(mock_session):
    """T040: Test that custom max_validation_retries value is respected."""
    mock_session.max_validation_retries = 2

    workflow = ReviewWorkflow(api_key="test-key", save_iterations=False)

    state = {
        "revised_content": "# Test Content",
        "max_validation_retries": 2,
        "strict_validation": False,
        "current_iteration": 1,
    }

    # Mock validator to always fail
    with patch("src.services.quarto_validator.QuartoValidator") as mock_validator_class:
        mock_validator = MagicMock()
        mock_validator.validate.return_value = (False, "Validation error")
        mock_validator.create_validation_feedback.return_value = MagicMock(issues=[])
        mock_validator_class.return_value = mock_validator

        # Mock revisor to return same content
        with patch.object(workflow, "_invoke_revisor_for_retry", new_callable=AsyncMock) as mock_revisor:
            mock_revisor.return_value = "# Test Content"

            # Should stop after 2 retries
            await workflow._validate_and_retry(state)

            # Initial validation + 2 retries + 2 post-fix validations = 5 calls
            # (initial, retry1_validate_post_fix, retry2_validate_post_fix)
            assert mock_validator.validate.call_count <= 5
            assert state.get("validation_retry_count", 0) <= 2


@pytest.mark.asyncio
async def test_strict_validation_true_raises_on_failure(mock_session):
    """T041: Test that strict_validation=True causes workflow to exit on validation failure."""
    mock_session.strict_validation = True

    workflow = ReviewWorkflow(api_key="test-key", save_iterations=False)

    state = {
        "revised_content": "# Test Content",
        "max_validation_retries": 1,
        "strict_validation": True,
        "current_iteration": 1,
    }

    # Mock validator to always fail
    with patch("src.services.quarto_validator.QuartoValidator") as mock_validator_class:
        mock_validator = MagicMock()
        mock_validator.validate.return_value = (False, "Validation error")
        mock_validator.create_validation_feedback.return_value = MagicMock(issues=[])
        mock_validator_class.return_value = mock_validator

        # Mock revisor to return same content
        with patch.object(workflow, "_invoke_revisor_for_retry", new_callable=AsyncMock) as mock_revisor:
            mock_revisor.return_value = "# Test Content"

            # Should raise ValueError after exhausting retries
            with pytest.raises(ValueError, match="Validation failed after .* retries"):
                await workflow._validate_and_retry(state)


@pytest.mark.asyncio
async def test_strict_validation_false_continues_on_failure(mock_session):
    """T042: Test that strict_validation=False allows workflow to continue with warning."""
    mock_session.strict_validation = False

    workflow = ReviewWorkflow(api_key="test-key", save_iterations=False)

    state = {
        "revised_content": "# Test Content",
        "max_validation_retries": 1,
        "strict_validation": False,
        "current_iteration": 1,
    }

    # Mock validator to always fail
    with patch("src.services.quarto_validator.QuartoValidator") as mock_validator_class:
        mock_validator = MagicMock()
        mock_validator.validate.return_value = (False, "Validation error")
        mock_validator.create_validation_feedback.return_value = MagicMock(issues=[])
        mock_validator_class.return_value = mock_validator

        # Mock revisor to return same content
        with patch.object(workflow, "_invoke_revisor_for_retry", new_callable=AsyncMock) as mock_revisor:
            mock_revisor.return_value = "# Test Content"

            # Should NOT raise error, just log warning and continue
            await workflow._validate_and_retry(state)

            # Validation should have been attempted
            assert mock_validator.validate.call_count > 0


@pytest.mark.asyncio
async def test_validation_success_stops_retry_loop():
    """Test that validation success stops retry loop immediately."""
    workflow = ReviewWorkflow(api_key="test-key", save_iterations=False)

    state = {
        "revised_content": "# Test Content",
        "max_validation_retries": 3,
        "strict_validation": False,
        "current_iteration": 1,
    }

    # Mock validator to succeed on first attempt
    with patch("src.services.quarto_validator.QuartoValidator") as mock_validator_class:
        mock_validator = MagicMock()
        mock_validator.validate.return_value = (True, None)
        mock_validator_class.return_value = mock_validator

        await workflow._validate_and_retry(state)

        # Should only validate once
        assert mock_validator.validate.call_count == 1
        assert state.get("validation_retry_count", 0) == 0
