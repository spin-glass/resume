# Contract: aggregator_node (Modified)

**Node Type**: Fan-in collector
**File**: `packages/resume-review/src/workflow/nodes/aggregator.py` (MODIFIED)
**Purpose**: Collect feedback from three parallel agent nodes and merge into canonical `current_feedback` list

---

## Function Signature

```python
async def aggregator_node(state: ReviewState) -> dict[str, Any]:
    """
    Aggregator node that collects and merges feedback from agent nodes.

    Waits for all three agent nodes (recruiter, tech_writer, copywriter)
    to complete via LangGraph's fan-in semantics, then merges their
    individual feedback into the canonical current_feedback list.

    Args:
        state: Full workflow state with per-agent feedback fields

    Returns:
        Partial state update with merged feedback and calculated scores
    """
```

---

## Input

### Required State Fields

| Field | Type | Description |
|-------|------|-------------|
| `score_threshold` | `float` | Score threshold for determining if revision needed (default: 8.0) |

### Optional State Fields (Per-Agent Feedback)

| Field | Type | Description |
|-------|------|-------------|
| `recruiter_feedback` | `Optional[Feedback]` | Feedback from recruiter node (may be absent if node failed) |
| `tech_writer_feedback` | `Optional[Feedback]` | Feedback from tech writer node |
| `copywriter_feedback` | `Optional[Feedback]` | Feedback from copywriter node |

**Note**: At least one feedback field should be present. If all three are missing, aggregator logs warning and returns minimal state.

---

## Output

### Return Value

```python
{
    "current_feedback": [recruiter_fb, tech_writer_fb, copywriter_fb],
    "integrated_score": 8.2,
    "threshold_met": True,
    "feedback_history": [[recruiter_fb, tech_writer_fb, copywriter_fb]],
    "final_score": 8.2
}
```

### Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `current_feedback` | `list[Feedback]` | Merged feedback list (order: recruiter, tech_writer, copywriter) |
| `integrated_score` | `float` | Weighted average score from all agents |
| `threshold_met` | `bool` | True if integrated_score >= score_threshold |
| `feedback_history` | `list[list[Feedback]]` | Appends current_feedback to history (uses reducer) |
| `final_score` | `float` | Copy of integrated_score for final output |

---

## Behavior

### Execution Flow

1. **Log start**:
   ```python
   logger.info("Aggregator: Collecting feedback from agent nodes")
   ```

2. **Collect feedback from state fields**:
   ```python
   current_feedback = []
   if "recruiter_feedback" in state:
       current_feedback.append(state["recruiter_feedback"])
   if "tech_writer_feedback" in state:
       current_feedback.append(state["tech_writer_feedback"])
   if "copywriter_feedback" in state:
       current_feedback.append(state["copywriter_feedback"])
   ```

3. **Validate feedback collected**:
   ```python
   if not current_feedback:
       logger.warning("Aggregator: No feedback collected from agent nodes")
       return {"error": "No feedback available"}
   ```

4. **Calculate integrated score**:
   ```python
   integrated_score = calculate_integrated_score(current_feedback)
   ```

5. **Compare against threshold**:
   ```python
   threshold_met = integrated_score >= state.get("score_threshold", 8.0)
   ```

6. **Log results**:
   ```python
   logger.debug(f"Received feedback from {len(current_feedback)} agents")
   logger.info(f"Integrated score: {integrated_score:.2f} (threshold: {state.get('score_threshold', 8.0)})")
   ```

7. **Return merged state**:
   ```python
   return {
       "current_feedback": current_feedback,
       "integrated_score": integrated_score,
       "threshold_met": threshold_met,
       "feedback_history": [current_feedback],  # Reducer appends
       "final_score": integrated_score,
   }
   ```

### Fan-In Coordination

**LangGraph Guarantee**: Aggregator only executes after ALL three agent nodes complete, regardless of individual durations.

**Example Timing**:
- Recruiter: 5s
- Tech Writer: 20s
- Copywriter: 12s
- **Aggregator starts**: After 20s (waits for slowest)

---

## Error Handling

### Partial Feedback (Graceful Degradation)

If one or more agents fail, aggregator proceeds with available feedback:

```python
# Example: Tech writer failed, but recruiter and copywriter succeeded
current_feedback = [
    recruiter_feedback,
    # tech_writer_feedback missing
    copywriter_feedback,
]
```

**Rationale**: Partial feedback is better than no feedback. The failed agent's error message is logged separately in its node.

### No Feedback (Critical Failure)

If all three agents fail:

```python
if not current_feedback:
    logger.error("Aggregator: All agents failed - no feedback available")
    return {"error": "All agents failed"}
```

**Impact**: Workflow will likely halt or enter error state.

---

## Logging

### Log Messages

**Start**:
```python
logger.info("Aggregator: Collecting feedback from agent nodes")
```

**Feedback Count**:
```python
logger.debug(f"Received feedback from {len(current_feedback)} agents")
```

**Score Calculation**:
```python
logger.info(f"Integrated score: {integrated_score:.2f} (threshold: {state.get('score_threshold', 8.0)})")
```

**Warning (Partial Feedback)**:
```python
logger.warning(f"Aggregator: Only {len(current_feedback)}/3 agents provided feedback")
```

**Error (No Feedback)**:
```python
logger.error("Aggregator: All agents failed - no feedback available")
```

---

## Score Calculation

Uses existing `calculate_integrated_score()` function from `workflow/scoring.py`:

```python
from ..scoring import calculate_integrated_score

integrated_score = calculate_integrated_score(current_feedback)
```

**Weights** (from `config/model_config.py`):
- Recruiter: 30%
- Technical Writer: 20%
- Copywriter: 25%
- UX Designer: 15% (not in this feature)
- Visual Designer: 10% (not in this feature)

**Formula**:
```python
integrated_score = (
    recruiter_score * 0.30 +
    tech_writer_score * 0.20 +
    copywriter_score * 0.25
) / 0.75  # Normalize to 10.0 scale when only 3 agents
```

---

## Testing

### Unit Test: Successful Aggregation

```python
@pytest.mark.asyncio
async def test_aggregator_collects_from_separate_fields():
    """Aggregator merges feedback from three separate state fields."""
    state = {
        "recruiter_feedback": Feedback(agent_name="recruiter", score=8.0, ...),
        "tech_writer_feedback": Feedback(agent_name="technical_writer", score=7.0, ...),
        "copywriter_feedback": Feedback(agent_name="copywriter", score=9.0, ...),
        "score_threshold": 8.0,
    }

    result = await aggregator_node(state)

    assert len(result["current_feedback"]) == 3
    assert result["integrated_score"] > 0
    assert "threshold_met" in result
```

### Unit Test: Partial Feedback

```python
@pytest.mark.asyncio
async def test_aggregator_handles_missing_feedback():
    """Aggregator proceeds with partial feedback if one agent failed."""
    state = {
        "recruiter_feedback": Feedback(agent_name="recruiter", score=8.0, ...),
        # tech_writer_feedback missing (agent failed)
        "copywriter_feedback": Feedback(agent_name="copywriter", score=9.0, ...),
        "score_threshold": 8.0,
    }

    result = await aggregator_node(state)

    assert len(result["current_feedback"]) == 2  # Only 2 agents succeeded
    assert result["integrated_score"] > 0  # Score calculated from available feedback
```

### Unit Test: No Feedback

```python
@pytest.mark.asyncio
async def test_aggregator_returns_error_if_no_feedback():
    """Aggregator returns error if all agents failed."""
    state = {"score_threshold": 8.0}  # No feedback fields

    result = await aggregator_node(state)

    assert "error" in result
    assert result["error"] == "All agents failed"
```

---

## Performance

**Expected Metrics**:
- Execution time: < 100ms (just merging and scoring)
- Memory: O(n) where n = number of feedback objects (~3)
- CPU: Minimal (weighted average calculation)

**Bottlenecks**: None

---

## Backward Compatibility

### Before (Supervisor-Based)

```python
# Supervisor returned
{
    "current_feedback": [fb1, fb2, fb3],  # Directly from asyncio.gather
    "token_usage": {...},
}
```

### After (Separate Agent Nodes)

```python
# Aggregator returns
{
    "current_feedback": [fb1, fb2, fb3],  # Collected from separate fields
    "integrated_score": 8.2,
    "threshold_met": True,
    "feedback_history": [[fb1, fb2, fb3]],
    "final_score": 8.2,
}
```

**Compatibility**:
- ✅ `current_feedback` format identical
- ✅ Downstream nodes (revisor, portfolio) unchanged
- ✅ Output format (ReviewSession) unchanged

---

## Key Changes from Current Implementation

### Before (`aggregator.py` - current)

Aggregator expected `current_feedback` to already exist (set by supervisor):

```python
def aggregator_node(state: ReviewState) -> dict[str, Any]:
    current_feedback = state.get("current_feedback", [])
    # Calculate score from existing feedback
    integrated_score = calculate_integrated_score(current_feedback)
    # ...
```

### After (`aggregator.py` - modified)

Aggregator **collects** feedback from separate fields:

```python
async def aggregator_node(state: ReviewState) -> dict[str, Any]:
    # NEW: Collect from separate fields
    current_feedback = []
    if "recruiter_feedback" in state:
        current_feedback.append(state["recruiter_feedback"])
    if "tech_writer_feedback" in state:
        current_feedback.append(state["tech_writer_feedback"])
    if "copywriter_feedback" in state:
        current_feedback.append(state["copywriter_feedback"])

    # Rest is similar to before
    integrated_score = calculate_integrated_score(current_feedback)
    # ...
```

---

## Related Contracts

- [router_node.md](./router_node.md): Fan-out coordinator
- [README.md](./README.md): Agent node pattern (recruiter, tech_writer, copywriter)
- [graph_edges.md](./graph_edges.md): Graph structure showing fan-in edges

---

## Change History

| Date | Change | Author |
|------|--------|--------|
| 2026-01-09 | Modified to collect from separate fields | Plan phase |
