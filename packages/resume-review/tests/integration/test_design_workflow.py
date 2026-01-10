"""Integration tests for design auto-fix workflow.

Tests for T017: Integration test for auto-design workflow.
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.models import ActionType, Severity
from src.models.design import CSSModification
from src.models.feedback import Feedback, Issue
from src.workflow.nodes.design_applier import design_applier_node


class TestDesignApplierNodeIntegration:
    """Integration tests for design_applier_node - T017."""

    @pytest.fixture
    def sample_design_feedback(self):
        """Create sample design feedback from UX and Visual Designer."""
        return [
            Feedback(
                agent_name="visual_designer",
                score=6.5,
                strengths=["Good color palette"],
                issues=[
                    Issue(
                        description="Heading font size too small, lacks visual hierarchy",
                        action_type=ActionType.EMPHASIZE,
                        severity=Severity.HIGH,
                        location="All headings",
                    ),
                    Issue(
                        description="Section spacing is cramped",
                        action_type=ActionType.RESTRUCTURE,
                        severity=Severity.MEDIUM,
                        location="Section gaps",
                    ),
                ],
                suggestions=["Increase font sizes", "Add more whitespace"],
            ),
            Feedback(
                agent_name="ux_designer",
                score=7.0,
                strengths=["Clear information structure"],
                issues=[
                    Issue(
                        description="Skills section should be more prominent",
                        action_type=ActionType.EMPHASIZE,
                        severity=Severity.HIGH,
                        location="Skills section",
                    ),
                ],
                suggestions=["Highlight key skills"],
            ),
        ]

    @pytest.fixture
    def sample_state(self, sample_design_feedback, tmp_path):
        """Create sample workflow state."""
        return {
            "current_feedback": sample_design_feedback,
            "auto_design_enabled": True,
            "design_preview_enabled": False,
            "css_output_path": str(tmp_path / "styles" / "resume-custom.css"),
            "target_role": "LLM Engineer",
            "gemini_api_key": None,
            "openai_api_key": None,
            "anthropic_api_key": "test-key",
            "override_model": None,
            "resume": Mock(
                file_path=Path("resume/resume-ja.qmd"),
                content="# Resume Content",
            ),
        }

    @pytest.fixture
    def mock_css_response(self):
        """Mock LLM response with valid CSS."""
        return """
Here are the CSS modifications:

```css
/* Improve heading hierarchy - address visual_designer feedback */
:root {
  --h2-size: 1.4rem;
  --h3-size: 1.1rem;
  --section-gap: 2rem;
}

h2 {
  font-size: var(--h2-size);
  font-weight: 600;
  margin-bottom: 1rem;
}

h3 {
  font-size: var(--h3-size);
  font-weight: 500;
}

/* Improve section spacing */
section {
  margin-bottom: var(--section-gap);
}
```
"""

    @pytest.mark.asyncio
    async def test_auto_design_generates_and_applies_css(
        self, sample_state, mock_css_response, tmp_path
    ):
        """Auto-design mode should generate CSS and apply it to file."""
        # Setup mock LLM client
        with patch(
            "src.workflow.nodes.design_applier.LLMClientFactory"
        ) as mock_factory:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = mock_css_response
            mock_client.generate_async = AsyncMock(return_value=mock_response)
            mock_factory.create_client.return_value = mock_client

            # Run the design applier node
            result = await design_applier_node(sample_state)

            # Verify CSS was generated
            assert "css_modification" in result
            css_mod = result["css_modification"]
            assert isinstance(css_mod, CSSModification)
            assert css_mod.validation_passed is True

            # Verify changes were applied
            assert result.get("design_changes_applied") is True
            assert len(result.get("design_changes_list", [])) > 0

    @pytest.mark.asyncio
    async def test_design_applier_skips_without_feedback(self, tmp_path):
        """Node should skip when no design feedback exists."""
        state = {
            "current_feedback": [],  # No feedback
            "auto_design_enabled": True,
            "design_preview_enabled": False,
        }

        result = await design_applier_node(state)

        assert result.get("design_changes_applied") is False
        assert result.get("design_changes_pending") is False
        assert "css_modification" not in result

    @pytest.mark.asyncio
    async def test_design_applier_skips_non_design_feedback(self, tmp_path):
        """Node should skip when feedback is not from design agents."""
        non_design_feedback = [
            Feedback(
                agent_name="recruiter",
                score=7.0,
                strengths=["Good experience"],
                issues=[
                    Issue(
                        description="Add more quantifiable achievements",
                        action_type=ActionType.QUANTIFY,
                        severity=Severity.MEDIUM,
                        location="Experience section",
                    ),
                ],
                suggestions=["Add metrics"],
            ),
        ]

        state = {
            "current_feedback": non_design_feedback,
            "auto_design_enabled": True,
            "design_preview_enabled": False,
        }

        result = await design_applier_node(state)

        assert result.get("design_changes_applied") is False
        assert "css_modification" not in result

    @pytest.mark.asyncio
    async def test_preview_mode_generates_without_applying(
        self, sample_state, mock_css_response
    ):
        """Preview mode should generate CSS but not apply it."""
        sample_state["auto_design_enabled"] = False
        sample_state["design_preview_enabled"] = True

        with patch(
            "src.workflow.nodes.design_applier.LLMClientFactory"
        ) as mock_factory:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = mock_css_response
            mock_client.generate_async = AsyncMock(return_value=mock_response)
            mock_factory.create_client.return_value = mock_client

            result = await design_applier_node(sample_state)

            # CSS should be generated but not applied
            assert "css_modification" in result
            assert result.get("design_changes_pending") is True
            assert result.get("design_changes_applied") is False

    @pytest.mark.asyncio
    async def test_css_validation_failure_prevents_application(
        self, sample_state, tmp_path
    ):
        """Invalid CSS should not be applied."""
        invalid_css_response = """
Here is the CSS:

```css
h2 {
  font-size: undefined;
}
```
"""
        with patch(
            "src.workflow.nodes.design_applier.LLMClientFactory"
        ) as mock_factory:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = invalid_css_response
            mock_client.generate_async = AsyncMock(return_value=mock_response)
            mock_factory.create_client.return_value = mock_client

            result = await design_applier_node(sample_state)

            # CSS validation should fail
            if "css_modification" in result:
                css_mod = result["css_modification"]
                assert css_mod.validation_passed is False

            # Changes should not be applied
            assert result.get("design_changes_applied") is False

    @pytest.mark.asyncio
    async def test_backup_created_for_existing_css(
        self, sample_state, mock_css_response, tmp_path
    ):
        """Backup should be created when overwriting existing CSS file."""
        # Create existing CSS file
        css_path = Path(sample_state["css_output_path"])
        css_path.parent.mkdir(parents=True, exist_ok=True)
        css_path.write_text("/* Existing CSS */")

        with patch(
            "src.workflow.nodes.design_applier.LLMClientFactory"
        ) as mock_factory:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = mock_css_response
            mock_client.generate_async = AsyncMock(return_value=mock_response)
            mock_factory.create_client.return_value = mock_client

            result = await design_applier_node(sample_state)

            # Backup should be recorded
            backup_paths = result.get("design_backup_paths", {})
            if result.get("design_changes_applied"):
                assert len(backup_paths) > 0


class TestDesignApplierCondition:
    """Tests for should_run_design_applier conditional."""

    def test_condition_returns_design_applier_when_enabled(self):
        """Condition should return 'design_applier' when auto_design enabled."""
        from src.workflow.conditions import should_run_design_applier

        state = {
            "auto_design_enabled": True,
            "design_preview_enabled": False,
            "current_feedback": [
                Feedback(
                    agent_name="visual_designer",
                    score=7.0,
                    strengths=["Basic structure"],
                    issues=[
                        Issue(
                            description="Test issue",
                            action_type=ActionType.EMPHASIZE,
                            severity=Severity.MEDIUM,
                            location="Test",
                        )
                    ],
                    suggestions=[],
                ),
            ],
        }

        result = should_run_design_applier(state)
        assert result == "design_applier"

    def test_condition_returns_design_applier_for_preview(self):
        """Condition should return 'design_applier' when preview enabled."""
        from src.workflow.conditions import should_run_design_applier

        state = {
            "auto_design_enabled": False,
            "design_preview_enabled": True,
            "current_feedback": [
                Feedback(
                    agent_name="ux_designer",
                    score=7.0,
                    strengths=["Basic structure"],
                    issues=[
                        Issue(
                            description="Test issue",
                            action_type=ActionType.EMPHASIZE,
                            severity=Severity.MEDIUM,
                            location="Test",
                        )
                    ],
                    suggestions=[],
                ),
            ],
        }

        result = should_run_design_applier(state)
        assert result == "design_applier"

    def test_condition_returns_end_when_disabled(self):
        """Condition should return 'end' when design features disabled."""
        from src.workflow.conditions import should_run_design_applier

        state = {
            "auto_design_enabled": False,
            "design_preview_enabled": False,
            "current_feedback": [
                Feedback(
                    agent_name="visual_designer",
                    score=7.0,
                    strengths=["Basic structure"],
                    issues=[
                        Issue(
                            description="Test issue",
                            action_type=ActionType.EMPHASIZE,
                            severity=Severity.MEDIUM,
                            location="Test",
                        )
                    ],
                    suggestions=[],
                ),
            ],
        }

        result = should_run_design_applier(state)
        assert result == "end"

    def test_condition_returns_end_when_no_design_feedback(self):
        """Condition should return 'end' when no design feedback."""
        from src.workflow.conditions import should_run_design_applier

        state = {
            "auto_design_enabled": True,
            "design_preview_enabled": False,
            "current_feedback": [
                Feedback(
                    agent_name="recruiter",  # Not a design agent
                    score=7.0,
                    strengths=["Good experience"],
                    issues=[
                        Issue(
                            description="Test issue",
                            action_type=ActionType.QUANTIFY,
                            severity=Severity.MEDIUM,
                            location="Test",
                        )
                    ],
                    suggestions=[],
                ),
            ],
        }

        result = should_run_design_applier(state)
        assert result == "end"


class TestEndToEndAutoDesign:
    """End-to-end tests for the complete auto-design workflow."""

    @pytest.mark.asyncio
    async def test_full_workflow_css_generation_and_output(self, tmp_path):
        """Test complete flow from feedback to CSS output."""
        # Create test directories
        styles_dir = tmp_path / "styles"
        styles_dir.mkdir(parents=True)

        # Sample design feedback
        design_feedback = [
            Feedback(
                agent_name="visual_designer",
                score=6.0,
                strengths=["Basic layout"],
                issues=[
                    Issue(
                        description="Headings lack visual weight and hierarchy",
                        action_type=ActionType.EMPHASIZE,
                        severity=Severity.HIGH,
                        location="All headings",
                    ),
                ],
                suggestions=["Increase heading font sizes"],
            ),
        ]

        state = {
            "current_feedback": design_feedback,
            "auto_design_enabled": True,
            "design_preview_enabled": False,
            "css_output_path": str(styles_dir / "resume-custom.css"),
            "target_role": "Software Engineer",
            "anthropic_api_key": "test-key",
            "gemini_api_key": None,
            "openai_api_key": None,
            "override_model": None,
        }

        mock_css = """
```css
:root {
  --h2-size: 1.4rem;
}
h2 {
  font-size: var(--h2-size);
  font-weight: 600;
}
```
"""

        with patch(
            "src.workflow.nodes.design_applier.LLMClientFactory"
        ) as mock_factory:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = mock_css
            mock_client.generate_async = AsyncMock(return_value=mock_response)
            mock_factory.create_client.return_value = mock_client

            result = await design_applier_node(state)

            # Verify complete workflow
            assert result.get("design_changes_applied") is True

            # Verify CSS file was created
            css_file = styles_dir / "resume-custom.css"
            assert css_file.exists()

            # Verify CSS content
            css_content = css_file.read_text()
            assert "h2" in css_content
            assert "--h2-size" in css_content


class TestPreviewWorkflowIntegration:
    """Integration tests for preview workflow - T036."""

    @pytest.fixture
    def sample_design_feedback(self):
        """Create sample design feedback."""
        return [
            Feedback(
                agent_name="visual_designer",
                score=6.5,
                strengths=["Good color palette"],
                issues=[
                    Issue(
                        description="Heading font size too small",
                        action_type=ActionType.EMPHASIZE,
                        severity=Severity.HIGH,
                        location="All headings",
                    ),
                ],
                suggestions=["Increase font sizes"],
            ),
        ]

    @pytest.fixture
    def mock_css_response(self):
        """Mock LLM response with valid CSS."""
        return """
```css
:root {
  --h2-size: 1.4rem;
}
h2 {
  font-size: var(--h2-size);
}
```
"""

    @pytest.mark.asyncio
    async def test_preview_mode_sets_pending_flag(
        self, sample_design_feedback, mock_css_response, tmp_path
    ):
        """Preview mode should set design_changes_pending to True."""
        state = {
            "current_feedback": sample_design_feedback,
            "auto_design_enabled": False,
            "design_preview_enabled": True,
            "css_output_path": str(tmp_path / "styles" / "resume-custom.css"),
            "target_role": "LLM Engineer",
            "anthropic_api_key": "test-key",
            "gemini_api_key": None,
            "openai_api_key": None,
            "override_model": None,
        }

        with patch(
            "src.workflow.nodes.design_applier.LLMClientFactory"
        ) as mock_factory:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = mock_css_response
            mock_client.generate_async = AsyncMock(return_value=mock_response)
            mock_factory.create_client.return_value = mock_client

            result = await design_applier_node(state)

            assert result.get("design_changes_pending") is True
            assert result.get("design_changes_applied") is False

    @pytest.mark.asyncio
    async def test_preview_mode_does_not_create_css_file(
        self, sample_design_feedback, mock_css_response, tmp_path
    ):
        """Preview mode should NOT create actual CSS file."""
        styles_dir = tmp_path / "styles"
        css_path = styles_dir / "resume-custom.css"

        state = {
            "current_feedback": sample_design_feedback,
            "auto_design_enabled": False,
            "design_preview_enabled": True,
            "css_output_path": str(css_path),
            "target_role": "LLM Engineer",
            "anthropic_api_key": "test-key",
            "gemini_api_key": None,
            "openai_api_key": None,
            "override_model": None,
        }

        with patch(
            "src.workflow.nodes.design_applier.LLMClientFactory"
        ) as mock_factory:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = mock_css_response
            mock_client.generate_async = AsyncMock(return_value=mock_response)
            mock_factory.create_client.return_value = mock_client

            await design_applier_node(state)

            # CSS file should NOT be created in preview mode
            assert not css_path.exists()

    @pytest.mark.asyncio
    async def test_preview_mode_generates_css_modification(
        self, sample_design_feedback, mock_css_response, tmp_path
    ):
        """Preview mode should generate CSS modification for display."""
        state = {
            "current_feedback": sample_design_feedback,
            "auto_design_enabled": False,
            "design_preview_enabled": True,
            "css_output_path": str(tmp_path / "styles" / "resume-custom.css"),
            "target_role": "LLM Engineer",
            "anthropic_api_key": "test-key",
            "gemini_api_key": None,
            "openai_api_key": None,
            "override_model": None,
        }

        with patch(
            "src.workflow.nodes.design_applier.LLMClientFactory"
        ) as mock_factory:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = mock_css_response
            mock_client.generate_async = AsyncMock(return_value=mock_response)
            mock_factory.create_client.return_value = mock_client

            result = await design_applier_node(state)

            # CSS modification should be generated for preview
            assert "css_modification" in result
            css_mod = result["css_modification"]
            assert isinstance(css_mod, CSSModification)
            assert css_mod.css_content  # Should have content

    @pytest.mark.asyncio
    async def test_preview_mode_preserves_existing_css(
        self, sample_design_feedback, mock_css_response, tmp_path
    ):
        """Preview mode should not modify existing CSS files."""
        styles_dir = tmp_path / "styles"
        styles_dir.mkdir(parents=True)
        css_path = styles_dir / "resume-custom.css"
        original_content = "/* Original CSS - should not be modified */"
        css_path.write_text(original_content)

        state = {
            "current_feedback": sample_design_feedback,
            "auto_design_enabled": False,
            "design_preview_enabled": True,
            "css_output_path": str(css_path),
            "target_role": "LLM Engineer",
            "anthropic_api_key": "test-key",
            "gemini_api_key": None,
            "openai_api_key": None,
            "override_model": None,
        }

        with patch(
            "src.workflow.nodes.design_applier.LLMClientFactory"
        ) as mock_factory:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = mock_css_response
            mock_client.generate_async = AsyncMock(return_value=mock_response)
            mock_factory.create_client.return_value = mock_client

            await design_applier_node(state)

            # Original CSS should be preserved
            assert css_path.read_text() == original_content

    @pytest.mark.asyncio
    async def test_preview_with_screenshot_url_state(
        self, sample_design_feedback, mock_css_response, tmp_path
    ):
        """Preview mode should accept screenshot_url in state."""
        state = {
            "current_feedback": sample_design_feedback,
            "auto_design_enabled": False,
            "design_preview_enabled": True,
            "css_output_path": str(tmp_path / "styles" / "resume-custom.css"),
            "screenshot_url": "http://localhost:3000/ja",  # Preview URL
            "target_role": "LLM Engineer",
            "anthropic_api_key": "test-key",
            "gemini_api_key": None,
            "openai_api_key": None,
            "override_model": None,
        }

        with patch(
            "src.workflow.nodes.design_applier.LLMClientFactory"
        ) as mock_factory:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = mock_css_response
            mock_client.generate_async = AsyncMock(return_value=mock_response)
            mock_factory.create_client.return_value = mock_client

            result = await design_applier_node(state)

            # Should work with screenshot_url in state
            assert result.get("design_changes_pending") is True


class TestSectionReorderWorkflowIntegration:
    """Integration tests for section reorder workflow - T049."""

    @pytest.fixture
    def ux_feedback_with_reorder(self):
        """Create UX feedback suggesting section reorder."""
        return [
            Feedback(
                agent_name="ux_designer",
                score=6.5,
                strengths=["Good content"],
                issues=[
                    Issue(
                        description="Skills section should be first for technical roles - move to top",
                        action_type=ActionType.RESTRUCTURE,
                        severity=Severity.HIGH,
                        location="Section order",
                    ),
                    Issue(
                        description="Experience is more valuable than Summary - prioritize it",
                        action_type=ActionType.RESTRUCTURE,
                        severity=Severity.MEDIUM,
                        location="Section order",
                    ),
                ],
                suggestions=["Reorder sections for technical emphasis"],
            ),
        ]

    @pytest.fixture
    def sample_qmd_with_sections(self, tmp_path):
        """Create sample QMD file with sections."""
        content = '''---
title: "Resume"
format: pdf
---

## Summary

Engineer with 5 years experience.

## Experience

### Company A
Built scalable systems.

## Skills

- Python
- JavaScript

## Education

B.S. Computer Science
'''
        qmd_path = tmp_path / "resume.qmd"
        qmd_path.write_text(content)
        return qmd_path

    def test_section_reorder_detects_order_suggestions(self, ux_feedback_with_reorder):
        """Should detect section reorder suggestions from UX feedback."""
        from src.services.section_reorder import SectionReorderService

        qmd_content = '''---
title: Test
---

## Summary
Summary content

## Experience
Experience content

## Skills
Skills content
'''
        service = SectionReorderService()
        result = service.analyze_and_recommend(
            qmd_content,
            ux_feedback_with_reorder,
            target_role="LLM Engineer"
        )

        assert result is not None
        assert result.is_changed()
        # Skills should move to top based on feedback
        assert result.new_order.index("Skills") < result.new_order.index("Experience")

    def test_section_reorder_preserves_content(self, sample_qmd_with_sections):
        """Section reorder should preserve all content."""
        from src.services.section_reorder import SectionReorderService

        original_content = sample_qmd_with_sections.read_text()
        service = SectionReorderService()

        new_order = ["Skills", "Experience", "Summary", "Education"]
        backup_path, reorder_result = service.reorder_with_backup(
            sample_qmd_with_sections,
            new_order,
            "Test reorder"
        )

        reordered_content = sample_qmd_with_sections.read_text()

        # All original content should be present
        assert "Engineer with 5 years experience" in reordered_content
        assert "Built scalable systems" in reordered_content
        assert "Python" in reordered_content
        assert "B.S. Computer Science" in reordered_content

        # Verify hash matches
        assert reorder_result.content_hash_before == reorder_result.content_hash_after

    def test_section_reorder_creates_backup(self, sample_qmd_with_sections):
        """Section reorder should create backup of original file."""
        from src.services.section_reorder import SectionReorderService

        original_content = sample_qmd_with_sections.read_text()
        service = SectionReorderService()

        new_order = ["Skills", "Experience", "Summary", "Education"]
        backup_path, _ = service.reorder_with_backup(
            sample_qmd_with_sections,
            new_order,
            "Test backup"
        )

        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == original_content

    def test_section_reorder_rollback_on_error(self, sample_qmd_with_sections, tmp_path):
        """Should rollback on content hash mismatch."""
        from src.services.section_reorder import SectionReorderService

        original_content = sample_qmd_with_sections.read_text()
        backup_path = tmp_path / "backups" / "backup.qmd"
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_text(original_content)

        service = SectionReorderService(backup_dir=str(tmp_path / "backups"))

        # Rollback should restore from backup
        target = tmp_path / "target.qmd"
        target.write_text("modified content")

        result = service.rollback(backup_path, target)

        assert result is True
        assert target.read_text() == original_content
