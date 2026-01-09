# Agent Interface Contract

**Branch**: `001-resume-review-agents` | **Date**: 2026-01-09 | **Related**: [spec.md](../spec.md), [plan.md](../plan.md)

## Overview

This document defines the interface contract for all evaluation agents in the multi-agent system. Each agent implements a common interface while providing specialized perspective-based feedback.

---

## Base Agent Interface

### Abstract Base Class

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Protocol

class Agent(ABC):
    """
    Base interface for all resume evaluation agents.

    Each agent evaluates the resume from a specific perspective and returns
    structured feedback with a numerical score.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this agent (e.g., 'recruiter', 'technical_writer')."""
        pass

    @property
    @abstractmethod
    def perspective(self) -> str:
        """Human-readable description of this agent's evaluation perspective."""
        pass

    @abstractmethod
    async def evaluate(
        self,
        resume_content: str,
        target_role: str,
        previous_feedback: list[Feedback] | None = None
    ) -> Feedback:
        """
        Evaluate the resume from this agent's perspective.

        Args:
            resume_content: Full text of the resume (markdown body, no YAML frontmatter)
            target_role: Target position (e.g., "LLM/Multi-Agent Engineer")
            previous_feedback: Feedback from previous iteration (for context on changes made)

        Returns:
            Feedback object with score, strengths, issues, and suggestions

        Raises:
            ValidationError: If resume_content is empty or invalid
            APIError: If LLM API call fails after retries
        """
        pass

    @abstractmethod
    def get_system_prompt(self, target_role: str) -> str:
        """
        Get the system prompt for this agent's LLM calls.

        Args:
            target_role: Target position to tailor feedback for

        Returns:
            System prompt string
        """
        pass
```

---

## Agent Implementations

### 1. Recruiter Agent

**Name**: `recruiter`
**Perspective**: Technical recruiter for high-value contract positions (100-140万円/month)
**Requirements**: FR-002 (recruiter appeal)

**Evaluation Focus**:
- Does the resume quickly communicate value for high-paying LLM/AI roles?
- Are relevant skills and technologies prominently featured?
- Does work experience demonstrate hands-on AI/LLM project delivery?
- Are achievements quantified and impactful?
- Is the candidate positioned as a senior/specialist-level engineer?

**System Prompt Template**:

```python
def get_system_prompt(self, target_role: str) -> str:
    return f"""You are a technical recruiter specializing in placing engineers in high-value contract positions (100-140万円/month) in the Japanese freelance market.

Your task is to evaluate this resume for a "{target_role}" position from a recruiter's perspective.

Evaluation Criteria:
1. **Immediate Impact**: Does the resume communicate value in the first 10 seconds?
2. **Skill Match**: Are required skills (LangGraph, RAG, MLOps, etc.) clearly demonstrated?
3. **Experience Quality**: Does work history show hands-on delivery of LLM/AI projects?
4. **Quantified Achievements**: Are results measured and impressive?
5. **Seniority Signals**: Is the candidate positioned as senior/specialist-level?

Scoring Guide:
- 9-10: Exceptional - would immediately submit to 140万円+ positions
- 7-8: Strong - good fit for 100-120万円 positions with minor improvements
- 5-6: Adequate - needs significant improvements to compete
- 3-4: Weak - missing critical skills or unclear value proposition
- 1-2: Poor - would not submit to clients

Provide structured feedback in this JSON format:
{{
  "agent_name": "recruiter",
  "score": <float 1.0-10.0>,
  "strengths": ["strength 1", "strength 2", ...],
  "issues": [
    {{
      "description": "problem description",
      "action_type": "add_content|add_portfolio|restructure|emphasize|quantify",
      "location": "resume section",
      "severity": "critical|high|medium|low"
    }}
  ],
  "suggestions": ["suggestion 1", "suggestion 2", ...]
}}

IMPORTANT: Never suggest fabricating work experience. If skills are missing, suggest portfolio projects instead (action_type: "add_portfolio").
"""
```

---

### 2. Technical Writer Agent

**Name**: `technical_writer`
**Perspective**: Technical documentation specialist evaluating clarity and depth
**Requirements**: FR-002 (technical depth)

**Evaluation Focus**:
- Is technical content clear, precise, and accurate?
- Are technologies and methodologies described with appropriate detail?
- Is the technical progression logical and well-structured?
- Are technical achievements explained in a way that demonstrates deep expertise?
- Is jargon used appropriately (demonstrates expertise without being opaque)?

**System Prompt Template**:

```python
def get_system_prompt(self, target_role: str) -> str:
    return f"""You are a technical writer specializing in engineering resumes and documentation.

Your task is to evaluate this resume for a "{target_role}" position from a technical clarity perspective.

Evaluation Criteria:
1. **Clarity**: Are technical concepts explained clearly and precisely?
2. **Depth**: Does the resume demonstrate deep technical expertise?
3. **Structure**: Is technical content organized logically?
4. **Accuracy**: Are technologies and methodologies described correctly?
5. **Progression**: Is technical growth and learning evident?

Scoring Guide:
- 9-10: Exceptional - technical depth is clear, accurate, and compelling
- 7-8: Strong - good technical clarity with minor areas for improvement
- 5-6: Adequate - some technical content is unclear or lacks depth
- 3-4: Weak - technical skills are vague or poorly explained
- 1-2: Poor - technical content is confusing or inaccurate

Provide structured feedback in the same JSON format as other agents.

Focus on:
- Adding technical detail where vague
- Clarifying complex concepts
- Correcting technical inaccuracies
- Improving logical flow of technical narrative
"""
```

---

### 3. Copywriter Agent

**Name**: `copywriter`
**Perspective**: Marketing copywriter evaluating persuasiveness and impact
**Requirements**: FR-002 (marketing effectiveness)

**Evaluation Focus**:
- Does the resume have a compelling hook/tagline?
- Is the value proposition clear and memorable?
- Are achievements framed as benefits (not just tasks)?
- Is the tone confident and professional?
- Does the resume tell a cohesive career story?

**System Prompt Template**:

```python
def get_system_prompt(self, target_role: str) -> str:
    return f"""You are a marketing copywriter specializing in personal branding for technical professionals.

Your task is to evaluate this resume for a "{target_role}" position from a marketing effectiveness perspective.

Evaluation Criteria:
1. **Hook**: Does the resume open with a memorable tagline/value proposition?
2. **Impact**: Are achievements framed as compelling benefits?
3. **Storytelling**: Does the resume tell a cohesive career narrative?
4. **Tone**: Is the writing confident, professional, and engaging?
5. **Differentiation**: Does the candidate stand out from other engineers?

Scoring Guide:
- 9-10: Exceptional - compelling personal brand, memorable impact
- 7-8: Strong - clear value proposition with good storytelling
- 5-6: Adequate - basic content but lacks marketing polish
- 3-4: Weak - reads like a task list, no compelling narrative
- 1-2: Poor - generic, boring, or unclear value

Provide structured feedback in the same JSON format as other agents.

Focus on:
- Adding taglines and hooks
- Reframing tasks as achievements
- Strengthening action verbs
- Creating narrative coherence
- Emphasizing unique strengths
"""
```

---

### 4. UX Designer Agent

**Name**: `ux_designer`
**Perspective**: Information architect evaluating content structure and scannability **from text source**
**Requirements**: FR-002, FR-013 (structural evaluation)

**Key Distinction**: Evaluates **structure and hierarchy from QMD text** without visual rendering. Focuses on content organization, not visual appearance.

**Evaluation Focus**:
- Is the most important information at the top of the document?
- Can a recruiter scan the **text structure** in 10 seconds and understand the value?
- Is the information hierarchy clear via **markdown structure** (headings levels, sections, bullet points)?
- Are there clear calls-to-action (portfolio links, contact info) in appropriate sections?
- Is the content logically organized and easy to navigate?

**System Prompt Template**:

```python
def get_system_prompt(self, target_role: str) -> str:
    return f"""You are a UX designer specializing in information architecture and scannability.

Your task is to evaluate this resume for a "{target_role}" position from a user experience perspective.

Evaluation Criteria:
1. **Scannability**: Can a recruiter grasp the value in 10 seconds?
2. **Hierarchy**: Is information prioritized correctly?
3. **Navigation**: Are sections clearly delineated and easy to find?
4. **CTAs**: Are contact info and portfolio links prominent?
5. **First View**: Does the opening section immediately establish credibility?

Scoring Guide:
- 9-10: Exceptional - perfect information hierarchy and scannability
- 7-8: Strong - easy to scan with minor improvements possible
- 5-6: Adequate - some structure but requires careful reading
- 3-4: Weak - confusing hierarchy, hard to scan quickly
- 1-2: Poor - wall of text, no clear structure

Provide structured feedback in the same JSON format as other agents.

Focus on:
- Restructuring content for better hierarchy
- Moving critical info to top
- Adding or improving section headings
- Emphasizing key achievements
- Suggesting visual improvements that can be made in QMD source
"""
```

---

### 5. Visual Designer Agent

**Name**: `visual_designer`
**Perspective**: Visual designer evaluating **rendered HTML appearance from screenshot**
**Requirements**: FR-013, FR-014 (screenshot-based visual design)

**Key Distinction**: Evaluates **actual visual presentation** from rendered screenshot using vision API. Focuses on typography, spacing, colors, and visual polish - NOT content structure.

**Evaluation Focus** (requires screenshot):
- Is the visual presentation professional and polished?
- Are fonts, font sizes, and line spacing readable and appropriate?
- Are colors professional and not distracting?
- Is there good use of whitespace (not cramped or too sparse)?
- Are visual elements (if any: icons, borders, dividers) tasteful and minimal?
- Does the visual hierarchy support quick scanning?

**System Prompt Template**:

```python
def get_system_prompt(self, target_role: str) -> str:
    return f"""You are a visual designer specializing in professional resumes and documents.

Your task is to evaluate the visual presentation of this resume for a "{target_role}" position based on the provided screenshot.

Evaluation Criteria:
1. **Professionalism**: Does the design look polished and credible?
2. **Readability**: Are fonts, sizes, and spacing easy to read?
3. **Visual Hierarchy**: Do headings, sections, and emphasis work visually?
4. **Whitespace**: Is there appropriate breathing room?
5. **Simplicity**: Is the design clean and distraction-free?

Scoring Guide:
- 9-10: Exceptional - publication-quality visual design
- 7-8: Strong - professional appearance with minor polish opportunities
- 5-6: Adequate - acceptable but could be more polished
- 3-4: Weak - amateurish or hard to read visually
- 1-2: Poor - unprofessional appearance detracts from content

Provide structured feedback in the same JSON format as other agents.

Focus ONLY on changes that can be made in the QMD source:
- Font size adjustments via CSS
- Spacing improvements via markdown/LaTeX
- Color changes (if supported by template)
- Section layout (columns, dividers, etc.)

Do NOT suggest changes that require design software (icons, graphics, etc.).
"""
```

**Special Behavior**:
- This agent is **optional** and only runs if `--screenshot-url` is provided (FR-013)
- Uses Anthropic's vision API to analyze screenshot image
- Skips evaluation if screenshot capture fails (edge case: dev server not running)

**Implementation Note**:

```python
async def evaluate(
    self,
    resume_content: str,
    target_role: str,
    previous_feedback: list[Feedback] | None = None,
    screenshot_path: str | None = None  # Additional parameter
) -> Feedback:
    if screenshot_path is None:
        raise ValueError("Visual Designer requires screenshot_path parameter")

    # Use Anthropic vision API to analyze screenshot
    # ... implementation
```

---

## Agent Coordination

### LangGraph State Schema

Agents are coordinated via LangGraph's StateGraph with shared state:

```python
from typing import TypedDict
from langgraph.graph import StateGraph

class ReviewState(TypedDict):
    # Input
    resume_content: str
    target_role: str
    score_threshold: float
    max_iterations: int

    # Iteration tracking
    current_iteration: int
    feedback_history: list[list[Feedback]]  # [iteration][agent]

    # Current iteration state
    current_feedback: list[Feedback]
    integrated_score: float
    threshold_met: bool

    # Portfolio analysis
    skill_gaps: list[str]
    portfolio_suggestions: list[PortfolioItem]

    # Output
    revised_content: str
    applied_revisions: list[str]
    final_score: float
```

### Supervisor Pattern

A supervisor node coordinates agent execution:

```python
async def supervisor_node(state: ReviewState) -> ReviewState:
    """
    Coordinates agent evaluation in parallel.
    """
    agents = [
        RecruiterAgent(),
        TechnicalWriterAgent(),
        CopywriterAgent(),
    ]

    # Run agents in parallel
    feedback_results = await asyncio.gather(
        *[agent.evaluate(
            resume_content=state["resume_content"],
            target_role=state["target_role"],
            previous_feedback=state["feedback_history"][-1] if state["feedback_history"] else None
        ) for agent in agents]
    )

    # Update state
    state["current_feedback"] = feedback_results
    state["integrated_score"] = calculate_integrated_score(feedback_results)
    state["threshold_met"] = state["integrated_score"] >= state["score_threshold"]

    return state
```

---

## Error Handling

### Retry Logic

All agents must implement retry logic for transient API failures:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class BaseAgent(Agent):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def _call_llm(self, prompt: str) -> str:
        """Make LLM API call with automatic retry."""
        # Implementation
        pass
```

**Requirements**: Edge case - network connectivity lost mid-review

---

### Validation Errors

Agents must validate LLM output and handle schema mismatches:

```python
async def evaluate(self, resume_content: str, target_role: str, previous_feedback=None) -> Feedback:
    try:
        raw_response = await self._call_llm(prompt)
        feedback = Feedback.model_validate_json(raw_response)  # Pydantic validation
        return feedback
    except ValidationError as e:
        # Retry with schema correction prompt
        correction_prompt = f"Previous output was invalid. Error: {e}\nPlease provide valid JSON."
        raw_response = await self._call_llm(correction_prompt)
        return Feedback.model_validate_json(raw_response)
```

---

## Testing Strategy

### Unit Tests

Each agent must have unit tests covering:

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_recruiter_agent_evaluate():
    agent = RecruiterAgent()
    agent._call_llm = AsyncMock(return_value='{"agent_name": "recruiter", "score": 8.0, ...}')

    feedback = await agent.evaluate(
        resume_content="# Sample Resume\n...",
        target_role="LLM/Multi-Agent Engineer"
    )

    assert feedback.agent_name == "recruiter"
    assert 1.0 <= feedback.score <= 10.0
    assert len(feedback.strengths) > 0

@pytest.mark.asyncio
async def test_recruiter_agent_handles_api_error():
    agent = RecruiterAgent()
    agent._call_llm = AsyncMock(side_effect=APIError("Connection timeout"))

    with pytest.raises(APIError):
        await agent.evaluate(resume_content="...", target_role="...")
```

### Integration Tests

Test agent coordination via LangGraph:

```python
@pytest.mark.asyncio
async def test_agent_coordination():
    workflow = create_review_workflow()

    result = await workflow.ainvoke({
        "resume_content": load_fixture("sample-resume.md"),
        "target_role": "LLM/Multi-Agent Engineer",
        "score_threshold": 8.0,
        "max_iterations": 3,
        "current_iteration": 0,
    })

    assert len(result["feedback_history"]) > 0
    assert result["integrated_score"] >= 0.0
```

---

## Performance Requirements

- **Single agent evaluation**: < 30 seconds (SC-001: 5 min total / 3 agents / 3 iterations max)
- **Parallel execution**: All content agents run concurrently
- **LLM streaming**: Use streaming for real-time feedback in verbose mode

---

## Agent Weights

**See**: [data-model.md](../data-model.md#scoring-system) for the complete weight definition and scoring algorithm.

**Summary**: Agent scores are weighted as follows (per FR-004):
- Recruiter: 30%, Copywriter: 25%, Technical Writer: 20%, UX Designer: 15%, Visual Designer: 10%

Implementation constants are defined in `agents/src/orchestration/scoring.py`.
