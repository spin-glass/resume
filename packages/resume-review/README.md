# Resume Review Multi-Agent System

A CLI tool that uses multi-agent AI workflow to automatically review and improve resumes for high-value contract positions.

## Architecture

This system uses [LangGraph](https://github.com/langchain-ai/langgraph) for multi-agent orchestration with Claude Sonnet 4.5 to evaluate resumes from multiple perspectives:

- **Recruiter Agent**: Evaluates content from contract acquisition perspective
- **Technical Writer Agent**: Assesses technical depth and clarity
- **Copywriter Agent**: Reviews marketing effectiveness and impact
- **UX Designer Agent**: Analyzes information hierarchy and scannability
- **Visual Designer Agent**: Evaluates visual presentation from screenshots

## Features

- **Multi-perspective evaluation**: Get feedback from 5 specialized AI agents
- **Iterative improvement**: Automatically revises content until quality threshold is met (default: 8.0/10)
- **Portfolio gap analysis**: Identifies missing skills and suggests portfolio projects
- **Visual design review**: Captures screenshots and evaluates visual presentation
- **Dry-run mode**: Preview changes before applying them
- **YAML preservation**: Maintains Quarto frontmatter integrity
- **No fabrication**: Enforces truthful enhancements only (FR-008)
- **Automatic validation retry**: Detects Quarto syntax errors and automatically retries with fixes (default: 3 retries)
- **Retry logging**: Detailed markdown logs track every validation attempt with timestamps

## Quick Start

See [quickstart.md](../specs/001-resume-review-agents/quickstart.md) for detailed setup instructions.

### Installation

```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
cd agents
uv sync

# Install Playwright browsers
source .venv/bin/activate
playwright install chromium
```

### Configuration

Create a `.env` file in the `agents/` directory:

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

### Usage

**IMPORTANT**: The review command NEVER overwrites the input file automatically. Results are saved in `review_TIMESTAMP/` directories. You must manually copy the desired iteration to apply changes.

```bash
# Basic review with iteration saves
python -m src.cli review --input ../public/assets/resume-ja.qmd --save-iterations

# Review creates: review_20260109_123456/iter1/resume.qmd
#                 review_20260109_123456/iter2/resume.qmd
#                 review_20260109_123456/iter3/resume.qmd

# Manually apply changes from desired iteration
cp review_20260109_123456/iter3/resume.qmd ../public/assets/resume-ja.qmd

# Dry-run preview (no saves)
python -m src.cli review --input ../public/assets/resume-ja.qmd --dry-run

# Full review with design analysis
python -m src.cli review \
  --input ../public/assets/resume-ja.qmd \
  --screenshot-url http://localhost:3000/ja \
  --save-iterations

# Custom threshold and target role
python -m src.cli review \
  --input ../public/assets/resume-ja.qmd \
  --threshold 9.0 \
  --target-role "Senior Backend Engineer" \
  --save-iterations

# With custom validation retry settings
python -m src.cli review \
  --input ../public/assets/resume-ja.qmd \
  --max-validation-retries 1 \
  --save-iterations

# Strict validation mode (exit on validation failure)
python -m src.cli review \
  --input ../public/assets/resume-ja.qmd \
  --strict-validation \
  --save-iterations
```

### Validation Retry Feature

When Quarto validation fails during content revision, the system automatically:

1. **Detects errors**: Parses Quarto error messages into structured feedback
2. **Retries with fixes**: Re-invokes the revisor agent with validation-specific feedback
3. **Logs attempts**: Creates detailed markdown logs showing each retry attempt
4. **Saves artifacts**: Stores intermediate QMD files for debugging

**Configuration options:**

- `--max-validation-retries N`: Set maximum retry attempts (default: 3, set to 0 to disable)
- `--strict-validation`: Exit workflow if validation fails after all retries (default: continue with warning)

**Output files:**

- `review_{timestamp}/iter{N}_retry{M}.qmd`: Retry artifacts for debugging
- `review_{timestamp}/iter{N}_validation_retry.md`: Detailed log with timestamps

See [validation_retry_log_example.md](docs/examples/validation_retry_log_example.md) for sample log format.

```

## Project Structure

```
agents/
├── src/
│   ├── cli.py                   # CLI entry point
│   ├── agents/                  # Agent implementations
│   │   ├── base.py              # Base agent interface
│   │   ├── recruiter.py         # Recruiter perspective
│   │   ├── technical_writer.py  # Technical depth
│   │   ├── copywriter.py        # Marketing effectiveness
│   │   ├── ux_designer.py       # Information hierarchy
│   │   └── visual_designer.py   # Visual presentation
│   ├── orchestration/           # Workflow coordination
│   │   ├── workflow.py          # LangGraph state machine
│   │   └── scoring.py           # Score aggregation
│   ├── models/                  # Pydantic data models
│   │   ├── feedback.py          # Feedback, Issue entities
│   │   ├── portfolio.py         # Portfolio item model
│   │   └── session.py           # Review session tracking
│   ├── services/                # Core services
│   │   ├── qmd_parser.py        # QMD file I/O
│   │   ├── screenshot.py        # Playwright screenshot capture
│   │   └── revision.py          # Content revision application
│   └── utils/
│       └── config.py            # Configuration management
├── tests/
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── fixtures/                # Test data
├── pyproject.toml               # Project configuration
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

## Data Model

See [data-model.md](../specs/001-resume-review-agents/data-model.md) for complete entity definitions.

### Core Entities

- **Resume**: QMD file with YAML frontmatter and content
- **Feedback**: Agent evaluation with score (1-10), strengths, issues, suggestions
- **Issue**: Specific problem with action_type (add_content, restructure, emphasize, etc.)
- **PortfolioItem**: Suggested project with repository naming convention
- **ReviewSession**: Complete workflow tracking iterations and state

### Scoring System

Weighted average of agent scores (FR-004):
- Recruiter: 30%
- Technical Writer: 20%
- Copywriter: 25%
- UX Designer: 15%
- Visual Designer: 10%

## Development

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# With coverage
pytest --cov=src --cov-report=html
```

### Type Checking

```bash
mypy src/
```

### Linting

```bash
ruff check .
ruff format .
```

## Cost Considerations

Each review costs approximately **$0.50-$1.50** depending on:
- Number of iterations (1-3)
- Whether design review is included
- Resume length

See [quickstart.md](../specs/001-resume-review-agents/quickstart.md#cost-management) for detailed cost breakdown and optimization tips.

## Design Principles

1. **Single Source of Truth**: QMD file is the only editable source
2. **YAML Preservation**: Frontmatter is never corrupted (FR-009)
3. **No Fabrication**: System cannot invent work experience (FR-008)
4. **Manual Application**: Review results are never automatically applied to the original file
5. **Preview-First**: Dry-run mode allows safe previewing
6. **Graceful Degradation**: Design review is optional, warnings not errors

## Requirements

- Python 3.13+ (3.14 support pending LangGraph compatibility)
- Anthropic API key (Claude Sonnet 4.5 access)
- Playwright (for screenshot capture)
- Node.js 22.x (for dev server, optional)

## Documentation

- [Specification](../specs/001-resume-review-agents/spec.md)
- [Implementation Plan](../specs/001-resume-review-agents/plan.md)
- [Data Model](../specs/001-resume-review-agents/data-model.md)
- [Quickstart Guide](../specs/001-resume-review-agents/quickstart.md)
- [CLI Interface Contract](../specs/001-resume-review-agents/contracts/cli-interface.md)
- [Agent Interface Contract](../specs/001-resume-review-agents/contracts/agent-interface.md)
- [Revision Service Contract](../specs/001-resume-review-agents/contracts/revision-service.md)

## License

This project is part of a personal resume workflow. Not intended for public distribution.
