"""Unit tests for CSSGeneratorAgent - CSS generation from design feedback.

Tests for T016: Unit test for CSSGeneratorAgent CSS generation.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.agents.css_generator import CSSGeneratorAgent
from src.models import ActionType, Severity
from src.models.design import CSSModification, DesignIssueType
from src.models.feedback import Feedback, Issue


class TestCSSGeneratorAgentInit:
    """Test cases for CSSGeneratorAgent initialization - T021."""

    def test_init_with_llm_client(self):
        """Agent should initialize with LLM client."""
        mock_client = Mock()
        agent = CSSGeneratorAgent(llm_client=mock_client)

        assert agent.llm_client == mock_client
        assert agent.agent_name == "css_generator"


class TestCSSGeneratorAgentPrompt:
    """Test cases for CSSGeneratorAgent.get_system_prompt() - T021."""

    def test_get_system_prompt_returns_css_prompt(self):
        """get_system_prompt should return CSS generation prompt."""
        mock_client = Mock()
        agent = CSSGeneratorAgent(llm_client=mock_client)

        prompt = agent.get_system_prompt("LLM Engineer")

        assert isinstance(prompt, str)
        assert "CSS" in prompt
        assert "custom properties" in prompt.lower() or "--" in prompt


class TestCSSGeneratorAgentClassifyIssue:
    """Test cases for CSSGeneratorAgent._classify_issue() - T023."""

    @pytest.fixture
    def agent(self):
        """Create agent with mock LLM client."""
        mock_client = Mock()
        return CSSGeneratorAgent(llm_client=mock_client)

    def test_classify_spacing_issue(self, agent):
        """Spacing keywords should classify as SPACING."""
        descriptions = [
            "Section spacing is too cramped",
            "Need more margin between items",
            "Padding should be increased",
            "Gap between sections is small",
        ]
        for desc in descriptions:
            result = agent._classify_issue(desc)
            assert result == DesignIssueType.SPACING, f"Failed for: {desc}"

    def test_classify_typography_issue(self, agent):
        """Typography keywords should classify as TYPOGRAPHY."""
        descriptions = [
            "Font size is too small",
            "Line height needs improvement",
            "Typography hierarchy is weak",
            "Text is not readable enough",
        ]
        for desc in descriptions:
            result = agent._classify_issue(desc)
            assert result == DesignIssueType.TYPOGRAPHY, f"Failed for: {desc}"

    def test_classify_hierarchy_issue(self, agent):
        """Hierarchy keywords should classify as HIERARCHY."""
        descriptions = [
            "Visual hierarchy is unclear",
            "Headings lack emphasis",
            "Content priority is not clear",
            "Section structure needs improvement",
        ]
        for desc in descriptions:
            result = agent._classify_issue(desc)
            assert result == DesignIssueType.HIERARCHY, f"Failed for: {desc}"

    def test_classify_color_issue(self, agent):
        """Color keywords should classify as COLOR."""
        descriptions = [
            "Color contrast is poor",
            "Accessibility issues with text color",
            "WCAG compliance needed",
        ]
        for desc in descriptions:
            result = agent._classify_issue(desc)
            assert result == DesignIssueType.COLOR, f"Failed for: {desc}"

    def test_classify_layout_issue(self, agent):
        """Layout keywords should classify as LAYOUT."""
        descriptions = [
            "Layout alignment is off",
            "Balance between sections needs work",
            "Content arrangement could improve",
        ]
        for desc in descriptions:
            result = agent._classify_issue(desc)
            assert result == DesignIssueType.LAYOUT, f"Failed for: {desc}"


class TestCSSGeneratorAgentFormatIssues:
    """Test cases for CSSGeneratorAgent._format_issues_for_prompt() - T022."""

    @pytest.fixture
    def agent(self):
        """Create agent with mock LLM client."""
        mock_client = Mock()
        return CSSGeneratorAgent(llm_client=mock_client)

    @pytest.fixture
    def sample_feedback(self):
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
                    Issue(
                        description="Spacing between sections cramped",
                        action_type=ActionType.RESTRUCTURE,
                        severity=Severity.MEDIUM,
                        location="Section gaps",
                    ),
                ],
                suggestions=["Increase font sizes"],
            ),
            Feedback(
                agent_name="ux_designer",
                score=7.0,
                strengths=["Clear structure"],
                issues=[
                    Issue(
                        description="Skills section should be more prominent",
                        action_type=ActionType.EMPHASIZE,
                        severity=Severity.HIGH,
                        location="Skills section",
                    ),
                ],
                suggestions=["Emphasize skills"],
            ),
        ]

    def test_format_includes_agent_name(self, agent, sample_feedback):
        """Formatted output should include agent names."""
        result = agent._format_issues_for_prompt(sample_feedback)

        assert "visual_designer" in result
        assert "ux_designer" in result

    def test_format_includes_issue_descriptions(self, agent, sample_feedback):
        """Formatted output should include issue descriptions."""
        result = agent._format_issues_for_prompt(sample_feedback)

        assert "Heading font size too small" in result
        assert "Spacing between sections cramped" in result
        assert "Skills section should be more prominent" in result

    def test_format_includes_severity(self, agent, sample_feedback):
        """Formatted output should include severity levels."""
        result = agent._format_issues_for_prompt(sample_feedback)

        assert "high" in result.lower() or "HIGH" in result
        assert "medium" in result.lower() or "MEDIUM" in result

    def test_format_classifies_issue_types(self, agent, sample_feedback):
        """Formatted output should include classified issue types."""
        result = agent._format_issues_for_prompt(sample_feedback)

        # Check that issue types are mentioned
        assert any(
            issue_type.value.upper() in result
            for issue_type in DesignIssueType
        )


class TestCSSGeneratorAgentGenerateCSS:
    """Test cases for CSSGeneratorAgent.generate_css() - T024."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client that returns CSS."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = """
Based on the design feedback, here are the CSS modifications:

```css
/* Improve heading hierarchy */
:root {
  --h2-size: 1.4rem;
  --section-gap: 2rem;
}

h2 {
  font-size: var(--h2-size);
  font-weight: 600;
}

.section {
  margin-bottom: var(--section-gap);
}
```
"""
        mock_client.generate = AsyncMock(return_value=mock_response)
        return mock_client

    @pytest.fixture
    def sample_feedback(self):
        """Create sample design feedback."""
        return [
            Feedback(
                agent_name="visual_designer",
                score=6.5,
                strengths=["Basic structure"],
                issues=[
                    Issue(
                        description="Heading font size too small",
                        action_type=ActionType.EMPHASIZE,
                        severity=Severity.HIGH,
                        location="All headings",
                    ),
                ],
                suggestions=[],
            ),
        ]

    @pytest.mark.asyncio
    async def test_generate_css_returns_css_modification(
        self, mock_llm_client, sample_feedback
    ):
        """generate_css should return CSSModification model."""
        agent = CSSGeneratorAgent(llm_client=mock_llm_client)

        result = await agent.generate_css(sample_feedback)

        assert isinstance(result, CSSModification)
        assert result.css_content is not None
        assert len(result.css_content) > 0

    @pytest.mark.asyncio
    async def test_generate_css_extracts_css_from_code_block(
        self, mock_llm_client, sample_feedback
    ):
        """generate_css should extract CSS from markdown code blocks."""
        agent = CSSGeneratorAgent(llm_client=mock_llm_client)

        result = await agent.generate_css(sample_feedback)

        # Should not include markdown code fence
        assert "```" not in result.css_content
        # Should include actual CSS content
        assert ":root" in result.css_content or "h2" in result.css_content

    @pytest.mark.asyncio
    async def test_generate_css_validates_output(
        self, mock_llm_client, sample_feedback
    ):
        """generate_css should validate generated CSS."""
        agent = CSSGeneratorAgent(llm_client=mock_llm_client)

        result = await agent.generate_css(sample_feedback)

        # validation_passed should be True for valid CSS
        assert result.validation_passed is True
        assert len(result.validation_errors) == 0

    @pytest.mark.asyncio
    async def test_generate_css_includes_issue_types(
        self, mock_llm_client, sample_feedback
    ):
        """generate_css should include classified issue types."""
        agent = CSSGeneratorAgent(llm_client=mock_llm_client)

        result = await agent.generate_css(sample_feedback)

        assert len(result.issue_types) > 0
        assert all(isinstance(t, DesignIssueType) for t in result.issue_types)

    @pytest.mark.asyncio
    async def test_generate_css_extracts_changes(
        self, mock_llm_client, sample_feedback
    ):
        """generate_css should extract human-readable changes."""
        agent = CSSGeneratorAgent(llm_client=mock_llm_client)

        result = await agent.generate_css(sample_feedback)

        assert len(result.changes) > 0

    @pytest.mark.asyncio
    async def test_generate_css_with_current_css(
        self, mock_llm_client, sample_feedback
    ):
        """generate_css should accept current CSS as context."""
        agent = CSSGeneratorAgent(llm_client=mock_llm_client)
        current_css = ":root { --primary: blue; }"

        await agent.generate_css(
            sample_feedback, current_css=current_css
        )

        # Verify LLM was called with current CSS in prompt
        mock_llm_client.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_css_handles_invalid_response(self, sample_feedback):
        """generate_css should handle LLM returning invalid CSS."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = "Here is some text without any CSS code blocks."
        mock_client.generate = AsyncMock(return_value=mock_response)

        agent = CSSGeneratorAgent(llm_client=mock_client)
        result = await agent.generate_css(sample_feedback)

        # Should return None on failure
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_css_handles_llm_error(self, sample_feedback):
        """generate_css should handle LLM errors gracefully."""
        mock_client = Mock()
        mock_client.generate = AsyncMock(side_effect=Exception("LLM error"))

        agent = CSSGeneratorAgent(llm_client=mock_client)
        result = await agent.generate_css(sample_feedback)

        # Should return None on failure
        assert result is None


class TestCSSGeneratorAgentExtractCSS:
    """Test cases for CSS extraction from LLM responses."""

    @pytest.fixture
    def agent(self):
        """Create agent with mock LLM client."""
        mock_client = Mock()
        return CSSGeneratorAgent(llm_client=mock_client)

    def test_extract_css_from_css_code_block(self, agent):
        """Should extract CSS from ```css code blocks."""
        response = """
Here is the CSS:

```css
h2 { color: blue; }
```

That should fix the issue.
"""
        result = agent._extract_css_from_response(response)
        assert "h2 { color: blue; }" in result
        assert "```" not in result

    def test_extract_css_from_generic_code_block(self, agent):
        """Should extract CSS from generic ``` code blocks."""
        response = """
```
h2 { color: red; }
```
"""
        result = agent._extract_css_from_response(response)
        assert "h2 { color: red; }" in result

    def test_extract_css_raises_on_no_code_block(self, agent):
        """Should raise ValueError when no code block found."""
        response = "No CSS here, just plain text."

        with pytest.raises(ValueError) as exc_info:
            agent._extract_css_from_response(response)

        assert "No CSS code found" in str(exc_info.value)


class TestCSSGeneratorAgentExtractChanges:
    """Test cases for extracting changes from CSS."""

    @pytest.fixture
    def agent(self):
        """Create agent with mock LLM client."""
        mock_client = Mock()
        return CSSGeneratorAgent(llm_client=mock_client)

    def test_extract_changes_from_comments(self, agent):
        """Should extract changes from CSS comments."""
        css = """
/* Improve heading hierarchy */
h2 {
  font-size: 1.4rem;
}

/* Increase section spacing */
.section {
  margin-bottom: 2rem;
}
"""
        changes = agent._extract_changes_from_css(css)

        assert len(changes) >= 2
        assert any("heading" in c.lower() for c in changes)
        assert any("spacing" in c.lower() for c in changes)

    def test_extract_changes_fallback_for_no_comments(self, agent):
        """Should provide fallback changes when no comments."""
        css = """
:root {
  --color: blue;
  --spacing: 1rem;
}

h2 {
  color: var(--color);
}
"""
        changes = agent._extract_changes_from_css(css)

        # Should have at least one change description
        assert len(changes) >= 1
