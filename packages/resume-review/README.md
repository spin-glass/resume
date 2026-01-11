# Resume Review Multi-Agent System

## 🎯 Portfolio Showcase

![LangGraph](https://img.shields.io/badge/LangGraph-1.0-0066cc?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEyIDJMMiAyMGgyMEwxMiAyeiIgZmlsbD0iI2ZmZiIvPjwvc3ZnPg==)
![Multi-Model](https://img.shields.io/badge/Multi--Model-Gemini%20%7C%20OpenAI%20%7C%20Claude-00b894)
![Cost Optimized](https://img.shields.io/badge/Cost-50%25%20Reduction-00b894)
![Python](https://img.shields.io/badge/Python-3.13+-3776ab?logo=python&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-2.0-e92063?logo=pydantic&logoColor=white)

**A production-grade multi-agent AI system showcasing:**
- ⚡ **LangGraph StateGraph** orchestration with fan-out/fan-in pattern
- 🧠 **Multi-model hybrid architecture** (Gemini, OpenAI o3-mini, Claude Sonnet 4.5)
- 💰 **50% cost reduction** and **70% faster execution** vs single-model baseline
- 🔧 **Type-safe state management** with Pydantic 2.0
- 🎨 **Advanced tool use**: Screenshot capture, Quarto validation, auto-retry loops

📖 **[Architecture Documentation](docs/architecture.md)** | 🎯 **[Live Demo](https://spin-glass.github.io/resume/portfolio)**

---
## Architecture

**For comprehensive architecture documentation, see [docs/architecture.md](docs/architecture.md)**

This system uses [LangGraph](https://github.com/langchain-ai/langgraph) for multi-agent orchestration with a **multi-model hybrid configuration** to optimize cost and performance:

- **Recruiter Agent**: Evaluates content from contract acquisition perspective (Gemini 3.0 Flash)
- **Technical Writer Agent**: Assesses technical depth and clarity (OpenAI o3-mini)
- **Copywriter Agent**: Reviews marketing effectiveness and impact (Claude Sonnet 4.5)
- **UX Designer Agent**: Analyzes information hierarchy and scannability (Gemini 3.0 Flash)
- **Visual Designer Agent**: Evaluates visual presentation from screenshots (Gemini 3.0 Flash)
- **Revisor Agent**: Applies full-rewrite revisions to eliminate errors (Gemini 3.0 Flash)

### Cost Optimization

By using different LLM providers for different agents, the system achieves:
- **50% cost reduction** compared to Claude-only baseline
- **70% faster execution** by leveraging lightweight models where appropriate
- **Enhanced technical evaluation** using o3-mini's advanced reasoning for Technical Writer
- **Full rewrite reliability** eliminating fuzzy replacement errors

Target cost per review: **<$0.55** (vs $1.10 baseline with Claude Opus 4.5 for all agents)

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

Create a `.env` file in the `packages/resume-review/` directory with API keys for all three providers:

```bash
# Required API Keys for Multi-Model Hybrid Configuration
ANTHROPIC_API_KEY=sk-ant-...           # For Copywriter agent (Claude Sonnet 4.5)
GEMINI_API_KEY=AIza...                 # For Recruiter, Designers, Revisor (Gemini 3.0 Flash)
OPENAI_API_KEY=sk-proj-...             # For Technical Writer (o3-mini)
```

**API Key Setup Instructions:**

1. **Anthropic API Key**: Get from [console.anthropic.com](https://console.anthropic.com/)
   - Used for Copywriter agent (Claude Sonnet 4.5)
   - Required for marketing effectiveness evaluation

2. **Gemini API Key**: Get from [aistudio.google.com](https://aistudio.google.com/apikey)
   - Used for Recruiter, UX/Visual Designers, and Revisor agents (Gemini 3.0 Flash)
   - Cost-effective for evaluation and full-rewrite tasks

3. **OpenAI API Key**: Get from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - Used for Technical Writer agent (o3-mini)
   - Advanced reasoning for technical evaluation

**Note**: You can start with just one API key (e.g., ANTHROPIC_API_KEY) using the `--model` override flag (see Model Override section below).

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

# Verbose mode (show model assignments)
python -m src.cli review \
  --input ../public/assets/resume-ja.qmd \
  --verbose \
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

### Model Override (Testing & Troubleshooting)

The `--model` flag allows you to override the hybrid configuration and use a single model for all agents:

```bash
# Use Gemini 3.0 Flash for all agents (lowest cost)
python -m src.cli review \
  --input ../public/assets/resume-ja.qmd \
  --model gemini-3.0-flash \
  --save-iterations

# Use Claude Sonnet 4.5 for all agents (highest quality)
python -m src.cli review \
  --input ../public/assets/resume-ja.qmd \
  --model claude-sonnet-4-5-20250929 \
  --save-iterations

# Use OpenAI o3-mini for all agents (balanced)
python -m src.cli review \
  --input ../public/assets/resume-ja.qmd \
  --model o3-mini \
  --save-iterations
```

**When to use model override:**
- Testing with a single API key
- Comparing model performance
- Debugging issues with specific providers
- Cost/quality trade-off experiments

**Supported models:**
- Gemini: `gemini-3.0-flash`, `gemini-2.5-flash`, etc.
- OpenAI: `o3-mini`, `o4-mini`, `gpt-4`, `gpt-3.5-turbo`, etc.
- Anthropic: `claude-sonnet-4-5-20250929`, `claude-opus-4-5-20251101`, etc.

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

### Hybrid vs Override Mode

**Hybrid Mode (Default)**:
- Each agent uses its optimal model (cost-effective + high quality)
- Requires all three API keys (Anthropic, Gemini, OpenAI)
- Target cost: <$0.55 per review
- Use `--verbose` to see model assignments

**Override Mode (with `--model` flag)**:
- All agents use the same model
- Only requires one API key
- Useful for testing, debugging, or single-provider setups
- Cost/quality depends on chosen model
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

## Troubleshooting

### API Key Issues

**Error: "Gemini API key is required but not provided"**
- Ensure `GEMINI_API_KEY` is set in `.env` file
- Alternative: Use `--model claude-sonnet-4-5-20250929` to bypass Gemini requirement

**Error: "OpenAI API key is required but not provided"**
- Ensure `OPENAI_API_KEY` is set in `.env` file
- Alternative: Use `--model gemini-3.0-flash` to bypass OpenAI requirement

**Error: "Could not detect provider from model name: [model]"**
- Check model name format (must start with `gemini-`, `o*-mini`, `gpt-`, or `claude-`)
- See supported models in "Model Override" section above

**Using only one API provider:**
```bash
# If you only have Anthropic API key
python -m src.cli review --input resume.qmd --model claude-sonnet-4-5-20250929

# If you only have Gemini API key
python -m src.cli review --input resume.qmd --model gemini-3.0-flash

# If you only have OpenAI API key
python -m src.cli review --input resume.qmd --model o3-mini
```

### Performance Issues

**Review taking longer than 3 minutes:**
- Check network connectivity to API providers
- Verify API rate limits haven't been exceeded
- Use `--verbose` to see which agent is slow
- Consider using `--model gemini-3.0-flash` for faster execution

**High API costs:**
- Hybrid mode targets <$0.55 per review
- Use `--dry-run` to preview without API costs
- Set higher `--threshold` (e.g., 9.0) to reduce revision iterations
- Check verbose output for token usage by agent

### Revision Errors

**"Fuzzy replacement failed" errors:**
- This should not occur with the new full-rewrite architecture
- If it does, please file a bug report with the resume content

**YAML frontmatter corrupted:**
- Full-rewrite architecture preserves YAML automatically
- If corruption occurs, check for manual edits to revision logic

### Model-Specific Issues

**Gemini 3.0 Flash returning empty responses:**
- Rare issue with very long resumes (>8000 tokens)
- Try `--model claude-sonnet-4-5-20250929` as fallback
- Check Gemini API status at [status.cloud.google.com](https://status.cloud.google.com)

**OpenAI o3-mini rate limits:**
- OpenAI has strict rate limits for o-series models
- Wait a few minutes and retry
- Alternative: Use `--model gemini-3.0-flash` temporarily

**Claude Sonnet 4.5 timeout:**
- Anthropic has generous rate limits, but large resumes may timeout
- Retry with smaller resume sections
- Check Anthropic API status at [status.anthropic.com](https://status.anthropic.com)

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
