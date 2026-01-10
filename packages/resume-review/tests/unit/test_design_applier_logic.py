import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from src.workflow.nodes.design_applier import design_applier_node
from src.models.feedback import Feedback

@pytest.mark.asyncio
async def test_design_applier_loop_logic(tmp_path):
    """Test design loop folder creation and iteration increment."""
    
    # Setup
    session_dir = tmp_path / "design_test_session"
    session_dir.mkdir()
    
    state = {
        "session_dir": str(session_dir),
        "current_iteration": 3,
        "design_loop_active": True,
        "design_iteration": 0,
        "design_preview_enabled": True,
        "auto_design_enabled": True,
        "screenshot_url": "http://example.com",
        "current_feedback": [
            Feedback(agent_name="ux_designer", score=5.0, strengths=["Good"], issues=[], suggestions=[]),
            Feedback(agent_name="visual_designer", score=5.0, strengths=["Good"], issues=[], suggestions=[])
        ],
        "design_changes_pending": False,
        "design_changes_applied": False,
        "resume": MagicMock(),
        "target_role": "Tester",
        "gemini_api_key": "dummy",
        "openai_api_key": "dummy", 
        "anthropic_api_key": "dummy",
        "css_output_path": str(session_dir / "styles.css")
    }

    # Context managers for mocks
    with patch("src.workflow.nodes.design_applier.ScreenshotService") as MockService, \
         patch("src.workflow.nodes.design_applier._generate_css", new_callable=AsyncMock) as mock_gen_css, \
         patch("src.workflow.nodes.design_applier.CSSService") as MockCSSService:
        
        # Mock ScreenshotService
        mock_instance = MockService.return_value
        mock_instance.capture = AsyncMock(return_value=Path("/tmp/dummy.png"))
        
        # Mock CSS generation return value
        mock_mod = MagicMock()
        mock_mod.css_content = "body { color: red; }"
        mock_mod.validation_passed = True
        mock_mod.target_file = Path("styles/resume.css")
        mock_gen_css.return_value = mock_mod
        
        # Mock CSSService
        mock_css_instance = MockCSSService.return_value
        mock_css_instance.write_with_backup.return_value = (None, mock_mod)

        # Run node
        result = await design_applier_node(state)
        
        # Verification
        
        # 1. Check iteration increment (0 -> 1)
        assert result.get("design_iteration") == 1, f"Design iteration expected 1, got {result.get('design_iteration')}"
        
        # 2. Check folder creation
        expected_dir = session_dir / "design_iter1"
        assert expected_dir.exists(), f"Directory {expected_dir} should be created"
        
        # 3. Verify design flags (Fix verification)
        # Should be True if bug is fixed (auto-design proceeds even if preview fails/is mocked)
        assert result.get("design_changes_applied") is True, f"design_changes_applied should be True, got {result.get('design_changes_applied')}"
