"""Integration tests for portfolio gap analysis."""

import os
from pathlib import Path

import pytest

from src.models import ActionType, Severity
from src.models.feedback import Feedback, Issue, Resume
from src.models.session import ReviewSession
from src.workflow import ReviewWorkflow

# Skip if no API key available
pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set"
)


@pytest.fixture
def sample_resume_path():
    """Get path to sample resume fixture."""
    return Path(__file__).parent.parent / "fixtures" / "sample-resume.qmd"


@pytest.fixture
def api_key():
    """Get API key from environment."""
    return os.getenv("ANTHROPIC_API_KEY")


@pytest.mark.integration
def test_portfolio_gap_detection(sample_resume_path, api_key):
    """
    Test T034: Integration test for portfolio gap detection.

    Verify skill gaps identified correctly.
    """
    from src.services.qmd_parser import QMDParser

    # Load resume
    parser = QMDParser()
    resume = parser.load_resume(sample_resume_path)

    # Create mock feedback with ADD_PORTFOLIO issues
    mock_feedback = Feedback(
        agent_name="recruiter",
        score=6.5,
        strengths=["Basic Python experience"],
        issues=[
            Issue(
                description="Missing LangGraph experience for 120万円+ positions",
                action_type=ActionType.ADD_PORTFOLIO,
                location="Skills section",
                severity=Severity.HIGH,
            ),
            Issue(
                description="No demonstration of multi-agent system architecture",
                action_type=ActionType.ADD_PORTFOLIO,
                location="Experience",
                severity=Severity.CRITICAL,
            ),
        ],
        suggestions=["Build a portfolio project using LangGraph"],
    )

    # Create session with the mock feedback
    session = ReviewSession(
        resume=resume,
        target_role="LLM/Multi-Agent Engineer",
        score_threshold=8.0,
        max_iterations=1,
        dry_run=True,
    )

    # Manually add feedback to history
    session.add_feedback([mock_feedback])

    # Run portfolio analysis
    workflow = ReviewWorkflow(api_key)
    result_session = workflow._portfolio_analysis(session)

    # Verify portfolio suggestions were generated
    assert len(result_session.portfolio_suggestions) > 0
    assert len(result_session.portfolio_suggestions) <= 2  # Max 2 issues

    # Verify portfolio items have required structure
    for item in result_session.portfolio_suggestions:
        assert item.repository_name
        assert "-" in item.repository_name  # Must have hyphen
        assert item.repository_name.islower()  # Must be lowercase
        assert len(item.skills) > 0
        assert item.description
        assert item.github_url.startswith("https://github.com/")
        assert item.priority >= 1


@pytest.mark.integration
def test_portfolio_naming_patterns(sample_resume_path, api_key):
    """
    Test T035: Integration test for portfolio naming.

    Verify URL patterns match SC-004.
    """
    from src.services.qmd_parser import QMDParser

    # Load resume
    parser = QMDParser()
    resume = parser.load_resume(sample_resume_path)

    # Create feedback with specific skill gap
    mock_feedback = Feedback(
        agent_name="recruiter",
        score=7.0,
        strengths=["Good foundation"],
        issues=[
            Issue(
                description="Missing LangGraph multi-agent orchestration experience",
                action_type=ActionType.ADD_PORTFOLIO,
                location="Skills",
                severity=Severity.HIGH,
            )
        ],
        suggestions=["Build LangGraph project"],
    )

    # Create session
    session = ReviewSession(
        resume=resume,
        target_role="LLM/Multi-Agent Engineer",
        score_threshold=8.0,
        max_iterations=1,
        dry_run=True,
    )
    session.add_feedback([mock_feedback])

    # Run portfolio analysis
    workflow = ReviewWorkflow(api_key)
    result_session = workflow._portfolio_analysis(session)

    # Verify at least one suggestion
    assert len(result_session.portfolio_suggestions) > 0

    # Verify naming patterns (SC-004)
    for item in result_session.portfolio_suggestions:
        # Repository name pattern: {technology}-{type}
        assert item.repository_name.count("-") >= 1
        assert item.repository_name == item.repository_name.lower()
        assert item.repository_name.replace("-", "").replace("_", "").isalnum()

        # GitHub URL pattern
        assert item.github_url == f"https://github.com/spin-glass/{item.repository_name}"

        # Demo URL pattern (if present)
        if item.demo_url:
            assert (
                item.demo_url == f"https://{item.repository_name}.vercel.app"
                or item.demo_url == f"https://{item.repository_name}.netlify.app"
            )


@pytest.mark.integration
def test_no_skill_gaps_no_suggestions(sample_resume_path, api_key):
    """
    Test that no portfolio suggestions are generated when no skill gaps exist.
    """
    from src.services.qmd_parser import QMDParser

    # Load resume
    parser = QMDParser()
    resume = parser.load_resume(sample_resume_path)

    # Create feedback with NO ADD_PORTFOLIO issues
    mock_feedback = Feedback(
        agent_name="recruiter",
        score=9.0,
        strengths=["Excellent experience", "All required skills present"],
        issues=[
            Issue(
                description="Could emphasize leadership more",
                action_type=ActionType.EMPHASIZE,
                location="Experience",
                severity=Severity.LOW,
            )
        ],
        suggestions=["Highlight team leadership"],
    )

    # Create session
    session = ReviewSession(
        resume=resume,
        target_role="LLM/Multi-Agent Engineer",
        score_threshold=8.0,
        max_iterations=1,
        dry_run=True,
    )
    session.add_feedback([mock_feedback])

    # Run portfolio analysis
    workflow = ReviewWorkflow(api_key)
    result_session = workflow._portfolio_analysis(session)

    # Should have zero portfolio suggestions
    assert len(result_session.portfolio_suggestions) == 0


@pytest.mark.integration
def test_portfolio_deduplication(sample_resume_path, api_key):
    """
    Test that duplicate portfolio suggestions are deduplicated.
    """
    from src.services.qmd_parser import QMDParser

    # Load resume
    parser = QMDParser()
    resume = parser.load_resume(sample_resume_path)

    # Create feedback with similar skill gaps (might generate same repo name)
    mock_feedback = Feedback(
        agent_name="recruiter",
        score=7.0,
        strengths=["Basic skills"],
        issues=[
            Issue(
                description="Missing LangGraph experience",
                action_type=ActionType.ADD_PORTFOLIO,
                severity=Severity.HIGH,
            ),
            Issue(
                description="No LangGraph projects demonstrated",
                action_type=ActionType.ADD_PORTFOLIO,
                severity=Severity.HIGH,
            ),
        ],
        suggestions=["Build LangGraph portfolio"],
    )

    # Create session
    session = ReviewSession(
        resume=resume,
        target_role="LLM/Multi-Agent Engineer",
        score_threshold=8.0,
        max_iterations=1,
        dry_run=True,
    )
    session.add_feedback([mock_feedback])

    # Run portfolio analysis
    workflow = ReviewWorkflow(api_key)
    result_session = workflow._portfolio_analysis(session)

    # Verify deduplication - repository names should be unique
    repo_names = [item.repository_name for item in result_session.portfolio_suggestions]
    assert len(repo_names) == len(set(repo_names))  # All unique
