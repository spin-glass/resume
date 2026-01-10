"""CSS file operations service for design auto-fix feature.

This service handles CSS validation, backup creation, and atomic file writing
to ensure safe application of CSS modifications.
"""

import logging
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import cssutils

from ..config.settings import BACKUP_DIRECTORY
from ..models.design import CSSModification

logger = logging.getLogger(__name__)

# Suppress cssutils logging
cssutils.log.setLevel(logging.CRITICAL)


class CSSService:
    """Service for safe CSS file operations with validation and backup."""

    def __init__(self, backup_dir: str = BACKUP_DIRECTORY):
        """Initialize CSS service.

        Args:
            backup_dir: Directory for backup files (default: from settings)
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def validate_css(self, css_content: str) -> tuple[bool, list[str]]:
        """Validate CSS content using cssutils parser.

        Args:
            css_content: CSS string to validate

        Returns:
            Tuple of (passed, errors) where passed is True if valid,
            and errors is list of validation error messages
        """
        errors = []

        try:
            # Parse CSS using cssutils
            sheet = cssutils.parseString(css_content)

            # Check for parsing errors
            if sheet.cssRules is None:
                errors.append("CSS parsing failed - no rules found")
                return False, errors

            # Check for forbidden @media print properties
            # (all styles must work in both screen and print)
            for rule in sheet:
                if hasattr(rule, "type") and rule.type == rule.MEDIA_RULE:
                    media_text = rule.media.mediaText
                    if "print" in media_text:
                        errors.append(
                            f"@media print is forbidden - use styles that work "
                            f"in both screen and print: {media_text}"
                        )

            # Additional validation: check for common syntax errors
            raw_css = sheet.cssText
            css_text = raw_css.decode("utf-8") if isinstance(raw_css, bytes) else raw_css

            if "undefined" in css_text.lower():
                errors.append("CSS contains 'undefined' value")

            return len(errors) == 0, errors

        except Exception as e:
            errors.append(f"CSS validation error: {str(e)}")
            return False, errors

    def create_backup(self, file_path: Path) -> Path:
        """Create timestamped backup of existing file.

        Args:
            file_path: Path to file to backup

        Returns:
            Path to backup file

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Cannot backup non-existent file: {file_path}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")

        return backup_path

    def write_with_backup(
        self, css_content: str, target_file: Path
    ) -> tuple[Path | None, CSSModification]:
        """Write CSS to file with validation and backup.

        This method follows atomic write pattern:
        1. Create backup of existing file (if exists)
        2. Write to temporary file
        3. Validate CSS
        4. Atomic rename to target location

        Args:
            css_content: CSS content to write
            target_file: Target file path

        Returns:
            Tuple of (backup_path, css_modification) where backup_path is Path to backup
            (or None if no backup created), and css_modification is the CSSModification
            model with validation results
        """
        # Ensure parent directory exists
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # Create backup if file exists
        backup_path = None
        if target_file.exists():
            try:
                backup_path = self.create_backup(target_file)
            except Exception as e:
                logger.error(f"Backup creation failed: {e}")
                return None, CSSModification(
                    css_content=css_content,
                    target_file=target_file,
                    validation_passed=False,
                    validation_errors=[f"Backup failed: {str(e)}"],
                )

        # Validate CSS
        passed, errors = self.validate_css(css_content)

        if not passed:
            logger.warning(f"CSS validation failed: {errors}")
            return backup_path, CSSModification(
                css_content=css_content,
                target_file=target_file,
                validation_passed=False,
                validation_errors=errors,
                backup_path=backup_path,
            )

        # Write to temporary file
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".css",
                dir=target_file.parent,
                delete=False,
                encoding="utf-8",
            ) as temp_file:
                temp_file.write(css_content)
                temp_path = Path(temp_file.name)

            # Atomic rename
            temp_path.replace(target_file)
            logger.info(f"CSS written successfully: {target_file}")

            return backup_path, CSSModification(
                css_content=css_content,
                target_file=target_file,
                validation_passed=True,
                backup_path=backup_path,
            )

        except Exception as e:
            logger.error(f"File write failed: {e}")
            # Rollback: restore from backup if exists
            if backup_path and backup_path.exists():
                try:
                    shutil.copy2(backup_path, target_file)
                    logger.info(f"Rolled back from backup: {backup_path}")
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")

            return backup_path, CSSModification(
                css_content=css_content,
                target_file=target_file,
                validation_passed=False,
                validation_errors=[f"File write failed: {str(e)}"],
                backup_path=backup_path,
            )

    def rollback(self, backup_path: Path, target_file: Path) -> bool:
        """Rollback to backup file.

        Args:
            backup_path: Path to backup file
            target_file: Target file to restore to

        Returns:
            True if rollback successful, False otherwise
        """
        try:
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False

            shutil.copy2(backup_path, target_file)
            logger.info(f"Rolled back to: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
