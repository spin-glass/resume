# Tasks: Quarto Validation Auto-Retry Loop

**Input**: Design documents from `/specs/009-quarto-retry-loop/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Tests**: Test tasks are NOT included as they were not explicitly requested in the feature specification.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Single project structure: `packages/resume-review/src/`, `packages/resume-review/tests/`
- All paths relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Verify Python 3.13 environment and existing dependencies (LangGraph 1.0.0+, Anthropic SDK 0.25.0+, Pydantic 2.0+)
- [x] T002 Review existing codebase structure in packages/resume-review/src/ to understand integration points

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 [P] Create models/validation.py with ValidationResult model including Pydantic validators
- [x] T004 [P] Create models/validation.py with RetryAttempt model including Pydantic validators
- [x] T005 Add validation_retry_count, max_validation_retries, strict_validation, current_retry_attempts fields to ReviewState in packages/resume-review/src/workflow/state.py
- [x] T006 Add max_validation_retries and strict_validation fields to ReviewSession model in packages/resume-review/src/models/session.py
- [x] T007 [P] Add DEFAULT_MAX_VALIDATION_RETRIES = 3 and DEFAULT_STRICT_VALIDATION = False to packages/resume-review/src/config/settings.py
- [x] T008 [P] Add --max-validation-retries CLI option to packages/resume-review/src/cli.py
- [x] T009 [P] Add --strict-validation CLI option to packages/resume-review/src/cli.py
- [x] T010 Update ReviewWorkflow._create_initial_state() in packages/resume-review/src/workflow/runner.py to initialize validation retry state fields

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automatic Recovery from Validation Failures (Priority: P1) 🎯 MVP

**Goal**: System automatically detects Quarto validation errors, generates corrective feedback, and retries revision process up to max_retries limit

**Independent Test**: Introduce Quarto syntax error (standalone `#`), run review workflow, verify automatic correction within retry limit

### Implementation for User Story 1

- [x] T011 [P] [US1] Add create_validation_feedback() method to QuartoValidator in packages/resume-review/src/services/quarto_validator.py
- [x] T012 [P] [US1] Implement error pattern matching for standalone `#` markers in create_validation_feedback()
- [x] T013 [P] [US1] Implement error pattern matching for YAML syntax errors in create_validation_feedback()
- [x] T014 [P] [US1] Implement error pattern matching for unclosed code blocks in create_validation_feedback()
- [x] T015 [P] [US1] Implement error pattern matching for invalid markdown tables in create_validation_feedback()
- [x] T016 [P] [US1] Implement fallback pattern for unknown Quarto errors in create_validation_feedback()
- [x] T017 [US1] Add _validate_and_retry() async method to ReviewWorkflow in packages/resume-review/src/workflow/runner.py
- [x] T018 [US1] Implement retry loop logic in _validate_and_retry() with max_retries enforcement
- [x] T019 [US1] Add _invoke_revisor_for_retry() async method to ReviewWorkflow in packages/resume-review/src/workflow/runner.py
- [x] T020 [US1] Add _save_retry_artifact() method to save intermediate QMD files in packages/resume-review/src/workflow/runner.py
- [x] T021 [US1] Modify _handle_node_persistence() in packages/resume-review/src/workflow/runner.py to call _validate_and_retry() after revisor node
- [x] T022 [US1] Implement strict_validation mode handling (exit on failure vs. continue with warning) in _validate_and_retry()
- [x] T023 [US1] Add retry count reset logic when incrementing current_iteration in packages/resume-review/src/workflow/runner.py
- [x] T024 [US1] Update ReviewWorkflow to pass max_validation_retries and strict_validation from ReviewSession to workflow state

**Checkpoint**: At this point, User Story 1 should be fully functional - automatic retry loop works end-to-end

---

## Phase 4: User Story 2 - Transparent Retry Visibility (Priority: P2)

**Goal**: Users can review detailed logs showing each validation attempt, errors detected, corrections applied, and final outcomes

**Independent Test**: Run workflow with validation failures, verify retry log file exists with timestamped entries for all attempts

### Implementation for User Story 2

- [x] T025 [P] [US2] Create services/retry_logger.py with RetryLogger class __init__ method
- [x] T026 [P] [US2] Implement log_initial_validation() method in RetryLogger with markdown formatting
- [x] T027 [P] [US2] Implement log_retry_attempt() method in RetryLogger with markdown formatting
- [x] T028 [P] [US2] Implement finalize_log() method in RetryLogger with summary section
- [x] T029 [P] [US2] Implement get_log_path() method in RetryLogger returning iteration log file path
- [x] T030 [P] [US2] Implement _ensure_log_file() helper method in RetryLogger to create log file and directories
- [x] T031 [P] [US2] Implement _append_to_log() helper method in RetryLogger for markdown content appending
- [x] T032 [US2] Integrate RetryLogger into _validate_and_retry() in packages/resume-review/src/workflow/runner.py
- [x] T033 [US2] Call RetryLogger.log_initial_validation() for first validation attempt in _validate_and_retry()
- [x] T034 [US2] Call RetryLogger.log_retry_attempt() for each retry iteration in _validate_and_retry()
- [x] T035 [US2] Call RetryLogger.finalize_log() when retry loop completes in _validate_and_retry()
- [x] T036 [US2] Add error handling in RetryLogger methods to log warnings on file I/O failures without crashing workflow

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - automatic retry with comprehensive logging

---

## Phase 5: User Story 3 - Configurable Retry Behavior (Priority: P3)

**Goal**: Users can configure maximum retry attempts and strict validation mode via CLI options

**Independent Test**: Run with --max-validation-retries=1 (verify 1 retry), run with --strict-validation (verify exit on failure)

### Implementation for User Story 3

- [x] T037 [US3] Verify CLI options from Phase 2 (T008, T009) correctly pass values to ReviewSession
- [x] T038 [US3] Add CLI option validation to ensure max_validation_retries >= 0 in packages/resume-review/src/cli.py
- [x] T039 [US3] Test that max_validation_retries=0 skips retry loop entirely in _validate_and_retry()
- [x] T040 [US3] Test that custom max_validation_retries value is respected in retry loop
- [x] T041 [US3] Test that strict_validation=True causes workflow to exit on validation failure
- [x] T042 [US3] Test that strict_validation=False allows workflow to continue with warning on validation failure
- [x] T043 [US3] Add help text and examples to CLI documentation for --max-validation-retries and --strict-validation options

**Checkpoint**: All user stories should now be independently functional with full configuration support

---

## Phase 6: Integration & Edge Cases

**Purpose**: Handle edge cases and ensure robustness across all user stories

- [x] T044 [P] Handle Quarto validation timeout (>30s) as validation failure in _validate_and_retry()
- [x] T045 [P] Handle case where revisor introduces new validation errors during retry
- [x] T046 [P] Verify retry artifacts (iter{N}_retry{M}.qmd files) are saved correctly in session directory
- [x] T047 [P] Verify retry count does not accumulate across iterations (resets properly)
- [x] T048 Add logging statements for retry loop entry, each attempt, and final outcome in _validate_and_retry()
- [x] T049 Ensure ValidationFeedback is distinguishable from normal agent feedback (agent_name="quarto_validator")
- [x] T050 Test that max_retries limit prevents infinite loops even if revisor consistently fails

---

## Phase 7: Polish & Documentation

**Purpose**: Final improvements and documentation updates

- [x] T051 [P] Update CLAUDE.md with validation retry workflow documentation
- [x] T052 [P] Add retry log example to docs/ directory showing sample validation_retry.md format
- [x] T053 [P] Update README with --max-validation-retries and --strict-validation CLI options
- [x] T054 [P] Review and update error messages for clarity and user-friendliness
- [x] T055 [P] Add code comments to complex retry logic in _validate_and_retry()
- [x] T056 Run full review workflow end-to-end test with intentional validation errors
- [x] T057 Verify performance: retry mechanism adds <30 seconds overhead per validation failure (SC-005)
- [x] T058 Validate against quickstart.md implementation checklist

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - MVP core functionality
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) and User Story 1 (logging integration)
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) and User Story 1 (configuration testing)
- **Integration & Edge Cases (Phase 6)**: Depends on all user stories being complete
- **Polish (Phase 7)**: Depends on all implementation being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Integrates with User Story 1 (adds logging to retry loop) - Can be developed in parallel but needs US1 for integration
- **User Story 3 (P3)**: Extends User Story 1 (tests configuration) - Can be developed in parallel but needs US1 for testing

### Within Each User Story

**User Story 1**:
- T011-T016 (error pattern matching) can run in parallel
- T017-T024 must run sequentially (retry loop implementation)
- T021 depends on T017-T020 being complete

**User Story 2**:
- T025-T031 (RetryLogger methods) can run in parallel
- T032-T036 must run sequentially after T025-T031 (integration with retry loop)
- T032 depends on User Story 1 being complete

**User Story 3**:
- T037-T043 can run mostly in parallel (different test scenarios)
- T037 verifies Phase 2 CLI work, so Phase 2 must be complete

### Parallel Opportunities

- **Phase 2 (Foundational)**: T003-T004 (models), T007 (settings), T008-T009 (CLI options) can run in parallel
- **Phase 3 (User Story 1)**: T011-T016 (all error patterns) can run in parallel
- **Phase 4 (User Story 2)**: T025-T031 (all RetryLogger methods) can run in parallel
- **Phase 5 (User Story 3)**: T037-T042 (all configuration tests) can run in parallel
- **Phase 6 (Integration)**: T044-T047, T049 can run in parallel
- **Phase 7 (Polish)**: T051-T055 (documentation) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all error pattern implementations together:
Task: "Implement error pattern matching for standalone # markers in create_validation_feedback()"
Task: "Implement error pattern matching for YAML syntax errors in create_validation_feedback()"
Task: "Implement error pattern matching for unclosed code blocks in create_validation_feedback()"
Task: "Implement error pattern matching for invalid markdown tables in create_validation_feedback()"
Task: "Implement fallback pattern for unknown Quarto errors in create_validation_feedback()"

# After patterns complete, implement retry loop sequentially:
Task: "Add _validate_and_retry() async method"
Task: "Implement retry loop logic in _validate_and_retry()"
Task: "Add _invoke_revisor_for_retry() async method"
# ... etc
```

---

## Parallel Example: User Story 2

```bash
# Launch all RetryLogger methods together:
Task: "Create services/retry_logger.py with RetryLogger class __init__ method"
Task: "Implement log_initial_validation() method in RetryLogger"
Task: "Implement log_retry_attempt() method in RetryLogger"
Task: "Implement finalize_log() method in RetryLogger"
Task: "Implement get_log_path() method in RetryLogger"
Task: "Implement _ensure_log_file() helper method in RetryLogger"
Task: "Implement _append_to_log() helper method in RetryLogger"

# After RetryLogger complete, integrate into workflow sequentially:
Task: "Integrate RetryLogger into _validate_and_retry()"
Task: "Call RetryLogger.log_initial_validation()"
# ... etc
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T010) - CRITICAL - blocks all stories
3. Complete Phase 3: User Story 1 (T011-T024)
4. **STOP and VALIDATE**: Test automatic retry loop independently
   - Introduce validation error (standalone `#`)
   - Run `pnpm review`
   - Verify automatic correction within 3 retries
   - Check that workflow continues without manual intervention
5. Deploy/demo if ready - **This is a functional MVP!**

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (T001-T010)
2. Add User Story 1 → Test independently → **Deploy MVP** (automatic retry works!)
3. Add User Story 2 → Test independently → Deploy (retry with logging!)
4. Add User Story 3 → Test independently → Deploy (fully configurable!)
5. Add Integration & Edge Cases → Harden implementation
6. Add Polish → Production-ready
7. Each phase adds value without breaking previous functionality

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T010)
2. Once Foundational is done:
   - **Developer A**: User Story 1 (T011-T024) - Core retry loop
   - **Developer B**: User Story 2 (T025-T036) - Logging (needs US1 for integration)
   - **Developer C**: User Story 3 (T037-T043) - Configuration (needs US1 for testing)
3. Stories integrate at defined points (US2 integrates into US1's retry loop)
4. Team converges on Integration & Edge Cases (T044-T050)
5. Team completes Polish together (T051-T058)

---

## Task Summary

**Total Tasks**: 58

**Breakdown by Phase**:
- Phase 1 (Setup): 2 tasks
- Phase 2 (Foundational): 8 tasks
- Phase 3 (User Story 1 - P1): 14 tasks
- Phase 4 (User Story 2 - P2): 12 tasks
- Phase 5 (User Story 3 - P3): 7 tasks
- Phase 6 (Integration): 7 tasks
- Phase 7 (Polish): 8 tasks

**Breakdown by User Story**:
- User Story 1 (Automatic Recovery): 14 tasks
- User Story 2 (Transparent Logging): 12 tasks
- User Story 3 (Configurable Behavior): 7 tasks
- Infrastructure/Shared: 25 tasks

**Parallel Opportunities**:
- Phase 2: 5 tasks can run in parallel
- Phase 3 (US1): 6 tasks can run in parallel
- Phase 4 (US2): 7 tasks can run in parallel
- Phase 5 (US3): 6 tasks can run in parallel
- Phase 6: 5 tasks can run in parallel
- Phase 7: 6 tasks can run in parallel

**MVP Scope** (Suggested):
- Phases 1-3 only (T001-T024)
- Total: 24 tasks
- Delivers: Automatic retry loop with basic functionality
- Independent test: Validates automatic error correction

---

## Notes

- **[P] tasks**: Different files, no dependencies - can run in parallel
- **[Story] label**: Maps task to specific user story for traceability
- **No test tasks**: Tests were not explicitly requested in the specification
- **Independent stories**: Each user story should be independently completable and testable
- **Commit strategy**: Commit after each task or logical group of parallel tasks
- **Validation checkpoints**: Stop at any checkpoint to validate story independently before proceeding
- **File paths**: All paths are absolute from repository root for clarity

---

## Format Validation

✅ All tasks follow checklist format: `- [ ] [ID] [P?] [Story?] Description`
✅ All tasks include file paths where applicable
✅ Task IDs sequential (T001-T058)
✅ [P] markers only on parallelizable tasks
✅ [Story] labels on all user story phase tasks
✅ Setup and Foundational phases have no story labels
✅ Polish phase has no story labels
