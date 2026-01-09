"""QMD file I/O service with YAML frontmatter preservation."""

import shutil
from pathlib import Path
from typing import Optional

import frontmatter

from ..models.feedback import Resume


class QMDParser:
    """Service for reading and writing QMD files with YAML frontmatter preservation."""

    @staticmethod
    def load_resume(file_path: Path) -> Resume:
        """
        Load resume from QMD file.

        Args:
            file_path: Path to QMD file

        Returns:
            Resume entity with parsed content

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If YAML frontmatter is invalid
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")

        # Read file with frontmatter library
        with open(file_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        # Get original full text for backup
        with open(file_path, "r", encoding="utf-8") as f:
            full_text = f.read()

        return Resume(
            file_path=file_path,
            yaml_frontmatter=post.metadata,
            content=post.content,
            full_text=full_text,
        )

    @staticmethod
    def save_resume(
        resume: Resume, output_path: Optional[Path] = None, create_backup: bool = True
    ) -> None:
        """
        Save resume to QMD file with YAML frontmatter preservation.

        Args:
            resume: Resume entity to save
            output_path: Optional output path (defaults to resume.file_path)
            create_backup: Whether to create .bak backup file (FR-009)

        Raises:
            ValueError: If YAML validation fails
        """
        target_path = output_path or resume.file_path

        # Create backup if requested and file exists (FR-009)
        if create_backup and target_path.exists():
            backup_path = target_path.with_suffix(target_path.suffix + ".bak")
            shutil.copy2(target_path, backup_path)

        # Pre-save validation (FR-009)
        try:
            # Reconstruct frontmatter with preserved metadata
            post = frontmatter.Post(resume.content, **resume.yaml_frontmatter)

            # Validate by attempting to dump
            output = frontmatter.dumps(post)

            # Additional size check
            if len(output) < 10:
                raise ValueError("Generated QMD content is suspiciously short")

            # Write to file
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(output)

        except Exception as e:
            # If backup exists, restore it
            if create_backup and target_path.with_suffix(target_path.suffix + ".bak").exists():
                backup_path = target_path.with_suffix(target_path.suffix + ".bak")
                shutil.copy2(backup_path, target_path)
            raise ValueError(f"Failed to save resume: {e}") from e

    @staticmethod
    def validate_yaml_integrity(original: Resume, modified: Resume) -> bool:
        """
        Validate that YAML frontmatter keys are preserved.

        Args:
            original: Original resume
            modified: Modified resume

        Returns:
            True if YAML keys match, False otherwise
        """
        original_keys = set(original.yaml_frontmatter.keys())
        modified_keys = set(modified.yaml_frontmatter.keys())
        return original_keys == modified_keys
