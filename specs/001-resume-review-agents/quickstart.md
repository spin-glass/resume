# Quickstart Guide: Resume Review Multi-Agent System

**Branch**: `001-resume-review-agents` | **Date**: 2026-01-09 | **Related**: [spec.md](./spec.md), [plan.md](./plan.md)

## Overview

This guide helps you get the resume review CLI tool running in under 10 minutes. Follow these steps to set up your environment, configure API access, and run your first review.

---

## Prerequisites

### System Requirements

- **Operating System**: macOS or Linux
- **Python**: 3.13.x (downgrade from 3.14.2 if needed - see below)
- **Node.js**: 22.x (already present in repository)
- **Quarto CLI**: For rendering resumes (already installed per constitution)

### API Access

- **Anthropic API Key**: Get one from [console.anthropic.com](https://console.anthropic.com/)
  - Required for Claude Sonnet 4.5 access
  - Free tier includes limited usage; production requires paid plan

---

## Step 1: Python Version Setup

LangGraph currently supports Python 3.10-3.13 (3.14 support coming soon). If you're running Python 3.14.2, downgrade to 3.13.

### Check Current Version

```bash
python3 --version
# Python 3.14.2 (needs downgrade)
```

### Option A: Using pyenv (Recommended)

```bash
# Install pyenv if not already installed
curl https://pyenv.run | bash

# Install Python 3.13
pyenv install 3.13.2

# Set local version for this project
cd /path/to/resume
pyenv local 3.13.2

# Verify
python --version
# Python 3.13.2
```

### Option B: Using conda/mamba

```bash
conda create -n resume-review python=3.13
conda activate resume-review
```

### Option C: System Python

Download Python 3.13 from [python.org](https://www.python.org/downloads/) and install globally (not recommended if you need 3.14 for other projects).

---

## Step 2: Install uv (Modern Python Package Manager)

### Install uv

[uv](https://github.com/astral-sh/uv) is a fast Python package manager written in Rust. It's significantly faster than pip and handles virtual environments automatically.

```bash
# Install uv (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via Homebrew
brew install uv

# Verify installation
uv --version
```

---

## Step 3: Install Dependencies

### Create Virtual Environment and Install Packages

```bash
cd /path/to/resume/agents

# Create venv and install all dependencies in one command
uv sync
```

**What `uv sync` does**:
- Creates `.venv` automatically if it doesn't exist
- Reads dependencies from `pyproject.toml` or `requirements.txt`
- Installs all packages with optimal parallelization
- Much faster than `pip install -r requirements.txt`

**Expected packages** (defined in `pyproject.toml` or `requirements.txt`):
- `langgraph>=1.0.0` - Multi-agent orchestration
- `langchain-anthropic>=0.1.0` - Anthropic SDK integration
- `anthropic>=0.25.0` - Claude API client
- `playwright>=1.40.0` - Screenshot capture
- `pydantic>=2.0.0` - Data validation
- `click>=8.1.0` - CLI framework
- `python-frontmatter>=1.0.0` - QMD YAML parsing
- `python-dotenv>=1.0.0` - Environment variable management
- `pytest>=7.4.0` - Testing
- `pytest-asyncio>=0.21.0` - Async test support
- `tenacity>=8.0.0` - Retry logic

### Install Playwright Browsers

```bash
# Activate the virtual environment
source .venv/bin/activate

# Install Chromium browser
playwright install chromium
```

This downloads the Chromium browser for screenshot capture (FR-014).

### Alternative: Manual Installation (if not using uv)

If you prefer traditional pip:

```bash
cd /path/to/resume
python -m venv agents/.venv
source agents/.venv/bin/activate
cd agents
pip install -r requirements.txt
playwright install chromium
```

---

## Step 3: Configure API Key

### Create .env File

Create a `.env` file in the `agents/` directory to store your API key:

```bash
cd /path/to/resume/agents

# Create .env file
cat > .env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-...
EOF
```

**Security Note**: The `.env` file should be added to `.gitignore` to prevent accidentally committing your API key.

```bash
# Add to .gitignore if not already present
echo ".env" >> .gitignore
```

### Verify API Access

The CLI tool will automatically load environment variables from `.env` using `python-dotenv`:

```bash
python -c "
from dotenv import load_dotenv
load_dotenv()
from anthropic import Anthropic
client = Anthropic()
print('API key configured successfully')
"
```

---

## Step 4: Run Your First Review

### Basic Review (Content Only)

```bash
cd /path/to/resume
python -m src.cli review --input public/assets/resume-ja.qmd
```

**What happens**:
1. Loads your resume QMD file
2. Evaluates content from 3 perspectives (recruiter, technical writer, copywriter)
3. Applies revisions until score >= 8.0 or 3 iterations max
4. Analyzes skill gaps and suggests portfolio projects
5. Saves improved resume back to the same file

**Expected output**:
```
Resume Review Starting...
✓ Content review completed (Score: 8.2/10.0)
✓ Portfolio analysis completed (2 suggestions)

Summary:
- Integrated Score: 8.2/10.0 (threshold: 8.0)
- Iterations Used: 2/3
- Changes Applied: 5
- Portfolio Projects Suggested: 2

Review completed successfully. Resume saved to: public/assets/resume-ja.qmd
```

---

## Step 5: Preview Changes (Dry Run)

Before modifying your actual resume, preview what changes would be made:

```bash
python -m src.cli review --input public/assets/resume-ja.qmd --dry-run
```

**What happens**:
- Full review runs as normal
- Feedback and suggestions are generated
- **Original file remains unchanged**
- Preview output shows proposed changes

**Use case**: Review the suggested changes, then run without `--dry-run` to apply them.

---

## Step 6: Full Review with Visual Design

To include visual design evaluation, start your development server and provide the screenshot URL:

### Start Next.js Dev Server

```bash
# Terminal 1
cd /path/to/resume
npm run dev
# Next.js starts on http://localhost:3000
```

### Run Review with Screenshot

```bash
# Terminal 2
python -m src.cli review \
  --input public/assets/resume-ja.qmd \
  --screenshot-url http://localhost:3000/ja
```

**What happens**:
1. Content review completes as before
2. System captures screenshot of rendered resume at the URL
3. UX Designer agent evaluates information hierarchy
4. Visual Designer agent evaluates visual presentation
5. Final score includes design feedback

**Note**: If dev server is not running, design review is skipped with a warning (not an error).

---

## Step 7: Verbose Mode for Debugging

See detailed progress output with `--verbose`:

```bash
python -m src.cli review \
  --input public/assets/resume-ja.qmd \
  --verbose
```

**Output includes**:
- Timestamp for each step
- Individual agent feedback details
- Score progression across iterations
- Applied revision descriptions
- Portfolio suggestion details

**Use case**: Debugging issues, understanding agent reasoning, or tracking performance.

---

## Common Use Cases

### Use Case 1: Quick Content Improvement

**Goal**: Improve resume content quickly before applying to a position.

```bash
# 1. Preview changes first
python -m src.cli review --dry-run

# 2. Apply changes if satisfied
python -m src.cli review

# 3. Rebuild all formats (PDF, HTML, MDX)
npm run resume:build
```

**Time**: ~5 minutes (SC-001)

---

### Use Case 2: Target Different Role

**Goal**: Tailor resume for a specific position (e.g., "Senior Backend Engineer" instead of default "LLM/Multi-Agent Engineer").

```bash
python -m src.cli review \
  --target-role "Senior Backend Engineer"
```

**What changes**: Agents evaluate skills and experience against Backend Engineer requirements instead of LLM/AI focus.

---

### Use Case 3: Higher Quality Bar

**Goal**: Aim for exceptional quality (score >= 9.0) for a high-stakes application.

```bash
python -m src.cli review \
  --threshold 9.0 \
  --max-iterations 5
```

**What changes**: More iterations allowed, higher bar for completion. May take longer but produces more polished output.

---

### Use Case 4: Complete Review with Design

**Goal**: Full end-to-end review including visual design analysis.

```bash
# Terminal 1: Start dev server
npm run dev

# Terminal 2: Run full review
python -m src.cli review \
  --screenshot-url http://localhost:3000/ja \
  --verbose
```

**Use case**: Before final deployment, ensure both content and visual presentation are optimized.

---

### Use Case 5: Integrated Workflow

**Goal**: Review + build in one command (as configured in package.json).

```bash
npm run review:build
```

**Expands to**:
```bash
cd agents && python -m src.cli review --input ../public/assets/resume-ja.qmd
npm run resume:build
```

**Use case**: Automated workflow for regular resume updates.

---

## Troubleshooting

### Problem: `ModuleNotFoundError: No module named 'langgraph'`

**Solution**: Install dependencies.

```bash
cd agents
source .venv/bin/activate
pip install -r requirements.txt
```

---

### Problem: `API key not configured`

**Solution**: Create `.env` file with your API key.

```bash
# Create .env file in agents/ directory
cd agents
cat > .env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-...
EOF

# Retry review
python -m src.cli review
```

---

### Problem: `Python version 3.14 not supported by LangGraph`

**Solution**: Downgrade to Python 3.13 (see Step 1).

```bash
pyenv install 3.13.2
pyenv local 3.13.2
```

---

### Problem: Screenshot capture fails with "Connection refused"

**Solution**: Start the development server first.

```bash
# Terminal 1
npm run dev

# Terminal 2 (wait for "ready on http://localhost:3000")
python -m src.cli review --screenshot-url http://localhost:3000/ja
```

---

### Problem: `YAML frontmatter is invalid`

**Solution**: Check QMD file for syntax errors in the frontmatter.

```yaml
---
title: Resume
author: Your Name
date: 2026-01-09
# Remove any invalid YAML syntax (unmatched braces, quotes, etc.)
---
```

---

### Problem: Review takes too long (>5 minutes)

**Possible causes**:
1. Network latency to Anthropic API
2. Too many iterations (default: 3)
3. Large resume file

**Solutions**:
```bash
# Reduce max iterations
python -m src.cli review --max-iterations 2

# Lower threshold for faster completion
python -m src.cli review --threshold 7.5
```

---

## Next Steps

Once you're comfortable with basic usage:

1. **Read the spec**: [spec.md](./spec.md) for detailed requirements and user stories
2. **Review contracts**: [contracts/](./contracts/) for API interfaces
3. **Explore data models**: [data-model.md](./data-model.md) for entity definitions
4. **Run tests**: `pytest agents/tests/` to verify implementation
5. **Build portfolio projects**: Follow suggestions from review output

---

## Package.json Integration

The tool is already integrated into package.json scripts:

```json
{
  "scripts": {
    "review": "cd agents && python -m src.cli review --input ../public/assets/resume-ja.qmd",
    "review:dry": "cd agents && python -m src.cli review --input ../public/assets/resume-ja.qmd --dry-run --verbose",
    "review:full": "cd agents && python -m src.cli review --input ../public/assets/resume-ja.qmd --screenshot-url http://localhost:3000/ja --verbose",
    "review:build": "npm run review && npm run resume:build"
  }
}
```

**Use these shortcuts**:

```bash
npm run review          # Basic review
npm run review:dry      # Dry run with verbose output
npm run review:full     # Full review with design (requires dev server)
npm run review:build    # Review + rebuild all formats
```

---

## Development Tips

### Enable Debug Logging

Add debug settings to your `.env` file:

```bash
# agents/.env
ANTHROPIC_API_KEY=sk-ant-...
RESUME_REVIEW_LOG_LEVEL=DEBUG
```

Then run with verbose mode:

```bash
python -m src.cli review --verbose
```

### Test with Sample Resume

```bash
# Use test fixtures instead of your actual resume
python -m src.cli review \
  --input agents/tests/fixtures/sample-resume.qmd \
  --output /tmp/output.qmd
```

### Profile Performance

```bash
time python -m src.cli review
# Should complete in <5 minutes per SC-001
```

---

## Production Considerations

### Cost Management

Anthropic API calls cost money. Here's a detailed breakdown:

#### Token Estimation

**Per Agent Evaluation**:
- Input: Resume content (~1500 tokens) + System prompt (~500 tokens) = **2000 input tokens**
- Output: Feedback JSON (~500 tokens) = **500 output tokens**

**Per Revision**:
- Input: Resume content (~1500 tokens) + Revision instructions (~300 tokens) = **1800 input tokens**
- Output: Revised content section (~400 tokens) = **400 output tokens**

**Design Review** (screenshot analysis):
- Input: Resume screenshot (image, ~800 tokens equivalent) + System prompt (~500 tokens) = **1300 input tokens**
- Output: Visual feedback (~500 tokens) = **500 output tokens**

#### Cost Calculation (Claude Sonnet 4.5 pricing as of Jan 2026)

Assuming **2 iterations** for typical review:

| Phase | Component | Input Tokens | Output Tokens | Cost (Sonnet 4.5) |
|-------|-----------|--------------|---------------|-------------------|
| Content Review Iteration 1 | 3 agents × 2000 in | 6000 | - | $0.18 |
| | 3 agents × 500 out | - | 1500 | $0.023 |
| Revision 1 | 5 changes × 1800 in | 9000 | - | $0.27 |
| | 5 changes × 400 out | - | 2000 | $0.030 |
| Content Review Iteration 2 | 3 agents × 2000 in | 6000 | - | $0.18 |
| | 3 agents × 500 out | - | 1500 | $0.023 |
| Revision 2 | 2 changes × 1800 in | 3600 | - | $0.11 |
| | 2 changes × 400 out | - | 800 | $0.012 |
| Portfolio Analysis | 1 call × 2000 in | 2000 | - | $0.06 |
| | 1 call × 600 out | - | 600 | $0.009 |
| Design Review | 2 agents × 1300 in | 2600 | - | $0.08 |
| | 2 agents × 500 out | - | 1000 | $0.015 |
| **Total** | | **29,200 in** | **7,400 out** | **~$1.00** |

**Pricing assumptions** (verify at [anthropic.com/pricing](https://www.anthropic.com/pricing)):
- Input: $3 per 1M tokens
- Output: $15 per 1M tokens

**Cost range**:
- **Minimum** (1 iteration, no design): ~$0.50
- **Typical** (2 iterations, with design): ~$1.00
- **Maximum** (3 iterations, with design): ~$1.50

#### Cost Reduction Tips

1. **Use Haiku for non-critical agents** (10× cheaper):
   - UX Designer: Structure evaluation doesn't need Sonnet
   - Portfolio Analysis: Simple skill gap identification
   - Estimated savings: ~$0.30 per review

2. **Skip design review during iteration**:
   - Only run visual design on final draft
   - Savings: ~$0.10 per iteration

3. **Lower max iterations for drafts**:
   ```bash
   python -m src.cli review --max-iterations 1  # Quick pass
   ```

4. **Use dry-run for testing**:
   - Preview changes without applying (no revision costs)
   - Re-run only when satisfied with proposed changes

5. **Batch reviews** (future enhancement):
   - Review multiple resumes in single session
   - Amortize setup costs across multiple files

### Rate Limits

Free tier: 50 requests/day. Paid tier: 3000 requests/minute.

For typical usage (1-2 reviews/day), free tier is sufficient.

---

## Summary Checklist

- [ ] Python 3.13 installed and active
- [ ] uv package manager installed
- [ ] Virtual environment created with `uv sync`
- [ ] Dependencies installed via `uv sync`
- [ ] Playwright browsers installed (`playwright install chromium`)
- [ ] `.env` file created in `agents/` directory with `ANTHROPIC_API_KEY`
- [ ] `.env` added to `.gitignore`
- [ ] API access verified
- [ ] First review completed successfully
- [ ] Dry-run mode tested
- [ ] Package.json scripts working

Once this checklist is complete, you're ready to use the resume review system!
