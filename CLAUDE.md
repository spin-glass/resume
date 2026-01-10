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
- Python 3.13, LangGraph 1.0.0+, Anthropic SDK 0.25.0+, Pydantic 2.0+
- Multi-model support: Gemini, OpenAI, Anthropic (003-multi-model-hybrid)
- Quarto validation with auto-retry (009-quarto-retry-loop)
- Python 3.13 (matching existing resume-review package) (013-design-auto-fix)
- File system (CSS output files, backups, screenshots) (013-design-auto-fix)

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

# AI Review with Validation Retry (009-quarto-retry-loop)
pnpm review --max-validation-retries 1        # Custom retry limit
pnpm review --strict-validation               # Exit on validation failure
pnpm review --max-validation-retries 0        # Skip retry loop

# Python testing
pnpm test:python           # Run pytest
pnpm lint:python           # Run ruff linter

# Sync
pnpm sync                  # Sync QMD to MDX for web
```

## Validation Retry Workflow (009-quarto-retry-loop)

**Feature**: Automatic retry loop for Quarto validation failures with comprehensive logging

### How It Works

1. **After Revisor Node**: Every iteration's revised QMD content is validated with Quarto
2. **On Validation Failure**:
   - Parses error message into structured Feedback
   - Re-invokes revisor with validation feedback
   - Saves retry artifacts: `iter{N}_retry{M}.qmd`
   - Logs to: `iter{N}_validation_retry.md`
3. **Retry Loop**: Continues until validation passes OR max retries exhausted
4. **Modes**:
   - **Default** (`strict_validation=False`): Continue workflow with warning if validation fails
   - **Strict** (`strict_validation=True`): Exit workflow if validation fails after all retries

### Configuration

```bash
# Default: 3 retries, continue on failure
pnpm review --save-iterations

# Custom retry limit
pnpm review --max-validation-retries 1 --save-iterations

# Strict mode (exit on failure)
pnpm review --strict-validation --save-iterations

# Disable retry (legacy behavior)
pnpm review --max-validation-retries 0 --save-iterations
```

### Output Files

- `review_{timestamp}/iter{N}/resume.qmd` - Final iteration output
- `review_{timestamp}/iter{N}_retry{M}.qmd` - Retry artifacts (if validation fails)
- `review_{timestamp}/iter{N}_validation_retry.md` - Detailed retry log with timestamps

### Error Patterns Detected

1. **Standalone # markers** (T012): Invalid heading syntax
2. **YAML frontmatter errors** (T013): Syntax errors in document header
3. **Unclosed code blocks** (T014): Missing closing ```
4. **Invalid markdown tables** (T015): Column count mismatch
5. **Fallback** (T016): Any other Quarto errors

## Code Style

- **Python**: Follow PEP 8, use type hints, workflow files must be <200 lines
- **TypeScript/JavaScript**: Follow Next.js conventions
- **Commits**: Include `Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>`

## Recent Changes
- 013-design-auto-fix: Added Python 3.13 (matching existing resume-review package)
- 003-multi-model-hybrid: Multi-provider LLM support (Gemini, OpenAI, Anthropic)
- 009-quarto-retry-loop: Quarto validation auto-retry with logging


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
