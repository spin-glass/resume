"""Section reordering service for QMD content.

This service handles parsing QMD files into sections, reordering them
based on UX feedback, and ensuring 100% content preservation through
hash verification.
"""

import hashlib
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path

from ..models.design import SectionReorder
from ..models.feedback import Feedback

logger = logging.getLogger(__name__)


class SectionReorderService:
    """Service for analyzing and reordering QMD sections.

    Ensures:
    - YAML frontmatter is preserved at the top
    - All section content is preserved (verified by content hash)
    - Nested headings (###) stay within their parent sections
    - Atomic write with backup for safety
    """

    def __init__(self, backup_dir: str | None = None):
        """Initialize section reorder service.

        Args:
            backup_dir: Directory for backups (default: same as QMD file)
        """
        self.backup_dir = Path(backup_dir) if backup_dir else None

    def _parse_sections(self, qmd_content: str) -> list[dict]:
        """Parse QMD content into sections (T051).

        Args:
            qmd_content: Raw QMD file content

        Returns:
            List of dicts with 'heading' and 'content' keys.
            First item may have heading='__yaml__' for frontmatter.
        """
        sections = []

        # Extract YAML frontmatter
        yaml_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', qmd_content, re.DOTALL)
        if yaml_match:
            yaml_content = yaml_match.group(0)
            sections.append({
                "heading": "__yaml__",
                "content": yaml_content
            })
            qmd_content = qmd_content[len(yaml_content):]

        # Split by ## headings (section level)
        # Pattern matches ## at start of line followed by heading text
        section_pattern = r'^(## .+?)(?=^## |\Z)'

        matches = list(re.finditer(section_pattern, qmd_content, re.MULTILINE | re.DOTALL))

        if not matches:
            # No ## sections found, treat entire content as one block
            if qmd_content.strip():
                sections.append({
                    "heading": "__content__",
                    "content": qmd_content
                })
            return sections

        # Check for content before first section
        first_match_start = matches[0].start()
        if first_match_start > 0:
            preamble = qmd_content[:first_match_start].strip()
            if preamble:
                sections.append({
                    "heading": "__preamble__",
                    "content": preamble + "\n\n"
                })

        # Extract each section
        for match in matches:
            section_text = match.group(1)
            lines = section_text.strip().split('\n', 1)
            heading_line = lines[0]

            # Extract heading text (remove ## prefix)
            heading = heading_line.replace('## ', '').strip()

            sections.append({
                "heading": heading,
                "content": section_text
            })

        return sections

    def _calculate_content_hash(self, qmd_content: str) -> str:
        """Calculate SHA256 hash of content, ignoring order (T052).

        The hash is calculated on normalized content to ensure
        that reordering doesn't change the hash.

        Args:
            qmd_content: QMD content to hash

        Returns:
            SHA256 hex digest of normalized content
        """
        # Extract all sections
        sections = self._parse_sections(qmd_content)

        # Normalize: sort section contents alphabetically, strip whitespace
        normalized_parts = []

        for section in sections:
            if section["heading"] == "__yaml__":
                # Keep YAML as-is but normalized
                normalized_parts.append(section["content"].strip())
            else:
                # Sort by content to make hash order-independent
                normalized_parts.append(section["content"].strip())

        # Sort normalized parts for order-independent hash
        normalized_parts.sort()

        # Join and hash
        normalized_content = "\n".join(normalized_parts)
        # Remove extra whitespace for consistency
        normalized_content = re.sub(r'\s+', ' ', normalized_content).strip()

        return hashlib.sha256(normalized_content.encode('utf-8')).hexdigest()

    def _reorder_sections(self, qmd_content: str, new_order: list[str]) -> str:
        """Reorder sections according to new_order (T053).

        Args:
            qmd_content: Original QMD content
            new_order: List of section headings in desired order

        Returns:
            QMD content with sections reordered
        """
        sections = self._parse_sections(qmd_content)

        # Separate YAML and other special sections
        yaml_section = None
        preamble_section = None
        content_sections = []

        for section in sections:
            if section["heading"] == "__yaml__":
                yaml_section = section
            elif section["heading"] == "__preamble__":
                preamble_section = section
            elif section["heading"] == "__content__":
                content_sections.append(section)
            else:
                content_sections.append(section)

        # Create mapping of heading to section
        section_map = {s["heading"]: s for s in content_sections}

        # Reorder
        reordered_sections = []
        for heading in new_order:
            if heading in section_map:
                reordered_sections.append(section_map[heading])

        # Add any sections not in new_order at the end
        for section in content_sections:
            if section["heading"] not in new_order:
                reordered_sections.append(section)

        # Reconstruct QMD
        result_parts = []

        if yaml_section:
            result_parts.append(yaml_section["content"])

        if preamble_section:
            result_parts.append(preamble_section["content"])

        for section in reordered_sections:
            result_parts.append(section["content"])

        return "\n".join(result_parts)

    def _reconstruct_qmd(
        self,
        sections: list[dict],
        new_order: list[str],
        original_hash: str
    ) -> str:
        """Reconstruct QMD from sections with hash verification (T053).

        Args:
            sections: Parsed sections
            new_order: Desired section order
            original_hash: Hash before reordering for verification

        Returns:
            Reconstructed QMD content

        Raises:
            ValueError: If content hash doesn't match after reconstruction
        """
        # Build content by combining sections
        yaml_part = ""
        reordered_parts = []

        section_map = {}
        for section in sections:
            if section["heading"] == "__yaml__":
                yaml_part = section["content"]
            else:
                section_map[section["heading"]] = section["content"]

        # Reorder sections
        for heading in new_order:
            if heading in section_map:
                reordered_parts.append(section_map[heading])

        # Combine
        result = yaml_part + "\n".join(reordered_parts)

        # Verify hash
        new_hash = self._calculate_content_hash(result)
        if new_hash != original_hash:
            raise ValueError(
                f"Content hash mismatch after reconstruction. "
                f"Original: {original_hash[:16]}..., New: {new_hash[:16]}..."
            )

        return result

    def analyze_and_recommend(
        self,
        qmd_content: str,
        ux_feedback: list[Feedback],
        target_role: str = ""
    ) -> SectionReorder | None:
        """Analyze UX feedback and recommend section reorder (T054).

        Args:
            qmd_content: Current QMD content
            ux_feedback: List of UX feedback containing order suggestions
            target_role: Target job role for prioritization

        Returns:
            SectionReorder with recommendation, or None if no reorder needed
        """
        # Parse current sections
        sections = self._parse_sections(qmd_content)
        current_order = [
            s["heading"] for s in sections
            if s["heading"] not in ("__yaml__", "__preamble__", "__content__")
        ]

        if not current_order:
            logger.info("No sections found to reorder")
            return None

        # Analyze feedback for order-related keywords
        order_keywords = [
            "reorder", "move", "prioritize", "first", "top", "before", "after",
            "sequence", "order", "position", "prominent", "emphasize early"
        ]

        # Look for order suggestions in feedback
        suggested_changes = []
        for feedback in ux_feedback:
            for issue in feedback.issues:
                desc_lower = issue.description.lower()
                for keyword in order_keywords:
                    if keyword in desc_lower:
                        suggested_changes.append(issue.description)
                        break

        if not suggested_changes:
            logger.info("No section reorder suggestions found in feedback")
            return None

        # Determine optimal order based on feedback and role
        new_order = self._determine_optimal_order(
            current_order, suggested_changes, target_role
        )

        if new_order == current_order:
            logger.info("Optimal order matches current order, no reorder needed")
            return None

        # Calculate content hash
        content_hash = self._calculate_content_hash(qmd_content)

        # Build rationale
        rationale = self._build_rationale(suggested_changes, current_order, new_order)

        return SectionReorder(
            original_order=current_order,
            new_order=new_order,
            rationale=rationale,
            content_hash_before=content_hash,
        )

    def _determine_optimal_order(
        self,
        current_order: list[str],
        feedback_suggestions: list[str],
        target_role: str
    ) -> list[str]:
        """Determine optimal section order based on feedback.

        Args:
            current_order: Current section order
            feedback_suggestions: Order-related feedback
            target_role: Target job role

        Returns:
            Optimal section order
        """
        # Priority mapping for technical roles
        role_priorities = {
            "engineer": ["Skills", "Experience", "Projects", "Summary", "Education"],
            "developer": ["Skills", "Experience", "Projects", "Summary", "Education"],
            "manager": ["Summary", "Experience", "Skills", "Education"],
            "data": ["Skills", "Experience", "Projects", "Education", "Summary"],
            "ml": ["Skills", "Projects", "Experience", "Education", "Summary"],
            "llm": ["Skills", "Projects", "Experience", "Education", "Summary"],
        }

        # Default priority
        default_priority = ["Summary", "Skills", "Experience", "Education"]

        # Find matching role priority
        target_priority = default_priority
        for role_key, priority in role_priorities.items():
            if role_key.lower() in target_role.lower():
                target_priority = priority
                break

        # Check if feedback suggests specific section moves
        for suggestion in feedback_suggestions:
            suggestion_lower = suggestion.lower()

            # Check for specific sections mentioned
            skills_first = "skills" in suggestion_lower
            at_top = "first" in suggestion_lower or "top" in suggestion_lower
            if skills_first and at_top and "Skills" in current_order:
                target_priority = ["Skills"] + [s for s in target_priority if s != "Skills"]

        # Build new order maintaining all sections
        new_order = []
        for section in target_priority:
            if section in current_order:
                new_order.append(section)

        # Add remaining sections not in priority
        for section in current_order:
            if section not in new_order:
                new_order.append(section)

        return new_order

    def _build_rationale(
        self,
        suggestions: list[str],
        old_order: list[str],
        new_order: list[str]
    ) -> str:
        """Build human-readable rationale for reordering."""
        changes = []
        for section in old_order:
            old_idx = old_order.index(section)
            new_idx = new_order.index(section)
            if old_idx != new_idx:
                direction = "up" if new_idx < old_idx else "down"
                changes.append(f"'{section}' moved {direction} ({old_idx+1} → {new_idx+1})")

        rationale_parts = [
            f"Based on {len(suggestions)} UX feedback suggestions:",
            *[f"  - {s[:100]}" for s in suggestions[:3]],
            "",
            "Section changes:",
            *[f"  - {c}" for c in changes],
        ]

        return "\n".join(rationale_parts)

    def reorder_with_backup(
        self,
        qmd_path: Path,
        new_order: list[str],
        rationale: str = ""
    ) -> tuple[Path | None, SectionReorder]:
        """Reorder sections in QMD file with backup (T055).

        Args:
            qmd_path: Path to QMD file
            new_order: Desired section order
            rationale: Reason for reordering

        Returns:
            Tuple of (backup_path, SectionReorder result)

        Raises:
            FileNotFoundError: If QMD file doesn't exist
            ValueError: If content hash mismatch after reordering
        """
        if not qmd_path.exists():
            raise FileNotFoundError(f"QMD file not found: {qmd_path}")

        # Read current content
        original_content = qmd_path.read_text(encoding="utf-8")

        # Get current order
        sections = self._parse_sections(original_content)
        original_order = [
            s["heading"] for s in sections
            if s["heading"] not in ("__yaml__", "__preamble__", "__content__")
        ]

        # Calculate hash before
        hash_before = self._calculate_content_hash(original_content)

        # Create backup
        backup_path = self._create_backup(qmd_path)

        try:
            # Reorder
            reordered_content = self._reorder_sections(original_content, new_order)

            # Calculate hash after
            hash_after = self._calculate_content_hash(reordered_content)

            # Verify content preservation
            if hash_before != hash_after:
                # Rollback
                self.rollback(backup_path, qmd_path)
                raise ValueError(
                    f"Content hash mismatch after reordering. Rolling back. "
                    f"Before: {hash_before[:16]}..., After: {hash_after[:16]}..."
                )

            # Write atomically
            temp_path = qmd_path.with_suffix(".tmp")
            temp_path.write_text(reordered_content, encoding="utf-8")
            temp_path.replace(qmd_path)

            logger.info(f"QMD file reordered successfully: {qmd_path}")

            return backup_path, SectionReorder(
                original_order=original_order,
                new_order=new_order,
                rationale=rationale or "Section reorder applied",
                content_hash_before=hash_before,
                content_hash_after=hash_after,
            )

        except Exception:
            # Rollback on any error
            if backup_path and backup_path.exists():
                self.rollback(backup_path, qmd_path)
            raise

    def _create_backup(self, qmd_path: Path) -> Path:
        """Create timestamped backup of QMD file.

        Args:
            qmd_path: Path to original file

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_dir or qmd_path.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup_name = f"{qmd_path.stem}_{timestamp}{qmd_path.suffix}"
        backup_path = backup_dir / backup_name

        shutil.copy2(qmd_path, backup_path)
        logger.info(f"Created backup: {backup_path}")

        return backup_path

    def rollback(self, backup_path: Path, target_path: Path) -> bool:
        """Restore QMD file from backup (T072).

        Args:
            backup_path: Path to backup file
            target_path: Path to restore to

        Returns:
            True if rollback successful, False otherwise
        """
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False

        try:
            shutil.copy2(backup_path, target_path)
            logger.info(f"Rolled back to backup: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
