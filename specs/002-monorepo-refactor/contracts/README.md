# Contracts: Monorepo Refactor

**Feature**: 002-monorepo-refactor

---

## Overview

This refactoring feature does not introduce new APIs or external contracts. The changes are internal structural reorganization.

## Preserved Interfaces

### CLI Interface (Unchanged)

The resume-review CLI maintains the same interface:

```bash
# These commands continue to work identically
python -m src.cli review --input <path> [options]
python -m src.cli review --input <path> --dry-run --verbose
python -m src.cli review --input <path> --screenshot-url <url>
```

### Python API (Unchanged)

The public API remains the same:

```python
from workflow import ReviewWorkflow, ReviewState

# Usage unchanged
workflow = ReviewWorkflow(api_key="...")
result = await workflow.run_review(input_path, target_role, ...)
```

### npm Scripts (Updated Paths Only)

Root package.json scripts work from repository root with updated internal paths:

```bash
pnpm dev         # Same behavior
pnpm build       # Same behavior
pnpm review      # Same behavior (paths updated internally)
pnpm resume:build  # Same behavior (paths updated internally)
```

---

## No New Contracts

This refactoring maintains all existing contracts. No new API endpoints, schemas, or interfaces are introduced.
