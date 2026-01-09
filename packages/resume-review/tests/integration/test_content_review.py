"""Integration tests for content review cycle."""

import os
from pathlib import Path

import pytest

from src.models.feedback import Resume
from src.models.session import ReviewSession
from src.workflow import ReviewWorkflow
from src.services.qmd_parser import QMDParser

# Skip if no API key available
pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
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
def test_complete_content_review_cycle(sample_resume_path, api_key):
    """
    Test T026: Integration test for complete content review cycle.

    Load QMD → evaluate → revise → save
    """
    # Load resume
    parser = QMDParser()
    resume = parser.load_resume(sample_resume_path)

    assert resume.file_path == sample_resume_path
    assert resume.content
    assert resume.yaml_frontmatter

    # Create session
    session = ReviewSession(
        resume=resume,
        target_role="LLM/Multi-Agent Engineer",
        score_threshold=7.0,  # Lower threshold for test
        max_iterations=1,  # Single iteration for faster test
        dry_run=False,
    )

    # Run workflow
    workflow = ReviewWorkflow(api_key)
    result_session = workflow.run_review(session)

    # Verify session completed
    assert result_session.status.value in ["completed", "failed"]

    # Verify feedback was collected
    assert len(result_session.feedback_history) > 0
    assert len(result_session.feedback_history[0]) == 3  # 3 agents

    # Verify scores were calculated
    assert result_session.final_score is not None
    assert 1.0 <= result_session.final_score <= 10.0

    # Verify feedback from each agent
    feedback_list = result_session.feedback_history[0]
    agent_names = {f.agent_name for f in feedback_list}
    assert "recruiter" in agent_names
    assert "technical_writer" in agent_names
    assert "copywriter" in agent_names

    # Each feedback should have required fields
    for feedback in feedback_list:
        assert 1.0 <= feedback.score <= 10.0
        assert feedback.strengths or feedback.issues  # At least one
        assert feedback.timestamp

    # Save to temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.qmd', delete=False) as f:
        temp_path = Path(f.name)

    try:
        parser.save_resume(result_session.resume, temp_path)
        assert temp_path.exists()

        # Verify saved file can be reloaded
        reloaded = parser.load_resume(temp_path)
        assert reloaded.yaml_frontmatter == resume.yaml_frontmatter
    finally:
        if temp_path.exists():
            temp_path.unlink()


@pytest.mark.integration
def test_iteration_loop(sample_resume_path, api_key):
    """
    Test T027: Integration test for iteration loop.

    Verify stops at threshold or max iterations.
    """
    # Load resume
    parser = QMDParser()
    resume = parser.load_resume(sample_resume_path)

    # Create session with max 2 iterations
    session = ReviewSession(
        resume=resume,
        target_role="LLM/Multi-Agent Engineer",
        score_threshold=9.5,  # High threshold to force iterations
        max_iterations=2,
        dry_run=False,
    )

    # Run workflow
    workflow = ReviewWorkflow(api_key)
    result_session = workflow.run_review(session)

    # Verify iteration behavior
    assert result_session.current_iteration <= result_session.max_iterations

    # Either met threshold OR reached max iterations
    if result_session.final_score >= result_session.score_threshold:
        # Met threshold - could be any iteration count
        assert result_session.current_iteration >= 0
    else:
        # Didn't meet threshold - should have used all iterations
        assert result_session.current_iteration == result_session.max_iterations

    # Verify feedback history matches iterations
    assert len(result_session.feedback_history) <= result_session.max_iterations


@pytest.mark.integration
def test_yaml_preservation(sample_resume_path, api_key):
    """
    Test T028: Integration test for YAML preservation.

    Verify frontmatter unchanged after revision.
    """
    # Load original resume
    parser = QMDParser()
    original_resume = parser.load_resume(sample_resume_path)
    original_yaml = original_resume.yaml_frontmatter.copy()

    # Create session
    session = ReviewSession(
        resume=original_resume,
        target_role="LLM/Multi-Agent Engineer",
        score_threshold=8.0,
        max_iterations=1,
        dry_run=False,
    )

    # Run workflow
    workflow = ReviewWorkflow(api_key)
    result_session = workflow.run_review(session)

    # Verify YAML frontmatter is preserved
    assert result_session.resume.yaml_frontmatter == original_yaml

    # Verify keys match
    assert set(result_session.resume.yaml_frontmatter.keys()) == set(original_yaml.keys())

    # Verify values match for each key
    for key in original_yaml:
        assert result_session.resume.yaml_frontmatter[key] == original_yaml[key]

    # Save and reload to verify persistence
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.qmd', delete=False) as f:
        temp_path = Path(f.name)

    try:
        parser.save_resume(result_session.resume, temp_path)
        reloaded = parser.load_resume(temp_path)

        # Verify YAML still matches after save/reload
        assert reloaded.yaml_frontmatter == original_yaml
    finally:
        if temp_path.exists():
            temp_path.unlink()


@pytest.mark.integration
def test_dry_run_mode(sample_resume_path, api_key):
    """
    Test dry-run mode doesn't modify content.
    """
    # Load original resume
    parser = QMDParser()
    original_resume = parser.load_resume(sample_resume_path)
    original_content = original_resume.content

    # Create session with dry-run
    session = ReviewSession(
        resume=original_resume,
        target_role="LLM/Multi-Agent Engineer",
        score_threshold=8.0,
        max_iterations=1,
        dry_run=True,  # Dry-run mode
    )

    # Run workflow
    workflow = ReviewWorkflow(api_key)
    result_session = workflow.run_review(session)

    # Verify content unchanged in dry-run
    assert result_session.resume.content == original_content

    # Verify feedback was still generated
    assert len(result_session.feedback_history) > 0
    assert result_session.final_score is not None

    # Verify revisions are logged but marked as dry-run
    for revision in result_session.applied_revisions:
        assert "[DRY RUN]" in revision


@pytest.mark.integration
def test_score_integration(sample_resume_path, api_key):
    """
    Test that integrated score is calculated correctly.
    """
    # Load resume
    parser = QMDParser()
    resume = parser.load_resume(sample_resume_path)

    # Create session
    session = ReviewSession(
        resume=resume,
        target_role="LLM/Multi-Agent Engineer",
        score_threshold=7.0,
        max_iterations=1,
        dry_run=True,
    )

    # Run workflow
    workflow = ReviewWorkflow(api_key)
    result_session = workflow.run_review(session)

    # Verify integrated score
    assert result_session.final_score is not None

    # Manual calculation to verify
    from src.workflow.scoring import calculate_integrated_score

    feedback_list = result_session.feedback_history[0]
    manual_score = calculate_integrated_score(feedback_list)

    # Should match (allowing small floating point differences)
    assert abs(result_session.final_score - manual_score) < 0.01

    # Verify weighted average is between min and max individual scores
    individual_scores = [f.score for f in feedback_list]
    assert min(individual_scores) <= result_session.final_score <= max(individual_scores)
