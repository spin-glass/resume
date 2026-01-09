# Tasks: Resume Review Multi-Agent System

**Feature Branch**: `001-resume-review-agents`
**Input Documents**: `/specs/001-resume-review-agents/` (spec.md, plan.md, data-model.md, quickstart.md, contracts/)
**Prerequisites**: spec.md (✓), plan.md (✓), research.md (✓), data-model.md (✓), contracts/ (✓)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story per acceptance criteria.

**Testing Strategy**: Integration tests are included for critical validation paths but not required for every component.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Create Python package structure and configure toolchain per plan.md specifications

- [X] T001 Create `agents/` directory structure with `src/`, `tests/`, and subdirectories per plan.md
- [X] T002 Initialize Python 3.13 virtual environment in `agents/.venv` (downgrade from 3.14 for LangGraph compatibility)
- [X] T003 [P] Create `agents/pyproject.toml` with project metadata and build config
- [X] T004 [P] Create `agents/requirements.txt` with dependencies: langgraph>=1.0.0, langchain-anthropic>=0.1.0, anthropic>=0.25.0, playwright>=1.40.0, pydantic>=2.0.0, click>=8.1.0, python-frontmatter>=1.0.0, pytest>=7.4.0, pytest-asyncio>=0.21.0, tenacity>=8.0.0
- [X] T005 [P] Create `agents/README.md` documenting agent system architecture and usage
- [X] T006 Install Playwright browser for screenshot capture in `agents/.venv`

**Checkpoint**: Python environment ready, dependencies installed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 [P] Create data model enums in `agents/src/models/__init__.py`: ActionType, Severity, SessionStatus per data-model.md
- [X] T008 [P] Create Resume entity in `agents/src/models/feedback.py` with file_path, yaml_frontmatter, content fields and Pydantic validation (FR-001)
- [X] T009 [P] Create Issue entity in `agents/src/models/feedback.py` with description, action_type, location, severity fields and validation (no fabrication enforcement per FR-008)
- [X] T010 [P] Create Feedback entity in `agents/src/models/feedback.py` with agent_name, score (1-10), strengths, issues, suggestions, timestamp fields (FR-003)
- [X] T011 [P] Create PortfolioItem entity in `agents/src/models/portfolio.py` with repository_name, skills, description, urls, priority and naming pattern validation (FR-007, SC-004)
- [X] T012 [P] Create ReviewSession entity in `agents/src/models/session.py` with session_id, resume, config, state tracking fields (FR-005)
- [X] T013 Create `agents/src/orchestration/state.py` with `ReviewState(TypedDict)` per plan.md LangGraph requirements
- [X] T014 Implement score integration function in `agents/src/orchestration/scoring.py` with weighted averaging logic (recruiter 30%, technical_writer 20%, copywriter 25%, ux_designer 15%, visual_designer 10%) per FR-004 and data-model.md
- [X] T015 [P] Create QMD parser service in `agents/src/services/qmd_parser.py` with YAML frontmatter preservation (FR-009)
- [X] T016 [P] Create base agent interface in `agents/src/agents/base.py` with async evaluate() method compatible with LangGraph nodes
- [X] T017 [P] Create configuration management in `agents/src/utils/config.py` for API keys, thresholds, timeouts
- [X] T018 [P] Setup logging infrastructure with console and file handlers in `agents/src/utils/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Content Review and Improvement (Priority: P1)

**Goal**: Multi-agent content evaluation with iterative revision until quality threshold met

**Independent Test**: Run review command on sample QMD file and verify structured feedback with scores from multiple perspectives

### Implementation for User Story 1

- [X] T019 [P] [US1] Implement RecruiterAgent in `agents/src/agents/recruiter.py` as async LangGraph node function with system prompt for high-value contract evaluation
- [X] T020 [P] [US1] Implement TechnicalWriterAgent in `agents/src/agents/technical_writer.py` as async LangGraph node function with system prompt for technical depth evaluation
- [X] T021 [P] [US1] Implement CopywriterAgent in `agents/src/agents/copywriter.py` as async LangGraph node function with system prompt for marketing effectiveness evaluation
- [X] T022 [US1] Implement RevisionService in `agents/src/services/revision.py` with methods to apply content changes while preserving YAML frontmatter (FR-009)
- [X] T023 [US1] Create LangGraph StateGraph workflow in `agents/src/orchestration/workflow.py` using `StateGraph(ReviewState)` with:
  - `workflow.add_node()` for each agent (recruiter, tech_writer, copywriter)
  - `workflow.add_node("supervisor")` for parallel agent coordination via `asyncio.gather`
  - `workflow.add_node("aggregator")` for score calculation
  - `workflow.add_node("revisor")` for content revision
  - `workflow.add_conditional_edges()` for iteration control (revise vs finish)
  - `workflow.compile()` to create executable app
- [X] T024 [US1] Add retry logic with exponential backoff for API calls in `agents/src/agents/base.py` using tenacity (3 attempts per agent)
- [X] T025 [US1] Implement file integrity safeguards in `agents/src/services/qmd_parser.py` with pre-save YAML validation and automatic backup (.bak file creation)

### Integration Tests for User Story 1

- [X] T026 [US1] Integration test for LangGraph workflow execution in `agents/tests/integration/test_langgraph_workflow.py` (verify StateGraph compiles and runs)
- [X] T027 [US1] Integration test for complete content review cycle in `agents/tests/integration/test_content_review.py` (load QMD → evaluate → revise → save)
- [X] T028 [US1] Integration test for iteration loop in `agents/tests/integration/test_content_review.py` (verify stops at threshold or max iterations)
- [X] T029 [US1] Integration test for YAML preservation in `agents/tests/integration/test_qmd_parser.py` (verify frontmatter unchanged after revision)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Portfolio Gap Analysis (Priority: P2)

**Goal**: Identify missing skills and suggest portfolio projects with consistent naming conventions

**Independent Test**: Provide resume lacking specific skills and verify portfolio recommendations with proper naming/URL patterns

### Implementation for User Story 2

- [X] T030 [US2] Create skill gap analysis LangGraph node in `agents/src/orchestration/workflow.py` that compares resume skills against target role requirements (FR-006)
- [X] T031 [US2] Implement portfolio suggestion logic as LangGraph node that generates PortfolioItem entities with `{technology}-{type}` naming pattern (FR-007)
- [X] T032 [US2] Add portfolio URL generation in `agents/src/models/portfolio.py` (GitHub: `https://github.com/{username}/{repo}`, Demo: `https://{repo}.vercel.app`)
- [X] T033 [US2] Integrate portfolio analysis phase into LangGraph StateGraph with `workflow.add_node("portfolio_analyzer")` after content review completes
- [X] T034 [US2] Add portfolio section insertion logic in `agents/src/services/revision.py` to append portfolio projects to QMD content

### Integration Tests for User Story 2

- [X] T035 [US2] Integration test for portfolio gap detection in `agents/tests/integration/test_portfolio_analysis.py` (verify skill gaps identified correctly)
- [X] T036 [US2] Integration test for portfolio naming in `agents/tests/integration/test_portfolio_analysis.py` (verify URL patterns match SC-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visual Design Review (Priority: P3)

**Goal**: Screenshot-based visual evaluation with UX and Visual Designer agents

**Independent Test**: Provide resume HTML screenshot and verify design feedback is returned

### Implementation for User Story 3

- [X] T037 [P] [US3] Implement ScreenshotService in `agents/src/services/screenshot.py` using Playwright for headless browser capture (FR-014)
- [X] T038 [P] [US3] Implement UXDesignerAgent in `agents/src/agents/ux_designer.py` as async LangGraph node with system prompt for information hierarchy and scannability evaluation
- [X] T039 [P] [US3] Implement VisualDesignerAgent in `agents/src/agents/visual_designer.py` as async LangGraph node with system prompt for visual presentation evaluation (uses vision API)
- [X] T040 [US3] Add design review phase to LangGraph StateGraph with `workflow.add_node("design_supervisor")` (only runs if screenshot_url provided, FR-013)
- [X] T041 [US3] Implement screenshot caching in `agents/src/services/screenshot.py` to `/tmp/resume-screenshots/` directory
- [X] T042 [US3] Add graceful degradation in `agents/src/orchestration/workflow.py` to skip design review if dev server not running (warning not error)

### Integration Tests for User Story 3

- [X] T043 [US3] Integration test for screenshot capture in `agents/tests/integration/test_screenshot.py` (verify Playwright captures image from URL)
- [X] T044 [US3] Integration test for design review in `agents/tests/integration/test_design_review.py` (verify UX and Visual agents evaluate screenshot)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Dry Run Preview (Priority: P4)

**Goal**: Preview changes without file modification

**Independent Test**: Run with dry-run flag and verify no file modifications occur while still receiving feedback

### Implementation for User Story 4

- [X] T045 [US4] Add dry_run flag support to ReviewState in `agents/src/orchestration/state.py` (FR-010)
- [X] T046 [US4] Implement dry-run mode in `agents/src/services/revision.py` to skip file write operations when dry_run=True
- [X] T047 [US4] Add dry-run output formatting in CLI to show "DRY RUN" prefix and "no changes saved" message

### Integration Tests for User Story 4

- [X] T048 [US4] Integration test for dry-run mode in `agents/tests/integration/test_dry_run.py` (verify file unchanged after dry-run review)

**Checkpoint**: Dry run mode allows safe preview of all changes

---

## Phase 7: CLI Interface & User Experience

**Purpose**: User-facing command-line interface with all options per cli-interface.md contract

- [X] T049 Create CLI entry point in `agents/src/cli.py` using Click framework with review command
- [X] T050 Add CLI options in `agents/src/cli.py`: --input, --output, --dry-run, --verbose, --target-role, --threshold, --max-iterations, --screenshot-url, --api-key per cli-interface.md
- [X] T051 Implement input validation in `agents/src/cli.py`: file exists, .qmd extension, readable, threshold 1-10, max-iterations >= 1
- [X] T052 Integrate compiled LangGraph workflow with CLI (use `workflow.invoke()` or `workflow.ainvoke()`)
- [X] T053 [P] Implement verbose mode output in `agents/src/cli.py` with timestamped progress logs per FR-012
- [X] T054 [P] Implement summary output in `agents/src/cli.py` with integrated score, iterations used, changes applied, portfolio suggestions per FR-011
- [X] T055 Add exit codes in `agents/src/cli.py`: 0=success, 1=file error, 2=validation error, 3=network error, 4=threshold not met, 5=screenshot warning, 6=partial failure
- [X] T056 Implement error messages in `agents/src/cli.py` with user-friendly troubleshooting guidance per cli-interface.md
- [X] T057 Add environment variable support in `agents/src/cli.py` for ANTHROPIC_API_KEY, RESUME_REVIEW_LOG_LEVEL, RESUME_REVIEW_TIMEOUT

### Integration Tests for CLI

- [X] T058 CLI integration test in `agents/tests/integration/test_cli.py` using Click CliRunner with mocked workflow
- [X] T059 CLI integration test in `agents/tests/integration/test_cli.py` for dry-run mode
- [X] T060 CLI integration test in `agents/tests/integration/test_cli.py` for verbose mode output
- [X] T061 CLI integration test in `agents/tests/integration/test_cli.py` for error handling (invalid file, missing API key)

**Checkpoint**: CLI interface complete with all options and error handling

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final integration

- [X] T062 [P] Create test fixtures in `agents/tests/fixtures/` with sample QMD files for different scenarios (basic resume, resume with gaps, invalid YAML)
- [X] T063 [P] Add package.json scripts integration: `review`, `review:dry`, `review:full`, `review:build` per quickstart.md
- [X] T064 Run quickstart.md validation: verify all setup steps work end-to-end
- [X] T065 Performance validation: verify review completes in <5 minutes (SC-001)
- [X] T066 [P] Add error logging to `~/.resume-review/error.log` for debugging
- [X] T067 [P] Code cleanup: remove debug prints, ensure consistent formatting, add docstrings
- [X] T068 Run constitution check validation: verify FR-009 (YAML preservation), FR-008 (no fabrication), all gates pass
- [X] T069 Create sample output in `agents/tests/fixtures/` showing expected feedback format for documentation

**Checkpoint**: System ready for production use

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-6)**: All depend on Foundational phase completion
  - User Story 1 (P1) is foundation for others but stories are independently testable
  - User Stories 2-4 can proceed in parallel after US1 core workflow exists
- **CLI Interface (Phase 7)**: Depends on all user stories being implemented
- **Polish (Phase 8)**: Depends on all previous phases

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories - MUST COMPLETE FIRST
- **User Story 2 (P2)**: Can start after US1 workflow structure exists - Integrates into workflow after content review
- **User Story 3 (P3)**: Can start after US1 workflow structure exists - Optional feature, independently testable
- **User Story 4 (P4)**: Can start after US1 core implementation - Adds flag to existing workflow

### Within Each User Story

- Models and data structures before services
- Services before agents
- Agents before workflow orchestration
- Core implementation before integration tests
- Story complete before moving to next priority

### Parallel Opportunities

**Setup Phase**:
- T003 (pyproject.toml) || T004 (requirements.txt) || T005 (README.md)

**Foundational Phase**:
- T007 (enums) || T008 (Resume) || T009 (Issue) || T010 (Feedback) || T011 (PortfolioItem) || T012 (ReviewSession)
- T015 (QMD parser) || T016 (base agent) || T017 (config) || T018 (logging)

**User Story 1 Implementation**:
- T019 (RecruiterAgent) || T020 (TechnicalWriterAgent) || T021 (CopywriterAgent)

**User Story 1 Tests**:
- T026 || T027 || T028 || T029 (all integration tests can run in parallel)

**User Story 2 Tests**:
- T035 || T036

**User Story 3 Implementation**:
- T037 (ScreenshotService) || T038 (UXDesignerAgent) || T039 (VisualDesignerAgent)

**User Story 3 Tests**:
- T043 || T044

**CLI Phase**:
- T053 (verbose mode) || T054 (summary output)

**Polish Phase**:
- T062 (fixtures) || T063 (package.json) || T066 (logging) || T067 (cleanup)

---

## Parallel Example: User Story 1

```bash
# Launch all agent implementations together (different files):
Task T019: "Implement RecruiterAgent in agents/src/agents/recruiter.py"
Task T020: "Implement TechnicalWriterAgent in agents/src/agents/technical_writer.py"
Task T021: "Implement CopywriterAgent in agents/src/agents/copywriter.py"

# Launch all integration tests together:
Task T026: "Integration test for LangGraph workflow execution"
Task T027: "Integration test for content review cycle"
Task T028: "Integration test for iteration loop"
Task T029: "Integration test for YAML preservation"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup → Python environment ready
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories) → Models, StateGraph state, and services ready
3. Complete Phase 3: User Story 1 → LangGraph StateGraph content review working
4. Complete Phase 7: CLI Interface → Basic CLI working
5. **STOP and VALIDATE**: Test User Story 1 independently with CLI
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (Day 1)
2. Add User Story 1 + CLI → Test independently → MVP Complete (Day 2-3)
3. Add User Story 2 → Test independently → Portfolio analysis working (Day 4)
4. Add User Story 3 → Test independently → Design review working (Day 5)
5. Add User Story 4 → Test independently → Dry run preview working (Day 5)
6. Polish & Integration → Production ready (Day 6)

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (Day 1)
2. Once Foundational is done:
   - Developer A: User Story 1 core workflow (T019-T025)
   - Developer B: User Story 2 preparation (research skill gap patterns)
   - Developer C: User Story 3 preparation (Playwright screenshot setup)
3. After US1 core workflow exists:
   - Developer A: CLI Interface (Phase 7)
   - Developer B: User Story 2 (T030-T034)
   - Developer C: User Story 3 (T037-T042)
4. Final integration and polish (all developers)

---

## Validation Checklist

### LangGraph StateGraph Compliance (CRITICAL)

- [X] `from langgraph.graph import StateGraph` in workflow.py
- [X] `ReviewState(TypedDict)` defined in state.py
- [X] `StateGraph(ReviewState)` instantiated
- [X] `workflow.add_node()` for each agent
- [X] `workflow.add_conditional_edges()` for iteration control
- [X] `workflow.compile()` called
- [X] Agents run in parallel via `asyncio.gather` in supervisor node

### Format Compliance

All tasks follow checklist format:
- Task ID present (T001-T069)
- [P] marker for parallelizable tasks
- [US#] label for user story phases (US1, US2, US3, US4)
- Exact file paths included in descriptions
- Requirements referenced (FR-XXX, SC-XXX)

### Coverage Verification

- All 4 user stories have dedicated phases
- All acceptance criteria from spec.md covered
- All functional requirements (FR-001 to FR-014) implemented
- All success criteria (SC-001 to SC-007) validated
- All entities from data-model.md created
- All CLI options from cli-interface.md included
- All quickstart.md setup steps validated

### Dependency Validation

- Foundational phase blocks all user stories
- User Story 1 (P1) identified as MVP foundation
- User Stories 2-4 can build on US1 independently
- Parallel opportunities clearly marked
- Integration tests placed after implementation

### Constitution Compliance

- QMD file is single source of truth (FR-001, FR-009)
- No fabrication allowed (FR-008, ActionType enum)
- YAML frontmatter preservation enforced (FR-009, T025)
- Dry-run preview workflow supported (FR-010, US4)
- No modifications to existing Quarto/Node.js toolchain

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Integration tests are included for critical validation but not exhaustive
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Python 3.13 required (downgrade from 3.14 for LangGraph compatibility)
- ANTHROPIC_API_KEY environment variable required for execution
- Review costs ~$1 per run (see quickstart.md cost analysis)
- Target completion time: <5 minutes per review (SC-001)
- **CRITICAL**: All workflow orchestration MUST use LangGraph StateGraph, not plain Python classes
