# resume Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-09

## Monorepo Structure

```text
resume/                     # Monorepo root
├── packages/
│   ├── web/               # Next.js/Nextra web application
│   │   ├── components/
│   │   ├── pages/
│   │   ├── styles/
│   │   └── package.json
│   └── resume-review/     # Python AI review tool
│       ├── src/
│       │   ├── agents/    # Individual review agents
│       │   ├── workflow/  # LangGraph workflow (split into <200 line files)
│       │   ├── models/
│       │   ├── services/
│       │   └── config/    # Centralized configuration
│       └── tests/
├── resume/                # Resume source files
│   ├── resume-ja.qmd     # Canonical resume source
│   └── output/           # Generated PDF/HTML
└── scripts/              # Build and sync scripts
```

## Active Technologies
- Python 3.13 (existing, LangGraph compatible) (003-multi-model-hybrid)
- In-memory state (LangGraph StateGraph), filesystem for resume files (003-multi-model-hybrid)

- **Web**: Next.js 14, Nextra 3.0 (alpha), React 18, Tailwind CSS
- **Python**: Python 3.13+ (LangGraph compatibility), LangGraph (multi-agent orchestration), Anthropic SDK (Claude API), Playwright (screenshot capture), pytest (testing)
- **Resume**: Quarto (QMD → PDF/HTML generation)

## Commands

All commands run from repository root:

```bash
# Web development
pnpm dev                    # Start Next.js dev server
pnpm build                  # Build web application
pnpm start                  # Start production server

# Resume generation
pnpm quarto:pdf            # Generate PDF in resume/output/
pnpm quarto:html           # Generate HTML in resume/output/
pnpm quarto:preview        # Preview resume in browser
pnpm resume:build          # Generate PDF + HTML + sync to web

# AI Review
pnpm review                # Run full review (modifies resume)
pnpm review:dry            # Dry run (preview only, no modifications)
pnpm review:full           # Full review with screenshot analysis

# Python testing
pnpm test:python           # Run pytest
pnpm lint:python           # Run ruff linter

# Sync
pnpm sync                  # Sync QMD to MDX for web
```

## Code Style

- **Python**: Follow PEP 8, use type hints, workflow files must be <200 lines
- **TypeScript/JavaScript**: Follow Next.js conventions
- **Commits**: Include `Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>`

## Recent Changes
- 003-multi-model-hybrid: Added Python 3.13 (existing, LangGraph compatible)

- 002-monorepo-refactor: Reorganized repository into pnpm monorepo with packages/web/, packages/resume-review/, and resume/ directories
- 001-resume-review-agents: Added multi-agent resume review system with LangGraph workflow

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
