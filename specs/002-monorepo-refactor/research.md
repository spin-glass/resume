# Research: Monorepo Refactor

**Feature**: 002-monorepo-refactor
**Date**: 2026-01-09
**Purpose**: Resolve technical decisions for repository reorganization

---

## 1. pnpm Workspace Configuration

### Decision
Use `pnpm-workspace.yaml` with glob patterns to manage workspace packages. Include both Node.js packages (`packages/*`) and reference Python packages explicitly even though pnpm won't manage their dependencies.

### Rationale
- pnpm workspaces require explicit declaration via `pnpm-workspace.yaml` (not in package.json like npm/yarn)
- Glob patterns allow flexible directory structures without hardcoding individual packages
- Single virtual store at monorepo root improves disk efficiency and prevents phantom dependencies
- Python packages are coordinated via root scripts, not pnpm dependency management

### Configuration

```yaml
# pnpm-workspace.yaml
packages:
  - 'packages/*'    # All immediate subdirectories in packages/
```

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Turborepo | Adds complexity; pnpm workspaces sufficient for 2 packages |
| Nx | Overkill for this project size |
| Single package.json | Doesn't support separate package dependencies |

---

## 2. Root package.json Scripts

### Decision
Use pnpm's `--filter` flag for Node.js packages and explicit `cd` commands for Python packages. Separate script namespaces for different ecosystems.

### Rationale
- Centralizes control and provides single entry point for developers
- pnpm's filtering is more powerful than npm workspaces for selective execution
- Explicit `cd` commands for Python packages make dependencies clear
- Streaming output shows interleaved logs from all packages simultaneously

### Configuration

```json
{
  "scripts": {
    "dev": "pnpm --filter web dev",
    "build": "pnpm --filter web build",
    "start": "pnpm --filter web start",

    "quarto:pdf": "cd resume && quarto render resume-ja.qmd --to pdf -o output/resume-ja.pdf",
    "quarto:html": "cd resume && quarto render resume-ja.qmd --to html -o output/resume-ja.html",
    "quarto:preview": "cd resume && quarto preview resume-ja.qmd",
    "quarto:preview:html": "cd resume && quarto preview resume-ja.qmd --to html",

    "sync": "python3 scripts/sync_qmd_to_mdx.py",
    "resume:build": "pnpm quarto:pdf && pnpm quarto:html && pnpm sync",

    "review": "cd packages/resume-review && python -m src.cli review --input ../../resume/resume-ja.qmd",
    "review:dry": "cd packages/resume-review && python -m src.cli review --input ../../resume/resume-ja.qmd --dry-run --verbose",
    "review:full": "cd packages/resume-review && python -m src.cli review --input ../../resume/resume-ja.qmd --screenshot-url http://localhost:3000/ja --verbose",
    "review:build": "pnpm review && pnpm resume:build",

    "test:python": "cd packages/resume-review && pytest",
    "lint:python": "cd packages/resume-review && ruff check ."
  }
}
```

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| mise task runner | Adds another tool; npm scripts sufficient for this scope |
| Shell wrapper script | Harder to discover; npm scripts are conventional |

---

## 3. Python Workflow Module Splitting

### Decision
Split the 829-line `workflow.py` into a directory structure with separate modules for nodes, edges (conditions), graph construction, and the workflow class.

### Rationale
- **Separation of Concerns**: Each module has single responsibility
- **Prevents Circular Dependencies**: Unidirectional import flow from state → nodes/edges → graph → workflow
- **Maintainability**: Files under 200 lines each
- **Testability**: Individual nodes can be tested independently
- **Follows LangGraph patterns**: Official documentation recommends similar structure

### Target Structure

```
workflow/                        # Renamed from orchestration
├── __init__.py                  # Public API exports
├── state.py                     # State schema & reducers (existing)
├── scoring.py                   # Score calculation (existing)
├── graph.py                     # Graph builder & compilation
├── runner.py                    # ReviewWorkflow class
├── nodes/
│   ├── __init__.py             # Node exports
│   ├── supervisor.py           # supervisor_node & design_supervisor_node
│   ├── aggregator.py           # aggregator_node
│   ├── revisor.py              # revisor_node
│   └── portfolio.py            # portfolio_analyzer_node
└── conditions.py               # Conditional edge functions
```

### Import Dependency Flow

```
state.py (foundation - no internal imports)
    ↓
scoring.py (imports state)
    ↓
nodes/*.py (imports state, agents, services)
conditions.py (imports state only)
    ↓
graph.py (imports state, nodes, conditions)
    ↓
runner.py (imports graph, models, services)
    ↓
__init__.py (exports graph, runner, state)
```

### File Size Distribution After Refactoring

| File | Approx Lines | Purpose |
|------|-------------|---------|
| state.py | 76 | State schema (existing) |
| scoring.py | 40 | Score calculation (existing) |
| nodes/supervisor.py | 80 | Supervisor & design supervisor nodes |
| nodes/aggregator.py | 40 | Aggregator node |
| nodes/revisor.py | 50 | Revisor node |
| nodes/portfolio.py | 110 | Portfolio analyzer node |
| conditions.py | 30 | Conditional edge functions |
| graph.py | 60 | Graph construction |
| runner.py | 300 | ReviewWorkflow class + utilities |
| **Total** | **~786** | Same logic, better organization |

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Keep single file | 829 lines violates 200-line requirement |
| Split by function type only | Doesn't provide enough isolation |
| Separate package per node | Over-engineering for 5 nodes |

---

## 4. Configuration Centralization

### Decision
Create a `config/` directory with separate modules for settings, prompts, and scoring weights.

### Rationale
- Centralizes all magic numbers and configuration values
- Makes prompts easier to edit without touching code logic
- Enables future configuration via environment variables

### Structure

```
config/
├── __init__.py
├── settings.py     # API keys, thresholds, paths
├── prompts.py      # System prompts for each agent
└── weights.py      # Scoring weights for each agent
```

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|------------------|
| Keep in utils/config.py | Grows too large; single responsibility violated |
| YAML/JSON config files | Adds parsing complexity; Python files simpler |
| pydantic-settings | Future enhancement, not needed for MVP refactor |

---

## 5. Handling Python Package in pnpm Workspace

### Decision
Do not include Python package in pnpm-workspace.yaml packages list. Keep it in `packages/resume-review/` but manage via explicit root scripts.

### Rationale
- pnpm cannot manage Python dependencies via pip/poetry/uv
- Explicit scripts make workflows clear
- Colocating in packages/ maintains logical organization
- Virtual environment stays within package directory

### Implementation

```yaml
# pnpm-workspace.yaml - only Node.js packages
packages:
  - 'packages/web'
```

```json
// package.json - explicit Python commands
{
  "scripts": {
    "review": "cd packages/resume-review && python -m src.cli review ...",
    "test:python": "cd packages/resume-review && pytest"
  }
}
```

---

## Sources

- [pnpm Workspaces Official Documentation](https://pnpm.io/workspaces)
- [LangGraph Application Structure Documentation](https://docs.langchain.com/langgraph-platform/application-structure)
- [Python Circular Import Best Practices](https://www.datacamp.com/tutorial/python-circular-import)
- [Complete Monorepo Guide: pnpm + Workspace](https://jsdev.space/complete-monorepo-guide/)
