"""Unit tests for SectionReorderService - QMD section parsing and reordering.

Tests for T047: Section parsing and T048: Section reordering with content preservation.
"""

import hashlib
from pathlib import Path

import pytest

from src.models.design import SectionReorder


class TestSectionParsing:
    """Test cases for section parsing - T047."""

    @pytest.fixture
    def sample_qmd_content(self):
        """Create sample QMD content with sections."""
        return '''---
title: "Resume"
author: "Test User"
format: pdf
---

## Summary

A skilled engineer with 5 years of experience.

## Experience

### Company A
- Built scalable systems
- Led team of 5 engineers

### Company B
- Developed APIs
- Improved performance by 50%

## Skills

- Python
- JavaScript
- Cloud Architecture

## Education

- B.S. Computer Science, University of Tokyo
'''

    @pytest.fixture
    def service(self):
        """Create SectionReorderService."""
        from src.services.section_reorder import SectionReorderService
        return SectionReorderService()

    def test_parse_sections_extracts_headings(self, service, sample_qmd_content):
        """Should extract all ## level headings."""
        sections = service._parse_sections(sample_qmd_content)

        headings = [s["heading"] for s in sections]
        assert "Summary" in headings
        assert "Experience" in headings
        assert "Skills" in headings
        assert "Education" in headings

    def test_parse_sections_preserves_content(self, service, sample_qmd_content):
        """Should preserve content under each section."""
        sections = service._parse_sections(sample_qmd_content)

        experience_section = next(s for s in sections if s["heading"] == "Experience")
        assert "Company A" in experience_section["content"]
        assert "Company B" in experience_section["content"]

    def test_parse_sections_preserves_yaml_frontmatter(self, service, sample_qmd_content):
        """Should preserve YAML frontmatter separately."""
        sections = service._parse_sections(sample_qmd_content)

        # First element should be YAML frontmatter
        assert sections[0]["heading"] == "__yaml__"
        assert "title:" in sections[0]["content"]
        assert "author:" in sections[0]["content"]

    def test_parse_sections_handles_nested_headings(self, service, sample_qmd_content):
        """Should handle ### headings within ## sections."""
        sections = service._parse_sections(sample_qmd_content)

        experience_section = next(s for s in sections if s["heading"] == "Experience")
        # Nested ### headings should be in the content
        assert "### Company A" in experience_section["content"]
        assert "### Company B" in experience_section["content"]

    def test_parse_sections_empty_content(self, service):
        """Should handle content without sections."""
        content = "Just some plain text without sections."
        sections = service._parse_sections(content)

        # Should return at least some content
        assert len(sections) >= 1

    def test_parse_sections_preserves_order(self, service, sample_qmd_content):
        """Should preserve original section order."""
        sections = service._parse_sections(sample_qmd_content)

        # Filter out YAML
        content_sections = [s for s in sections if s["heading"] != "__yaml__"]
        headings = [s["heading"] for s in content_sections]

        assert headings == ["Summary", "Experience", "Skills", "Education"]


class TestSectionReordering:
    """Test cases for section reordering - T048."""

    @pytest.fixture
    def sample_qmd_content(self):
        """Create sample QMD content with sections."""
        return '''---
title: "Resume"
format: pdf
---

## Summary

Engineer summary.

## Experience

Work history.

## Skills

Technical skills.

## Education

Degrees and certifications.
'''

    @pytest.fixture
    def service(self):
        """Create SectionReorderService."""
        from src.services.section_reorder import SectionReorderService
        return SectionReorderService()

    def test_reorder_changes_section_order(self, service, sample_qmd_content):
        """Should reorder sections according to new_order."""
        new_order = ["Skills", "Experience", "Summary", "Education"]

        reordered_content = service._reorder_sections(
            sample_qmd_content,
            new_order
        )

        # Find indices of sections in reordered content
        skills_idx = reordered_content.find("## Skills")
        experience_idx = reordered_content.find("## Experience")
        summary_idx = reordered_content.find("## Summary")
        education_idx = reordered_content.find("## Education")

        assert skills_idx < experience_idx < summary_idx < education_idx

    def test_reorder_preserves_all_content(self, service, sample_qmd_content):
        """Should preserve all original content after reordering."""
        new_order = ["Skills", "Experience", "Summary", "Education"]

        reordered_content = service._reorder_sections(
            sample_qmd_content,
            new_order
        )

        # All content should still be present
        assert "Engineer summary" in reordered_content
        assert "Work history" in reordered_content
        assert "Technical skills" in reordered_content
        assert "Degrees and certifications" in reordered_content

    def test_reorder_preserves_yaml_frontmatter(self, service, sample_qmd_content):
        """Should keep YAML frontmatter at the beginning."""
        new_order = ["Skills", "Experience", "Summary", "Education"]

        reordered_content = service._reorder_sections(
            sample_qmd_content,
            new_order
        )

        # YAML should still be at the start
        assert reordered_content.strip().startswith("---")
        assert "title:" in reordered_content

    def test_reorder_content_hash_matches(self, service, sample_qmd_content):
        """Content hash should match before and after reordering."""
        new_order = ["Skills", "Experience", "Summary", "Education"]

        hash_before = service._calculate_content_hash(sample_qmd_content)

        reordered_content = service._reorder_sections(
            sample_qmd_content,
            new_order
        )

        hash_after = service._calculate_content_hash(reordered_content)

        assert hash_before == hash_after

    def test_reorder_no_content_lost(self, service, sample_qmd_content):
        """No content should be lost during reordering."""
        new_order = ["Education", "Skills", "Experience", "Summary"]

        original_lines = set(sample_qmd_content.strip().split("\n"))

        reordered_content = service._reorder_sections(
            sample_qmd_content,
            new_order
        )

        reordered_lines = set(reordered_content.strip().split("\n"))

        # All original non-empty lines should be present
        for line in original_lines:
            if line.strip():
                assert line in reordered_lines or line.strip() in " ".join(reordered_lines)


class TestContentHashCalculation:
    """Test cases for content hash verification."""

    @pytest.fixture
    def service(self):
        """Create SectionReorderService."""
        from src.services.section_reorder import SectionReorderService
        return SectionReorderService()

    def test_hash_ignores_section_order(self, service):
        """Hash should be same regardless of section order."""
        content1 = """## A

Content A

## B

Content B
"""
        content2 = """## B

Content B

## A

Content A
"""
        hash1 = service._calculate_content_hash(content1)
        hash2 = service._calculate_content_hash(content2)

        assert hash1 == hash2

    def test_hash_detects_content_changes(self, service):
        """Hash should differ when content is modified."""
        content1 = "## Section\n\nOriginal content"
        content2 = "## Section\n\nModified content"

        hash1 = service._calculate_content_hash(content1)
        hash2 = service._calculate_content_hash(content2)

        assert hash1 != hash2

    def test_hash_ignores_whitespace_differences(self, service):
        """Hash should be same with different whitespace."""
        content1 = "## Section\n\nContent  here"
        content2 = "## Section\n\n\nContent  here\n"

        hash1 = service._calculate_content_hash(content1)
        hash2 = service._calculate_content_hash(content2)

        # Whitespace normalization means these should match
        assert hash1 == hash2


class TestSectionReorderModel:
    """Test cases for SectionReorder Pydantic model."""

    def test_section_reorder_valid_creation(self):
        """Should create valid SectionReorder model."""
        reorder = SectionReorder(
            original_order=["A", "B", "C"],
            new_order=["C", "B", "A"],
            rationale="Prioritize skills for technical roles",
        )

        assert reorder.original_order == ["A", "B", "C"]
        assert reorder.new_order == ["C", "B", "A"]
        assert reorder.is_changed() is True

    def test_section_reorder_unchanged(self):
        """is_changed should return False when order unchanged."""
        reorder = SectionReorder(
            original_order=["A", "B", "C"],
            new_order=["A", "B", "C"],
            rationale="No changes needed",
        )

        assert reorder.is_changed() is False

    def test_section_reorder_invalid_missing_section(self):
        """Should reject new_order missing a section."""
        with pytest.raises(ValueError, match="Missing"):
            SectionReorder(
                original_order=["A", "B", "C"],
                new_order=["A", "B"],  # Missing C
                rationale="Test",
            )

    def test_section_reorder_invalid_extra_section(self):
        """Should reject new_order with extra section."""
        with pytest.raises(ValueError, match="Extra"):
            SectionReorder(
                original_order=["A", "B"],
                new_order=["A", "B", "C"],  # Extra C
                rationale="Test",
            )

    def test_section_reorder_get_movements(self):
        """Should correctly identify moved sections."""
        reorder = SectionReorder(
            original_order=["A", "B", "C", "D"],
            new_order=["C", "A", "B", "D"],
            rationale="Move C to top",
        )

        movements = reorder.get_movements()

        # A moved from 0 to 1, B moved from 1 to 2, C moved from 2 to 0
        assert ("A", 0, 1) in movements
        assert ("B", 1, 2) in movements
        assert ("C", 2, 0) in movements
        # D stayed at same relative position to others but index changed
        assert ("D", 3, 3) not in movements  # D didn't move

    def test_section_reorder_content_hash_validation(self):
        """Should reject if content hash mismatch after reorder."""
        reorder = SectionReorder(
            original_order=["A", "B"],
            new_order=["B", "A"],
            rationale="Reorder test",
            content_hash_before="abc123",
        )

        # Setting different hash_after should fail validation
        with pytest.raises(ValueError, match="Content hash mismatch"):
            SectionReorder(
                original_order=["A", "B"],
                new_order=["B", "A"],
                rationale="Reorder test",
                content_hash_before="abc123",
                content_hash_after="different_hash",  # Different hash
            )
