# Implementation Plan: StateGraph Agent Node Separation

**Branch**: `011-stategraph-node-separation` | **Date**: 2026-01-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/011-stategraph-node-separation/spec.md`

## Summary

Refactor the LangGraph workflow to expose individual agent nodes (recruiter, tech_writer, copywriter) instead of hiding them within a supervisor node. This enables per-agent monitoring, debugging, and LangSmith tracing without changing behavior or output.

**Technical Approach**: Split the `supervisor_node` function into four separate node functions (router, recruiter, tech_writer, copywriter) and update the StateGraph to use fan-out/fan-in edges. The aggregator node collects results from dedicated state fields and merges them for backward compatibility.

## Technical Context

**Language/Version**: Python 3.13 (project requirement from CLAUDE.md)
**Primary Dependencies**: LangGraph 1.0.0+, Anthropic SDK 0.25.0+, Pydantic 2.0+
**Storage**: N/A (state flows through LangGraph's in-memory StateGraph)
**Testing**: pytest (existing test suite)
**Target Platform**: Python 3.13+ runtime (macOS/Linux)
**Project Type**: Single Python package (`packages/resume-review`)
**Performance Goals**: Maintain existing parallel execution performance (all three agents run concurrently)
**Constraints**:
- Total workflow execution time must remain within 5% of current implementation
- All existing tests must pass (except node name checks)
- Zero breaking changes to CLI, State schema, or ReviewSession output
- Node functions must remain under 200 lines (per CLAUDE.md guidelines)
**Scale/Scope**:
- 4 new node functions (router, recruiter_node, tech_writer_node, copywriter_node)
- 3 new state fields (recruiter_feedback, tech_writer_feedback, copywriter_feedback)
- 1 modified aggregator_node function
- 6 new graph edges (3 fan-out, 3 fan-in)
- ~15 existing unit/integration tests to update

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle Compliance

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Single Source of Truth** | ✅ Compliant | Feature does not touch resume content or generation (focused on workflow orchestration) |
| **II. Automated Generation** | ✅ Compliant | No changes to build pipeline or generated artifacts |
| **III. Preview-First Workflow** | ✅ Compliant | Testing workflow does not affect preview/build process |
| **IV. Deployment Simplicity** | ✅ Compliant | No deployment changes (Python package refactor only) |
| **V. Toolchain Consistency** | ✅ Compliant | Uses existing LangGraph/Python toolchain, no new dependencies |

### Quality Standards Compliance

| Standard | Status | Notes |
|----------|--------|-------|
| **Content Quality** | ✅ N/A | No resume content changes |
| **Output Quality** | ✅ Compliant | Backward compatible - same scores, feedback, and output format |
| **Accessibility** | ✅ N/A | No UI changes |

### Development Workflow Compliance

| Step | Status | Notes |
|------|--------|-------|
| **Change Process** | ✅ Compliant | Standard Python development - edit, test, commit |
| **Dependency Management** | ✅ Compliant | Uses existing pnpm/Python dependency management |

### Gate Result

✅ **PASS** - No constitution violations. Feature is a pure refactoring of Python workflow orchestration code without affecting resume content, build pipeline, or deployment process.

## Project Structure

### Documentation (this feature)

```text
specs/011-stategraph-node-separation/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - LangGraph patterns investigation
├── data-model.md        # Phase 1 output - State schema extensions
├── quickstart.md        # Phase 1 output - Developer testing guide
├── contracts/           # Phase 1 output - Node function signatures
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created yet)
```

### Source Code (repository root)

**Current Structure** (before changes):
```text
packages/resume-review/src/
├── workflow/
│   ├── nodes/
│   │   ├── supervisor.py          # Contains supervisor_node (to be split)
│   │   ├── aggregator.py          # To be modified
│   │   └── [other nodes...]
│   ├── graph.py                   # To be modified (update edges)
│   ├── state.py                   # To be extended (add feedback fields)
│   └── [other workflow files...]
└── [agents/, models/, services/...]
```

**Target Structure** (after changes):
```text
packages/resume-review/src/
├── workflow/
│   ├── nodes/
│   │   ├── supervisor.py          # Renamed to routing.py (or kept with router_node)
│   │   ├── recruiter.py           # NEW: recruiter_node
│   │   ├── tech_writer.py         # NEW: tech_writer_node
│   │   ├── copywriter.py          # NEW: copywriter_node
│   │   ├── aggregator.py          # MODIFIED: collect from separate fields
│   │   └── [other nodes...]
│   ├── graph.py                   # MODIFIED: add fan-out/fan-in edges
│   ├── state.py                   # MODIFIED: add 3 feedback fields
│   └── [other workflow files...]
└── [agents/, models/, services/...]
```

**Structure Decision**: Keep existing single Python package structure. New node functions are added to `workflow/nodes/` directory following the established pattern (one node function per file). The supervisor.py file will be refactored to contain only the router_node function, or renamed to routing.py for clarity. This maintains consistency with existing code organization and keeps each file under 200 lines.

## Complexity Tracking

> **No violations to justify** - Feature adheres to all constitution principles and project guidelines.

---

# Phase 0: Research & Technical Discovery

## Research Tasks

### RT-001: LangGraph Fan-Out/Fan-In Patterns
**Question**: How does LangGraph handle parallel execution when multiple edges originate from the same source node?

**Findings Required**:
- Official LangGraph documentation on parallel edge execution
- Fan-out/fan-in semantics and guarantees
- State update behavior when multiple nodes write to different fields
- Error handling and exception propagation in parallel nodes

**Success Criteria**: Document the exact behavior of `workflow.add_edge(source, target1)` + `workflow.add_edge(source, target2)` with respect to:
- Execution order (parallel vs sequential)
- State collection at fan-in node
- Error handling when one parallel node fails

**Output**: `research.md` section "Fan-Out/Fan-In Execution Semantics"

---

### RT-002: State Field Reducer Behavior
**Question**: Do we need custom reducers for the new feedback fields, or can we use simple overwrites?

**Findings Required**:
- TypedDict field behavior with `total=False`
- When to use `Annotated[type, reducer]` vs plain types
- State merging behavior when multiple nodes write to different fields
- Backward compatibility guarantees for adding optional fields

**Success Criteria**: Document whether `recruiter_feedback: Optional[Feedback]` requires a reducer, and confirm that adding optional fields doesn't break existing code.

**Output**: `research.md` section "State Schema Extension Patterns"

---

### RT-003: LangSmith Node Visibility
**Question**: Do separate LangGraph nodes automatically appear as separate traces in LangSmith, or is additional configuration required?

**Findings Required**:
- LangSmith tracing integration with LangGraph StateGraph
- Node name visibility in trace visualization
- Configuration required for per-node metrics (tokens, latency)
- Best practices for naming nodes for trace clarity

**Success Criteria**: Confirm that renaming nodes from "supervisor" to "recruiter", "tech_writer", "copywriter" will automatically expose them in LangSmith without code changes beyond the graph structure.

**Output**: `research.md` section "LangSmith Tracing Integration"

---

### RT-004: Error Attribution in Parallel Nodes
**Question**: How are exceptions in parallel nodes surfaced to the user, and how can we ensure clear error messages indicating which agent failed?

**Findings Required**:
- Exception handling in asyncio.gather vs LangGraph parallel edges
- Error message formatting in LangGraph node failures
- Best practices for logging node-specific errors
- Retry logic compatibility with parallel nodes

**Success Criteria**: Document the error handling pattern that ensures failures in the recruiter node show "Error in recruiter node" instead of generic "supervisor failed" messages.

**Output**: `research.md` section "Error Handling in Parallel Execution"

---

### RT-005: Logging and Timing Best Practices
**Question**: What's the recommended pattern for logging node start/stop with timing information in LangGraph?

**Findings Required**:
- Python logging best practices for async functions
- Timing measurement patterns (time.time vs time.perf_counter)
- Integration with existing logger ("resume_review")
- Verbosity levels for developer vs production use

**Success Criteria**: Define a reusable logging decorator or helper function that can wrap node functions to emit "Starting {node_name}" and "{node_name} completed in {duration}s" logs.

**Output**: `research.md` section "Node Logging Patterns"

---

### RT-006: Test Migration Strategy
**Question**: Which existing tests check node names, and what's the update strategy?

**Findings Required**:
- Grep codebase for "supervisor" references in tests
- Identify tests that assert on graph structure (node names, edges)
- Determine if any tests verify specific node execution order
- Plan for updating or skipping legacy tests during migration

**Success Criteria**: List all test files requiring updates, categorized by:
- Unit tests (node function tests)
- Integration tests (full workflow tests)
- Graph structure tests (node/edge assertions)

**Output**: `research.md` section "Test Update Inventory"

---

## Research Consolidation

**Output File**: `specs/011-stategraph-node-separation/research.md`

**Required Sections**:
1. **Fan-Out/Fan-In Execution Semantics** (RT-001)
2. **State Schema Extension Patterns** (RT-002)
3. **LangSmith Tracing Integration** (RT-003)
4. **Error Handling in Parallel Execution** (RT-004)
5. **Node Logging Patterns** (RT-005)
6. **Test Update Inventory** (RT-006)
7. **Summary and Recommendations**

Each section must include:
- **Decision**: What approach to use
- **Rationale**: Why this is the right choice
- **Alternatives Considered**: What else was evaluated
- **Implementation Notes**: Key gotchas or considerations

---

# Phase 1: Design & Contracts

**Prerequisites**: `research.md` complete with all NEEDS CLARIFICATION resolved

## Phase 1.1: Data Model Design

**Output File**: `specs/011-stategraph-node-separation/data-model.md`

### Entity: ReviewState (Extended)

**Description**: Extended LangGraph state schema with per-agent feedback fields.

**New Fields**:
| Field Name | Type | Required | Reducer | Description |
|------------|------|----------|---------|-------------|
| `recruiter_feedback` | `Optional[Feedback]` | No | None (overwrite) | Feedback from recruiter agent node |
| `tech_writer_feedback` | `Optional[Feedback]` | No | None (overwrite) | Feedback from technical writer agent node |
| `copywriter_feedback` | `Optional[Feedback]` | No | None (overwrite) | Feedback from copywriter agent node |

**Backward Compatibility**: These fields are optional (`total=False` in TypedDict), so existing code that doesn't reference them continues to work. The `current_feedback` field remains the canonical list for downstream nodes.

**Validation Rules**:
- Fields are populated by respective agent nodes
- Aggregator node merges these fields into `current_feedback`
- Fields are cleared on each iteration (overwrite, not accumulate)

**State Transitions**:
1. `router_node` executes → no state changes (pass-through)
2. `recruiter_node`, `tech_writer_node`, `copywriter_node` execute in parallel → each writes to its dedicated field
3. `aggregator_node` waits for all three → reads three fields → combines into `current_feedback` list

---

### Entity: Node Function Contract

**Description**: Standard contract for all new node functions.

**Input**: `state: ReviewState` (full state dictionary)

**Output**: `dict[str, Any]` (partial state updates)

**Async Requirement**: All agent nodes are `async def` to support `asyncio.gather` in current implementation (though with separate nodes, LangGraph handles parallelism)

**Error Handling**: Node functions should catch exceptions and either:
- Return partial state with error field set
- Let exception propagate for LangGraph to handle

**Logging**: Each node must log:
- Start: `logger.info(f"Starting {node_name} node")`
- Success: `logger.info(f"{node_name} node completed in {duration:.2f}s")`
- Error: `logger.error(f"Error in {node_name} node: {exception}")`

---

## Phase 1.2: API Contracts

**Output Directory**: `specs/011-stategraph-node-separation/contracts/`

### Contract 1: router_node

**File**: `contracts/router_node.md`

**Signature**:
```python
async def router_node(state: ReviewState) -> dict[str, Any]
```

**Purpose**: Stateless fan-out node that triggers parallel execution of agent nodes.

**Input**:
- `state["resume"]`: Resume object
- `state["target_role"]`: Target role string

**Output**:
```python
{}  # Empty dict - no state changes
```

**Behavior**:
- Log iteration start
- Pass through immediately
- LangGraph handles parallel execution of outgoing edges

**Error Handling**: No expected errors (stateless)

**Logging**:
```python
logger.info(f"Router: Starting agent evaluation (iteration {state.get('current_iteration', 0) + 1})")
```

---

### Contract 2: recruiter_node

**File**: `contracts/recruiter_node.md`

**Signature**:
```python
async def recruiter_node(state: ReviewState) -> dict[str, Any]
```

**Purpose**: Execute recruiter agent evaluation and store result in dedicated state field.

**Input**:
- `state["resume"]`: Resume object
- `state["target_role"]`: Target role string
- `state["gemini_api_key"]`, `state["openai_api_key"]`, `state["anthropic_api_key"]`: API keys
- `state["override_model"]`: Optional model override

**Output**:
```python
{
    "recruiter_feedback": Feedback(
        agent_name="recruiter",
        score=8.5,
        strengths=["Strong technical depth"],
        issues=[Issue(...)],
        suggestions=["Add metrics"]
    )
}
```

**Behavior**:
1. Create LLM client using LLMClientFactory for RECRUITER agent
2. Initialize RecruiterAgent with client
3. Call `agent.evaluate_async(resume, target_role)`
4. Log start, duration, and score
5. Return feedback in `recruiter_feedback` field

**Error Handling**:
- If agent fails, return minimal feedback with score 5.0 and error message in suggestions
- Log error with node name for debugging

**Logging**:
```python
logger.info("Starting recruiter node")
logger.debug(f"Recruiter score: {feedback.score}/10.0")
logger.info(f"Recruiter node completed in {duration:.2f}s")
```

---

### Contract 3: tech_writer_node

**File**: `contracts/tech_writer_node.md`

**Signature**:
```python
async def tech_writer_node(state: ReviewState) -> dict[str, Any]
```

**Purpose**: Execute technical writer agent evaluation and store result in dedicated state field.

**Input**: Same as recruiter_node

**Output**:
```python
{
    "tech_writer_feedback": Feedback(
        agent_name="technical_writer",
        score=7.0,
        strengths=[...],
        issues=[...],
        suggestions=[...]
    )
}
```

**Behavior**: Identical to recruiter_node but uses TechnicalWriterAgent and TECHNICAL_WRITER agent name.

**Error Handling**: Same as recruiter_node

**Logging**: Same pattern as recruiter_node, but with "tech_writer" in log messages

---

### Contract 4: copywriter_node

**File**: `contracts/copywriter_node.md`

**Signature**:
```python
async def copywriter_node(state: ReviewState) -> dict[str, Any]
```

**Purpose**: Execute copywriter agent evaluation and store result in dedicated state field.

**Input**: Same as recruiter_node

**Output**:
```python
{
    "copywriter_feedback": Feedback(
        agent_name="copywriter",
        score=8.0,
        strengths=[...],
        issues=[...],
        suggestions=[...]
    )
}
```

**Behavior**: Identical to recruiter_node but uses CopywriterAgent and COPYWRITER agent name.

**Error Handling**: Same as recruiter_node

**Logging**: Same pattern as recruiter_node, but with "copywriter" in log messages

---

### Contract 5: aggregator_node (Modified)

**File**: `contracts/aggregator_node.md`

**Signature**:
```python
async def aggregator_node(state: ReviewState) -> dict[str, Any]
```

**Purpose**: Collect feedback from three agent nodes and merge into canonical `current_feedback` list.

**Input**:
- `state["recruiter_feedback"]`: Optional[Feedback]
- `state["tech_writer_feedback"]`: Optional[Feedback]
- `state["copywriter_feedback"]`: Optional[Feedback]

**Output**:
```python
{
    "current_feedback": [recruiter_fb, tech_writer_fb, copywriter_fb],
    "integrated_score": 8.2,
    "threshold_met": True,
    "feedback_history": [[recruiter_fb, tech_writer_fb, copywriter_fb]],
    "final_score": 8.2
}
```

**Behavior**:
1. Check for presence of each feedback field (skip if None)
2. Collect into `current_feedback` list (order: recruiter, tech_writer, copywriter)
3. Calculate integrated score using existing `calculate_integrated_score()`
4. Compare against `state["score_threshold"]`
5. Return merged state

**Error Handling**:
- If no feedback fields found, log warning and return minimal state
- If only partial feedback, proceed with available feedback

**Logging**:
```python
logger.info("Aggregator: Collecting feedback from agent nodes")
logger.debug(f"Received feedback from {len(current_feedback)} agents")
logger.info(f"Integrated score: {integrated_score:.2f}")
```

---

### Contract 6: Graph Edges (Updated)

**File**: `contracts/graph_edges.md`

**Current Structure**:
```python
workflow.set_entry_point("supervisor")
workflow.add_edge("supervisor", "aggregator")
```

**New Structure**:
```python
# Entry point: router node
workflow.set_entry_point("router")

# Fan-out: router → three agents (parallel execution)
workflow.add_edge("router", "recruiter")
workflow.add_edge("router", "tech_writer")
workflow.add_edge("router", "copywriter")

# Fan-in: three agents → aggregator
workflow.add_edge("recruiter", "aggregator")
workflow.add_edge("tech_writer", "aggregator")
workflow.add_edge("copywriter", "aggregator")

# Rest of graph unchanged
workflow.add_conditional_edges("aggregator", should_continue_review, {...})
workflow.add_edge("revisor", "router")  # Loop back to router, not supervisor
workflow.add_conditional_edges("portfolio", should_do_design_review, {...})
workflow.add_edge("design", END)
```

**Key Change**: The `revisor` node now loops back to `router` instead of `supervisor` (since supervisor is removed).

---

## Phase 1.3: Quickstart Guide

**Output File**: `specs/011-stategraph-node-separation/quickstart.md`

**Content**:
1. **What Changed**: Brief explanation of the refactoring
2. **Running Tests**: How to verify the changes
3. **Viewing Logs**: How to see per-agent timing information
4. **LangSmith Tracing**: How to view separate agent nodes in traces
5. **Debugging Tips**: How to identify which agent is causing issues
6. **Migration Notes**: What existing code (if any) needs updates

**Target Audience**: Developers working on the resume-review package

---

## Phase 1.4: Update Agent Context

**Script**: `.specify/scripts/bash/update-agent-context.sh claude`

**Purpose**: Update CLAUDE.md with any new technologies or patterns introduced in this plan (in this case, none - only refactoring existing LangGraph code).

**Action**: Run the script after completing Phase 1 to ensure agent context is current. Since this feature doesn't introduce new dependencies or patterns, the script should detect no changes.

---

# Phase 2: Tasks Generation

**Command**: `/speckit.tasks` (separate command, NOT created by this plan)

**Output**: `specs/011-stategraph-node-separation/tasks.md`

**Prerequisites**:
- Phase 0 research complete
- Phase 1 design complete
- All NEEDS CLARIFICATION resolved

**Expected Task Categories**:
1. **State Schema Extension** (modify `state.py`)
2. **Node Function Creation** (create 4 new node files)
3. **Aggregator Update** (modify `aggregator.py`)
4. **Graph Restructuring** (modify `graph.py`)
5. **Test Updates** (update tests to use new node names)
6. **Integration Testing** (verify end-to-end behavior)
7. **Documentation Updates** (update code comments and docstrings)

---

# Validation & Success Criteria

## Phase 0 Validation
- ✅ All 6 research tasks completed with documented decisions
- ✅ No remaining NEEDS CLARIFICATION markers
- ✅ research.md file exists with all required sections

## Phase 1 Validation
- ✅ data-model.md defines ReviewState extensions
- ✅ contracts/ directory contains 6 contract files (5 nodes + 1 graph edges)
- ✅ quickstart.md provides developer testing guide
- ✅ Agent context updated (or confirmed no changes needed)

## Phase 2 Readiness
- ✅ All design artifacts reviewed and approved
- ✅ Constitution check re-verified (no new violations)
- ✅ Ready to run `/speckit.tasks` command

---

# Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| LangGraph parallel semantics differ from asyncio.gather | Low | High | RT-001 research task validates exact behavior |
| Adding state fields breaks existing code | Low | Medium | TypedDict total=False ensures backward compatibility |
| Performance regression from node overhead | Low | Low | Benchmark before/after, LangGraph is optimized for this pattern |
| Test failures due to node name changes | High | Low | RT-006 inventories all affected tests upfront |
| Logging becomes too verbose | Medium | Low | Use existing logger levels (info for key events, debug for details) |
| LangSmith doesn't auto-discover new nodes | Low | Medium | RT-003 confirms tracing behavior |

---

# Open Questions for Phase 0 Research

1. **RT-001**: Does LangGraph guarantee parallel execution for multiple edges from same source?
2. **RT-002**: Do new Optional[Feedback] fields need custom reducers?
3. **RT-003**: Do node renames automatically appear in LangSmith traces?
4. **RT-004**: What's the error message format for parallel node failures?
5. **RT-005**: What's the cleanest logging pattern for async node functions?
6. **RT-006**: Which tests assert on "supervisor" node name?

All questions must be answered in research.md before proceeding to Phase 1.
