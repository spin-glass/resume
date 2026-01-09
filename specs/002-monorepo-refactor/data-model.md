# Data Model: Monorepo Refactor

**Feature**: 002-monorepo-refactor
**Date**: 2026-01-09

---

## Overview

This refactoring does not introduce new data entities. It reorganizes existing code and configuration. This document describes the file/directory structure as the "data model" for this refactoring.

---

## Directory Entities

### 1. Workspace Package

A self-contained package with its own configuration and dependencies.

| Attribute | Type | Description |
|-----------|------|-------------|
| name | string | Package name in package.json or pyproject.toml |
| path | string | Location under `packages/` directory |
| type | enum | `node` or `python` |
| config_file | string | `package.json` or `pyproject.toml` |

**Instances**:
- `packages/web` (Node.js - Next.js/Nextra)
- `packages/resume-review` (Python - LangGraph agents)

### 2. Resume Source

The canonical resume content file.

| Attribute | Type | Description |
|-----------|------|-------------|
| path | string | `resume/resume-ja.qmd` |
| format | string | Quarto Markdown |
| outputs | list | PDF, HTML generated to `resume/output/` |

**Relationship**: Resume Source → Resume Output (1:N)

### 3. Resume Output

Generated artifacts from resume source.

| Attribute | Type | Description |
|-----------|------|-------------|
| path | string | `resume/output/{format}` |
| format | enum | `pdf`, `html` |
| source | reference | Link to Resume Source |

### 4. Workflow Module

A Python module containing workflow logic.

| Attribute | Type | Description |
|-----------|------|-------------|
| path | string | Location under `workflow/` directory |
| responsibility | string | Single concern (state, nodes, conditions, graph, runner) |
| max_lines | int | ≤200 lines |

**Instances**:
- `workflow/state.py` - State schema
- `workflow/nodes/supervisor.py` - Supervisor node
- `workflow/nodes/aggregator.py` - Aggregator node
- `workflow/nodes/revisor.py` - Revisor node
- `workflow/nodes/portfolio.py` - Portfolio node
- `workflow/conditions.py` - Edge conditions
- `workflow/graph.py` - Graph builder
- `workflow/runner.py` - Workflow class

---

## Configuration Entities

### 5. Config Module

Centralized configuration for the resume-review package.

| Attribute | Type | Description |
|-----------|------|-------------|
| path | string | `config/{name}.py` |
| content_type | enum | `settings`, `prompts`, `weights` |

**Instances**:
- `config/settings.py` - API keys, thresholds, paths
- `config/prompts.py` - System prompts for agents
- `config/weights.py` - Scoring weights

---

## File Migration Map

### Files Moving

| Current Path | New Path | Notes |
|--------------|----------|-------|
| `public/assets/resume-ja.qmd` | `resume/resume-ja.qmd` | Canonical source |
| `resume.pdf` (root) | `resume/output/resume-ja.pdf` | Generated output |
| `components/` | `packages/web/components/` | React components |
| `pages/` | `packages/web/pages/` | Next.js pages |
| `styles/` | `packages/web/styles/` | CSS |
| `next.config.mjs` | `packages/web/next.config.mjs` | Next.js config |
| `theme.config.tsx` | `packages/web/theme.config.tsx` | Nextra theme |
| `tailwind.config.js` | `packages/web/tailwind.config.js` | Tailwind config |
| `tsconfig.json` | `packages/web/tsconfig.json` | TypeScript config |
| `middleware.ts` | `packages/web/middleware.ts` | Next.js middleware |
| `agents/` | `packages/resume-review/` | Python package |
| `agents/src/orchestration/` | `packages/resume-review/src/workflow/` | Renamed |

### Files Created

| New Path | Purpose |
|----------|---------|
| `packages/web/package.json` | Web package config |
| `resume/output/` | Output directory |
| `packages/resume-review/src/workflow/nodes/` | Node modules |
| `packages/resume-review/src/workflow/conditions.py` | Edge conditions |
| `packages/resume-review/src/workflow/graph.py` | Graph builder |
| `packages/resume-review/src/workflow/runner.py` | Workflow class |
| `packages/resume-review/src/config/` | Configuration modules |

### Files Updated

| Path | Changes |
|------|---------|
| `package.json` (root) | Remove web deps, add workspace scripts |
| `pnpm-workspace.yaml` | Add `packages/web` to packages list |
| `scripts/sync_qmd_to_mdx.py` | Update paths |
| `CLAUDE.md` | Update paths in commands |

---

## State Transitions

### Migration Phases

```
Phase 1: Create Directories
├── mkdir packages/
├── mkdir packages/web/
├── mkdir resume/
└── mkdir resume/output/

Phase 2: Move Web Package
├── mv components/ → packages/web/
├── mv pages/ → packages/web/
├── mv styles/ → packages/web/
├── mv *.config.* → packages/web/
├── Create packages/web/package.json
└── Update pnpm-workspace.yaml

Phase 3: Move Resume Source
├── mv public/assets/resume-ja.qmd → resume/
├── mv resume.pdf → resume/output/
└── Update build scripts

Phase 4: Move Python Package
├── mv agents/ → packages/resume-review/
└── Update root scripts

Phase 5: Refactor Workflow
├── Rename orchestration/ → workflow/
├── Split workflow.py → nodes/, conditions.py, graph.py, runner.py
├── Create config/
└── Update imports

Phase 6: Verification
├── Run tests
├── Start web dev server
├── Generate PDF
└── Run review command
```

---

## Validation Rules

### Workspace Package Validation

- Each package under `packages/` MUST have a valid config file
- Node.js packages MUST have `package.json`
- Python packages MUST have `pyproject.toml`
- All packages MUST be recognized by their respective tooling

### Workflow Module Validation

- No file in `workflow/` directory MAY exceed 200 lines
- All existing tests MUST pass after migration
- No circular imports MUST exist between modules
- Import flow MUST be: state → nodes/conditions → graph → runner

### Resume Source Validation

- `resume/resume-ja.qmd` MUST exist
- `resume/output/` MUST be creatable by build scripts
- Generated files MUST appear in `resume/output/`
