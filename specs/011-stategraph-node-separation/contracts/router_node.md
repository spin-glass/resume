# Contract: router_node

**Node Type**: Fan-out coordinator
**File**: `packages/resume-review/src/workflow/nodes/routing.py` (or keep in supervisor.py)
**Purpose**: Stateless pass-through node that triggers parallel execution of three agent nodes

---

## Function Signature

```python
async def router_node(state: ReviewState) -> dict[str, Any]:
    """
    Router node that initiates parallel agent evaluation.

    This is a stateless fan-out node. LangGraph handles the actual
    parallel execution via multiple outgoing edges (router → recruiter,
    router → tech_writer, router → copywriter).

    Args:
        state: Full workflow state containing resume and target_role

    Returns:
        Empty dict (no state changes) - parallel execution triggered by edges
    """
```

---

## Input

### Required State Fields

| Field | Type | Description |
|-------|------|-------------|
| `resume` | `Resume` | Resume object to be evaluated |
| `target_role` | `str` | Target role (e.g., "LLM/Multi-Agent Engineer") |
| `current_iteration` | `int` | Iteration counter (for logging) |

### Optional State Fields

| Field | Type | Description |
|-------|------|-------------|
| None | - | Router is stateless |

---

## Output

### Return Value

```python
{}  # Empty dictionary - no state modifications
```

**Rationale**: The router's job is purely to trigger parallel execution via graph edges. LangGraph's fan-out semantics handle the parallelism automatically.

---

## Behavior

### Execution Flow

1. **Log iteration start**:
   ```python
   logger.info(f"Router: Starting agent evaluation (iteration {state.get('current_iteration', 0) + 1})")
   ```

2. **Return immediately**:
   ```python
   return {}  # LangGraph executes all outgoing edges in parallel
   ```

### Side Effects

- **Logging**: Single info-level log message
- **No state changes**: Returns empty dict
- **No I/O operations**: Pure pass-through

### Timing

- **Expected duration**: < 1ms (just logging)
- **Does not block**: Parallel agents start immediately after router completes

---

## Error Handling

### Expected Errors

None - router is stateless and performs no operations that can fail.

### Unexpected Errors

If an exception occurs (e.g., logger misconfiguration):
- Let exception propagate (LangGraph will catch and report)
- Log entry may be missing, but workflow continues

---

## Logging

### Log Messages

**Start**:
```python
logger.info(f"Router: Starting agent evaluation (iteration {state.get('current_iteration', 0) + 1})")
```

**Example Output**:
```
INFO: Router: Starting agent evaluation (iteration 1)
INFO: Router: Starting agent evaluation (iteration 2)
```

### Log Level Guidelines

- `INFO`: Iteration start (always visible)
- `DEBUG`: Not used (no debugging needed for pass-through)
- `ERROR`: Not expected (stateless node)

---

## Testing

### Unit Test

```python
@pytest.mark.asyncio
async def test_router_node_returns_empty_dict():
    """Router node should return empty dict (stateless)."""
    state = {"resume": mock_resume, "target_role": "Engineer", "current_iteration": 1}

    result = await router_node(state)

    assert result == {}  # No state changes


@pytest.mark.asyncio
async def test_router_node_logs_iteration_number(caplog):
    """Router should log iteration number."""
    state = {"resume": mock_resume, "target_role": "Engineer", "current_iteration": 2}

    with caplog.at_level(logging.INFO):
        await router_node(state)

    assert "iteration 3" in caplog.text  # current_iteration + 1
```

### Integration Test

```python
@pytest.mark.asyncio
async def test_router_triggers_parallel_execution():
    """Verify router fans out to three agent nodes."""
    # This test requires graph-level verification
    # Mock agent nodes and verify all three execute after router
    pass  # Covered in graph integration tests
```

---

## Performance

**Expected Metrics**:
- Execution time: < 1ms
- Memory: O(1) (no allocations)
- CPU: Negligible

**Bottlenecks**: None

---

## Dependencies

### Internal

- `logging.getLogger("resume_review")`: Logger instance
- `ReviewState`: Type hint for state parameter

### External

- None (no API calls or I/O)

---

## Implementation Notes

### Design Rationale

The router node exists solely for **architectural clarity** and **LangSmith visibility**. Without it, we'd have multiple edges from `__start__` to agent nodes, which:
- Makes the graph less readable
- Mixes initialization logic with agent execution
- Prevents logging the iteration start in one place

With the router, the graph structure is clear:
```
__start__ → router → [recruiter, tech_writer, copywriter] → aggregator
```

### Alternative Designs Considered

1. **No router node**: Direct edges from `__start__` to agents
   - **Rejected**: Less clear graph structure, no single log point

2. **Router with state initialization**: Set defaults for missing fields
   - **Rejected**: State initialization happens in workflow runner, not nodes

3. **Router with agent orchestration**: Manually manage parallel execution
   - **Rejected**: LangGraph handles this automatically via edges

---

## Related Contracts

- [recruiter_node.md](./recruiter_node.md): Agent node that router fans out to
- [tech_writer_node.md](./tech_writer_node.md): Agent node that router fans out to
- [copywriter_node.md](./copywriter_node.md): Agent node that router fans out to
- [aggregator_node.md](./aggregator_node.md): Fan-in node that collects results
- [graph_edges.md](./graph_edges.md): Graph structure showing router's role

---

## Change History

| Date | Change | Author |
|------|--------|--------|
| 2026-01-09 | Initial contract | Plan phase |
