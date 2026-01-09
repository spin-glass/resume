# Implementation Plan: Resume Review Multi-Agent System

**Branch**: `001-resume-review-agents` | **Date**: 2026-01-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-resume-review-agents/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a CLI tool using a multi-agent workflow to automatically review and improve resumes for high-value contract positions (110-140万円/month). The system evaluates resume content from multiple perspectives (recruiter, technical writer, copywriter), provides scored feedback, iteratively improves content until a quality threshold is met, identifies skill gaps, suggests portfolio projects, and optionally evaluates visual design from rendered HTML screenshots.

## Technical Context

**Language/Version**: Python 3.13+ (downgrade from 3.14.2 to 3.13.x for LangGraph compatibility; upgrade to 3.14 when support is confirmed - see [LangGraph Issue #5253](https://github.com/langchain-ai/langgraph/issues/5253) for tracking)

**Primary Dependencies**:
- `langgraph>=1.0.0` (multi-agent orchestration) - **MANDATORY: Must use StateGraph**
- `langchain-anthropic>=0.1.0` (Anthropic SDK integration layer)
- `anthropic>=0.25.0` (Claude Sonnet 4.5 API client)
- `playwright>=1.40.0` (screenshot capture)
- `pydantic>=2.0.0` (data validation)
- `click>=8.1.0` (CLI framework)
- `python-frontmatter>=1.0.0` (QMD YAML parsing)
- `python-dotenv>=1.0.0` (environment variable management from .env files)
- `pytest>=7.4.0` (testing)
- `pytest-asyncio>=0.21.0` (async test support)
- `tenacity>=8.0.0` (retry logic with exponential backoff)

**Python 3.14 Fallback**: If LangGraph 3.14 support is delayed beyond Q2 2026, remain on Python 3.13.x as it is fully supported and stable
**Storage**: Files (QMD input/output, cached screenshots)
**Testing**: pytest
**Target Platform**: CLI tool (macOS/Linux, Node.js 22.x environment already present)
**Project Type**: single (CLI application with multi-agent architecture)
**Performance Goals**: Complete content review cycle in <5 minutes ([SC-001](./spec.md#measurable-outcomes))
**Constraints**: No fabricated work experience ([FR-008](./spec.md#functional-requirements)), preserve YAML frontmatter ([FR-009](./spec.md#functional-requirements)), configurable score threshold (default 8.0/10, [FR-005](./spec.md#functional-requirements))
**Scale/Scope**: Single-user CLI tool, processes individual QMD files, 3-5 specialized agents (recruiter, technical writer, copywriter, UX designer, visual designer), max 3 iterations per review phase

## ⚠️ CRITICAL: LangGraph StateGraph Requirement

**THIS IS A MANDATORY ARCHITECTURAL REQUIREMENT**

The implementation MUST use LangGraph's `StateGraph` for multi-agent orchestration. This is NOT optional.

### Required Architecture

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class ReviewState(TypedDict):
    resume_content: str
    target_role: str
    score_threshold: float
    max_iterations: int
    current_iteration: int
    feedback_history: list[list[Feedback]]
    current_feedback: list[Feedback]
    integrated_score: float
    threshold_met: bool
    skill_gaps: list[str]
    portfolio_suggestions: list[PortfolioItem]
    revised_content: str
    applied_revisions: list[str]
    final_score: float

# Build workflow graph
workflow = StateGraph(ReviewState)
workflow.add_node("recruiter", recruiter_agent)
workflow.add_node("tech_writer", tech_writer_agent)
workflow.add_node("copywriter", copywriter_agent)
workflow.add_node("aggregator", score_aggregator)
workflow.add_node("revisor", content_revisor)
workflow.add_conditional_edges(
    "aggregator",
    should_continue,
    {"revise": "revisor", "finish": END}
)
app = workflow.compile()
```

### Why StateGraph is Required

1. **State Management**: Explicit, typed state schema (`ReviewState(TypedDict)`)
2. **Workflow Control**: Graph-based edges with conditional routing
3. **Parallel Execution**: Agents can run concurrently via `asyncio.gather`
4. **Checkpointing**: Built-in persistence for long-running workflows
5. **Debugging**: Clear workflow visualization and state inspection
6. **Testability**: Nodes can be tested in isolation

### What is NOT Acceptable

❌ Plain Python class with method calls (`ReviewWorkflow` class)
❌ Sequential agent execution without async parallelization
❌ Manual iteration loops instead of graph-based conditional edges
❌ Pydantic models instead of `TypedDict` for workflow state

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Single Source of Truth
**Status**: ✅ PASS
**Validation**: The CLI tool will read from and write to `public/assets/resume-ja.qmd` exclusively. No direct modification of generated artifacts (PDF, HTML, MDX).

### Principle II: Automated Generation
**Status**: ✅ PASS
**Validation**: The review tool modifies only the QMD source. After review, existing build pipeline (`npm run resume:build`) regenerates all output formats. Package.json already includes `review:build` script combining review + build.

### Principle III: Preview-First Workflow
**Status**: ✅ PASS
**Validation**: FR-010 requires dry-run mode for previewing changes. Users can run `--dry-run` to see proposed changes before applying them. Visual design review (FR-013) requires screenshot from live preview server.

### Principle IV: Deployment Simplicity
**Status**: ✅ PASS
**Validation**: No changes to deployment process. CLI tool operates pre-deployment, modifying source content only.

### Principle V: Toolchain Consistency
**Status**: ✅ PASS
**Validation**: Adds Python-based CLI tool for content review. Does not modify Quarto/LuaLaTeX/font toolchain. Python 3.14.2 already present in environment.

### Overall Assessment
**GATE STATUS**: ✅ PASS - No constitution violations. Feature integrates cleanly into existing workflow.

---

### Post-Design Re-evaluation (after Phase 1)

After completing Phase 1 design (data models, contracts, quickstart), the Constitution Check has been re-evaluated:

**Principle I (Single Source of Truth)**: ✅ STILL PASS
- Design confirms QMD file remains sole source
- Data model shows Resume entity with `file_path` and content preservation
- CLI contract validates only .qmd files are accepted
- No new output formats introduced

**Principle II (Automated Generation)**: ✅ STILL PASS
- CLI modifies QMD source only
- Quickstart guide integrates with existing `npm run resume:build`
- No manual generation steps required
- Package.json scripts properly chain review → build

**Principle III (Preview-First Workflow)**: ✅ STILL PASS
- Dry-run mode implemented in CLI contract (--dry-run flag)
- Quickstart documents preview workflow
- Visual design review requires live preview server running
- No bypassing of preview step in normal workflow

**Principle IV (Deployment Simplicity)**: ✅ STILL PASS
- No deployment changes required
- CLI operates locally pre-deployment
- Git push workflow unchanged
- No new CI/CD steps needed

**Principle V (Toolchain Consistency)**: ✅ STILL PASS
- Python 3.13 added (compatible with existing environment)
- LangGraph/Anthropic SDK/Playwright are isolated to `agents/` directory
- No modifications to Quarto/LaTeX/font requirements
- Quickstart documents toolchain compatibility

**FINAL GATE STATUS**: ✅ PASS - Design phase confirms no constitution violations. Implementation may proceed.

---

## Phase Completion Criteria

### Phase 0: Research → Phase 1: Design

- [x] SDK selection complete ([research.md](./research.md))
- [x] Technology decisions documented with rationale
- [x] Python version strategy defined (3.13 with 3.14 upgrade path)
- [x] Constitution Check PASS

**Status**: ✅ Complete

---

### Phase 1: Design → Phase 2: Implementation

- [x] Data model definitions complete ([data-model.md](./data-model.md))
  - [x] All entities defined (Resume, Feedback, Issue, PortfolioItem, ReviewSession)
  - [x] Validation rules specified
  - [x] Scoring system documented
- [x] CLI interface contract complete ([contracts/cli-interface.md](./contracts/cli-interface.md))
  - [x] All options and flags defined
  - [x] Exit codes (0-6) specified
  - [x] Error recovery scenarios documented
- [x] Agent interface contract complete ([contracts/agent-interface.md](./contracts/agent-interface.md))
  - [x] Base agent interface defined
  - [x] All 5 agent implementations specified
  - [x] System prompts documented
  - [x] **LangGraph StateGraph integration specified**
- [x] Revision service contract complete ([contracts/revision-service.md](./contracts/revision-service.md))
  - [x] All 6 ActionTypes documented
  - [x] YAML preservation strategy defined
- [x] Quickstart guide complete ([quickstart.md](./quickstart.md))
  - [x] Setup steps documented
  - [x] Usage examples provided
  - [x] Cost estimation detailed
- [x] Constitution Check re-evaluation PASS
- [x] Task breakdown generated ([tasks.md](./tasks.md))

**Status**: ✅ Complete

---

### Phase 2: Implementation → Phase 3: Completion

Prerequisites for declaring implementation complete:

- [ ] All tasks in [tasks.md](./tasks.md) completed
- [ ] **LangGraph StateGraph properly implemented** (CRITICAL)
  - [ ] `ReviewState(TypedDict)` defined and used
  - [ ] `StateGraph(ReviewState)` created with nodes
  - [ ] Conditional edges for iteration control
  - [ ] `workflow.compile()` called to create executable app
- [ ] All 8 phases executed successfully
- [ ] All integration tests passing
- [ ] Success criteria verified:
  - [ ] [SC-001](./spec.md#measurable-outcomes): Content review cycle completes in <5 minutes
  - [ ] [SC-002](./spec.md#measurable-outcomes): 80% of resumes improve by ≥1.5 points
  - [ ] [SC-003](./spec.md#measurable-outcomes): No fabricated claims (100% accuracy)
  - [ ] [SC-004](./spec.md#measurable-outcomes): Portfolio naming patterns valid (100%)
  - [ ] [SC-005](./spec.md#measurable-outcomes): Dry-run accurately predicts changes
  - [ ] [SC-006](./spec.md#measurable-outcomes): Feedback reasoning is clear
  - [ ] [SC-007](./spec.md#measurable-outcomes): No data loss or corruption (100%)
- [ ] All functional requirements validated (FR-001 to FR-014)
- [ ] Documentation complete (README.md in `agents/`)
- [ ] Package ready for distribution (`pyproject.toml` configured)

**Status**: ⏳ Pending - Requires StateGraph refactoring

---

## Key Risks & Mitigations

| Risk | Impact | Probability | Mitigation | Reference |
|------|--------|-------------|------------|-----------|
| **Python 3.14 support delayed** | Low | Medium | Stay on Python 3.13.x (fully supported and stable) | [LangGraph Issue #5253](https://github.com/langchain-ai/langgraph/issues/5253) |
| **Claude API rate limits** | Medium | Low | Implement exponential backoff with `tenacity` library (3 retries) | [cli-interface.md](./contracts/cli-interface.md#network-error-recovery) |
| **LLM output schema violations** | Medium | Medium | Pydantic validation + retry with schema correction prompt | [agent-interface.md](./contracts/agent-interface.md#error-handling) |
| **YAML frontmatter corruption** | High | Low | Pre-save validation + automatic `.bak` file backup | [revision-service.md](./contracts/revision-service.md#yaml-frontmatter-preservation) |
| **Screenshot capture failure** | Low | Medium | Graceful degradation - skip design review, continue with exit code 5 | [cli-interface.md](./contracts/cli-interface.md#graceful-degradation) |
| **Cost overruns (API usage)** | Low | Low | Haiku for non-critical agents (~$0.30 savings/review), dry-run testing | [quickstart.md](./quickstart.md#cost-management) |
| **Performance < 5 min (SC-001)** | Medium | Low | Parallel agent execution (3 agents concurrent), streaming responses | [agent-interface.md](./contracts/agent-interface.md#performance-requirements) |
| **StateGraph not implemented** | **CRITICAL** | **High** | **Explicit requirement in plan + validation in tasks** | This document |

### Risk Response Plan

**CRITICAL Risk** (StateGraph not implemented):
- **Prevention**: Explicit architectural requirement in plan.md
- **Detection**: Code review for `from langgraph.graph import StateGraph`
- **Recovery**: Immediate refactoring before any further development

**High-Impact Risks** (YAML corruption):
- **Prevention**: Triple-validation before file write (parse, compare keys, size check)
- **Detection**: Automated pre-save checks in `qmd_parser.py`
- **Recovery**: Automatic restore from `.bak` file on any save error

**Medium-Impact Risks** (API rate limits, schema violations, performance):
- **Prevention**: Retry logic, validation, parallel execution
- **Detection**: Error logging to `~/.resume-review/error.log`
- **Recovery**: Partial success handling (exit code 6), graceful degradation

**Low-Impact Risks** (Python 3.14, screenshot, costs):
- **Acceptance**: Known limitations, documented workarounds
- **Monitoring**: Track Python 3.14 LangGraph issue, cost per review

---

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
agents/                          # Python CLI tool package (NEW)
├── src/
│   ├── __init__.py
│   ├── cli.py                   # Entry point for review command
│   ├── agents/                  # Multi-agent implementations
│   │   ├── __init__.py
│   │   ├── base.py              # Base agent interface
│   │   ├── recruiter.py         # Recruiter perspective agent
│   │   ├── technical_writer.py  # Technical depth agent
│   │   ├── copywriter.py        # Marketing effectiveness agent
│   │   ├── ux_designer.py       # UX/scannability agent
│   │   └── visual_designer.py   # Visual presentation agent
│   ├── orchestration/           # Multi-agent coordination
│   │   ├── __init__.py
│   │   ├── workflow.py          # LangGraph StateGraph workflow (MUST use StateGraph)
│   │   ├── state.py             # ReviewState TypedDict definition (NEW)
│   │   └── scoring.py           # Score aggregation & thresholds
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   ├── feedback.py          # Feedback, Issue entities
│   │   ├── portfolio.py         # Portfolio item model
│   │   └── session.py           # Review session tracking
│   ├── services/                # Services
│   │   ├── __init__.py
│   │   ├── qmd_parser.py        # QMD file I/O with YAML preservation
│   │   ├── screenshot.py        # Headless browser screenshot capture
│   │   └── revision.py          # Content revision application
│   └── utils/
│       ├── __init__.py
│       └── config.py            # Configuration management
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/                # Sample QMD files for testing
├── pyproject.toml               # Python package config
├── requirements.txt             # Dependencies
└── README.md                    # Agent system documentation

public/assets/resume-ja.qmd      # EXISTING - Single source of truth (input/output)
```

**Structure Decision**: Single Python package (`agents/`) added to existing repository. Uses Option 1 (single project) structure. No changes to existing Next.js/Nextra web application or Quarto build pipeline.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - No constitution violations detected.

---

## Implementation Status (2026-01-09)

### Current State: ⚠️ ARCHITECTURE VIOLATION

The current implementation in `agents/src/orchestration/workflow.py` does NOT use LangGraph StateGraph:

**Expected (per spec)**:
```python
from langgraph.graph import StateGraph
workflow = StateGraph(ReviewState)
workflow.add_node("recruiter", recruiter_agent)
# ...
app = workflow.compile()
```

**Actual (current code)**:
```python
class ReviewWorkflow:  # Plain Python class, no StateGraph
    def run_review(self, session: ReviewSession):  # Pydantic model, not TypedDict
        # Sequential method calls, no graph
```

### Required Refactoring

1. Create `agents/src/orchestration/state.py` with `ReviewState(TypedDict)`
2. Refactor `workflow.py` to use `StateGraph(ReviewState)`
3. Convert agents to async functions returning state updates
4. Add conditional edges for iteration control
5. Implement parallel agent execution with `asyncio.gather`

See [tasks.md](./tasks.md) for detailed refactoring tasks.
