# Data Model: StateGraph Agent Node Separation

**Feature**: 011-stategraph-node-separation
**Date**: 2026-01-09
**Status**: Design

## Overview

This document defines the data model extensions required to support separate agent nodes in the LangGraph workflow. The primary change is adding three optional state fields to collect per-agent feedback before merging in the aggregator node.

---

## Entity: ReviewState (Extended)

**File**: `packages/resume-review/src/workflow/state.py`

**Purpose**: LangGraph state schema that flows through the workflow, extended with per-agent feedback fields.

### New Fields

| Field Name | Type | Required | Default | Reducer | Description |
|------------|------|----------|---------|---------|-------------|
| `recruiter_feedback` | `Optional[Feedback]` | No | `None` | None | Feedback from recruiter agent node (overwritten each iteration) |
| `tech_writer_feedback` | `Optional[Feedback]` | No | `None` | None | Feedback from technical writer agent node (overwritten each iteration) |
| `copywriter_feedback` | `Optional[Feedback]` | No | `None` | None | Feedback from copywriter agent node (overwritten each iteration) |

### Field Semantics

**Write Pattern**:
- Each agent node writes to its dedicated field: `return {"recruiter_feedback": feedback}`
- Fields are **overwritten** on each iteration (no accumulation across iterations)
- No reducer needed - simple state update

**Read Pattern**:
- Aggregator node reads all three fields after parallel execution completes
- Checks for presence: `if "recruiter_feedback" in state: ...`
- Merges into canonical `current_feedback` list for downstream nodes

**Lifecycle**:
1. **Initialization**: Fields are unset (`None` or not present in state dict)
2. **Agent Execution**: Each agent writes to its field (parallel, no conflicts)
3. **Aggregation**: Aggregator reads and merges into `current_feedback`
4. **Next Iteration**: Fields are overwritten with new feedback (no accumulation)

### Backward Compatibility

✅ **Fully Backward Compatible**

- `TypedDict` with `total=False` allows optional fields
- Existing code that doesn't reference these fields continues to work
- The `current_feedback` field remains the canonical source for downstream nodes
- No breaking changes to CLI, ReviewSession, or output formats

**Example**:
```python
class ReviewState(TypedDict, total=False):
    # Existing fields (unchanged)
    resume: Resume
    target_role: str
    current_feedback: list[Feedback]
    feedback_history: Annotated[list[list[Feedback]], add_feedback]
    # ... other existing fields ...

    # NEW: Per-agent feedback fields
    recruiter_feedback: Optional[Feedback]
    tech_writer_feedback: Optional[Feedback]
    copywriter_feedback: Optional[Feedback]
```

### State Transitions

```
┌─────────────┐
│ router_node │ (no state changes)
└──────┬──────┘
       │ Fan-out (parallel execution)
       ├────────────────┬────────────────┐
       ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│recruiter_node│ │tech_writer_  │ │copywriter_   │
│              │ │node          │ │node          │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       │ Write          │ Write          │ Write
       │ recruiter_     │ tech_writer_   │ copywriter_
       │ feedback       │ feedback       │ feedback
       │                │                │
       └────────────────┴────────────────┘
                        │ Fan-in (wait for all)
                        ▼
                 ┌─────────────┐
                 │ aggregator_ │
                 │ node        │
                 └──────┬──────┘
                        │
                        │ Merge into current_feedback
                        │ = [recruiter, tech_writer, copywriter]
                        ▼
```

### Validation Rules

1. **Type Safety**: Each field must be `Optional[Feedback]` or absent
2. **Mutual Exclusivity**: Each agent writes only to its own field (enforced by node isolation)
3. **Completeness**: Aggregator tolerates partial feedback (e.g., if one agent failed)
4. **Order Preservation**: Aggregator merges in consistent order: recruiter, tech_writer, copywriter

### Example State Flow

**After Router Node**:
```python
{
    "resume": Resume(...),
    "target_role": "LLM Engineer",
    "current_iteration": 1,
    # Per-agent fields not yet set
}
```

**After Parallel Agent Execution**:
```python
{
    "resume": Resume(...),
    "target_role": "LLM Engineer",
    "current_iteration": 1,
    "recruiter_feedback": Feedback(agent_name="recruiter", score=8.5, ...),
    "tech_writer_feedback": Feedback(agent_name="technical_writer", score=7.0, ...),
    "copywriter_feedback": Feedback(agent_name="copywriter", score=8.0, ...),
}
```

**After Aggregator Node**:
```python
{
    "resume": Resume(...),
    "target_role": "LLM Engineer",
    "current_iteration": 1,
    # Per-agent fields still present but no longer used
    "recruiter_feedback": Feedback(...),
    "tech_writer_feedback": Feedback(...),
    "copywriter_feedback": Feedback(...),
    # Canonical merged list
    "current_feedback": [
        Feedback(agent_name="recruiter", score=8.5, ...),
        Feedback(agent_name="technical_writer", score=7.0, ...),
        Feedback(agent_name="copywriter", score=8.0, ...),
    ],
    "integrated_score": 7.8,
    "threshold_met": False,
}
```

---

## Entity: Feedback (Unchanged)

**File**: `packages/resume-review/src/models/feedback.py`

**No changes required** - existing `Feedback` model is used as-is.

**Relevant Fields**:
```python
class Feedback(BaseModel):
    agent_name: str  # "recruiter", "technical_writer", "copywriter"
    score: float     # 0.0 - 10.0
    strengths: list[str]
    issues: list[Issue]
    suggestions: list[str]
```

---

## Entity: Node Function Contract

**Purpose**: Standard interface for all node functions in the workflow.

### Input Type

```python
state: ReviewState  # Full state dictionary
```

**Key Fields Used by Agent Nodes**:
- `state["resume"]`: Resume object to evaluate
- `state["target_role"]`: Target role string (e.g., "LLM Engineer")
- `state["gemini_api_key"]`: Optional Gemini API key
- `state["openai_api_key"]`: Optional OpenAI API key
- `state["anthropic_api_key"]`: Optional Anthropic API key
- `state["override_model"]`: Optional model override for testing

### Output Type

```python
dict[str, Any]  # Partial state update
```

**Agent Node Output Example**:
```python
{
    "recruiter_feedback": Feedback(
        agent_name="recruiter",
        score=8.5,
        strengths=["Strong technical background"],
        issues=[Issue(...)],
        suggestions=["Add quantitative metrics"]
    )
}
```

**Aggregator Node Output Example**:
```python
{
    "current_feedback": [recruiter_fb, tech_writer_fb, copywriter_fb],
    "integrated_score": 7.8,
    "threshold_met": False,
    "feedback_history": [[recruiter_fb, tech_writer_fb, copywriter_fb]],
    "final_score": 7.8
}
```

### Node Function Signature

All agent nodes follow this pattern:

```python
async def <agent>_node(state: ReviewState) -> dict[str, Any]:
    """
    Execute <agent> agent evaluation.

    Args:
        state: Full workflow state

    Returns:
        Partial state update with <agent>_feedback field
    """
    start_time = time.perf_counter()
    logger.info("Starting <agent> node")

    try:
        # Create LLM client
        client = LLMClientFactory.create_client(
            agent_name=AgentName.<AGENT>,
            gemini_api_key=state.get("gemini_api_key"),
            openai_api_key=state.get("openai_api_key"),
            anthropic_api_key=state.get("anthropic_api_key"),
            override_model=state.get("override_model"),
        )

        # Initialize agent
        agent = <Agent>Agent(llm_client=client)

        # Evaluate
        feedback = await agent.evaluate_async(
            state["resume"],
            state["target_role"]
        )

        # Log success
        duration = time.perf_counter() - start_time
        logger.debug(f"<Agent> score: {feedback.score}/10.0")
        logger.info(f"<Agent> node completed in {duration:.2f}s")

        return {"<agent>_feedback": feedback}

    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.error(f"Error in <agent> node after {duration:.2f}s: {e}")

        # Return minimal feedback (neutral score)
        return {
            "<agent>_feedback": Feedback(
                agent_name="<agent>",
                score=5.0,
                strengths=["Evaluation failed"],
                issues=[],
                suggestions=[f"Error: {str(e)}"],
            )
        }
```

---

## Entity: Graph Structure (Updated)

**File**: `packages/resume-review/src/workflow/graph.py`

### Node Inventory

**Before** (3 nodes):
- `supervisor` (contains 3 agents internally)
- `aggregator`
- `revisor`, `portfolio`, `design` (unchanged)

**After** (6 nodes):
- `router` (fan-out coordinator)
- `recruiter` (agent evaluation)
- `tech_writer` (agent evaluation)
- `copywriter` (agent evaluation)
- `aggregator` (modified to collect from separate fields)
- `revisor`, `portfolio`, `design` (unchanged)

### Edge Definitions

**Before**:
```python
workflow.set_entry_point("supervisor")
workflow.add_edge("supervisor", "aggregator")
workflow.add_edge("revisor", "supervisor")  # Loop back
```

**After**:
```python
# Entry point
workflow.set_entry_point("router")

# Fan-out (parallel execution)
workflow.add_edge("router", "recruiter")
workflow.add_edge("router", "tech_writer")
workflow.add_edge("router", "copywriter")

# Fan-in (wait for all)
workflow.add_edge("recruiter", "aggregator")
workflow.add_edge("tech_writer", "aggregator")
workflow.add_edge("copywriter", "aggregator")

# Loop back to router (not supervisor)
workflow.add_edge("revisor", "router")

# Remainder unchanged
workflow.add_conditional_edges("aggregator", should_continue_review, {...})
workflow.add_conditional_edges("portfolio", should_do_design_review, {...})
workflow.add_edge("design", END)
```

### Execution Flow

```
__start__
    ↓
router (logs "Starting iteration N")
    ↓ (fan-out, parallel)
    ├── recruiter (writes recruiter_feedback)
    ├── tech_writer (writes tech_writer_feedback)
    └── copywriter (writes copywriter_feedback)
    ↓ (fan-in, wait for all)
aggregator (merges into current_feedback)
    ↓ (conditional)
    ├── revisor → router (loop)
    └── portfolio → design/END
```

---

## Data Validation & Error Handling

### Valid State Scenarios

1. **All agents succeed**:
   - All three feedback fields populated
   - Aggregator merges all three into `current_feedback`

2. **One agent fails**:
   - Failed agent writes minimal feedback (score 5.0)
   - Aggregator merges all three (including failed one)

3. **Multiple agents fail**:
   - Each writes minimal feedback with error message
   - Workflow continues with degraded feedback

### Invalid State Scenarios (Should Not Occur)

1. **Missing feedback fields**: Aggregator handles gracefully by skipping None fields
2. **Type mismatch**: Pydantic validation catches at runtime
3. **Reducer conflict**: Impossible - separate fields prevent conflicts

### Error Recovery Pattern

```python
# In agent node
try:
    feedback = await agent.evaluate_async(resume, target_role)
    return {"<agent>_feedback": feedback}
except Exception as e:
    logger.error(f"Error in <agent> node: {e}")
    return {
        "<agent>_feedback": Feedback(
            agent_name="<agent>",
            score=5.0,  # Neutral score - doesn't bias final score
            strengths=["Evaluation failed"],
            issues=[],
            suggestions=[f"Error: {str(e)}"],
        )
    }
```

**Rationale**: Graceful degradation allows workflow to complete even if one agent fails, providing partial feedback instead of cascading failure.

---

## Performance Characteristics

**State Size Impact**: Minimal
- Three additional optional fields per iteration
- Each `Feedback` object is ~1-2 KB
- Total overhead: ~3-6 KB per iteration
- Negligible compared to resume content (~10-50 KB)

**Serialization**: Standard TypedDict → dict conversion (no custom serializers needed)

**Memory Footprint**: O(1) per iteration (fields are overwritten, not accumulated)

---

## Migration Path

### Phase 1: Add Optional Fields

```python
# In state.py - ADD these fields (no breaking changes)
class ReviewState(TypedDict, total=False):
    # ... existing fields ...

    # NEW: Per-agent feedback
    recruiter_feedback: Optional[Feedback]
    tech_writer_feedback: Optional[Feedback]
    copywriter_feedback: Optional[Feedback]
```

**Impact**: Zero - TypedDict `total=False` allows optional fields

### Phase 2: Update Graph & Nodes

- Create router, recruiter, tech_writer, copywriter node functions
- Update graph.py with new edges
- Modify aggregator to read from separate fields
- Remove supervisor_node

**Impact**: Existing tests may fail (node name assertions) - covered in RT-006

### Phase 3: Update Tests

- Update test assertions to check for new node names
- Verify fan-out/fan-in behavior
- Confirm output format unchanged

**Impact**: Test suite passes with new implementation

---

## Summary

**Key Changes**:
- ✅ Three new optional state fields (recruiter_feedback, tech_writer_feedback, copywriter_feedback)
- ✅ No custom reducers needed (simple overwrites)
- ✅ Fully backward compatible (TypedDict total=False)
- ✅ Clear state transitions (router → agents → aggregator)
- ✅ Graceful error handling (minimal feedback on failure)

**Validation**:
- ✅ Matches research findings (RT-002: no reducers needed)
- ✅ Supports fan-out/fan-in pattern (RT-001)
- ✅ Enables per-agent error attribution (RT-004)

**Ready for**: Contract definition (Phase 1.2)
