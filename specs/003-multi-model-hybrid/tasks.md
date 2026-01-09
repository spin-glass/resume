# Tasks: Multi-Model Hybrid Configuration

**Input**: Design documents from `/specs/003-multi-model-hybrid/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in specification - unit/integration tests included only for critical components

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

All paths relative to `packages/resume-review/`:
- Implementation: `src/`
- Tests: `tests/`
- Config: `pyproject.toml`, `README.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency setup for multi-provider LLM support

- [ ] T001 Add new dependencies to packages/resume-review/pyproject.toml (google-genai[aiohttp]>=1.0.0, openai>=1.0.0)
- [ ] T002 Install dependencies via pip install -e . from packages/resume-review/
- [ ] T003 [P] Update packages/resume-review/.env to include GEMINI_API_KEY and OPENAI_API_KEY (keep existing ANTHROPIC_API_KEY)
- [ ] T004 [P] Create packages/resume-review/src/config/model_config.py for agent-to-model mappings
- [ ] T005 [P] Create empty packages/resume-review/src/services/llm_client.py file
- [ ] T006 [P] Create empty packages/resume-review/src/services/llm_factory.py file

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core LLM client abstraction that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Implement LLMResponse dataclass in packages/resume-review/src/services/llm_client.py
- [ ] T008 Implement BaseLLMClient abstract base class with generate_async() method in packages/resume-review/src/services/llm_client.py
- [ ] T009 [P] Implement GeminiClient with google-genai SDK in packages/resume-review/src/services/llm_client.py
- [ ] T010 [P] Implement OpenAIClient with openai SDK in packages/resume-review/src/services/llm_client.py
- [ ] T011 [P] Implement AnthropicClient wrapper for existing AsyncAnthropic in packages/resume-review/src/services/llm_client.py
- [ ] T012 Implement AGENT_MODEL_MAP constant in packages/resume-review/src/config/model_config.py
- [ ] T013 Implement MODEL_PRICING constant in packages/resume-review/src/config/model_config.py
- [ ] T014 Implement AgentName enum in packages/resume-review/src/config/model_config.py
- [ ] T015 Implement LLMClientFactory.create_client() method in packages/resume-review/src/services/llm_factory.py
- [ ] T016 Add API key validation logic to LLMClientFactory in packages/resume-review/src/services/llm_factory.py
- [ ] T017 Create MockLLMClient for testing in packages/resume-review/tests/unit/services/test_llm_client.py
- [ ] T018 Write unit tests for GeminiClient in packages/resume-review/tests/unit/services/test_llm_client.py
- [ ] T019 Write unit tests for OpenAIClient in packages/resume-review/tests/unit/services/test_llm_client.py
- [ ] T020 Write unit tests for AnthropicClient in packages/resume-review/tests/unit/services/test_llm_client.py
- [ ] T021 Write unit tests for LLMClientFactory in packages/resume-review/tests/unit/services/test_llm_factory.py
- [ ] T022 [P] Update Config class in packages/resume-review/src/utils/config.py to load GEMINI_API_KEY and OPENAI_API_KEY from environment
- [ ] T023 [P] Add get_gemini_api_key() and get_openai_api_key() methods to Config class in packages/resume-review/src/utils/config.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Fast and Cost-Effective Review Execution (Priority: P1) 🎯 MVP

**Goal**: Enable hybrid model configuration with automatic optimal model assignment per agent to achieve 50% cost reduction and 70% speed improvement

**Independent Test**: Run review with hybrid configuration, measure execution time (<3 min) and cost (<$0.55)

### Implementation for User Story 1

- [ ] T024 [P] [US1] Update BaseAgent.__init__() to accept llm_client parameter instead of api_key in packages/resume-review/src/agents/base.py
- [ ] T025 [P] [US1] Update BaseAgent.evaluate_async() to use self.llm_client.generate_async() in packages/resume-review/src/agents/base.py
- [ ] T026 [P] [US1] Add gemini_api_key field to ReviewState in packages/resume-review/src/workflow/state.py
- [ ] T027 [P] [US1] Add openai_api_key field to ReviewState in packages/resume-review/src/workflow/state.py
- [ ] T028 [P] [US1] Add anthropic_api_key field to ReviewState in packages/resume-review/src/workflow/state.py
- [ ] T029 [P] [US1] Add token_usage dict field to ReviewState in packages/resume-review/src/workflow/state.py
- [ ] T030 [P] [US1] Add override_model field to ReviewState in packages/resume-review/src/workflow/state.py
- [ ] T031 [US1] Update supervisor_node to construct llm_client via LLMClientFactory in packages/resume-review/src/workflow/nodes/supervisor.py
- [ ] T032 [US1] Pass llm_client to agent constructors in supervisor_node in packages/resume-review/src/workflow/nodes/supervisor.py
- [ ] T033 [US1] Add token usage logging after each agent call in supervisor_node in packages/resume-review/src/workflow/nodes/supervisor.py
- [ ] T034 [US1] Update ReviewWorkflow._create_initial_state() to accept 3 API keys in packages/resume-review/src/workflow/runner.py
- [ ] T035 [US1] Pass API keys to ReviewState in ReviewWorkflow._create_initial_state() in packages/resume-review/src/workflow/runner.py
- [ ] T036 [US1] Add --gemini-api-key CLI option in packages/resume-review/src/cli.py
- [ ] T037 [US1] Add --openai-api-key CLI option in packages/resume-review/src/cli.py
- [ ] T038 [US1] Add --anthropic-api-key CLI option (replace --api-key) in packages/resume-review/src/cli.py
- [ ] T039 [US1] Implement calculate_cost() function using MODEL_PRICING in packages/resume-review/src/config/model_config.py
- [ ] T040 [US1] Add cost summary logging at end of review in packages/resume-review/src/workflow/runner.py
- [ ] T041 [US1] Write unit test for BaseAgent with injected llm_client in packages/resume-review/tests/unit/agents/test_base.py
- [ ] T042 [US1] Write unit test for ReviewState with new API key fields in packages/resume-review/tests/unit/workflow/test_state.py

**Validation Tasks**:
- [ ] T043 [US1] Run dry-run review with hybrid configuration and verify no errors
- [ ] T044 [US1] Measure execution time with hybrid config (target: <3 min)
- [ ] T045 [US1] Measure API cost with hybrid config (target: <$0.55)
- [ ] T046 [US1] Verify each agent uses assigned model (check logs)

**Checkpoint**: User Story 1 complete - Hybrid configuration functional with cost/speed optimization

---

## Phase 4: User Story 2 - Reliable Resume Revision (Priority: P1)

**Goal**: Eliminate fuzzy replacement errors by implementing full-rewrite architecture in Revisor

**Independent Test**: Run 10 revision cycles, verify 0 "Fuzzy replacement failed" errors

### Implementation for User Story 2

- [ ] T047 [P] [US2] Create REVISOR_SYSTEM_PROMPT for full rewrite in packages/resume-review/src/config/prompts.py
- [ ] T048 [US2] Implement RevisorAgent.apply_revisions_async() with full rewrite logic in packages/resume-review/src/agents/revisor.py (create new file if needed)
- [ ] T049 [US2] Implement YAML frontmatter extraction in apply_revisions_async() in packages/resume-review/src/agents/revisor.py
- [ ] T050 [US2] Implement YAML frontmatter validation after generation in packages/resume-review/src/agents/revisor.py
- [ ] T051 [US2] Set max_tokens=8000 for full resume rewrite in packages/resume-review/src/agents/revisor.py
- [ ] T052 [US2] Update revisor_node to use RevisorAgent.apply_revisions_async() in packages/resume-review/src/workflow/nodes/revisor.py
- [ ] T053 [US2] Update revisor_node to construct Revisor's llm_client (Gemini) via LLMClientFactory in packages/resume-review/src/workflow/nodes/revisor.py
- [ ] T054 [US2] Remove calls to old RevisionService if present in packages/resume-review/src/workflow/nodes/revisor.py
- [ ] T055 [US2] Add explicit "no truncation" instruction to REVISOR_SYSTEM_PROMPT in packages/resume-review/src/config/prompts.py
- [ ] T056 [US2] Add output length validation in apply_revisions_async() in packages/resume-review/src/agents/revisor.py

**Validation Tasks**:
- [ ] T057 [US2] Create test resume with complex revisions (deletions, fixes, completions)
- [ ] T058 [US2] Run 10 consecutive reviews with test resume, verify 0 replacement errors
- [ ] T059 [US2] Verify YAML frontmatter unchanged in all 10 runs
- [ ] T060 [US2] Verify all revision instructions applied correctly

**Checkpoint**: User Story 2 complete - Revision process 100% reliable with full rewrite

---

## Phase 5: User Story 3 - Enhanced Technical Evaluation (Priority: P2)

**Goal**: Improve technical evaluation depth using o3-mini model for Technical Writer agent

**Independent Test**: Run evaluation on resume with intentional technical issues, verify 90%+ detection

### Implementation for User Story 3

- [ ] T061 [P] [US3] Update TECHNICAL_WRITER_SYSTEM_PROMPT with enhanced detection instructions in packages/resume-review/src/config/prompts.py
- [ ] T062 [P] [US3] Add anachronistic technology detection logic to Technical Writer prompt in packages/resume-review/src/config/prompts.py
- [ ] T063 [P] [US3] Add incompatible stack detection logic to Technical Writer prompt in packages/resume-review/src/config/prompts.py
- [ ] T064 [P] [US3] Add duplicate project detection logic to Technical Writer prompt in packages/resume-review/src/config/prompts.py
- [ ] T065 [US3] Verify Technical Writer uses o3-mini model in AGENT_MODEL_MAP in packages/resume-review/src/config/model_config.py
- [ ] T066 [US3] Update TechnicalWriterAgent to output structured RevisionInstruction format in packages/resume-review/src/agents/technical_writer.py

**Validation Tasks**:
- [ ] T067 [US3] Create test resume with anachronistic tech (e.g., "Next.js 14 in 2015")
- [ ] T068 [US3] Create test resume with incompatible stack (e.g., "Django + Flask")
- [ ] T069 [US3] Create test resume with duplicate projects
- [ ] T070 [US3] Run Technical Writer evaluation, verify detection of all 3 issues
- [ ] T071 [US3] Calculate detection rate (target: ≥90%)

**Checkpoint**: User Story 3 complete - Technical evaluation quality significantly improved

---

## Phase 6: User Story 4 - Flexible Model Override for Testing (Priority: P3)

**Goal**: Allow users to override default hybrid configuration with single model for all agents

**Independent Test**: Run review with --model flag, verify all agents use specified model

### Implementation for User Story 4

- [ ] T072 [P] [US4] Add --model CLI option for override in packages/resume-review/src/cli.py
- [ ] T073 [P] [US4] Implement detect_provider_from_model() helper in packages/resume-review/src/services/llm_factory.py
- [ ] T074 [US4] Update LLMClientFactory.create_client() to check override_model first in packages/resume-review/src/services/llm_factory.py
- [ ] T075 [US4] If override_model set, use same provider/model for all agents in packages/resume-review/src/services/llm_factory.py
- [ ] T076 [US4] Add validation for invalid model names in override mode in packages/resume-review/src/services/llm_factory.py
- [ ] T077 [US4] Add validation that required API key exists for override model in packages/resume-review/src/services/llm_factory.py

**Validation Tasks**:
- [ ] T078 [US4] Test --model gemini-3.0-flash flag, verify all agents use Gemini
- [ ] T079 [US4] Test --model claude-sonnet-4-5-20250929 flag, verify all agents use Claude
- [ ] T080 [US4] Test --model o3-mini flag, verify all agents use OpenAI
- [ ] T081 [US4] Test invalid model name, verify clear error message
- [ ] T082 [US4] Test override without required API key, verify error message

**Checkpoint**: User Story 4 complete - Model override functional for testing/troubleshooting

---

## Phase 7: User Story 5 - Verbose Model Selection Reporting (Priority: P3)

**Goal**: Display which models are assigned to each agent when verbose mode enabled

**Independent Test**: Run review with --verbose, verify model assignments visible in output

### Implementation for User Story 5

- [ ] T083 [P] [US5] Add verbose mode check in CLI review() function in packages/resume-review/src/cli.py
- [ ] T084 [P] [US5] If verbose and hybrid mode, print "Mode: Hybrid configuration" in packages/resume-review/src/cli.py
- [ ] T085 [P] [US5] If verbose and hybrid mode, print agent-to-model mapping in packages/resume-review/src/cli.py
- [ ] T086 [P] [US5] If verbose and override mode, print "Mode: Override all with [model]" in packages/resume-review/src/cli.py
- [ ] T087 [US5] Add model name logging in each agent's evaluate_async() call in packages/resume-review/src/agents/base.py
- [ ] T088 [US5] Format verbose output with clear model assignments per agent in packages/resume-review/src/cli.py

**Validation Tasks**:
- [ ] T089 [US5] Run review with --verbose (hybrid mode), verify model assignments printed
- [ ] T090 [US5] Run review with --verbose (override mode), verify override model printed
- [ ] T091 [US5] Verify verbose output shows different models for different agents (hybrid)
- [ ] T092 [US5] Verify verbose output shows same model for all agents (override)

**Checkpoint**: User Story 5 complete - Verbose mode provides transparency

---

## Phase 8: Integration & End-to-End Testing

**Purpose**: Validate all user stories work together and meet success criteria

- [ ] T093 [P] Create integration test suite in packages/resume-review/tests/integration/test_multi_model.py
- [ ] T094 [P] Write integration test for hybrid configuration (US1) in packages/resume-review/tests/integration/test_multi_model.py
- [ ] T095 [P] Write integration test for full rewrite reliability (US2) in packages/resume-review/tests/integration/test_multi_model.py
- [ ] T096 [P] Write integration test for enhanced technical eval (US3) in packages/resume-review/tests/integration/test_multi_model.py
- [ ] T097 [P] Write integration test for model override (US4) in packages/resume-review/tests/integration/test_multi_model.py
- [ ] T098 [P] Write integration test for verbose reporting (US5) in packages/resume-review/tests/integration/test_multi_model.py
- [ ] T099 Mark integration tests with @pytest.mark.integration in packages/resume-review/tests/integration/test_multi_model.py
- [ ] T100 Run all unit tests (pytest tests/unit -v)
- [ ] T101 Run integration tests with real APIs (pytest tests/integration -v -m integration)

**Success Criteria Validation**:
- [ ] T102 SC-001: Measure execution time on actual resume (<3 minutes)
- [ ] T103 SC-002: Measure API cost on actual resume (<$0.55)
- [ ] T104 SC-003: Run 20 consecutive reviews, verify 0 replacement errors
- [ ] T105 SC-004: Test technical detection rate (≥90%)
- [ ] T106 SC-005: Test incomplete sentence correction (100%)
- [ ] T107 SC-006: Test YAML preservation (100%)
- [ ] T108 SC-007: Test hybrid execution (all agents use assigned models)
- [ ] T109 SC-008: Test override for all supported models
- [ ] T110 SC-009: Test verbose reporting displays model assignments

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and final improvements

- [ ] T111 [P] Update packages/resume-review/README.md with multi-model configuration section
- [ ] T112 [P] Add API key setup instructions for Gemini/OpenAI to packages/resume-review/README.md
- [ ] T113 [P] Document --model override flag usage in packages/resume-review/README.md
- [ ] T114 [P] Add troubleshooting section for API key issues in packages/resume-review/README.md
- [ ] T115 [P] Document cost optimization benefits in packages/resume-review/README.md
- [ ] T116 [P] Add examples of hybrid vs override mode usage in packages/resume-review/README.md
- [ ] T117 [P] Deprecate old RevisionService in packages/resume-review/src/services/revision.py (add deprecation comment)
- [ ] T118 Run quickstart.md validation (follow guide, verify all steps work)
- [ ] T119 Run final smoke test: full review with real resume in hybrid mode
- [ ] T120 Verify all success criteria met (SC-001 through SC-009)
- [ ] T121 Create summary report of cost/speed improvements vs baseline

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 & US2 (P1): Should be done first (core value proposition)
  - US3 (P2): Can start after US1 complete (builds on hybrid config)
  - US4 & US5 (P3): Can start anytime after Foundational (independent features)
- **Integration (Phase 8)**: Depends on all user stories being complete
- **Polish (Phase 9)**: Depends on integration testing complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - No dependencies, but uses US1's llm_client infrastructure
- **User Story 3 (P2)**: Can start after US1 complete (uses hybrid configuration)
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Independent, extends US1
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - Independent, extends US1

### Critical Path

```
Setup (T002-T006)
  → Foundational (T007-T021) [BLOCKING]
    → US1: Hybrid Config (T024-T046) [P1, MVP]
    → US2: Full Rewrite (T047-T060) [P1, MVP]
    → US3: Enhanced Tech Eval (T061-T071) [P2]
    → US4: Model Override (T072-T082) [P3]
    → US5: Verbose Reporting (T083-T092) [P3]
      → Integration Testing (T093-T110)
        → Polish (T111-T121)
```

### Parallel Opportunities

**Setup Phase**: T004, T005, T006 can run in parallel

**Foundational Phase**: T009, T010, T011 (client implementations) can run in parallel after T007-T008

**User Story 1**: T024-T030 (state/base agent updates) can run in parallel

**User Story 2**: T047, T055 (prompt updates) can run in parallel

**User Story 3**: T061-T064 (prompt enhancements) can run in parallel

**User Story 4**: T072, T073 (CLI and helper) can run in parallel

**User Story 5**: T083-T086 (verbose output) can run in parallel

**Integration**: T093-T098 (test writing) can run in parallel

**Polish**: T111-T116 (documentation) can run in parallel

---

## Parallel Example: Foundational Phase

```bash
# After T007-T008 complete, launch client implementations together:
Task T009: "Implement GeminiClient in llm_client.py"
Task T010: "Implement OpenAIClient in llm_client.py"
Task T011: "Implement AnthropicClient in llm_client.py"

# After T015-T016 complete, launch unit tests together:
Task T018: "Unit tests for GeminiClient"
Task T019: "Unit tests for OpenAIClient"
Task T020: "Unit tests for AnthropicClient"
Task T021: "Unit tests for LLMClientFactory"
```

---

## Parallel Example: User Story 1

```bash
# Launch state and agent updates together:
Task T024: "Update BaseAgent.__init__() to accept llm_client"
Task T025: "Update BaseAgent.evaluate_async() to use llm_client"
Task T026: "Add gemini_api_key to ReviewState"
Task T027: "Add openai_api_key to ReviewState"
Task T028: "Add anthropic_api_key to ReviewState"
Task T029: "Add token_usage to ReviewState"
Task T030: "Add override_model to ReviewState"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup (T002-T006)
2. Complete Phase 2: Foundational (T007-T021) **[CRITICAL BLOCKING PHASE]**
3. Complete Phase 3: User Story 1 (T024-T046)
4. Complete Phase 4: User Story 2 (T047-T060)
5. **STOP and VALIDATE**: Test US1 & US2 together
   - Verify hybrid config works
   - Verify full rewrite eliminates errors
   - Measure cost (<$0.55) and time (<3 min)
6. Deploy/demo if ready - **This is a complete, valuable MVP**

### Incremental Delivery

1. MVP (US1 + US2) → 50% cost reduction + 100% revision reliability
2. Add US3 → Enhanced technical evaluation quality
3. Add US4 → Model override for testing flexibility
4. Add US5 → Verbose reporting for transparency
5. Each addition enhances value without breaking previous functionality

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T002-T021)
2. Once Foundational is done (after T021):
   - **Developer A**: User Story 1 (T024-T046)
   - **Developer B**: User Story 2 (T047-T060)
   - Both can work in parallel since they modify different files
3. Once US1 & US2 complete:
   - **Developer A**: User Story 3 (T061-T071)
   - **Developer B**: User Story 4 (T072-T082)
   - **Developer C**: User Story 5 (T083-T092)
4. Integration testing (T093-T110) done together
5. Polish (T111-T121) divided among team

---

## Task Count Summary

- **Phase 1 (Setup)**: 6 tasks (+1 for .env update)
- **Phase 2 (Foundational)**: 17 tasks [BLOCKING] (+2 for utils/config.py updates)
- **Phase 3 (US1)**: 23 tasks [P1, MVP]
- **Phase 4 (US2)**: 14 tasks [P1, MVP]
- **Phase 5 (US3)**: 11 tasks [P2]
- **Phase 6 (US4)**: 11 tasks [P3]
- **Phase 7 (US5)**: 10 tasks [P3]
- **Phase 8 (Integration)**: 18 tasks
- **Phase 9 (Polish)**: 11 tasks

**Total**: 121 tasks

**MVP Scope** (US1 + US2): 60 tasks (50% of total, includes Setup + Foundational)
**P1 Priority** (US1 + US2): 37 implementation tasks
**P2 Priority** (US3): 11 tasks
**P3 Priority** (US4 + US5): 21 tasks

**Parallel Opportunities Identified**: 35 tasks marked [P]

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Foundational phase (T007-T021) MUST complete before ANY user story work begins
- MVP = US1 + US2 (hybrid config + full rewrite) delivers maximum value
- US3-US5 are enhancements that can be added incrementally
- All 9 success criteria (SC-001 through SC-009) validated in Phase 8
