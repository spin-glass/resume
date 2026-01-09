"""Integration tests for validation retry edge cases (T044-T050)."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import shutil

from src.workflow.runner import ReviewWorkflow
from src.models.session import ReviewSession
from src.models.feedback import Resume


@pytest.fixture
def temp_session_dir():
    """Create a temporary session directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_quarto_timeout_handled_as_validation_failure():
    """T044: Handle Quarto validation timeout (>30s) as validation failure."""
    workflow = ReviewWorkflow(api_key="test-key", save_iterations=False)

    state = {
        "revised_content": "# Test Content",
        "max_validation_retries": 1,
        "strict_validation": False,
        "current_iteration": 1,
    }

    # Mock validator to simulate timeout
    with patch("src.workflow.runner.QuartoValidator") as mock_validator_class:
        mock_validator = MagicMock()
        # First call returns timeout error
        mock_validator.validate.return_value = (False, "Validation timed out after 30 seconds")
        mock_validator.create_validation_feedback.return_value = MagicMock(issues=[])
        mock_validator_class.return_value = mock_validator

        with patch.object(workflow, "_invoke_revisor_for_retry", new_callable=AsyncMock) as mock_revisor:
            mock_revisor.return_value = "# Fixed Content"

            # Should handle timeout gracefully
            await workflow._validate_and_retry(state)

            # Should have attempted to create validation feedback
            assert mock_validator.create_validation_feedback.call_count > 0


@pytest.mark.asyncio
async def test_revisor_introduces_new_validation_errors():
    """T045: Handle case where revisor introduces new validation errors during retry."""
    workflow = ReviewWorkflow(api_key="test-key", save_iterations=False)

    state = {
        "revised_content": "# Original Content",
        "max_validation_retries": 2,
        "strict_validation": False,
        "current_iteration": 1,
    }

    # Mock validator to return different errors
    with patch("src.workflow.runner.QuartoValidator") as mock_validator_class:
        mock_validator = MagicMock()

        # First validation: error A
        # Second validation (after first retry): error B (new error!)
        # Third validation (after second retry): success
        validation_results = [
            (False, "Error A: Invalid heading"),
            (False, "Error B: YAML syntax error"),  # New error introduced
            (True, None),  # Finally succeeds
        ]
        mock_validator.validate.side_effect = validation_results
        mock_validator.create_validation_feedback.return_value = MagicMock(issues=[MagicMock()])
        mock_validator_class.return_value = mock_validator

        with patch.object(workflow, "_invoke_revisor_for_retry", new_callable=AsyncMock) as mock_revisor:
            mock_revisor.return_value = "# Revised Content"

            # Should handle changing errors and eventually succeed
            await workflow._validate_and_retry(state)

            # Should have made 2 retry attempts before success
            assert mock_revisor.call_count == 2


@pytest.mark.asyncio
async def test_retry_artifacts_saved_correctly(temp_session_dir):
    """T046: Verify retry artifacts (iter{N}_retry{M}.qmd files) are saved correctly."""
    workflow = ReviewWorkflow(
        api_key="test-key",
        save_iterations=True,
        output_dir=temp_session_dir,
    )
    workflow.session_dir = temp_session_dir

    state = {
        "revised_content": "# Original Content",
        "max_validation_retries": 2,
        "strict_validation": False,
        "current_iteration": 1,
    }

    # Mock validator to fail twice then succeed
    with patch("src.workflow.runner.QuartoValidator") as mock_validator_class:
        mock_validator = MagicMock()
        validation_results = [
            (False, "Error 1"),
            (False, "Error 2"),
            (True, None),
        ]
        mock_validator.validate.side_effect = validation_results
        mock_validator.create_validation_feedback.return_value = MagicMock(issues=[MagicMock()])
        mock_validator_class.return_value = mock_validator

        with patch.object(workflow, "_invoke_revisor_for_retry", new_callable=AsyncMock) as mock_revisor:
            mock_revisor.return_value = "# Revised Content"

            await workflow._validate_and_retry(state)

            # Check that retry artifacts were created
            retry1_path = temp_session_dir / "iter1_retry1.qmd"
            retry2_path = temp_session_dir / "iter1_retry2.qmd"

            assert retry1_path.exists(), "Retry 1 artifact should exist"
            assert retry2_path.exists(), "Retry 2 artifact should exist"

            # Verify content
            assert retry1_path.read_text() == "# Revised Content"
            assert retry2_path.read_text() == "# Revised Content"


@pytest.mark.asyncio
async def test_retry_count_resets_across_iterations():
    """T047: Verify retry count does not accumulate across iterations."""
    workflow = ReviewWorkflow(api_key="test-key", save_iterations=False)

    # Simulate iteration 1
    state_iter1 = {
        "revised_content": "# Content 1",
        "max_validation_retries": 2,
        "strict_validation": False,
        "current_iteration": 1,
    }

    with patch("src.workflow.runner.QuartoValidator") as mock_validator_class:
        mock_validator = MagicMock()
        # Fail validation to trigger retries
        validation_results_iter1 = [
            (False, "Error"),
            (False, "Error"),
            (False, "Error"),
        ]
        mock_validator.validate.side_effect = validation_results_iter1
        mock_validator.create_validation_feedback.return_value = MagicMock(issues=[MagicMock()])
        mock_validator_class.return_value = mock_validator

        with patch.object(workflow, "_invoke_revisor_for_retry", new_callable=AsyncMock) as mock_revisor:
            mock_revisor.return_value = "# Revised"

            await workflow._validate_and_retry(state_iter1)

            # State should show 2 retries
            assert state_iter1.get("validation_retry_count", 0) == 2

    # Simulate iteration 2 - retry count should reset
    state_iter2 = {
        "revised_content": "# Content 2",
        "max_validation_retries": 2,
        "strict_validation": False,
        "current_iteration": 2,
    }

    with patch("src.workflow.runner.QuartoValidator") as mock_validator_class:
        mock_validator = MagicMock()
        mock_validator.validate.return_value = (True, None)  # Success immediately
        mock_validator_class.return_value = mock_validator

        await workflow._validate_and_retry(state_iter2)

        # State should show 0 retries (reset)
        assert state_iter2.get("validation_retry_count", 0) == 0


@pytest.mark.asyncio
async def test_retry_logger_creates_correct_log_files(temp_session_dir):
    """T048: Verify retry logger creates log files with correct naming."""
    from src.services.retry_logger import RetryLogger
    from src.models.validation import ValidationResult

    logger = RetryLogger(session_dir=temp_session_dir, iteration=2)

    # Log initial validation
    result = ValidationResult(
        is_valid=False,
        error_message="Test error",
        attempt_number=0,
    )
    logger.log_initial_validation(result)

    # Check log file exists
    log_path = temp_session_dir / "iter2_validation_retry.md"
    assert log_path.exists(), "Retry log file should exist"

    # Check content format
    content = log_path.read_text()
    assert "# Iteration 2 - Validation Retry Log" in content
    assert "## Initial Validation" in content
    assert "Test error" in content


@pytest.mark.asyncio
async def test_state_current_retry_attempts_serialization():
    """T049: Verify current_retry_attempts list is properly serialized in state."""
    workflow = ReviewWorkflow(api_key="test-key", save_iterations=False)

    state = {
        "revised_content": "# Test Content",
        "max_validation_retries": 1,
        "strict_validation": False,
        "current_iteration": 1,
    }

    with patch("src.workflow.runner.QuartoValidator") as mock_validator_class:
        mock_validator = MagicMock()
        validation_results = [
            (False, "Error 1"),
            (True, None),
        ]
        mock_validator.validate.side_effect = validation_results
        mock_validator.create_validation_feedback.return_value = MagicMock(issues=[MagicMock()])
        mock_validator_class.return_value = mock_validator

        with patch.object(workflow, "_invoke_revisor_for_retry", new_callable=AsyncMock) as mock_revisor:
            mock_revisor.return_value = "# Revised"

            await workflow._validate_and_retry(state)

            # Check that retry attempts were recorded
            assert "current_retry_attempts" in state
            assert isinstance(state["current_retry_attempts"], list)
            assert len(state["current_retry_attempts"]) == 1

            # Check that retry attempt is serialized as dict
            retry_attempt = state["current_retry_attempts"][0]
            assert isinstance(retry_attempt, dict)
            assert "attempt_number" in retry_attempt
            assert "validation_result" in retry_attempt


@pytest.mark.asyncio
async def test_max_retries_exhausted_with_strict_false_saves_last_attempt():
    """T050: Verify that when max retries exhausted with strict=false, last attempt is saved."""
    workflow = ReviewWorkflow(api_key="test-key", save_iterations=False)

    state = {
        "revised_content": "# Original",
        "max_validation_retries": 1,
        "strict_validation": False,
        "current_iteration": 1,
    }

    with patch("src.workflow.runner.QuartoValidator") as mock_validator_class:
        mock_validator = MagicMock()
        # Always fail validation
        mock_validator.validate.return_value = (False, "Persistent error")
        mock_validator.create_validation_feedback.return_value = MagicMock(issues=[MagicMock()])
        mock_validator_class.return_value = mock_validator

        with patch.object(workflow, "_invoke_revisor_for_retry", new_callable=AsyncMock) as mock_revisor:
            mock_revisor.return_value = "# Last Attempt"

            # Should not raise error
            await workflow._validate_and_retry(state)

            # Content should be updated to last attempt
            assert state["revised_content"] == "# Last Attempt"
            # Retry count should equal max
            assert state.get("validation_retry_count", 0) == 1
