# Workflow Visualization Scripts

Visualization tools for the LangGraph StateGraph resume review workflow.

## visualize_graph.py

Generate visual representations of the workflow graph structure.

### Usage

```bash
# ASCII format (default) - shows node/edge lists and flow diagram
python scripts/visualize_graph.py --format ascii

# Mermaid format - uses LangGraph's native mermaid generation
python scripts/visualize_graph.py --format mermaid

# PNG format - generates image file (requires additional dependencies)
python scripts/visualize_graph.py --format png --output workflow.png

# LangSmith instructions - shows how to enable interactive trace viewer
python scripts/visualize_graph.py --format langsmith
```

### Via pnpm (from repository root)

```bash
# ASCII visualization
pnpm graph:view

# Mermaid diagram
pnpm graph:mermaid

# PNG image (requires: pip install grandalf)
pnpm graph:png

# LangSmith instructions
pnpm graph:langsmith
```

## Visualization Formats

### 1. ASCII Format

Shows:
- Complete node list (10 nodes including __start__ and __end__)
- Complete edge list (13 edges)
- Fan-out pattern (router → 3 agents in parallel)
- Fan-in pattern (3 agents → aggregator, waits for all)
- Execution flow diagram with ASCII art

Optionally includes LangGraph's native ASCII visualization if `grandalf` is installed:
```bash
pip install grandalf
```

### 2. Mermaid Format

Uses LangGraph's built-in `draw_mermaid()` method to generate a Mermaid diagram with:
- Flowchart configuration
- All nodes with proper styling
- All edges including conditional edges
- Compatible with Mermaid viewers and GitHub

### 3. PNG Format

Uses LangGraph's `draw_mermaid_png()` to generate a PNG image.

**Requirements:**
```bash
pip install grandalf
```

Outputs a workflow.png file with a visual graph representation.

### 4. LangSmith Format

Prints instructions for using LangSmith's interactive trace viewer, which provides:
- Real-time execution traces
- Individual node timing and outputs
- Parallel execution visualization
- Per-agent LLM call inspection

To enable LangSmith tracing:
```bash
export LANGSMITH_API_KEY=your-api-key
export LANGSMITH_TRACING=true
pnpm review:dry --verbose
```

View traces at: https://smith.langchain.com/

## Graph Structure Overview

### Nodes
- `router` - Fan-out coordinator (entry point)
- `recruiter` - Recruiter agent evaluation
- `tech_writer` - Technical writer agent evaluation
- `copywriter` - Copywriter agent evaluation
- `aggregator` - Collects feedback and calculates integrated score
- `revisor` - Revises resume based on feedback
- `portfolio` - Analyzes skill gaps and portfolio suggestions
- `design` - Reviews visual design (optional)

### Key Patterns

**Fan-out (Parallel Execution):**
```
router → recruiter
router → tech_writer
router → copywriter
```

**Fan-in (Convergence):**
```
recruiter → aggregator
tech_writer → aggregator
copywriter → aggregator
```

**Iteration Loop:**
```
aggregator → revisor → router
```

## Implementation Details

- Uses LangGraph's native visualization methods when available
- Falls back to manual generation if dependencies are missing
- All formats are generated from the compiled workflow graph
- No hardcoded graph structure - always reflects actual implementation
