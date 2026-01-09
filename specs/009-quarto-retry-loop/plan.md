# Implementation Plan: Quarto Validation Auto-Retry Loop

**Branch**: `009-quarto-retry-loop` | **Date**: 2026-01-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-quarto-retry-loop/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Extend the existing Quarto syntax validation (#7) with automatic retry logic. When validation fails after a resume revision iteration, the system will parse Quarto error messages into structured feedback, trigger the revisor node to apply corrections, and retry up to 3 times (configurable). This eliminates manual intervention for common syntax errors and ensures final QMD files are valid before workflow completion.

## Technical Context

**Language/Version**: Python 3.13 (LangGraph compatibility requirement)
**Primary Dependencies**: LangGraph 1.0.0+, Anthropic SDK 0.25.0+, Pydantic 2.0+, existing QuartoValidator service
**Storage**: File-based (QMD files, retry logs, session artifacts)
**Testing**: pytest 7.4.0+ with asyncio support
**Target Platform**: CLI tool (macOS/Linux with Quarto installed)
**Project Type**: Single project (Python package with CLI)
**Performance Goals**: Retry validation adds <30 seconds overhead per failure (SC-005), validate within 30 seconds per attempt
**Constraints**:
- Must integrate with existing LangGraph workflow without breaking current nodes
- Retry loop must terminate within max_retries limit to prevent infinite loops
- File I/O for retry artifacts must not block workflow execution
**Scale/Scope**:
- 3 retry attempts per iteration (configurable)
- Handle 5+ common Quarto error patterns
- Generate retry logs for each failed iteration

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Single Source of Truth ✅

**Status**: PASS - Not applicable to this feature

**Rationale**: This feature does not modify the canonical resume source (`resume/resume-ja.qmd`). It operates on the QMD validation and retry logic within the review workflow, which generates revised QMD content but does not change the source-of-truth principle.

### Principle II: Automated Generation ✅

**Status**: PASS - Supports automation

**Rationale**: This feature enhances automation by automatically retrying validation failures instead of requiring manual intervention. Aligns with the constitution's emphasis on automated workflows.

### Principle III: Preview-First Workflow ✅

**Status**: PASS - Not applicable to this feature

**Rationale**: This feature operates during the review workflow execution, not during the preview-build workflow. It validates generated QMD syntax but doesn't interfere with the preview-first principle.

### Principle IV: Deployment Simplicity ✅

**Status**: PASS - Not applicable to deployment

**Rationale**: This is an internal workflow enhancement that doesn't affect deployment mechanisms.

### Principle V: Toolchain Consistency ✅

**Status**: PASS - Uses existing toolchain

**Rationale**: This feature uses the existing Quarto CLI for validation (already documented in requirements). No new toolchain dependencies introduced.

### Constitution Compliance Summary

**Overall Status**: ✅ PASS

All constitution principles are satisfied. This feature enhances the existing workflow automation without violating any core principles. No complexity justifications required.

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
packages/resume-review/
├── src/
│   ├── models/
│   │   ├── feedback.py          # Existing (Feedback, Issue models)
│   │   └── validation.py        # NEW: ValidationResult, RetryAttempt models
│   ├── services/
│   │   ├── quarto_validator.py  # MODIFIED: Add error parsing and feedback generation
│   │   └── retry_logger.py      # NEW: Retry log file management
│   ├── workflow/
│   │   ├── runner.py            # MODIFIED: Add validation retry loop after revisor
│   │   ├── state.py             # MODIFIED: Add retry-related state fields
│   │   └── persistence.py       # MODIFIED: Save retry artifacts
│   ├── config/
│   │   └── settings.py          # MODIFIED: Add max_validation_retries, strict_validation
│   └── cli.py                   # MODIFIED: Add --max-validation-retries, --strict-validation
└── tests/
    ├── unit/
    │   ├── test_quarto_validator.py      # MODIFIED: Add error parsing tests
    │   ├── test_validation_models.py     # NEW: Test ValidationResult, RetryAttempt
    │   └── test_retry_logger.py          # NEW: Test retry log generation
    └── integration/
        └── test_retry_workflow.py        # NEW: End-to-end retry loop tests
```

**Structure Decision**: This feature extends the existing single-project Python package structure. All new code resides within `packages/resume-review/src/` following the established pattern of models/, services/, and workflow/ directories. No new packages or directories are introduced at the top level.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - No constitution violations. All principles satisfied.

## Phase 0: Research & Decisions ✅

**Status**: COMPLETE

**Deliverables**:
- [research.md](research.md) - All technical unknowns resolved
  - Q1: Retry integration point → `_handle_node_persistence()` method
  - Q2: Error parsing strategy → Pattern-based string matching
  - Q3: Infinite loop prevention → max_retries counter + strict mode
  - Q4: Retry log format → Markdown per-iteration files
  - Q5: Configuration approach → CLI options + settings defaults
  - Best practices: Async patterns, Pydantic models, file I/O

**Key Decisions**:
- Inject retry logic in existing workflow hook (no graph modifications)
- Parse Quarto errors with pattern matching (5 common patterns + fallback)
- Enforce strict retry limit to prevent infinite loops
- Use markdown logs for human readability
- Follow existing codebase patterns (Pydantic, async, atomic writes)

---

## Phase 1: Design & Contracts ✅

**Status**: COMPLETE

**Deliverables**:
- [data-model.md](data-model.md) - Entity definitions
  - ValidationResult: Validation attempt outcome
  - ValidationFeedback: Reuses existing Feedback model with specific construction pattern
  - RetryAttempt: Single retry record
  - RetryLog: File-based markdown log (not a Python model)
  - Error pattern mapping table
  - State extensions for ReviewState
- [contracts/quarto_validator_service.md](contracts/quarto_validator_service.md) - QuartoValidator API
  - Existing `validate()` method (unchanged)
  - New `create_validation_feedback()` method
  - Error pattern parsing specification
  - Testing contract
- [contracts/retry_logger_service.md](contracts/retry_logger_service.md) - RetryLogger API
  - `log_initial_validation()` method
  - `log_retry_attempt()` method
  - `finalize_log()` method
  - Markdown format specification
- [contracts/workflow_retry_integration.md](contracts/workflow_retry_integration.md) - Workflow integration
  - Modified `_handle_node_persistence()` method
  - New `_validate_and_retry()` method
  - New `_invoke_revisor_for_retry()` method
  - State schema extensions
  - Configuration extensions
- [quickstart.md](quickstart.md) - Developer guide
  - Architecture overview
  - Implementation checklist
  - Testing examples
  - Common pitfalls

**Agent Context Updated**:
- CLAUDE.md updated with Python 3.13, LangGraph, Pydantic, file-based storage

---

## Constitution Re-Check (Post-Design) ✅

**Re-evaluation after Phase 1 design complete**:

### Principle I: Single Source of Truth ✅
**Status**: PASS - Still not applicable
**Rationale**: Design does not touch `resume/resume-ja.qmd` source. Only validates generated QMD from review workflow.

### Principle II: Automated Generation ✅
**Status**: PASS - Enhances automation
**Rationale**: Automatic retry reduces manual intervention, further automating the review workflow.

### Principle III: Preview-First Workflow ✅
**Status**: PASS - Still not applicable
**Rationale**: Design operates during review workflow execution, not preview-build workflow.

### Principle IV: Deployment Simplicity ✅
**Status**: PASS - No deployment impact
**Rationale**: Internal workflow enhancement, doesn't change deployment process.

### Principle V: Toolchain Consistency ✅
**Status**: PASS - Uses existing toolchain
**Rationale**: Design uses existing Quarto CLI (already documented). No new tools introduced.

**Post-Design Status**: ✅ ALL GATES PASSED

All constitution principles remain satisfied after detailed design. No violations introduced during Phase 1.

---

## Next Phase

The implementation plan is complete through Phase 1. To proceed with task breakdown:

```bash
/speckit.tasks
```

This will generate [tasks.md](tasks.md) with detailed implementation tasks based on the contracts and data model defined above.
