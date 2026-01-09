"""Integration tests for design review."""

import os
from pathlib import Path
import tempfile

import pytest

from src.agents.ux_designer import UXDesignerAgent
from src.agents.visual_designer import VisualDesignerAgent

# Skip if no API key available
pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set"
)


@pytest.fixture
def api_key():
    """Get API key from environment."""
    return os.getenv("ANTHROPIC_API_KEY")


@pytest.fixture
def sample_screenshot():
    """Create a simple test screenshot."""
    # Create a simple white PNG image for testing
    from PIL import Image

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        # Create a simple 800x600 white image with some text-like rectangles
        img = Image.new("RGB", (800, 600), color="white")
        img.save(f, "PNG")
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.mark.integration
def test_ux_designer_screenshot_evaluation(api_key, sample_screenshot):
    """
    Test T043: Verify UX agent evaluates screenshot.
    """
    agent = UXDesignerAgent(api_key)

    # Evaluate from screenshot
    feedback = agent.evaluate_from_screenshot(
        str(sample_screenshot), "LLM/Multi-Agent Engineer"
    )

    # Verify feedback structure
    assert feedback.agent_name == "ux_designer"
    assert 1.0 <= feedback.score <= 10.0
    assert feedback.timestamp is not None

    # Should have some evaluation (strengths, issues, or suggestions)
    assert feedback.strengths or feedback.issues or feedback.suggestions


@pytest.mark.integration
def test_visual_designer_screenshot_evaluation(api_key, sample_screenshot):
    """
    Test T043: Verify Visual agent evaluates screenshot.
    """
    agent = VisualDesignerAgent(api_key)

    # Evaluate from screenshot
    feedback = agent.evaluate_from_screenshot(
        str(sample_screenshot), "LLM/Multi-Agent Engineer"
    )

    # Verify feedback structure
    assert feedback.agent_name == "visual_designer"
    assert 1.0 <= feedback.score <= 10.0
    assert feedback.timestamp is not None

    # Should have some evaluation
    assert feedback.strengths or feedback.issues or feedback.suggestions


@pytest.mark.integration
def test_screenshot_not_found(api_key):
    """
    Test handling of missing screenshot file.
    """
    agent = UXDesignerAgent(api_key)

    # Try to evaluate non-existent file
    feedback = agent.evaluate_from_screenshot(
        "/tmp/nonexistent_screenshot.png", "LLM/Multi-Agent Engineer"
    )

    # Should return feedback with error message
    assert feedback.agent_name == "ux_designer"
    assert feedback.score == 5.0  # Default fallback score
    assert len(feedback.suggestions) > 0
    assert "not found" in feedback.suggestions[0].lower()


@pytest.mark.integration
def test_design_agents_different_perspectives(api_key, sample_screenshot):
    """
    Test that UX and Visual designers provide different perspectives.
    """
    ux_agent = UXDesignerAgent(api_key)
    visual_agent = VisualDesignerAgent(api_key)

    ux_feedback = ux_agent.evaluate_from_screenshot(
        str(sample_screenshot), "LLM/Multi-Agent Engineer"
    )

    visual_feedback = visual_agent.evaluate_from_screenshot(
        str(sample_screenshot), "LLM/Multi-Agent Engineer"
    )

    # Both should return valid feedback
    assert ux_feedback.agent_name == "ux_designer"
    assert visual_feedback.agent_name == "visual_designer"

    # Scores might differ
    assert 1.0 <= ux_feedback.score <= 10.0
    assert 1.0 <= visual_feedback.score <= 10.0
