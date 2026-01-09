# Data Model: Resume Review Multi-Agent System

**Branch**: `001-resume-review-agents` | **Date**: 2026-01-09 | **Related**: [spec.md](./spec.md), [plan.md](./plan.md)

## Overview

This document defines the core data entities for the resume review system. All models use Pydantic for validation and serialization, ensuring type safety across the multi-agent workflow.

---

## Entity Definitions

### 1. Resume

The QMD document being reviewed, containing professional experience, skills, and portfolio sections.

**Fields**:
- `file_path` (str): Absolute path to the QMD file
- `yaml_frontmatter` (dict): Parsed YAML metadata (must be preserved during edits)
- `content` (str): Markdown content body (without frontmatter)
- `full_text` (str): Complete file content including frontmatter

**Validation Rules**:
- File must exist and be readable (FR-001)
- YAML frontmatter must be valid and parseable
- Content must be valid Markdown/QMD syntax

**State Transitions**:
```
Initial → Validated → Under Review → Revised → Completed
```

**Implementation Notes**:
- Use `frontmatter` library or regex parsing to separate YAML from content
- Preserve exact formatting of YAML (including comments, whitespace) per FR-009
- Store original content for rollback in case of errors

---

### 2. Feedback

Evaluation output from a single agent perspective, including score, strengths, issues, and improvement suggestions.

**Fields**:
- `agent_name` (str): Name of the evaluating agent (e.g., "recruiter", "technical_writer")
- `score` (float): Numerical score from 1.0 to 10.0
- `strengths` (list[str]): List of positive aspects identified
- `issues` (list[Issue]): List of problems to address (see Issue entity)
- `suggestions` (list[str]): Specific improvement recommendations
- `timestamp` (datetime): When the feedback was generated

**Validation Rules**:
- Score must be between 1.0 and 10.0 (FR-003)
- At least one strength or issue must be provided
- Each issue must have a valid action_type

**Relationships**:
- One-to-many with Issue entities
- Part of ReviewSession aggregation

---

### 3. Issue

A specific problem identified during review, categorized by action type.

**Fields**:
- `description` (str): Human-readable problem description
- `action_type` (ActionType): Enum of possible actions
- `location` (str | None): Section of resume where issue occurs (optional)
- `severity` (Severity): Priority level (critical, high, medium, low)
- `resolution` (str | None): Applied fix description (populated after revision)

**Enums**:

```python
class ActionType(str, Enum):
    ADD_CONTENT = "add_content"           # Missing information
    ADD_PORTFOLIO = "add_portfolio"       # Skill gap requiring project
    RESTRUCTURE = "restructure"           # Reorganize content
    EMPHASIZE = "emphasize"               # Strengthen existing content
    REMOVE = "remove"                     # Delete unnecessary content
    QUANTIFY = "quantify"                 # Add metrics/numbers

class Severity(str, Enum):
    CRITICAL = "critical"  # Blocks high-value positions
    HIGH = "high"          # Major improvement opportunity
    MEDIUM = "medium"      # Noticeable quality issue
    LOW = "low"            # Minor polish item
```

**Validation Rules**:
- action_type must not be "fabricate" or "invent" (FR-008 enforcement)
- ADD_PORTFOLIO issues must reference a specific skill gap
- location should reference a valid resume section when provided

---

### 4. Portfolio Item

A suggested project to demonstrate a skill, with repository name, associated skills, and generated URLs.

**Fields**:
- `repository_name` (str): GitHub repo name following convention `{technology}-{type}`
- `skills` (list[str]): Technologies/skills demonstrated by this project
- `description` (str): Brief explanation of what the project showcases
- `github_url` (str): Generated GitHub URL (e.g., `https://github.com/{username}/{repo}`)
- `demo_url` (str | None): Generated demo URL (e.g., `https://{repo}.vercel.app`)
- `priority` (int): Order in which to build (1 = highest priority)

**Validation Rules**:
- repository_name must match pattern `^[a-z0-9-]+-[a-z0-9-]+$` (at least one hyphen, lowercase alphanumeric)
- At least one skill must be specified
- GitHub URL must follow consistent pattern (FR-007, SC-004)
- Priority must be >= 1

**Business Logic**:
- Portfolio items are generated only when skills are missing from work experience (FR-007)
- Naming convention ensures consistent URL patterns: `{tech}-{description}`
  - Format: lowercase with hyphens, descriptive of project purpose
  - Examples: `langgraph-multi-agent`, `rag-evaluation-toolkit`, `mlops-deployment-api`
  - Multi-word components allowed: `langgraph-multi-agent` (not restricted to single-word suffixes)
- Demo URL may be null for backend-only or CLI projects

**State Transitions**:
```
Suggested → Approved → (Built - tracked externally)
```

---

### 5. Review Session

The complete workflow from input to output, tracking iterations, score progression, and applied changes.

**Fields**:
- `session_id` (str): Unique identifier (UUID)
- `resume` (Resume): The resume being reviewed
- `target_role` (str): Target position (default: "LLM/Multi-Agent Engineer")
- `score_threshold` (float): Minimum score to pass (default: 8.0)
- `max_iterations` (int): Maximum revision cycles (default: 3)
- `current_iteration` (int): Current iteration number (starts at 0)
- `feedback_history` (list[list[Feedback]]): Feedback from each iteration (outer list = iterations, inner list = agents)
- `portfolio_suggestions` (list[PortfolioItem]): Accumulated portfolio items
- `applied_revisions` (list[str]): Log of changes made to resume
- `final_score` (float | None): Integrated score after completion
- `status` (SessionStatus): Current workflow state
- `dry_run` (bool): Whether this is a preview-only session
- `screenshot_url` (str | None): URL for visual design review (optional)

**Enums**:

```python
class SessionStatus(str, Enum):
    INITIALIZED = "initialized"
    CONTENT_REVIEW = "content_review"
    PORTFOLIO_ANALYSIS = "portfolio_analysis"
    DESIGN_REVIEW = "design_review"
    COMPLETED = "completed"
    FAILED = "failed"
```

**Validation Rules**:
- score_threshold must be between 1.0 and 10.0 (FR-005)
- max_iterations must be >= 1 (FR-005)
- current_iteration must be <= max_iterations
- final_score is populated only when status = COMPLETED

**State Transitions**:
```
INITIALIZED → CONTENT_REVIEW → PORTFOLIO_ANALYSIS → DESIGN_REVIEW* → COMPLETED
                                                                     ↓
                                                                   FAILED
```
*Design review only occurs if screenshot_url is provided

**Business Logic**:
- Iterations continue until:
  1. Integrated score >= score_threshold, OR
  2. current_iteration >= max_iterations (FR-005)
- In dry-run mode, resume file is never modified (FR-010)
- Portfolio suggestions accumulate across iterations but are deduplicated
- Applied revisions are appended to log for audit trail (FR-011)

---

## Scoring System

### Score Integration

Individual agent scores are combined using weighted averaging (FR-004):

```python
def calculate_integrated_score(feedback: list[Feedback]) -> float:
    """
    Weighted average of agent scores.

    Weights based on SC-002 and assumptions section:
    - Recruiter: 30% (most important for contract acquisition)
    - Technical Writer: 20% (technical depth)
    - Copywriter: 25% (marketing effectiveness)
    - UX Designer: 15% (scannability)
    - Visual Designer: 10% (visual polish)
    """
    weights = {
        "recruiter": 0.30,
        "technical_writer": 0.20,
        "copywriter": 0.25,
        "ux_designer": 0.15,
        "visual_designer": 0.10,
    }

    total_score = 0.0
    total_weight = 0.0

    for fb in feedback:
        weight = weights.get(fb.agent_name, 0.0)
        total_score += fb.score * weight
        total_weight += weight

    return total_score / total_weight if total_weight > 0 else 0.0
```

### Score Thresholds

Per FR-005 and SC-002:
- **Default threshold**: 8.0/10
- **Target improvement**: +1.5 points after revision (SC-002)
- **Configurable**: Users can override via CLI flag

---

## Data Flow Diagram

```
Input QMD File
     ↓
Resume Entity (parsed)
     ↓
Review Session (initialized)
     ↓
┌──────────────────────────────────────┐
│  Content Review Phase (Iteration N)  │
│  ┌──────────────────────────────┐    │
│  │ Recruiter Agent → Feedback   │    │
│  │ Tech Writer Agent → Feedback │    │
│  │ Copywriter Agent → Feedback  │    │
│  └──────────────────────────────┘    │
│           ↓                           │
│  Calculate Integrated Score          │
│           ↓                           │
│  [Score >= Threshold?]               │
│    No → Apply Revisions → Iterate    │
│    Yes → Continue                    │
└──────────────────────────────────────┘
     ↓
Portfolio Gap Analysis
     ↓
Portfolio Items (suggested)
     ↓
Design Review Phase (if screenshot_url)
     ↓
UX/Visual Feedback
     ↓
Final Revised Resume
     ↓
Output Summary (FR-011)
```

---

## Persistence Strategy

### File-Based Storage

- **Resume files**: Read from and written to disk (QMD format)
- **Session state**: No persistent storage required (single-run CLI tool)
- **Screenshots**: Temporarily cached in `/tmp/resume-screenshots/` during session

### Error Handling

- **File I/O errors**: Preserve original resume, report error, exit gracefully (FR-009)
- **Network errors**: Retry AI API calls up to 3 times with exponential backoff
- **Validation errors**: Fail fast with clear error messages (edge case: invalid YAML)

---

## Validation Summary

| Requirement | Validation Location |
|-------------|---------------------|
| FR-001: File exists | Resume.__init__ |
| FR-003: Score 1-10 | Feedback.score validator |
| FR-005: Threshold & iterations | ReviewSession validators |
| FR-007: Portfolio naming | PortfolioItem.repository_name validator |
| FR-008: No fabrication | Issue.action_type enum (no "fabricate" option) |
| FR-009: Preserve YAML | Resume.save() method |
| FR-010: Dry-run mode | ReviewSession.dry_run flag |

---

## Example JSON Schemas

### Feedback Schema

```json
{
  "agent_name": "recruiter",
  "score": 7.5,
  "strengths": [
    "Strong LLM project experience at Acme Corp",
    "Clear progression in AI/ML roles"
  ],
  "issues": [
    {
      "description": "Missing LangGraph experience for 120万円+ positions",
      "action_type": "add_portfolio",
      "location": "Skills section",
      "severity": "high",
      "resolution": null
    },
    {
      "description": "RAG evaluation metrics not quantified",
      "action_type": "quantify",
      "location": "Experience → Acme Corp",
      "severity": "medium",
      "resolution": null
    }
  ],
  "suggestions": [
    "Add a portfolio project demonstrating LangGraph multi-agent coordination",
    "Include specific RAG metrics (e.g., 'Improved retrieval accuracy from 72% to 89%')"
  ],
  "timestamp": "2026-01-09T10:30:00Z"
}
```

### Portfolio Item Schema

```json
{
  "repository_name": "langgraph-multi-agent",
  "skills": ["LangGraph", "Multi-agent systems", "Claude API"],
  "description": "Multi-agent research assistant using LangGraph for task orchestration and Claude Sonnet for analysis",
  "github_url": "https://github.com/spin-glass/langgraph-multi-agent",
  "demo_url": "https://langgraph-multi-agent.vercel.app",
  "priority": 1
}
```

---

## Implementation Notes

### Pydantic Models

All entities will be implemented as Pydantic v2 models:

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum

class Feedback(BaseModel):
    agent_name: str
    score: float = Field(ge=1.0, le=10.0)
    strengths: list[str]
    issues: list[Issue]
    suggestions: list[str]
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator('score')
    @classmethod
    def validate_score(cls, v: float) -> float:
        if not 1.0 <= v <= 10.0:
            raise ValueError('Score must be between 1.0 and 10.0')
        return v
```

### Type Safety

- Use `TypedDict` or Pydantic models for LangGraph StateGraph
- Enable mypy strict mode for static type checking
- Validate all external inputs (CLI args, file contents, API responses)
