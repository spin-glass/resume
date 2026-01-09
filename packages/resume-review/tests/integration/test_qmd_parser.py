"""Integration tests for QMD parser."""

import tempfile
from pathlib import Path

import pytest

from src.services.qmd_parser import QMDParser


@pytest.fixture
def sample_resume_path():
    """Get path to sample resume fixture."""
    return Path(__file__).parent.parent / "fixtures" / "sample-resume.qmd"


@pytest.fixture
def temp_qmd_file():
    """Create a temporary QMD file for testing."""
    content = """---
title: "Test Resume"
author: "Test User"
date: "2026-01-09"
format: html
custom_field: "custom_value"
---

# Test Content

This is test content.

## Section 1

Some text here.
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.qmd', delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()
    # Also cleanup backup if exists
    backup = temp_path.with_suffix(temp_path.suffix + ".bak")
    if backup.exists():
        backup.unlink()


@pytest.mark.integration
def test_yaml_preservation_after_modification(temp_qmd_file):
    """
    Test T028: Verify frontmatter unchanged after revision.
    """
    parser = QMDParser()

    # Load original
    original = parser.load_resume(temp_qmd_file)
    original_yaml = original.yaml_frontmatter.copy()
    original_keys = set(original_yaml.keys())

    # Modify content but not YAML
    from src.models.feedback import Resume

    modified = Resume(
        file_path=original.file_path,
        yaml_frontmatter=original.yaml_frontmatter,  # Keep same
        content=original.content + "\n\n## New Section\n\nAdded content.",
        full_text=original.full_text,
    )

    # Save
    parser.save_resume(modified, temp_qmd_file)

    # Reload
    reloaded = parser.load_resume(temp_qmd_file)

    # Verify YAML preserved
    assert reloaded.yaml_frontmatter == original_yaml
    assert set(reloaded.yaml_frontmatter.keys()) == original_keys

    # Verify content was updated
    assert "New Section" in reloaded.content
    assert "Added content" in reloaded.content


@pytest.mark.integration
def test_backup_file_creation(temp_qmd_file):
    """
    Test that backup file is created when saving.
    """
    parser = QMDParser()

    # Load resume
    resume = parser.load_resume(temp_qmd_file)

    # Modify content
    from src.models.feedback import Resume

    modified = Resume(
        file_path=resume.file_path,
        yaml_frontmatter=resume.yaml_frontmatter,
        content=resume.content + "\n\nModified content.",
        full_text=resume.full_text,
    )

    # Save with backup
    parser.save_resume(modified, temp_qmd_file, create_backup=True)

    # Verify backup exists
    backup_path = temp_qmd_file.with_suffix(temp_qmd_file.suffix + ".bak")
    assert backup_path.exists()

    # Verify backup contains original content by reading as text
    with open(backup_path, 'r') as f:
        backup_content = f.read()
    assert "Modified content" not in backup_content
    assert "Test Content" in backup_content  # Original content should be there


@pytest.mark.integration
def test_yaml_integrity_validation(sample_resume_path):
    """
    Test YAML integrity validation.
    """
    parser = QMDParser()

    # Load resume
    original = parser.load_resume(sample_resume_path)

    # Create modified version with same YAML
    from src.models.feedback import Resume

    same_yaml = Resume(
        file_path=original.file_path,
        yaml_frontmatter=original.yaml_frontmatter.copy(),
        content=original.content + "\nExtra content",
        full_text=original.full_text,
    )

    # Validate integrity - should pass
    assert parser.validate_yaml_integrity(original, same_yaml) is True

    # Create version with different YAML
    different_yaml = Resume(
        file_path=original.file_path,
        yaml_frontmatter={**original.yaml_frontmatter, "new_key": "new_value"},
        content=original.content,
        full_text=original.full_text,
    )

    # Validate integrity - should fail
    assert parser.validate_yaml_integrity(original, different_yaml) is False


@pytest.mark.integration
def test_load_nonexistent_file():
    """
    Test loading a file that doesn't exist.
    """
    parser = QMDParser()

    with pytest.raises(FileNotFoundError):
        parser.load_resume(Path("/nonexistent/file.qmd"))


@pytest.mark.integration
def test_roundtrip_preservation(temp_qmd_file):
    """
    Test that loading and saving preserves all content.
    """
    parser = QMDParser()

    # Load
    original = parser.load_resume(temp_qmd_file)

    # Create temp output
    with tempfile.NamedTemporaryFile(mode='w', suffix='.qmd', delete=False) as f:
        output_path = Path(f.name)

    try:
        # Save to new file
        parser.save_resume(original, output_path, create_backup=False)

        # Reload from new file
        reloaded = parser.load_resume(output_path)

        # Compare
        assert reloaded.yaml_frontmatter == original.yaml_frontmatter
        assert reloaded.content.strip() == original.content.strip()

    finally:
        if output_path.exists():
            output_path.unlink()


@pytest.mark.integration
def test_special_yaml_characters(temp_qmd_file):
    """
    Test handling of special characters in YAML.
    """
    parser = QMDParser()

    # Create resume with special chars
    from src.models.feedback import Resume

    special_yaml = {
        "title": "Resume: Engineer's Guide",
        "description": "Multi-line\ndescription with\nspecial chars: @#$%",
        "tags": ["python", "AI/ML", "LLM's"],
        "number": 42,
    }

    resume = Resume(
        file_path=temp_qmd_file,
        yaml_frontmatter=special_yaml,
        content="# Test\n\nContent here.",
        full_text="",
    )

    # Save
    parser.save_resume(resume, temp_qmd_file)

    # Reload
    reloaded = parser.load_resume(temp_qmd_file)

    # Verify special chars preserved
    assert reloaded.yaml_frontmatter["title"] == "Resume: Engineer's Guide"
    assert "Multi-line" in reloaded.yaml_frontmatter["description"]
    assert reloaded.yaml_frontmatter["tags"] == ["python", "AI/ML", "LLM's"]
    assert reloaded.yaml_frontmatter["number"] == 42
