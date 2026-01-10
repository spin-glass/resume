# Data Model: Job Personalization

**Feature**: Job Personalization
**Created**: 2026-01-09
**Status**: Design Phase

## Overview

This document defines the data models for job personalization, including job posting structure, personalization results, and state extensions. All models use Pydantic for validation and are designed to integrate seamlessly with the existing LangGraph workflow.

---

## Core Models

### JobPosting

**Purpose**: Structured representation of a job description extracted from a file or URL.

**Module**: `packages/resume-review/src/models/job_posting.py`

**Schema**:

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class JobPosting(BaseModel):
    """
    Structured job posting data extracted from job descriptions.

    This model stores parsed information from job postings in either
    file (text/Markdown) or URL format.
    """

    # Required fields
    title: str = Field(
        ...,
        description="Job title (e.g., 'Senior Backend Engineer')",
        min_length=1
    )

    required_skills: list[str] = Field(
        default_factory=list,
        description="Must-have skills, qualifications, or technologies"
    )

    raw_text: str = Field(
        ...,
        description="Original job description text (full content)",
        min_length=10
    )

    source: str = Field(
        ...,
        description="File path or URL where job posting was sourced"
    )

    # Optional fields (may not be present in all postings)
    company: Optional[str] = Field(
        None,
        description="Company name (if detected in posting)"
    )

    preferred_skills: list[str] = Field(
        default_factory=list,
        description="Nice-to-have skills or qualifications"
    )

    responsibilities: list[str] = Field(
        default_factory=list,
        description="Key job duties and responsibilities"
    )

    qualifications: list[str] = Field(
        default_factory=list,
        description="Education, experience, or certification requirements"
    )

    salary_range: Optional[str] = Field(
        None,
        description="Compensation information (if provided)"
    )

    contract_type: Optional[str] = Field(
        None,
        description="Employment type (e.g., 'Full-time', 'Contract', '業務委託')"
    )

    @field_validator("required_skills", "preferred_skills", "responsibilities", "qualifications")
    @classmethod
    def remove_empty_strings(cls, v: list[str]) -> list[str]:
        """Remove empty or whitespace-only strings from lists."""
        return [item.strip() for item in v if item and item.strip()]

    @field_validator("raw_text", "title")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace from text fields."""
        return v.strip()

    def model_post_init(self, __context) -> None:
        """Validate that at least some structured data was extracted."""
        if not self.required_skills and not self.responsibilities and not self.preferred_skills:
            raise ValueError(
                "JobPosting must contain at least one of: required_skills, "
                "responsibilities, or preferred_skills. The posting appears to be empty "
                "or parsing failed."
            )

    def get_all_skills(self) -> list[str]:
        """Return combined list of required and preferred skills (deduplicated)."""
        all_skills = set(self.required_skills) | set(self.preferred_skills)
        return sorted(all_skills)

    def get_skill_count(self) -> dict[str, int]:
        """Return count of required vs preferred skills."""
        return {
            "required": len(self.required_skills),
            "preferred": len(self.preferred_skills),
            "total": len(self.get_all_skills())
        }
```

**Validation Rules**:
1. `title` and `raw_text` cannot be empty
2. At least one of `required_skills`, `responsibilities`, or `preferred_skills` must be non-empty
3. All text fields are stripped of leading/trailing whitespace
4. List fields remove empty strings during validation

**Example**:

```python
job = JobPosting(
    title="Senior LangGraph Engineer",
    company="AI Startup Inc.",
    required_skills=[
        "Python 3.11+",
        "LangGraph or LangChain",
        "Multi-agent systems",
        "Async/await patterns"
    ],
    preferred_skills=[
        "Anthropic Claude API",
        "Gemini API",
        "React (for tools)",
        "Japanese language (N2+)"
    ],
    responsibilities=[
        "Design and implement multi-agent workflows",
        "Optimize LLM costs via model routing",
        "Build CLI tools for resume review"
    ],
    qualifications=[
        "5+ years Python experience",
        "Experience with LLM APIs",
        "Open source contributions"
    ],
    salary_range="110-140万円/月",
    contract_type="業務委託",
    raw_text="[Full job posting text...]",
    source="https://example.com/jobs/123"
)

print(job.get_skill_count())
# Output: {"required": 4, "preferred": 4, "total": 8}
```

---

### PersonalizationResult

**Purpose**: Results of matching a resume against a job posting, including match scores, skill gaps, and recommendations.

**Module**: `packages/resume-review/src/models/job_posting.py`

**Schema**:

```python
from pydantic import BaseModel, Field, computed_field
from typing import Optional

class SkillMatch(BaseModel):
    """Individual skill match with confidence."""

    skill: str = Field(
        ...,
        description="Skill name from job posting"
    )

    matched: bool = Field(
        ...,
        description="Whether skill was found in resume"
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Match confidence (0.0-1.0)"
    )

    explanation: Optional[str] = Field(
        None,
        description="Why skill matched (e.g., 'Resume mentions React projects')"
    )

class PersonalizationResult(BaseModel):
    """
    Results of personalized resume-job matching analysis.

    Contains match scores, skill gaps, and actionable recommendations
    for tailoring the resume to a specific job posting.
    """

    # Match scores (0-100 scale)
    required_match_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Match percentage for required skills (0-100)"
    )

    preferred_match_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Match percentage for preferred skills (0-100)"
    )

    # Matched skills
    matched_required_skills: list[SkillMatch] = Field(
        default_factory=list,
        description="Required skills found in resume"
    )

    matched_preferred_skills: list[SkillMatch] = Field(
        default_factory=list,
        description="Preferred skills found in resume"
    )

    # Missing skills
    missing_required_skills: list[str] = Field(
        default_factory=list,
        description="Required skills NOT found in resume (critical gaps)"
    )

    missing_preferred_skills: list[str] = Field(
        default_factory=list,
        description="Preferred skills NOT found in resume (nice-to-have gaps)"
    )

    # Recommendations
    emphasis_suggestions: list[str] = Field(
        default_factory=list,
        description="Recommendations for what to emphasize or reframe"
    )

    keyword_additions: list[str] = Field(
        default_factory=list,
        description="Keywords to naturally incorporate for ATS optimization"
    )

    @computed_field
    @property
    def match_score(self) -> float:
        """
        Overall match score (0-100) using weighted average.

        Formula: (required * 0.7) + (preferred * 0.3)
        Required skills are weighted more heavily as they're critical.
        """
        return (self.required_match_score * 0.7) + (self.preferred_match_score * 0.3)

    @computed_field
    @property
    def match_level(self) -> str:
        """
        Human-readable match level based on overall score.

        - Excellent: 80-100%
        - Good: 60-79%
        - Moderate: 40-59%
        - Weak: 0-39%
        """
        score = self.match_score
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Moderate"
        else:
            return "Weak"

    @computed_field
    @property
    def has_critical_gaps(self) -> bool:
        """Whether there are missing required skills (critical gaps)."""
        return len(self.missing_required_skills) > 0

    def get_match_summary(self) -> dict:
        """Return summary statistics for display."""
        return {
            "overall_score": round(self.match_score, 1),
            "match_level": self.match_level,
            "required_match": f"{len(self.matched_required_skills)}/{len(self.matched_required_skills) + len(self.missing_required_skills)}",
            "preferred_match": f"{len(self.matched_preferred_skills)}/{len(self.matched_preferred_skills) + len(self.missing_preferred_skills)}",
            "critical_gaps": len(self.missing_required_skills),
            "has_critical_gaps": self.has_critical_gaps
        }
```

**Calculation Logic**:
- **Overall Match Score**: Weighted average of required (70%) and preferred (30%) matches
- **Required Match Score**: `(matched_required / total_required) * 100`
- **Preferred Match Score**: `(matched_preferred / total_preferred) * 100`
- **Match Level**: Categorical label based on overall score thresholds

**Example**:

```python
result = PersonalizationResult(
    required_match_score=75.0,  # 3 of 4 required skills
    preferred_match_score=50.0,  # 2 of 4 preferred skills
    matched_required_skills=[
        SkillMatch(skill="Python", matched=True, confidence=1.0, explanation="Multiple Python projects"),
        SkillMatch(skill="LangGraph", matched=True, confidence=0.9, explanation="Resume review project uses LangGraph"),
        SkillMatch(skill="Multi-agent systems", matched=True, confidence=0.8, explanation="Built multi-agent workflow")
    ],
    missing_required_skills=["Async/await patterns"],
    matched_preferred_skills=[
        SkillMatch(skill="Claude API", matched=True, confidence=1.0),
        SkillMatch(skill="Japanese N2+", matched=True, confidence=0.7)
    ],
    missing_preferred_skills=["Gemini API", "React"],
    emphasis_suggestions=[
        "Highlight LangGraph experience in 職務経歴 section",
        "Add metrics for multi-agent project (e.g., '3 agents, 10min reviews')",
        "Emphasize async Python patterns in technical skills"
    ],
    keyword_additions=[
        "非同期処理 (async processing)",
        "LLMコスト最適化 (LLM cost optimization)"
    ]
)

print(result.match_score)  # 67.5 (75*0.7 + 50*0.3)
print(result.match_level)  # "Good"
print(result.get_match_summary())
# {
#   "overall_score": 67.5,
#   "match_level": "Good",
#   "required_match": "3/4",
#   "preferred_match": "2/4",
#   "critical_gaps": 1,
#   "has_critical_gaps": True
# }
```

---

## State Extensions

### ReviewState (Extended)

**Module**: `packages/resume-review/src/workflow/state.py`

**New Fields**:

```python
class ReviewState(TypedDict, total=False):
    # ... [all existing fields] ...

    # Job personalization fields (NEW)
    job_posting: Optional[JobPosting]
    """Parsed job posting data (if --job-posting or --job-url provided)."""

    personalization_result: Optional[PersonalizationResult]
    """Match score and personalization analysis results."""

    job_source_type: Optional[str]
    """Source type: 'file', 'url', or None (for logging/debugging)."""
```

**Integration Notes**:
- Fields are optional (backward compatibility)
- When `job_posting` is None, workflow behaves as before (standard review)
- When `job_posting` is present, personalization nodes execute
- `personalization_result` is populated after personalizer node runs

---

## Data Flow

### Standard Review (No Personalization)

```text
Input: resume.qmd, target_role
  ↓
State: {resume, target_role, job_posting: None, ...}
  ↓
Workflow: supervisor → aggregator → revisor → ...
  ↓
Output: Feedback (generic to target_role)
```

### Personalized Review

```text
Input: resume.qmd, job_posting_file/url, target_role
  ↓
Job Parser Node: Parse file/URL → JobPosting
  ↓
State: {resume, target_role, job_posting: JobPosting(...), ...}
  ↓
Supervisor Node: Pass job_posting to agents
  ↓
Agents: Generate feedback referencing job requirements
  ↓
Aggregator Node: Collect feedback
  ↓
Personalizer Node: Calculate match score → PersonalizationResult
  ↓
State: {personalization_result: PersonalizationResult(...), ...}
  ↓
Output: Feedback + match score + skill gaps + recommendations
```

---

## Relationships

```text
JobPosting (1)
    ↓ used by
PersonalizerAgent (1)
    ↓ produces
PersonalizationResult (1)
    ↓ stored in
ReviewState (1)
    ↓ flows through
LangGraph Workflow (1)
```

**Key Interactions**:
1. **JobPosting → Agents**: Injected into agent system prompts via conditional sections
2. **JobPosting + Resume → PersonalizerAgent**: Input for match calculation
3. **PersonalizationResult → Output**: Displayed in review summary

---

## Validation and Error Handling

### JobPosting Validation

| Error Condition | Validation | Action |
|----------------|------------|---------|
| Empty title or raw_text | `field_validator` | Raise ValueError |
| No structured data extracted | `model_post_init` | Raise ValueError with helpful message |
| Empty strings in lists | `remove_empty_strings` | Filter out automatically |

### PersonalizationResult Validation

| Error Condition | Validation | Action |
|----------------|------------|---------|
| Score out of range | `ge=0.0, le=100.0` | Pydantic raises ValidationError |
| Confidence out of range | `ge=0.0, le=1.0` | Pydantic raises ValidationError |

### State Validation

| Error Condition | Check | Action |
|----------------|-------|---------|
| Both --job-posting and --job-url | CLI validation | Raise click.BadParameter |
| Invalid file path | CLI validation | Raise click.BadParameter (exists=True) |
| Parsing failure | Try-except in node | Return error in state, continue workflow |

---

## Serialization

All models support JSON serialization for:
- Session persistence (saved in `review_*/session.json`)
- Logging and debugging
- Future API integration

**Example**:

```python
result = PersonalizationResult(...)
json_str = result.model_dump_json(indent=2)
# Can be saved to session.json or logged
```

---

## Testing Strategy

### Unit Tests

**File**: `tests/unit/test_job_posting_models.py`

- Test JobPosting validation (empty fields, missing data)
- Test PersonalizationResult score calculations
- Test SkillMatch confidence ranges
- Test computed fields (match_score, match_level)
- Test helper methods (get_all_skills, get_match_summary)

### Integration Tests

**File**: `tests/integration/test_job_personalization.py`

- Test end-to-end: file input → parsing → personalization → output
- Test URL input → HTML extraction → parsing → personalization
- Test backward compatibility (no job posting = unchanged output)
- Test state flow through LangGraph workflow

---

## Performance Considerations

- **JobPosting**: Lightweight model, minimal overhead (<1ms validation)
- **PersonalizationResult**: Computed fields cached by Pydantic
- **State extensions**: Optional fields don't impact performance when None
- **Serialization**: JSON dumps/loads tested at <10ms for typical data

---

## Future Extensions

Potential enhancements (out of scope for v1):

1. **JobPosting.location**: Geographic location for remote/on-site analysis
2. **PersonalizationResult.match_history**: Track changes across iterations
3. **SkillMatch.resume_evidence**: Link to specific resume sections
4. **PersonalizationResult.match_trend**: Compare with previous applications
5. **JobPosting.expires_at**: Track job posting freshness

---

## API Interface Summary

### Internal Python API

```python
# Job Parsing
from src.services.job_parser import JobParserService

parser = JobParserService(llm_client=...)
job = parser.parse_file(Path("job.md"))
job = parser.parse_url("https://example.com/jobs/123")

# Match Analysis
from src.agents.personalizer import PersonalizerAgent

agent = PersonalizerAgent(llm_client=...)
result = await agent.analyze_match(resume=resume, job_posting=job)

# Access Results
print(f"Match Score: {result.match_score}% ({result.match_level})")
print(f"Critical Gaps: {', '.join(result.missing_required_skills)}")
```

No external REST/GraphQL API for v1.
