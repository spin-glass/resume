"""Unit tests for JobPosting and PersonalizationResult models (T078)."""

import pytest
from pydantic import ValidationError
from src.models.job_posting import JobPosting, PersonalizationResult, SkillMatch

def test_job_posting_validation_valid():
    """Test valid JobPosting creation."""
    job = JobPosting(
        title="Software Engineer",
        raw_text="Full text content checking validation length",
        source="test.md",
        required_skills=["Python", "  git  ", ""],  # Testing validator cleanup
        responsibilities=["Coding"]
    )
    assert job.title == "Software Engineer"
    assert "Python" in job.required_skills
    assert "git" in job.required_skills
    assert "  git  " not in job.required_skills
    assert "" not in job.required_skills
    assert len(job.required_skills) == 2

def test_job_posting_validation_missing_fields():
    """Test validation when required content is missing."""
    with pytest.raises(ValidationError):
        # Missing title
        JobPosting(raw_text="Long enough text", source="file")
        
    with pytest.raises(ValidationError):
        # Missing raw_text
        JobPosting(title="Title", source="file")
        
    with pytest.raises(ValidationError):
        # Valid fields but empty lists (T009 check: ensure at least one list is non-empty)
        JobPosting(
            title="Title",
            raw_text="Long enough text content here",
            source="file",
            required_skills=[],
            preferred_skills=[],
            responsibilities=[]
        )

def test_job_posting_helper_methods():
    """Test get_all_skills and get_skill_count."""
    job = JobPosting(
        title="Dev",
        raw_text="Long enough text content to pass validation",
        source="s",
        required_skills=["Python", "Go"],
        preferred_skills=["Docker"]
    )
    all_skills = job.get_all_skills()
    assert len(all_skills) == 3
    assert set(all_skills) == {"Python", "Go", "Docker"}
    
    counts = job.get_skill_count()
    assert counts["required"] == 2
    assert counts["preferred"] == 1
    assert counts["total"] == 3

def test_personalization_result_score_calculation():
    """Test match_score calculation logic (T013)."""
    # Case 1: Mixed match
    result = PersonalizationResult(
        required_match_score=100.0,
        preferred_match_score=0.0,
        matched_required_skills=[], matched_preferred_skills=[],
        missing_required_skills=[], missing_preferred_skills=[],
        emphasis_suggestions=[], keyword_additions=[]
    )
    # Formula: required*0.7 + preferred*0.3
    # 100*0.7 + 0*0.3 = 70.0
    assert result.match_score == 70.0
    assert result.match_level == "Good"  # 60-79

    # Case 2: Perfect match
    result_perfect = PersonalizationResult(
        required_match_score=100.0,
        preferred_match_score=100.0,
        matched_required_skills=[], matched_preferred_skills=[],
        missing_required_skills=[], missing_preferred_skills=[],
        emphasis_suggestions=[], keyword_additions=[]
    )
    assert result_perfect.match_score == 100.0
    assert result_perfect.match_level == "Excellent"  # 80-100

    # Case 3: Weak match
    result_weak = PersonalizationResult(
        required_match_score=10.0,
        preferred_match_score=10.0,
        matched_required_skills=[], matched_preferred_skills=[],
        missing_required_skills=[], missing_preferred_skills=[],
        emphasis_suggestions=[], keyword_additions=[]
    )
    assert result_weak.match_score == 10.0
    assert result_weak.match_level == "Weak"  # 0-39

def test_critical_gaps():
    """Test has_critical_gaps property (T015)."""
    result = PersonalizationResult(
        required_match_score=50.0,
        preferred_match_score=50.0,
        matched_required_skills=[], matched_preferred_skills=[],
        missing_required_skills=["Python"], # Critical gap
        missing_preferred_skills=[],
        emphasis_suggestions=[], keyword_additions=[]
    )
    assert result.has_critical_gaps is True

    result_no_gaps = PersonalizationResult(
        required_match_score=50.0,
        preferred_match_score=50.0,
        matched_required_skills=[], matched_preferred_skills=[],
        missing_required_skills=[], 
        missing_preferred_skills=["Aws"],
        emphasis_suggestions=[], keyword_additions=[]
    )
    assert result_no_gaps.has_critical_gaps is False
