# Tasks: StateGraph Agent Node Separation

**Feature**: 011-stategraph-node-separation
**Input**: Design documents from `/specs/011-stategraph-node-separation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Test tasks are included as this is a refactoring that requires validation of behavior preservation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Project type**: Single Python package (`packages/resume-review`)
- **Source root**: `packages/resume-review/src/`
- **Test root**: `packages/resume-review/tests/`
- All paths relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Extend ReviewState schema and prepare for node separation

- [X] T001 Extend ReviewState in packages/resume-review/src/workflow/state.py with three optional feedback fields (recruiter_feedback, tech_writer_feedback, copywriter_feedback)
- [X] T002 [P] Create packages/resume-review/src/workflow/nodes/routing.py for router_node implementation
- [X] T003 [P] Verify all required imports in packages/resume-review/src/workflow/nodes/__init__.py exist (RecruiterAgent, TechnicalWriterAgent, CopywriterAgent, LLMClientFactory)

**Checkpoint**: State schema extended, new files created

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core node functions that MUST be complete before graph restructuring

**⚠️ CRITICAL**: No graph modification can happen until all node functions are implemented and tested

- [X] T004 Implement router_node in packages/resume-review/src/workflow/nodes/routing.py per contracts/router_node.md (stateless pass-through with iteration logging)
- [X] T005 [P] Create packages/resume-review/src/workflow/nodes/recruiter.py and implement recruiter_node per contracts/README.md agent pattern
- [X] T006 [P] Create packages/resume-review/src/workflow/nodes/tech_writer.py and implement tech_writer_node per contracts/README.md agent pattern
- [X] T007 [P] Create packages/resume-review/src/workflow/nodes/copywriter.py and implement copywriter_node per contracts/README.md agent pattern
- [X] T008 Modify aggregator_node in packages/resume-review/src/workflow/nodes/aggregator.py to collect from separate state fields (recruiter_feedback, tech_writer_feedback, copywriter_feedback) per contracts/aggregator_node.md

**Checkpoint**: All 5 node functions implemented (router, 3 agents, modified aggregator) - ready for graph integration

---

## Phase 3: User Story 1 - Real-time Agent Monitoring (Priority: P1) 🎯 MVP

**Goal**: Developers can see which agent is executing and how long each takes via real-time logs

**Independent Test**: Run `pnpm review --verbose` and verify logs show "Starting recruiter node", "Starting tech_writer node", "Starting copywriter node" with timestamps, plus completion messages with durations

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Create test_router_node.py in packages/resume-review/tests/unit/workflow/nodes/ and add test_router_node_returns_empty_dict per contracts/router_node.md
- [X] T010 [P] [US1] Create test_recruiter_node.py in packages/resume-review/tests/unit/workflow/nodes/ and add test_recruiter_node_success per contracts/README.md
- [X] T011 [P] [US1] Create test_tech_writer_node.py in packages/resume-review/tests/unit/workflow/nodes/ and add test_tech_writer_node_success per contracts/README.md
- [X] T012 [P] [US1] Create test_copywriter_node.py in packages/resume-review/tests/unit/workflow/nodes/ and add test_copywriter_node_success per contracts/README.md
- [X] T013 [P] [US1] Add test_aggregator_collects_from_separate_fields in packages/resume-review/tests/unit/workflow/nodes/test_aggregator.py per contracts/aggregator_node.md

### Implementation for User Story 1

- [X] T014 [US1] Update graph.py in packages/resume-review/src/workflow/graph.py to add router, recruiter, tech_writer, copywriter nodes per contracts/graph_edges.md
- [X] T015 [US1] Add fan-out edges (router→recruiter, router→tech_writer, router→copywriter) in packages/resume-review/src/workflow/graph.py per contracts/graph_edges.md
- [X] T016 [US1] Add fan-in edges (recruiter→aggregator, tech_writer→aggregator, copywriter→aggregator) in packages/resume-review/src/workflow/graph.py per contracts/graph_edges.md
- [X] T017 [US1] Update entry point from "supervisor" to "router" in packages/resume-review/src/workflow/graph.py per contracts/graph_edges.md
- [X] T018 [US1] Update revisor loop edge from "revisor"→"supervisor" to "revisor"→"router" in packages/resume-review/src/workflow/graph.py per contracts/graph_edges.md
- [X] T019 [US1] Remove supervisor_node import and add new node imports in packages/resume-review/src/workflow/graph.py
- [X] T020 [US1] Verify logging shows per-agent timing by running `pnpm review:dry --verbose` and checking output matches quickstart.md expectations

**Checkpoint**: User Story 1 complete - real-time per-agent monitoring functional via logs

---

## Phase 4: User Story 2 - LangSmith Trace Analysis (Priority: P2)

**Goal**: Each agent appears as a separate node in LangSmith traces for per-agent performance analysis

**Independent Test**: Enable LangSmith (`export LANGCHAIN_TRACING_V2=true`), run `pnpm review`, verify trace shows three separate nodes (recruiter, tech_writer, copywriter) with individual metrics in LangSmith UI

### Tests for User Story 2

- [X] T021 [P] [US2] Add test_graph_has_separate_agent_nodes in packages/resume-review/tests/integration/test_langgraph_workflow.py to verify node names include "router", "recruiter", "tech_writer", "copywriter"
- [X] T022 [P] [US2] Add test_graph_has_fan_out_edges in packages/resume-review/tests/integration/test_langgraph_workflow.py to verify router→agent edges exist
- [X] T023 [P] [US2] Add test_graph_has_fan_in_edges in packages/resume-review/tests/integration/test_langgraph_workflow.py to verify agent→aggregator edges exist

### Implementation for User Story 2

- [X] T024 [US2] Update test assertions that check for "supervisor" node to check for new node names in packages/resume-review/tests/integration/test_langgraph_workflow.py per research.md RT-006
- [X] T025 [US2] Remove test_supervisor_node_runs_agents_in_parallel (no longer relevant) in packages/resume-review/tests/integration/test_langgraph_workflow.py
- [X] T026 [US2] Add integration test test_agent_nodes_run_in_parallel in packages/resume-review/tests/integration/test_langgraph_workflow.py to verify parallel execution via timing
- [X] T027 [US2] Verify LangSmith integration by running with LANGCHAIN_TRACING_V2=true and checking trace structure per quickstart.md

**Checkpoint**: User Story 2 complete - LangSmith shows separate agent nodes with individual metrics

---

## Phase 5: User Story 3 - Workflow Visualization (Priority: P3)

**Goal**: Visual graph shows agents running in parallel (router → agents → aggregator) for architectural understanding

**Independent Test**: Generate workflow graph using `build_review_workflow().get_graph().draw_mermaid()` and verify three parallel arrows from router to agents, then convergence at aggregator

### Tests for User Story 3

- [X] T028 [P] [US3] Add test_graph_visualization_shows_fan_out in packages/resume-review/tests/integration/test_langgraph_workflow.py to verify graph structure via mermaid export
- [X] T029 [P] [US3] Add test_router_fans_out_to_three_agents in packages/resume-review/tests/integration/test_langgraph_workflow.py per contracts/graph_edges.md

### Implementation for User Story 3

- [X] T030 [US3] Create script or documentation in specs/011-stategraph-node-separation/quickstart.md for generating graph visualization (already exists, verify it works)
- [X] T031 [US3] Add example mermaid diagram to specs/011-stategraph-node-separation/quickstart.md showing fan-out/fan-in pattern (already exists, verify accuracy)
- [X] T032 [US3] Test graph export functionality by running `python -c "from packages.resume_review.src.workflow.graph import build_review_workflow; print(build_review_workflow().get_graph().draw_mermaid())"` and comparing to expected structure

**Checkpoint**: User Story 3 complete - workflow visualization clearly shows fan-out/fan-in pattern

---

## Phase 6: User Story 4 - Agent-Specific Retry Logic (Priority: P4)

**Goal**: Enable retrying only failed agents without re-running successful ones (future enhancement)

**Independent Test**: NOT IMPLEMENTED IN THIS FEATURE - marked as future work in spec.md "Out of Scope"

**Note**: This user story is explicitly out of scope for this feature. Tasks below document the groundwork laid for future implementation.

### Groundwork for User Story 4 (Documentation Only)

- [X] T033 [US4] Document per-agent state fields enable future retry logic in specs/011-stategraph-node-separation/research.md (already documented in RT-004, verify completeness)
- [X] T034 [US4] Add comment in packages/resume-review/src/workflow/nodes/aggregator.py noting that partial feedback collection enables future per-agent retry
- [X] T035 [US4] Document retry strategy in specs/011-stategraph-node-separation/spec.md User Story 4 section (already exists, no changes needed)

**Checkpoint**: User Story 4 groundwork documented - future implementation path clear

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

### Error Handling & Edge Cases

- [X] T036 [P] Add test_recruiter_node_handles_exception in packages/resume-review/tests/unit/workflow/nodes/test_recruiter_node.py per contracts/README.md to verify graceful degradation
- [X] T037 [P] Add test_tech_writer_node_handles_exception in packages/resume-review/tests/unit/workflow/nodes/test_tech_writer_node.py per contracts/README.md
- [X] T038 [P] Add test_copywriter_node_handles_exception in packages/resume-review/tests/unit/workflow/nodes/test_copywriter_node.py per contracts/README.md
- [X] T039 [P] Add test_aggregator_handles_missing_feedback in packages/resume-review/tests/unit/workflow/nodes/test_aggregator.py to verify partial feedback handling
- [X] T040 Add test_aggregator_returns_error_if_no_feedback in packages/resume-review/tests/unit/workflow/nodes/test_aggregator.py per contracts/aggregator_node.md

### Graph Structure Validation

- [X] T041 Add test_graph_loops_back_to_router in packages/resume-review/tests/integration/test_langgraph_workflow.py to verify revisor→router edge per contracts/graph_edges.md
- [X] T042 Add test_supervisor_node_removed in packages/resume-review/tests/integration/test_langgraph_workflow.py to verify "supervisor" no longer exists in node list

### Performance & Backward Compatibility

- [X] T043 Run end-to-end review with timing comparison to verify total duration within 5% of baseline per spec.md SC-008
- [X] T044 Verify ReviewSession output format unchanged by comparing before/after review outputs per spec.md SC-005
- [X] T045 Run all existing integration tests to ensure backward compatibility per spec.md SC-006

### Documentation & Code Quality

- [X] T046 [P] Update docstrings in packages/resume-review/src/workflow/graph.py to reflect new fan-out/fan-in architecture
- [X] T047 [P] Update docstrings in packages/resume-review/src/workflow/nodes/aggregator.py to document state field collection behavior
- [X] T048 [P] Add inline comments explaining fan-out/fan-in semantics in packages/resume-review/src/workflow/graph.py
- [X] T049 Verify all node files are under 200 lines per CLAUDE.md guidelines
- [X] T050 Run quickstart.md validation steps per specs/011-stategraph-node-separation/quickstart.md

### Final Integration Test

- [X] T051 Run full review with screenshot analysis (`pnpm review:full --verbose`) to verify design agents still work with new architecture
- [X] T052 Verify Quarto validation retry loop (009-quarto-retry-loop) works with new graph structure
- [X] T053 Run `pnpm test:python` to ensure entire test suite passes

**Checkpoint**: All polish tasks complete - feature ready for production

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - Core functionality
- **User Story 2 (Phase 4)**: Depends on US1 (needs graph structure) - Can run in parallel with US3/US4 if team capacity
- **User Story 3 (Phase 5)**: Depends on US1 (needs graph structure) - Can run in parallel with US2/US4
- **User Story 4 (Phase 6)**: Documentation only - Can run anytime after US1
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational phase - No dependencies on other stories ✅ MVP
- **User Story 2 (P2)**: Depends on US1 (needs new graph structure) - Otherwise independent
- **User Story 3 (P3)**: Depends on US1 (needs new graph structure) - Otherwise independent
- **User Story 4 (P4)**: Documentation only - No implementation dependencies

### Within Each Phase

**Phase 2 (Foundational)**:
- T004 (router) can run in parallel with T005-T007 (agent nodes)
- T005, T006, T007 can run in parallel (separate files)
- T008 (aggregator) depends on T005-T007 being understood (same pattern)

**Phase 3 (US1 - Tests)**:
- T009-T013 can all run in parallel (separate test files)

**Phase 3 (US1 - Implementation)**:
- T014-T019 must run sequentially (all modify graph.py)
- T020 runs after all implementation

**Phase 4 (US2 - Tests)**:
- T021-T023 can run in parallel (separate test files)

**Phase 4 (US2 - Implementation)**:
- T024-T026 modify same test file (sequential)
- T027 runs after all changes

**Phase 5 (US3)**:
- T028-T029 can run in parallel (tests)
- T030-T032 run sequentially (documentation verification)

**Phase 7 (Polish)**:
- T036-T040 can run in parallel (separate test files)
- T041-T042 modify same file (sequential)
- T043-T045 must run sequentially (integration tests)
- T046-T049 can run in parallel (different files)
- T051-T053 must run sequentially (final validation)

### Parallel Opportunities

**Setup (Phase 1)**: T002 and T003 can run in parallel

**Foundational (Phase 2)**: T005, T006, T007 (agent nodes) can run in parallel

**US1 Tests**: T009, T010, T011, T012, T013 can all run in parallel

**US2 Tests**: T021, T022, T023 can run in parallel

**US3 Tests**: T028, T029 can run in parallel

**Polish Error Tests**: T036, T037, T038, T039 can run in parallel

**Polish Docs**: T046, T047, T048 can run in parallel

---

## Parallel Example: User Story 1 (Real-time Agent Monitoring)

```bash
# Step 1: Launch all test creation in parallel
Task T009: "Create test_router_node.py and add test_router_node_returns_empty_dict"
Task T010: "Create test_recruiter_node.py and add test_recruiter_node_success"
Task T011: "Create test_tech_writer_node.py and add test_tech_writer_node_success"
Task T012: "Create test_copywriter_node.py and add test_copywriter_node_success"
Task T013: "Add test_aggregator_collects_from_separate_fields to test_aggregator.py"

# Step 2: Graph updates (sequential, same file)
Task T014: "Add nodes to graph.py"
Task T015: "Add fan-out edges to graph.py"
Task T016: "Add fan-in edges to graph.py"
Task T017: "Update entry point to router"
Task T018: "Update revisor loop edge"
Task T019: "Update imports in graph.py"

# Step 3: Validation
Task T020: "Verify logging shows per-agent timing"
```

---

## Parallel Example: User Story 2 (LangSmith Tracing)

```bash
# Launch all test creation in parallel
Task T021: "Add test_graph_has_separate_agent_nodes"
Task T022: "Add test_graph_has_fan_out_edges"
Task T023: "Add test_graph_has_fan_in_edges"

# Test updates (sequential, same file)
Task T024: "Update test assertions for new node names"
Task T025: "Remove obsolete supervisor test"
Task T026: "Add new parallel execution test"

# Validation
Task T027: "Verify LangSmith integration"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

This feature's MVP is **User Story 1: Real-time Agent Monitoring**, which delivers immediate value by exposing per-agent visibility in logs.

**Minimum Viable Implementation**:
1. Complete Phase 1: Setup (extend state, create files)
2. Complete Phase 2: Foundational (implement all 5 node functions)
3. Complete Phase 3: User Story 1 (graph restructuring + tests)
4. **STOP and VALIDATE**: Run `pnpm review --verbose` and verify per-agent logs
5. If working: Merge and deploy

**Time Estimate**: ~6-8 hours for MVP (Phases 1-3)

### Incremental Delivery

1. **MVP (US1)** → Real-time monitoring functional → Merge & Deploy
2. **US2 (LangSmith)** → Trace analysis enabled → Merge & Deploy
3. **US3 (Visualization)** → Graph export documented → Merge & Deploy
4. **Polish** → Error handling hardened, docs complete → Final Release

Each increment adds value without breaking previous functionality.

### Parallel Team Strategy

With multiple developers:

1. **Developer A**: Phase 1 + Phase 2 (foundation)
2. Once Phase 2 done:
   - **Developer A**: User Story 1 (graph restructuring)
   - **Developer B**: User Story 2 tests (can prep while A finishes US1)
   - **Developer C**: User Story 3 documentation (can prep in parallel)
3. After US1 done, US2 and US3 complete quickly (just test + doc updates)
4. **All**: Polish tasks can be divided (error tests, integration tests, docs)

**Parallelization Note**: US2 and US3 depend on US1's graph changes, so true parallelization is limited. Best strategy is sequential delivery (US1→US2→US3) with quick iterations.

---

## Task Count Summary

- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational)**: 5 tasks ⚠️ BLOCKS all user stories
- **Phase 3 (US1 - Real-time Monitoring)**: 12 tasks (5 tests + 7 implementation) 🎯 MVP
- **Phase 4 (US2 - LangSmith Tracing)**: 7 tasks (3 tests + 4 implementation)
- **Phase 5 (US3 - Workflow Visualization)**: 5 tasks (2 tests + 3 verification)
- **Phase 6 (US4 - Retry Logic)**: 3 tasks (documentation only, out of scope)
- **Phase 7 (Polish)**: 18 tasks (tests, docs, validation)

**Total**: 53 tasks

**Parallelizable Tasks**: 18 tasks marked with [P] (34% can run in parallel within phases)

**Critical Path**: Setup → Foundational → US1 → US2 → US3 → Polish (sequential due to dependencies)

---

## Notes

- **[P]** tasks indicate different files with no dependencies - can run in parallel
- **[Story]** labels map tasks to user stories for traceability and independent testing
- Each user story has clear checkpoint where it should be independently testable
- Tests are written FIRST (TDD approach) to ensure they fail before implementation
- Commit frequently (ideally after each task or logical group)
- Stop at any checkpoint to validate story independently before proceeding
- **MVP scope**: Phase 1 + Phase 2 + Phase 3 (User Story 1) - delivers core monitoring value
- **Out of scope**: User Story 4 is documentation only (future feature groundwork)
- **Performance requirement**: Total duration must stay within 5% of baseline (SC-008)
- **Backward compatibility**: All existing tests must pass except node name checks (SC-006)

---

## Format Validation ✅

All tasks follow the required format:
- ✅ Every task starts with `- [ ]` (checkbox)
- ✅ Every task has sequential ID (T001-T053)
- ✅ Parallelizable tasks marked with [P]
- ✅ User story tasks marked with [US1], [US2], [US3], [US4]
- ✅ All tasks include file paths
- ✅ Setup/Foundational/Polish tasks have NO story label (correct)
- ✅ User Story phase tasks have story labels (correct)
