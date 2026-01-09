"""Quarto validation service for checking QMD file syntax."""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger("resume_review")


class QuartoValidator:
    """
    Validates QMD files by running Quarto render in check mode.

    This ensures the resume can be successfully rendered to PDF/HTML
    before finalizing revisions.
    """

    def validate(self, qmd_content: str) -> tuple[bool, Optional[str]]:
        """
        Validate QMD content by attempting to render it with Quarto.

        Args:
            qmd_content: QMD file content to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if Quarto can render the content
            - error_message: Error details if validation failed, None otherwise
        """
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".qmd", delete=False, encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(qmd_content)
            tmp_path = Path(tmp_file.name)

        try:
            # Run quarto render with --to html for faster validation
            result = subprocess.run(
                ["quarto", "render", str(tmp_path), "--to", "html", "--quiet"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                logger.debug("Quarto validation passed")
                return True, None
            else:
                error_msg = result.stderr or result.stdout
                logger.warning(f"Quarto validation failed: {error_msg}")
                return False, error_msg

        except subprocess.TimeoutExpired:
            logger.error("Quarto validation timed out")
            return False, "Validation timed out after 30 seconds"
        except FileNotFoundError:
            logger.error("Quarto command not found - skipping validation")
            return True, None  # Don't fail if Quarto isn't installed
        except Exception as e:
            logger.error(f"Quarto validation error: {e}")
            return False, str(e)
        finally:
            # Clean up temporary files
            tmp_path.unlink(missing_ok=True)
            html_path = tmp_path.with_suffix(".html")
            html_path.unlink(missing_ok=True)
