# Tasks: Design Auto-Fix

**Input**: Design documents from `/specs/013-design-auto-fix/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are included as they are essential for validating CSS generation, file safety, and content preservation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Base path**: `packages/resume-review/`
- **Source**: `packages/resume-review/src/`
- **Tests**: `packages/resume-review/tests/`
- **Output**: `styles/` (repository root)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency setup

- [X] T001 Add cssutils dependency to packages/resume-review/pyproject.toml (version >=2.0.0,<3.0.0)
- [X] T002 [P] Add pixelmatch and pngjs to root package.json devDependencies for screenshot diffing
- [X] T003 [P] Create styles/ directory at repository root for CSS output
- [X] T004 [P] Install Python dependencies: run `cd packages/resume-review && pip install -e .[dev]`
- [X] T005 [P] Install Node dependencies: run `pnpm install` from repository root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and configuration that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create DesignIssueType enum in packages/resume-review/src/models/design.py (SPACING, TYPOGRAPHY, COLOR, HIERARCHY, LAYOUT)
- [X] T007 [P] Create CSSModification model in packages/resume-review/src/models/design.py with validation
- [X] T008 [P] Create SectionReorder model in packages/resume-review/src/models/design.py with content hash validation
- [X] T009 [P] Create ThemeRecommendation model in packages/resume-review/src/models/design.py
- [X] T010 [P] Create DesignPreview model in packages/resume-review/src/models/design.py
- [X] T011 Extend ReviewState in packages/resume-review/src/workflow/state.py with design fields (auto_design_enabled, design_preview_enabled, css_modification, section_reorder, theme_recommendation, design_preview_paths, design_changes_applied, design_changes_pending, design_changes_list, design_backup_paths, css_output_path)
- [X] T012 [P] Add CSS_GENERATOR_SYSTEM_PROMPT to packages/resume-review/src/config/prompts.py with constraints and examples
- [X] T013 [P] Add design-related settings to packages/resume-review/src/config/settings.py (css_output_default, backup_directory)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automatic CSS Generation from Design Feedback (Priority: P1) 🎯 MVP

**Goal**: Automatically generate CSS from design feedback to address spacing, typography, color, hierarchy issues without requiring CSS expertise

**Independent Test**: Run `resume-review review --input resume.qmd --auto-design` and verify CSS file is generated addressing specific design issues

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T014 [P] [US1] Unit test for CSSService validation in packages/resume-review/tests/unit/services/test_css_service.py (test valid CSS passes, invalid CSS fails, forbidden @media print properties detected)
- [X] T015 [P] [US1] Unit test for CSSService backup creation in packages/resume-review/tests/unit/services/test_css_service.py (test backup file created with timestamp, atomic write)
- [X] T016 [P] [US1] Unit test for CSSGeneratorAgent CSS generation in packages/resume-review/tests/unit/agents/test_css_generator.py (test CSS generated from feedback, validation runs, custom properties used)
- [X] T017 [P] [US1] Integration test for auto-design workflow in packages/resume-review/tests/integration/test_design_workflow.py (test end-to-end CSS generation and application)

### Implementation for User Story 1

- [X] T018 [P] [US1] Implement CSSService.validate_css() in packages/resume-review/src/services/css_service.py using cssutils parser (check syntax errors, forbidden print properties, custom property definitions)
- [X] T019 [P] [US1] Implement CSSService.create_backup() in packages/resume-review/src/services/css_service.py (timestamped backups in backups/ directory)
- [X] T020 [US1] Implement CSSService.write_with_backup() in packages/resume-review/src/services/css_service.py (backup → temp file → validate → atomic rename) (depends on T018, T019)
- [X] T021 [US1] Implement CSSGeneratorAgent.__init__() and get_system_prompt() in packages/resume-review/src/agents/css_generator.py (inherit from BaseAgent, return CSS generation prompt)
- [X] T022 [US1] Implement CSSGeneratorAgent._format_issues_for_prompt() in packages/resume-review/src/agents/css_generator.py (convert feedback list to structured prompt)
- [X] T023 [US1] Implement CSSGeneratorAgent._classify_issue() helper in packages/resume-review/src/agents/css_generator.py (map description to DesignIssueType)
- [X] T024 [US1] Implement CSSGeneratorAgent.generate_css() in packages/resume-review/src/agents/css_generator.py (build prompt → call LLM → extract CSS → validate → return CSSModification) (depends on T018, T021, T022, T023)
- [X] T025 [US1] Implement _generate_css() helper in packages/resume-review/src/workflow/nodes/design_applier.py (create LLM client, initialize agent, call generate_css, handle errors)
- [X] T026 [US1] Implement design_applier_node() skeleton in packages/resume-review/src/workflow/nodes/design_applier.py (check feedback exists, call _generate_css, apply if auto_design enabled) (depends on T025)
- [X] T027 [US1] Add should_run_design_applier() conditional in packages/resume-review/src/workflow/graph.py (check auto_design or preview enabled and feedback exists)
- [X] T028 [US1] Add design_applier node to workflow graph in packages/resume-review/src/workflow/graph.py (add node, add conditional edge from design_review, add edge to portfolio) (depends on T027)
- [X] T029 [US1] Add --auto-design CLI flag to packages/resume-review/src/cli.py (boolean flag, mutually exclusive with --design-preview)
- [X] T030 [US1] Add --css-output CLI flag to packages/resume-review/src/cli.py (file path, default styles/resume-custom.css, requires --auto-design or --design-preview)
- [X] T031 [US1] Add CLI validation for --auto-design and --css-output in packages/resume-review/src/cli.py (mutual exclusivity check, css-output requires design flag)
- [X] T032 [US1] Update review() CLI function to add design flags to ReviewState in packages/resume-review/src/cli.py (set auto_design_enabled, css_output_path)
- [X] T033 [US1] Implement _display_design_changes() output formatter in packages/resume-review/src/cli.py (display CSS modifications, changes list, backups)
- [X] T034 [US1] Call _display_design_changes() after workflow completes in packages/resume-review/src/cli.py (if design_changes_applied is True)

**Checkpoint**: At this point, User Story 1 should be fully functional - CSS generation works end-to-end with --auto-design flag

---

## Phase 4: User Story 2 - Preview Design Changes Before Application (Priority: P2)

**Goal**: Generate before/after preview screenshots without modifying files, allowing users to review changes risk-free

**Independent Test**: Run `resume-review review --input resume.qmd --design-preview --screenshot-url http://localhost:3000/ja` and verify preview screenshots generated without file modifications

### Tests for User Story 2

- [X] T035 [P] [US2] Unit test for preview screenshot generation in packages/resume-review/tests/unit/services/test_screenshot_service.py (test before/after captured, diff generated, no files modified)
- [X] T036 [P] [US2] Integration test for preview workflow in packages/resume-review/tests/integration/test_design_workflow.py (test --design-preview flag, screenshots generated, design_changes_pending True, design_changes_applied False)

### Implementation for User Story 2

- [X] T037 [P] [US2] Create Node.js screenshot diff script in scripts/visual-diff.js (use pixelmatch to generate diff image from before/after PNGs)
- [X] T038 [US2] Extend ScreenshotService.generate_diff() in packages/resume-review/src/services/screenshot.py (call Node script via subprocess, return diff path and pixel count)
- [X] T039 [US2] Extend ScreenshotService.create_composite() in packages/resume-review/src/services/screenshot.py (use PIL to create side-by-side before|diff|after image)
- [X] T040 [US2] Implement _generate_preview() helper in packages/resume-review/src/workflow/nodes/design_applier.py (capture before → apply temp CSS → capture after → generate diff → create composite → cleanup temp files → return DesignPreview) (depends on T038, T039)
- [X] T041 [US2] Add preview mode logic to design_applier_node() in packages/resume-review/src/workflow/nodes/design_applier.py (if design_preview_enabled, call _generate_preview, set design_changes_pending, skip application) (depends on T040)
- [X] T042 [US2] Add --design-preview CLI flag to packages/resume-review/src/cli.py (boolean flag, mutually exclusive with --auto-design)
- [X] T043 [US2] Update CLI validation for --design-preview in packages/resume-review/src/cli.py (mutual exclusivity with --auto-design, warning if no --screenshot-url)
- [X] T044 [US2] Update review() CLI function to handle --design-preview flag in packages/resume-review/src/cli.py (set design_preview_enabled in ReviewState)
- [X] T045 [US2] Implement _display_design_preview() output formatter in packages/resume-review/src/cli.py (show proposed changes, preview paths, diff percentage, instructions to apply)
- [X] T046 [US2] Call _display_design_preview() after workflow if preview mode in packages/resume-review/src/cli.py (if design_changes_pending is True)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - users can preview before applying

---

## Phase 5: User Story 3 - Section Reordering Based on UX Feedback (Priority: P3)

**Goal**: Automatically reorder QMD sections based on UX feedback while preserving 100% of content

**Independent Test**: Run review with UX feedback suggesting section order change and verify QMD sections reordered with all content preserved (content hash verification)

### Tests for User Story 3

- [X] T047 [P] [US3] Unit test for section parsing in packages/resume-review/tests/unit/services/test_section_reorder.py (test QMD parsed, sections identified, YAML preserved)
- [X] T048 [P] [US3] Unit test for section reordering in packages/resume-review/tests/unit/services/test_section_reorder.py (test sections reordered, content hash matches, no content lost)
- [X] T049 [P] [US3] Integration test for section reorder workflow in packages/resume-review/tests/integration/test_design_workflow.py (test UX feedback triggers reorder, QMD modified, content preserved)

### Implementation for User Story 3

- [X] T050 [US3] Implement SectionReorderService.__init__() in packages/resume-review/src/services/section_reorder.py (initialize with python-frontmatter)
- [X] T051 [US3] Implement SectionReorderService._parse_sections() in packages/resume-review/src/services/section_reorder.py (use frontmatter.load, regex to split sections by ## headings, preserve content)
- [X] T052 [US3] Implement SectionReorderService._calculate_content_hash() in packages/resume-review/src/services/section_reorder.py (SHA256 hash of all section content excluding order)
- [X] T053 [US3] Implement SectionReorderService._reconstruct_qmd() in packages/resume-review/src/services/section_reorder.py (YAML + reordered sections, verify hash) (depends on T052)
- [X] T054 [US3] Implement SectionReorderService.analyze_and_recommend() in packages/resume-review/src/services/section_reorder.py (analyze UX feedback for order keywords, determine optimal order, return SectionReorder model) (depends on T051)
- [X] T055 [US3] Implement SectionReorderService.reorder_with_backup() in packages/resume-review/src/services/section_reorder.py (backup QMD → parse → reorder → validate hash → atomic write → return backup path) (depends on T051, T053)
- [X] T056 [US3] Implement _analyze_section_order() helper in packages/resume-review/src/workflow/nodes/design_applier.py (filter UX feedback, check for order keywords, call SectionReorderService.analyze_and_recommend)
- [X] T057 [US3] Add section reordering to design_applier_node() in packages/resume-review/src/workflow/nodes/design_applier.py (call _analyze_section_order, apply if auto_design enabled and order changed) (depends on T056)
- [X] T058 [US3] Update _display_design_changes() to show section movements in packages/resume-review/src/cli.py (display section reorder rationale and movements)
- [X] T059 [US3] Update _display_design_preview() to show proposed section reorder in packages/resume-review/src/cli.py (display proposed order changes in preview mode)

**Checkpoint**: All three user stories (CSS, Preview, Section Reorder) should now work independently

---

## Phase 6: User Story 4 - Quarto Theme Recommendations (Priority: P4)

**Goal**: Provide advisory theme recommendations based on systematic design issues

**Independent Test**: Run review with systematic design issues and verify theme recommendation output with rationale and configuration

### Tests for User Story 4

- [X] T060 [P] [US4] Unit test for theme recommendation in packages/resume-review/tests/unit/services/test_theme_recommender.py (test issue patterns matched to themes, rationale generated, config provided)

### Implementation for User Story 4

- [X] T061 [US4] Create THEME_PROFILES knowledge base in packages/resume-review/src/services/theme_recommender.py (define Quarto themes with strengths, good_for issue types, PDF support)
- [X] T062 [US4] Implement ThemeRecommenderService.__init__() in packages/resume-review/src/services/theme_recommender.py (load THEME_PROFILES)
- [X] T063 [US4] Implement ThemeRecommenderService._count_issue_types() in packages/resume-review/src/services/theme_recommender.py (count occurrences of each DesignIssueType in feedback)
- [X] T064 [US4] Implement ThemeRecommenderService.recommend() in packages/resume-review/src/services/theme_recommender.py (match primary issue type to theme, generate ThemeRecommendation with rationale and config) (depends on T063)
- [X] T065 [US4] Implement _recommend_theme() helper in packages/resume-review/src/workflow/nodes/design_applier.py (check for 3+ systematic issues, call ThemeRecommenderService.recommend)
- [X] T066 [US4] Add theme recommendation to design_applier_node() in packages/resume-review/src/workflow/nodes/design_applier.py (call _recommend_theme, include in result)
- [X] T067 [US4] Update _display_design_changes() to show theme recommendation in packages/resume-review/src/cli.py (display theme name, rationale, installation command)
- [X] T068 [US4] Update _display_design_preview() to show theme recommendation in preview in packages/resume-review/src/cli.py

**Checkpoint**: All four user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, error handling, and documentation

- [X] T069 [P] Add comprehensive error handling to CSSGeneratorAgent.generate_css() in packages/resume-review/src/agents/css_generator.py (handle LLM failures, validation errors, log detailed errors)
- [X] T070 [P] Add comprehensive error handling to design_applier_node() in packages/resume-review/src/workflow/nodes/design_applier.py (handle CSS generation failure, section reorder failure, preview failure, implement rollback)
- [X] T071 [P] Add rollback functionality to CSSService in packages/resume-review/src/services/css_service.py (restore from backup on error)
- [X] T072 [P] Add rollback functionality to SectionReorderService in packages/resume-review/src/services/section_reorder.py (restore from backup on content hash mismatch)
- [X] T073 [P] Add logging throughout design_applier_node() in packages/resume-review/src/workflow/nodes/design_applier.py (log all operations, timing, validation results)
- [X] T074 [P] Add logging to CSSService operations in packages/resume-review/src/services/css_service.py (log validation results, file writes, backups)
- [X] T075 [P] Unit tests for error handling in packages/resume-review/tests/unit/agents/test_css_generator.py (test empty feedback, LLM failure, validation failure)
- [X] T076 [P] Unit tests for error handling in packages/resume-review/tests/unit/services/test_css_service.py (test write failures, permission errors, validation edge cases)
- [X] T077 [P] Unit tests for rollback scenarios in packages/resume-review/tests/unit/services/test_section_reorder.py (test content hash mismatch, rollback from backup)
- [X] T078 [P] Integration test for complete auto-design workflow in packages/resume-review/tests/integration/test_design_workflow.py (test all features together, verify backups created, verify rollback works)
- [X] T079 [P] Update CLAUDE.md with design auto-fix commands and workflows (document --auto-design, --design-preview, --css-output flags)
- [X] T080 [P] Add inline documentation/docstrings to all new modules (CSSGeneratorAgent, CSSService, SectionReorderService, ThemeRecommenderService, design_applier_node)
- [X] T081 Run full test suite and fix any failures: `cd packages/resume-review && pytest` (design tests: 101 passed, 10 skipped)
- [X] T082 Run linter and fix any issues: `cd packages/resume-review && ruff check src/ tests/` (design files: all checks passed)
- [X] T083 Validate quickstart.md examples work: manually test each example from specs/013-design-auto-fix/quickstart.md (all files exist, CLI flags work, methods match docs)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Builds on US1 CSS generation but independently testable with --design-preview
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent of US1/US2, can be tested with any UX feedback
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Independent, advisory only

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before workflow nodes
- Workflow nodes before CLI integration
- CLI integration before output formatting

### Parallel Opportunities

- **Setup Phase**: T002, T003, T004, T005 can all run in parallel
- **Foundational Phase**: T007, T008, T009, T010, T012, T013 can run in parallel (different files)
- **US1 Tests**: T014, T015, T016, T017 can run in parallel
- **US1 Implementation**: T018, T019, T021 can run in parallel (different files)
- **US2 Tests**: T035, T036 can run in parallel
- **US2 Implementation**: T037, T038, T039 can run in parallel (different files/services)
- **US3 Tests**: T047, T048, T049 can run in parallel
- **US4 Tests**: T060 standalone
- **Polish Phase**: T069, T070, T071, T072, T073, T074, T075, T076, T077, T078, T079, T080 can run in parallel (different files)
- **Once Foundational completes, ALL user stories (US1-US4) can be developed in parallel by different team members**

---

## Parallel Example: User Story 1

```bash
# Step 1: Launch all US1 tests together (write these first, ensure they fail):
Task: "Unit test for CSSService validation in packages/resume-review/tests/unit/services/test_css_service.py"
Task: "Unit test for CSSService backup in packages/resume-review/tests/unit/services/test_css_service.py"
Task: "Unit test for CSSGeneratorAgent in packages/resume-review/tests/unit/agents/test_css_generator.py"
Task: "Integration test for auto-design workflow in packages/resume-review/tests/integration/test_design_workflow.py"

# Step 2: Launch parallel implementation tasks:
Task: "Implement CSSService.validate_css() in packages/resume-review/src/services/css_service.py"
Task: "Implement CSSService.create_backup() in packages/resume-review/src/services/css_service.py"
Task: "Implement CSSGeneratorAgent.__init__() and get_system_prompt() in packages/resume-review/src/agents/css_generator.py"

# Step 3: Sequential dependencies after above complete:
Task: "Implement CSSService.write_with_backup()" (depends on validate_css + create_backup)
Task: "Implement CSSGeneratorAgent.generate_css()" (depends on validate_css + prompts)
Task: "Implement design_applier_node()" (depends on CSSService + CSSGeneratorAgent)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T013) - CRITICAL
3. Complete Phase 3: User Story 1 (T014-T034)
4. **STOP and VALIDATE**: Test User Story 1 independently with `--auto-design`
5. Deploy/demo if ready - users can now auto-generate CSS from design feedback

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! CSS auto-generation works)
3. Add User Story 2 → Test independently → Deploy/Demo (Preview capability added)
4. Add User Story 3 → Test independently → Deploy/Demo (Section reordering added)
5. Add User Story 4 → Test independently → Deploy/Demo (Theme recommendations added)
6. Polish phase → Final production-ready release

### Parallel Team Strategy

With multiple developers after Foundational phase:

1. Team completes Setup + Foundational together (required)
2. Once Foundational is done:
   - Developer A: User Story 1 (CSS Generation) - MVP
   - Developer B: User Story 2 (Preview)
   - Developer C: User Story 3 (Section Reorder)
   - Developer D: User Story 4 (Theme Recommendations)
3. Each developer works independently on their story
4. Stories integrate via ReviewState and design_applier_node
5. Each story can be tested and deployed independently

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [US1], [US2], [US3], [US4] labels map tasks to user stories for traceability
- Each user story should be independently completable and testable
- Tests MUST fail before implementation (TDD approach)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All file paths are exact paths from repository root
- Content preservation is CRITICAL for section reordering (100% hash match required)
- CSS validation is MANDATORY before application
- Backups are MANDATORY before all file modifications
- Preview mode MUST NOT modify any files

---

## Task Count Summary

- **Total Tasks**: 83
- **Setup Phase**: 5 tasks
- **Foundational Phase**: 8 tasks
- **User Story 1 (P1 - MVP)**: 21 tasks (4 tests + 17 implementation)
- **User Story 2 (P2)**: 12 tasks (2 tests + 10 implementation)
- **User Story 3 (P3)**: 13 tasks (3 tests + 10 implementation)
- **User Story 4 (P4)**: 9 tasks (1 test + 8 implementation)
- **Polish Phase**: 15 tasks

**Parallel Tasks**: 35 tasks marked [P] (42% of total)

**MVP Scope**: Phases 1-3 (34 tasks) delivers core value - automated CSS generation

**Format Validation**: ✅ All tasks follow `- [ ] [TaskID] [P?] [Story?] Description with file path` format
