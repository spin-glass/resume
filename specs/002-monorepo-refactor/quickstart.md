# Quickstart: Monorepo Refactor

**Feature**: 002-monorepo-refactor
**Date**: 2026-01-09

---

## Prerequisites

- Node.js 22.x
- pnpm 9.x
- Python 3.13
- uv (Python package manager)
- Quarto CLI

---

## After Migration: Quick Commands

### From Repository Root

```bash
# Install all dependencies
pnpm install                      # Node.js packages
cd packages/resume-review && uv sync  # Python packages

# Development
pnpm dev                          # Start web dev server
pnpm quarto:preview               # Preview resume

# Build
pnpm build                        # Build web app
pnpm resume:build                 # Build PDF + HTML + sync MDX

# Review
pnpm review                       # Run AI review
pnpm review:dry                   # Dry run with verbose output

# Testing
pnpm test:python                  # Run Python tests
pnpm lint:python                  # Lint Python code
```

---

## Directory Navigation

```bash
# Web package
cd packages/web
pnpm dev                          # Start dev server

# Resume review package
cd packages/resume-review
pytest                            # Run tests
python -m src.cli --help          # CLI help

# Resume content
cd resume
quarto preview resume-ja.qmd      # Preview
ls output/                        # Generated files
```

---

## Common Tasks

### Edit Resume Content

```bash
# 1. Edit the source file
$EDITOR resume/resume-ja.qmd

# 2. Preview changes
pnpm quarto:preview:html

# 3. Build all outputs
pnpm resume:build

# 4. Verify outputs
ls resume/output/
```

### Run AI Review

```bash
# Basic review
pnpm review

# Review with screenshot (web server must be running)
pnpm dev &                        # Start web server
pnpm review:full                  # Full review with design analysis

# Review then build
pnpm review:build
```

### Develop Web Package

```bash
cd packages/web
pnpm dev                          # http://localhost:3000

# Or from root
pnpm dev
```

### Develop Python Package

```bash
cd packages/resume-review

# Activate virtual environment
source .venv/bin/activate

# Run tests
pytest tests/ -v

# Run specific test
pytest tests/integration/test_langgraph_workflow.py -v

# Lint
ruff check .

# Run CLI directly
python -m src.cli review --input ../../resume/resume-ja.qmd --dry-run
```

---

## Workflow Module Structure

After refactoring, the workflow module has this structure:

```
packages/resume-review/src/workflow/
├── __init__.py          # Public API
├── state.py             # ReviewState definition
├── scoring.py           # Score calculation
├── conditions.py        # Edge conditions
├── graph.py             # StateGraph builder
├── runner.py            # ReviewWorkflow class
└── nodes/
    ├── __init__.py
    ├── supervisor.py    # supervisor_node, design_supervisor_node
    ├── aggregator.py    # aggregator_node
    ├── revisor.py       # revisor_node
    └── portfolio.py     # portfolio_analyzer_node
```

### Import Pattern

```python
# From outside the workflow module
from workflow import ReviewWorkflow, ReviewState

# From within workflow module (in runner.py)
from .graph import build_review_workflow
from .state import ReviewState

# From within nodes (in supervisor.py)
from ..state import ReviewState
from ...agents import RecruiterAgent
```

---

## Configuration

### Environment Variables

```bash
# Python package
export ANTHROPIC_API_KEY="your-key"

# Or use .env file in packages/resume-review/
echo "ANTHROPIC_API_KEY=your-key" > packages/resume-review/.env
```

### Configuration Files

```
packages/resume-review/src/config/
├── settings.py          # API keys, thresholds
├── prompts.py           # Agent system prompts
└── weights.py           # Scoring weights
```

---

## Troubleshooting

### Web Package Issues

```bash
# Clear Next.js cache
rm -rf packages/web/.next
pnpm dev

# Reinstall dependencies
rm -rf packages/web/node_modules
pnpm install
```

### Python Package Issues

```bash
# Recreate virtual environment
cd packages/resume-review
rm -rf .venv
uv venv
uv sync

# Check imports
python -c "from src.workflow import ReviewWorkflow; print('OK')"
```

### Resume Build Issues

```bash
# Check Quarto installation
quarto check

# Check resume source exists
ls resume/resume-ja.qmd

# Create output directory
mkdir -p resume/output
```

---

## Verification Checklist

After migration, verify:

- [ ] `pnpm dev` starts web server at localhost:3000
- [ ] `pnpm build` completes without errors
- [ ] `pnpm quarto:pdf` generates `resume/output/resume-ja.pdf`
- [ ] `pnpm review:dry` runs without errors
- [ ] `pnpm test:python` passes all tests
- [ ] No workflow file exceeds 200 lines: `wc -l packages/resume-review/src/workflow/*.py packages/resume-review/src/workflow/nodes/*.py`
