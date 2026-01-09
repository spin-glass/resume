# Implementation Plan: Monorepo Refactor

**Branch**: `002-monorepo-refactor` | **Date**: 2026-01-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-monorepo-refactor/spec.md`

## Summary

Reorganize the repository from a flat structure with mixed concerns into a proper pnpm monorepo with clear package separation. The primary changes are:
1. Move web application (Next.js/Nextra) to `packages/web/`
2. Move AI review tool to `packages/resume-review/`
3. Move resume source to `resume/` at root with dedicated `output/` directory
4. Split the 829-line `workflow.py` into manageable modules under 200 lines each
5. Centralize configuration in `config/` directory

## Technical Context

**Language/Version**:
- Python 3.13 (agents/resume-review package)
- TypeScript/Node.js 22.x (web package)
- Quarto (resume source)

**Primary Dependencies**:
- Web: Next.js 14, Nextra 3.0.0-alpha.31, React 18
- Python: LangGraph, langchain-anthropic, Playwright, Pydantic 2.x, Click

**Storage**: Files (QMD input/output, cached screenshots)

**Testing**:
- Python: pytest, pytest-asyncio
- TypeScript: N/A (no tests currently)

**Target Platform**: macOS/Linux development, Vercel deployment

**Project Type**: Monorepo (pnpm workspaces)

**Performance Goals**: N/A (refactoring, no functional changes)

**Constraints**:
- All existing functionality must continue to work
- CLI interface must remain compatible
- No workflow file over 200 lines after refactor

**Scale/Scope**:
- 2 packages (web, resume-review)
- 1 resume source directory
- ~15 Python files to reorganize

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Single Source of Truth | PASS | Resume source moves to `resume/resume-ja.qmd` - still single source, just new location |
| II. Automated Generation | PASS | Build scripts updated to new paths, automation preserved |
| III. Preview-First Workflow | PASS | Quarto preview commands updated to new paths |
| IV. Deployment Simplicity | PASS | Vercel auto-deploy unchanged, just package location changes |
| V. Toolchain Consistency | PASS | Same toolchain (Quarto, LuaLaTeX, Hiragino), paths updated in docs |

**Gate Result**: PASS - All constitution principles maintained. The refactoring changes structure only, not workflow or toolchain.

## Project Structure

### Documentation (this feature)

```text
specs/002-monorepo-refactor/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - no API contracts)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

**Current Structure** (before refactor):
```text
resume/                              # Repository root
├── agents/                          # Python CLI (829-line workflow.py)
├── components/                      # React components
├── pages/                           # Next.js pages
├── public/assets/resume-ja.qmd     # Resume source (deep path)
├── scripts/                         # Sync scripts
├── styles/                          # CSS
├── package.json                     # Root (web app config)
├── pnpm-workspace.yaml              # Empty workspace config
└── resume.pdf                       # Generated PDF (root level)
```

**Target Structure** (after refactor):
```text
resume/                              # Repository root (monorepo)
├── packages/
│   ├── web/                         # Next.js/Nextra package
│   │   ├── components/
│   │   ├── pages/
│   │   ├── styles/
│   │   ├── public/
│   │   ├── next.config.mjs
│   │   ├── theme.config.tsx
│   │   ├── tailwind.config.js
│   │   ├── tsconfig.json
│   │   ├── middleware.ts
│   │   └── package.json
│   │
│   └── resume-review/               # Python AI agents package
│       ├── src/
│       │   ├── cli.py
│       │   ├── agents/
│       │   │   ├── base.py
│       │   │   ├── recruiter.py
│       │   │   ├── technical_writer.py
│       │   │   ├── copywriter.py
│       │   │   ├── ux_designer.py
│       │   │   └── visual_designer.py
│       │   ├── models/
│       │   │   ├── feedback.py
│       │   │   ├── session.py
│       │   │   └── portfolio.py
│       │   ├── workflow/            # Renamed from orchestration
│       │   │   ├── state.py         # State definitions
│       │   │   ├── graph.py         # StateGraph construction
│       │   │   ├── conditions.py    # Edge conditions
│       │   │   ├── runner.py        # Workflow execution
│       │   │   ├── scoring.py       # Score calculation
│       │   │   └── nodes/           # Individual node functions
│       │   │       ├── __init__.py
│       │   │       ├── supervisor.py
│       │   │       ├── aggregator.py
│       │   │       ├── revisor.py
│       │   │       ├── portfolio.py
│       │   │       └── design.py
│       │   ├── services/
│       │   │   ├── qmd_parser.py
│       │   │   ├── revision.py
│       │   │   └── screenshot.py
│       │   ├── config/              # Centralized config
│       │   │   ├── settings.py
│       │   │   ├── prompts.py
│       │   │   └── weights.py
│       │   └── utils/
│       │       └── config.py
│       ├── tests/
│       ├── pyproject.toml
│       └── README.md
│
├── resume/                          # Resume source directory
│   ├── resume-ja.qmd               # Canonical source
│   └── output/                      # Generated outputs
│       ├── resume-ja.pdf
│       └── resume-ja.html
│
├── scripts/                         # Shared scripts
│   └── sync_qmd_to_mdx.py
│
├── specs/                           # Feature specifications
├── docs/                            # Documentation
│
├── package.json                     # Root package.json (workspace scripts)
├── pnpm-workspace.yaml              # Workspace configuration
├── crowdin.yml
├── CLAUDE.md
└── README.md
```

**Structure Decision**: Monorepo with `packages/` for workspace packages and `resume/` for content source. This separates concerns (web, AI tools, content) while enabling unified command execution from root.

## Complexity Tracking

No constitution violations requiring justification. The refactoring simplifies the structure rather than adding complexity.

| Aspect | Before | After | Improvement |
|--------|--------|-------|-------------|
| Workflow.py lines | 829 | <200 per file | 75%+ reduction per file |
| Resume source path | `public/assets/resume-ja.qmd` | `resume/resume-ja.qmd` | Clearer location |
| Package separation | Mixed in root | `packages/web`, `packages/resume-review` | Clear boundaries |
| Generated output | Root level | `resume/output/` | Organized |
