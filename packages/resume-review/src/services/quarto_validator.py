"""Quarto validation service for checking QMD file syntax."""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from ..models import ActionType, Severity
from ..models.feedback import Feedback, Issue

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

    def create_validation_feedback(self, error_message: str) -> Feedback:
        """
        Parse Quarto error message and generate structured Feedback for revisor.

        Args:
            error_message: Error message from Quarto validation

        Returns:
            Feedback object with Issues parsed from error patterns
        """
        issues = []
        error_lower = error_message.lower()

        # Pattern 1: Standalone # markers (T012)
        if "invalid heading" in error_lower or "unexpected #" in error_lower:
            issues.append(Issue(
                description="単独の # 記号が検出されました。セクション区切りとして不適切です。",
                severity=Severity.CRITICAL,
                action_type=ActionType.REMOVE,
                location=None  # Global fix
            ))

        # Pattern 2: YAML syntax errors (T013)
        if "yaml" in error_lower or "frontmatter" in error_lower:
            issues.append(Issue(
                description="YAMLフロントマターに構文エラーがあります。",
                severity=Severity.CRITICAL,
                action_type=ActionType.RESTRUCTURE,
                location="## YAML Header"
            ))

        # Pattern 3: Unclosed code blocks (T014)
        if "code block" in error_lower or "```" in error_message:
            issues.append(Issue(
                description="コードブロックが正しく閉じられていません。",
                severity=Severity.HIGH,
                action_type=ActionType.RESTRUCTURE,
                location=None
            ))

        # Pattern 4: Invalid markdown tables (T015)
        if "table" in error_lower or "column" in error_lower:
            issues.append(Issue(
                description="Markdownテーブルの列数が不一致です。",
                severity=Severity.HIGH,
                action_type=ActionType.REMOVE,
                location=None
            ))

        # Pattern 5: Fallback for unknown errors (T016)
        if not issues:
            issues.append(Issue(
                description=f"Quarto検証エラー: {error_message[:200]}",
                severity=Severity.HIGH,
                action_type=ActionType.RESTRUCTURE,
                location=None
            ))

        return Feedback(
            agent_name="quarto_validator",
            score=3.0,  # Low score to trigger revision
            strengths=[],
            issues=issues,
            suggestions=["Quarto構文エラーを修正してください"]
        )
