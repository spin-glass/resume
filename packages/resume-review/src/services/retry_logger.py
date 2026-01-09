"""Retry log file management for validation attempts."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models.validation import RetryAttempt, ValidationResult

logger = logging.getLogger("resume_review")


class RetryLogger:
    """Manage retry log files for validation attempts."""

    def __init__(self, session_dir: Path, iteration: int):
        """
        Initialize retry logger for a specific iteration.

        Args:
            session_dir: Session directory where logs will be saved
            iteration: Current iteration number (used in log filename)
        """
        self.session_dir = session_dir
        self.iteration = iteration
        self.log_path = session_dir / f"iter{iteration}_validation_retry.md"
        self._log_created = False

    def log_initial_validation(self, result: ValidationResult) -> None:
        """
        Log the initial validation result before retries.

        Args:
            result: Result from first validation attempt
        """
        try:
            self._ensure_log_file()

            status = "PASSED" if result.is_valid else "FAILED"
            error_text = result.error_message or "None"
            action = "Proceeding to next iteration" if result.is_valid else "Creating fix feedback"

            content = f"""# Iteration {self.iteration} - Validation Retry Log

## Initial Validation ({status})
- Timestamp: {result.timestamp.isoformat()}
- Error: {error_text}
- Action: {action}

"""
            self._append_to_log(content)
            logger.debug(f"Logged initial validation for iteration {self.iteration}")

        except Exception as e:
            logger.warning(f"Failed to log initial validation: {e}")

    def log_retry_attempt(self, retry: RetryAttempt) -> None:
        """
        Log a single retry attempt.

        Args:
            retry: Record of retry attempt with corrections and result
        """
        try:
            self._ensure_log_file()

            status = "PASSED" if retry.validation_result.is_valid else "FAILED"
            error_text = retry.validation_result.error_message or "None"

            if retry.validation_result.is_valid:
                action = "Validation passed ✅"
            elif retry.attempt_number >= 3:  # Assuming max_retries default
                action = "Max retries exhausted"
            else:
                action = "Creating fix feedback"

            content = f"""## Retry {retry.attempt_number}
- Timestamp: {retry.timestamp.isoformat()}
- Fix Applied: {retry.correction_applied}
- Validation Result: {status}
- Error: {error_text}
- Action: {action}

"""
            self._append_to_log(content)
            logger.debug(f"Logged retry attempt {retry.attempt_number} for iteration {self.iteration}")

        except Exception as e:
            logger.warning(f"Failed to log retry attempt: {e}")

    def finalize_log(self, success: bool, total_retries: int, final_file: Path) -> None:
        """
        Write summary section and close log.

        Args:
            success: Whether validation ultimately succeeded
            total_retries: Total number of retry attempts made
            final_file: Path to final QMD file (successful or last attempt)
        """
        try:
            self._ensure_log_file()

            status_emoji = "SUCCESS ✅" if success else "FAILED ❌"

            content = f"""## Summary
- Total Retries: {total_retries}
- Final Status: {status_emoji}
- Final File: {final_file.name if final_file else 'N/A'}
"""
            self._append_to_log(content)
            logger.info(f"Finalized retry log for iteration {self.iteration} ({status_emoji})")

        except Exception as e:
            logger.warning(f"Failed to finalize retry log: {e}")

    def get_log_path(self) -> Path:
        """
        Get the path to the retry log file.

        Returns:
            Absolute path to log file
        """
        return self.log_path

    def _ensure_log_file(self) -> None:
        """Create log file and parent directories if they don't exist."""
        if not self._log_created:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.log_path.exists():
                self.log_path.touch()
            self._log_created = True

    def _append_to_log(self, content: str) -> None:
        """
        Append markdown content to log file.

        Args:
            content: Markdown content to append
        """
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(content)
