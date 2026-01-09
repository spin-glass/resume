"""Unit tests for data models."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.models import ActionType, Severity, SessionStatus
from src.models.feedback import Feedback, Issue, Resume
from src.models.portfolio import PortfolioItem
from src.models.session import ReviewSession


class TestIssue:
    """Tests for Issue model."""

    def test_valid_issue(self):
        """Test creating valid issue."""
        issue = Issue(
            description="Missing technical details",
            action_type=ActionType.ADD_CONTENT,
            location="Experience section",
            severity=Severity.HIGH,
        )

        assert issue.description == "Missing technical details"
        assert issue.action_type == ActionType.ADD_CONTENT
        assert issue.severity == Severity.HIGH
        assert issue.resolution is None

    def test_issue_without_location(self):
        """Test issue can be created without location."""
        issue = Issue(
            description="General improvement needed",
            action_type=ActionType.EMPHASIZE,
            severity=Severity.MEDIUM,
        )

        assert issue.location is None


class TestFeedback:
    """Tests for Feedback model."""

    def test_valid_feedback(self):
        """Test creating valid feedback."""
        issue = Issue(
            description="Test issue",
            action_type=ActionType.QUANTIFY,
            severity=Severity.MEDIUM,
        )

        feedback = Feedback(
            agent_name="recruiter",
            score=8.5,
            strengths=["Strong experience"],
            issues=[issue],
            suggestions=["Add metrics"],
        )

        assert feedback.agent_name == "recruiter"
        assert feedback.score == 8.5
        assert len(feedback.strengths) == 1
        assert len(feedback.issues) == 1
        assert len(feedback.suggestions) == 1

    def test_score_validation_range(self):
        """Test score must be 1-10."""
        # Valid scores
        Feedback(agent_name="test", score=1.0, strengths=["test"], issues=[], suggestions=[])
        Feedback(agent_name="test", score=10.0, strengths=["test"], issues=[], suggestions=[])

        # Invalid scores
        with pytest.raises(ValidationError):
            Feedback(agent_name="test", score=0.9, strengths=["test"], issues=[], suggestions=[])

        with pytest.raises(ValidationError):
            Feedback(agent_name="test", score=10.1, strengths=["test"], issues=[], suggestions=[])

    def test_feedback_requires_content(self):
        """Test feedback must have at least one strength or issue."""
        # Valid: has strength
        Feedback(agent_name="test", score=8.0, strengths=["Good"], issues=[], suggestions=[])

        # Valid: has issue
        issue = Issue(
            description="Problem",
            action_type=ActionType.ADD_CONTENT,
            severity=Severity.HIGH,
        )
        Feedback(agent_name="test", score=8.0, strengths=[], issues=[issue], suggestions=[])

        # Invalid: no strength or issue
        with pytest.raises(ValidationError):
            Feedback(agent_name="test", score=8.0, strengths=[], issues=[], suggestions=[])

    def test_timestamp_auto_generated(self):
        """Test timestamp is automatically generated."""
        feedback = Feedback(
            agent_name="test",
            score=8.0,
            strengths=["test"],
            issues=[],
            suggestions=[],
        )

        assert isinstance(feedback.timestamp, datetime)
        assert feedback.timestamp <= datetime.now()


class TestPortfolioItem:
    """Tests for PortfolioItem model."""

    def test_valid_portfolio_item(self):
        """Test creating valid portfolio item."""
        item = PortfolioItem(
            repository_name="langgraph-multi-agent",
            skills=["LangGraph", "Multi-agent systems"],
            description="Multi-agent system demo",
            github_url="https://github.com/spin-glass/langgraph-multi-agent",
            demo_url="https://langgraph-multi-agent.vercel.app",
            priority=1,
        )

        assert item.repository_name == "langgraph-multi-agent"
        assert len(item.skills) == 2
        assert item.priority == 1

    def test_repository_naming_pattern(self):
        """Test repository name must follow {technology}-{type} pattern."""
        # Valid patterns
        PortfolioItem(
            repository_name="python-api",
            skills=["Python"],
            description="Test",
            github_url="https://github.com/user/python-api",
            priority=1,
        )

        PortfolioItem(
            repository_name="langgraph-multi-agent",
            skills=["LangGraph"],
            description="Test",
            github_url="https://github.com/user/langgraph-multi-agent",
            priority=1,
        )

        # Invalid patterns (no hyphen)
        with pytest.raises(ValidationError):
            PortfolioItem(
                repository_name="pythonapi",
                skills=["Python"],
                description="Test",
                github_url="https://github.com/user/pythonapi",
                priority=1,
            )

        # Invalid patterns (uppercase)
        with pytest.raises(ValidationError):
            PortfolioItem(
                repository_name="Python-API",
                skills=["Python"],
                description="Test",
                github_url="https://github.com/user/Python-API",
                priority=1,
            )

    def test_github_url_pattern(self):
        """Test GitHub URL must follow pattern."""
        # Valid
        PortfolioItem(
            repository_name="test-repo",
            skills=["Test"],
            description="Test",
            github_url="https://github.com/username/test-repo",
            priority=1,
        )

        # Invalid (not HTTPS)
        with pytest.raises(ValidationError):
            PortfolioItem(
                repository_name="test-repo",
                skills=["Test"],
                description="Test",
                github_url="http://github.com/username/test-repo",
                priority=1,
            )

    def test_generate_github_url(self):
        """Test GitHub URL generation."""
        url = PortfolioItem.generate_github_url("spin-glass", "test-repo")
        assert url == "https://github.com/spin-glass/test-repo"

    def test_generate_demo_url(self):
        """Test demo URL generation."""
        vercel_url = PortfolioItem.generate_demo_url("test-app", "vercel")
        assert vercel_url == "https://test-app.vercel.app"

        netlify_url = PortfolioItem.generate_demo_url("test-app", "netlify")
        assert netlify_url == "https://test-app.netlify.app"

        with pytest.raises(ValueError):
            PortfolioItem.generate_demo_url("test-app", "invalid")


class TestResume:
    """Tests for Resume model."""

    @pytest.fixture
    def temp_qmd_file(self):
        """Create temporary QMD file."""
        content = """---
title: "Test Resume"
---

# Content
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.qmd', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        yield temp_path

        if temp_path.exists():
            temp_path.unlink()

    def test_valid_resume(self, temp_qmd_file):
        """Test creating valid resume."""
        resume = Resume(
            file_path=temp_qmd_file,
            yaml_frontmatter={"title": "Test"},
            content="# Content",
            full_text="---\ntitle: Test\n---\n# Content",
        )

        assert resume.file_path == temp_qmd_file
        assert resume.yaml_frontmatter["title"] == "Test"

    def test_in_memory_resume(self):
        """Test in-memory resume can be created without file existing."""
        # In-memory resume is allowed (for revision workflow)
        resume = Resume(
            file_path=Path("/nonexistent/file.qmd"),
            yaml_frontmatter={"title": "Test"},
            content="# Content",
            full_text="---\ntitle: Test\n---\n# Content",
        )
        assert resume.file_path == Path("/nonexistent/file.qmd")

    def test_from_file_validates_existence(self, temp_qmd_file):
        """Test from_file validates file exists."""
        # Valid file
        resume = Resume.from_file(temp_qmd_file)
        assert resume.file_path == temp_qmd_file

        # Non-existent file
        with pytest.raises(FileNotFoundError):
            Resume.from_file(Path("/nonexistent/file.qmd"))

    def test_must_be_qmd_extension(self, temp_qmd_file):
        """Test file must have .qmd extension."""
        # Valid .qmd
        Resume(
            file_path=temp_qmd_file,
            yaml_frontmatter={},
            content="",
            full_text="",
        )

        # Invalid extension
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
            md_path = Path(f.name)

        try:
            with pytest.raises(ValidationError):
                Resume(
                    file_path=md_path,
                    yaml_frontmatter={},
                    content="",
                    full_text="",
                )
        finally:
            md_path.unlink()


class TestReviewSession:
    """Tests for ReviewSession model."""

    @pytest.fixture
    def sample_resume(self):
        """Create sample resume for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.qmd', delete=False) as f:
            f.write("---\ntitle: Test\n---\n# Content")
            temp_path = Path(f.name)

        resume = Resume(
            file_path=temp_path,
            yaml_frontmatter={"title": "Test"},
            content="# Content",
            full_text="---\ntitle: Test\n---\n# Content",
        )

        yield resume

        temp_path.unlink()

    def test_valid_session(self, sample_resume):
        """Test creating valid review session."""
        session = ReviewSession(
            resume=sample_resume,
            target_role="Software Engineer",
            score_threshold=8.0,
            max_iterations=3,
        )

        assert session.target_role == "Software Engineer"
        assert session.score_threshold == 8.0
        assert session.max_iterations == 3
        assert session.current_iteration == 0
        assert session.status == SessionStatus.INITIALIZED

    def test_threshold_validation(self, sample_resume):
        """Test score threshold must be 1-10."""
        # Valid
        ReviewSession(resume=sample_resume, score_threshold=1.0)
        ReviewSession(resume=sample_resume, score_threshold=10.0)

        # Invalid
        with pytest.raises(ValidationError):
            ReviewSession(resume=sample_resume, score_threshold=0.5)

        with pytest.raises(ValidationError):
            ReviewSession(resume=sample_resume, score_threshold=10.5)

    def test_max_iterations_validation(self, sample_resume):
        """Test max iterations must be >= 1."""
        # Valid
        ReviewSession(resume=sample_resume, max_iterations=1)
        ReviewSession(resume=sample_resume, max_iterations=5)

        # Invalid
        with pytest.raises(ValidationError):
            ReviewSession(resume=sample_resume, max_iterations=0)

    def test_should_continue_iteration(self, sample_resume):
        """Test iteration continuation logic."""
        session = ReviewSession(
            resume=sample_resume,
            score_threshold=8.0,
            max_iterations=3,
        )

        # No score yet
        assert session.should_continue_iteration() is True

        # Below threshold, under max iterations
        session.final_score = 7.0
        session.current_iteration = 1
        assert session.should_continue_iteration() is True

        # Met threshold
        session.final_score = 8.0
        assert session.should_continue_iteration() is False

        # Exceeded threshold
        session.final_score = 9.0
        assert session.should_continue_iteration() is False

        # Below threshold but reached max iterations
        session.final_score = 7.0
        session.current_iteration = 3
        assert session.should_continue_iteration() is False

    def test_add_portfolio_suggestion_deduplication(self, sample_resume):
        """Test portfolio suggestions are deduplicated."""
        session = ReviewSession(resume=sample_resume)

        item1 = PortfolioItem(
            repository_name="test-repo",
            skills=["Python"],
            description="Test",
            github_url="https://github.com/user/test-repo",
            priority=1,
        )

        item2 = PortfolioItem(
            repository_name="test-repo",  # Same name
            skills=["JavaScript"],
            description="Different",
            github_url="https://github.com/user/test-repo",
            priority=2,
        )

        session.add_portfolio_suggestion(item1)
        session.add_portfolio_suggestion(item2)  # Should be skipped

        assert len(session.portfolio_suggestions) == 1
        assert session.portfolio_suggestions[0].skills == ["Python"]
