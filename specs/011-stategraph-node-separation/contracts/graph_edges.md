# Contract: Graph Edges (Updated)

**File**: `packages/resume-review/src/workflow/graph.py`
**Purpose**: Define the LangGraph StateGraph structure with fan-out/fan-in edges

---

## Graph Structure Changes

### Before (Current Implementation)

```python
workflow = StateGraph(ReviewState)

# Nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("aggregator", aggregator_node)
workflow.add_node("revisor", revisor_node)
workflow.add_node("portfolio", portfolio_analyzer_node)
workflow.add_node("design", design_supervisor_node)

# Entry point
workflow.set_entry_point("supervisor")

# Edges
workflow.add_edge("supervisor", "aggregator")
workflow.add_conditional_edges("aggregator", should_continue_review, {...})
workflow.add_edge("revisor", "supervisor")  # Loop back
workflow.add_conditional_edges("portfolio", should_do_design_review, {...})
workflow.add_edge("design", END)
```

**Graph Visualization**:
```
__start__ → supervisor → aggregator → [revisor/portfolio]
                ↑______________|
```

---

### After (New Implementation)

```python
workflow = StateGraph(ReviewState)

# Nodes
workflow.add_node("router", router_node)
workflow.add_node("recruiter", recruiter_node)
workflow.add_node("tech_writer", tech_writer_node)
workflow.add_node("copywriter", copywriter_node)
workflow.add_node("aggregator", aggregator_node)
workflow.add_node("revisor", revisor_node)
workflow.add_node("portfolio", portfolio_analyzer_node)
workflow.add_node("design", design_supervisor_node)

# Entry point
workflow.set_entry_point("router")

# Fan-out: router → three agents (parallel execution)
workflow.add_edge("router", "recruiter")
workflow.add_edge("router", "tech_writer")
workflow.add_edge("router", "copywriter")

# Fan-in: three agents → aggregator (waits for all)
workflow.add_edge("recruiter", "aggregator")
workflow.add_edge("tech_writer", "aggregator")
workflow.add_edge("copywriter", "aggregator")

# Conditional: aggregator → revisor or portfolio
workflow.add_conditional_edges(
    "aggregator",
    should_continue_review,
    {
        "revisor": "revisor",
        "portfolio": "portfolio",
    },
)

# Loop back to router (not supervisor)
workflow.add_edge("revisor", "router")

# Conditional: portfolio → design or end
workflow.add_conditional_edges(
    "portfolio",
    should_do_design_review,
    {
        "design": "design",
        "end": END,
    },
)

# Design ends workflow
workflow.add_edge("design", END)

return workflow.compile()
```

**Graph Visualization**:
```
                      ┌─→ recruiter ─────┐
                      │                   │
__start__ → router ───├─→ tech_writer ───├─→ aggregator → [revisor/portfolio]
                      │                   │            ↓
                      └─→ copywriter ─────┘      portfolio → [design/__end__]
                                                       ↓
                ┌──────────────────────────────────revisor
                │
                └─→ router (loop back)
```

---

## Edge Definitions

### Fan-Out Edges (Router → Agents)

```python
workflow.add_edge("router", "recruiter")
workflow.add_edge("router", "tech_writer")
workflow.add_edge("router", "copywriter")
```

**Semantics**:
- **Parallel execution**: All three agent nodes start simultaneously
- **No ordering**: Execution order is undefined (depends on LangGraph scheduler)
- **Independent**: Each agent runs independently, no shared state writes

**LangGraph Guarantee**: When multiple edges originate from the same source node, LangGraph executes them in parallel.

---

### Fan-In Edges (Agents → Aggregator)

```python
workflow.add_edge("recruiter", "aggregator")
workflow.add_edge("tech_writer", "aggregator")
workflow.add_edge("copywriter", "aggregator")
```

**Semantics**:
- **Wait for all**: Aggregator only starts after ALL three agent nodes complete
- **State collection**: Aggregator receives merged state with all three feedback fields
- **Deterministic**: Order of completion doesn't matter, aggregator always waits for all

**LangGraph Guarantee**: When multiple edges target the same node, LangGraph waits for all incoming edges before executing the target.

---

## Conditional Edges (Unchanged)

### Aggregator → Revisor or Portfolio

```python
workflow.add_conditional_edges(
    "aggregator",
    should_continue_review,  # Condition function
    {
        "revisor": "revisor",
        "portfolio": "portfolio",
    },
)
```

**Condition** (`should_continue_review`):
```python
def should_continue_review(state: ReviewState) -> str:
    """Route to revisor if threshold not met, else portfolio."""
    threshold_met = state.get("threshold_met", False)
    max_iterations = state.get("max_iterations", 3)
    current_iteration = state.get("current_iteration", 0)

    if not threshold_met and current_iteration < max_iterations:
        return "revisor"
    else:
        return "portfolio"
```

---

### Portfolio → Design or End

```python
workflow.add_conditional_edges(
    "portfolio",
    should_do_design_review,
    {
        "design": "design",
        "end": END,
    },
)
```

**Condition** (`should_do_design_review`):
```python
def should_do_design_review(state: ReviewState) -> str:
    """Route to design if screenshot URL provided, else end."""
    screenshot_url = state.get("screenshot_url")
    return "design" if screenshot_url else "end"
```

---

## Loop Edge (Revisor → Router)

```python
workflow.add_edge("revisor", "router")
```

**Key Change**: Loops back to `router`, not `supervisor` (which no longer exists).

**Impact**: On retry, workflow goes through router → agents → aggregator again with revised content.

---

## Node Count Comparison

| Implementation | Total Nodes | Agent Nodes | Coordinator Nodes |
|----------------|-------------|-------------|-------------------|
| **Before** | 5 | 0 (hidden in supervisor) | 1 (supervisor) |
| **After** | 8 | 3 (recruiter, tech_writer, copywriter) | 1 (router) |

---

## Edge Count Comparison

| Edge Type | Before | After | Change |
|-----------|--------|-------|--------|
| Sequential | 3 | 3 | 0 (revisor loop, design end, portfolio conditional) |
| Conditional | 2 | 2 | 0 (aggregator→revisor/portfolio, portfolio→design/end) |
| Fan-out | 0 | 3 | +3 (router→agents) |
| Fan-in | 0 | 3 | +3 (agents→aggregator) |
| **Total** | 5 | 11 | +6 |

---

## Execution Flow Examples

### Iteration 1: Score Below Threshold (Retry)

```
1. __start__ → router
2. router → [recruiter, tech_writer, copywriter] (parallel)
3. [recruiter, tech_writer, copywriter] → aggregator (fan-in waits)
4. aggregator: integrated_score = 7.5, threshold = 8.0 → threshold_met = False
5. aggregator → revisor (conditional: score below threshold)
6. revisor: applies revisions to resume content
7. revisor → router (loop back)
8. [Iteration 2 starts...]
```

### Iteration 2: Score Meets Threshold

```
1. router → [recruiter, tech_writer, copywriter] (parallel)
2. [recruiter, tech_writer, copywriter] → aggregator
3. aggregator: integrated_score = 8.3, threshold = 8.0 → threshold_met = True
4. aggregator → portfolio (conditional: threshold met)
5. portfolio: analyzes skill gaps and suggests projects
6. portfolio → design (conditional: screenshot_url provided)
7. design: UX/visual review
8. design → __end__
```

---

## Testing Graph Structure

### Test: Node Existence

```python
def test_graph_has_separate_agent_nodes():
    """Verify graph contains router and three agent nodes."""
    workflow = build_review_workflow()
    node_names = list(workflow.nodes.keys())

    assert "router" in node_names
    assert "recruiter" in node_names
    assert "tech_writer" in node_names
    assert "copywriter" in node_names
    assert "supervisor" not in node_names  # Removed
```

### Test: Fan-Out Edges

```python
def test_graph_has_fan_out_edges():
    """Verify router fans out to three agent nodes."""
    workflow = build_review_workflow()
    edges = workflow.get_graph().edges

    router_targets = [e.target for e in edges if e.source == "router"]
    assert set(router_targets) == {"recruiter", "tech_writer", "copywriter"}
```

### Test: Fan-In Edges

```python
def test_graph_has_fan_in_edges():
    """Verify three agent nodes converge at aggregator."""
    workflow = build_review_workflow()
    edges = workflow.get_graph().edges

    aggregator_sources = [e.source for e in edges if e.target == "aggregator"]
    assert set(aggregator_sources) == {"recruiter", "tech_writer", "copywriter"}
```

### Test: Loop Back to Router

```python
def test_graph_loops_back_to_router():
    """Verify revisor loops back to router, not supervisor."""
    workflow = build_review_workflow()
    edges = workflow.get_graph().edges

    revisor_target = [e.target for e in edges if e.source == "revisor"]
    assert revisor_target == ["router"]
```

---

## Performance Impact

**Before**:
- Total nodes visited per iteration: 2 (supervisor, aggregator)
- Parallel execution: Inside supervisor node (asyncio.gather)

**After**:
- Total nodes visited per iteration: 5 (router, recruiter, tech_writer, copywriter, aggregator)
- Parallel execution: LangGraph schedules recruiter/tech_writer/copywriter in parallel

**Performance Change**: ✅ **None** (same parallelism, different orchestration)

**Latency Formula**:
- **Before**: `latency = max(agent durations)`
- **After**: `latency = max(agent durations)` (identical)

---

## Migration Checklist

- [ ] Remove `supervisor_node` from imports
- [ ] Add `router_node`, `recruiter_node`, `tech_writer_node`, `copywriter_node` imports
- [ ] Update `add_node()` calls (remove supervisor, add 4 new nodes)
- [ ] Change `set_entry_point()` from "supervisor" to "router"
- [ ] Add 3 fan-out edges (router → agents)
- [ ] Add 3 fan-in edges (agents → aggregator)
- [ ] Update loop edge: "revisor" → "router" (not "supervisor")
- [ ] Update tests that assert on graph structure

---

## Related Contracts

- [router_node.md](./router_node.md): Entry point node
- [README.md](./README.md): Agent node implementations
- [aggregator_node.md](./aggregator_node.md): Fan-in collector

---

## Change History

| Date | Change | Author |
|------|--------|--------|
| 2026-01-09 | Initial graph redesign | Plan phase |
