# CLI Interface Contract

**Branch**: `001-resume-review-agents` | **Date**: 2026-01-09 | **Related**: [spec.md](../spec.md), [plan.md](../plan.md)

## Overview

This document defines the command-line interface contract for the resume review tool. The CLI is implemented using Python's `argparse` or `click` and follows POSIX conventions.

---

## Command Structure

```bash
python -m src.cli review [OPTIONS]
```

---

## Arguments & Options

### Required Arguments

None - all options have sensible defaults.

### Options

| Option | Short | Type | Default | Description | Requirement |
|--------|-------|------|---------|-------------|-------------|
| `--input` | `-i` | Path | `../public/assets/resume-ja.qmd` | Path to QMD resume file (relative to `agents/` directory) | FR-001 |
| `--output` | `-o` | Path | Same as input | Path for revised resume output | FR-009 |
| `--dry-run` | `-n` | Flag | False | Preview changes without modifying files | FR-010 |
| `--verbose` | `-v` | Flag | False | Enable detailed progress output | FR-012 |
| `--target-role` | `-r` | String | `"LLM/Multi-Agent Engineer"` | Target position for skill matching | FR-006 |
| `--threshold` | `-t` | Float | `8.0` | Minimum score to pass (1.0-10.0) | FR-005 |
| `--max-iterations` | `-m` | Int | `3` | Maximum revision cycles | FR-005 |
| `--screenshot-url` | `-s` | URL | None | URL for visual design review | FR-013, FR-014 |
| `--api-key` | | String | `$ANTHROPIC_API_KEY` | Anthropic API key (env var default) | N/A |
| `--help` | `-h` | Flag | N/A | Show help message and exit | N/A |

---

## Input Validation

### File Path Validation (--input)

```python
def validate_input_file(path: str) -> Path:
    """
    Validates the input file path.

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file extension is not .qmd
        PermissionError: If file is not readable
    """
    file_path = Path(path).resolve()

    if not file_path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    if file_path.suffix != ".qmd":
        raise ValueError(f"Input must be a .qmd file, got: {file_path.suffix}")

    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"Cannot read file: {file_path}")

    return file_path
```

**Requirements**: FR-001

---

### Score Threshold Validation (--threshold)

```python
def validate_threshold(value: float) -> float:
    """
    Validates score threshold is in valid range.

    Raises:
        ValueError: If threshold not in [1.0, 10.0]
    """
    if not 1.0 <= value <= 10.0:
        raise ValueError(f"Threshold must be between 1.0 and 10.0, got: {value}")
    return value
```

**Requirements**: FR-005

---

### Max Iterations Validation (--max-iterations)

```python
def validate_max_iterations(value: int) -> int:
    """
    Validates max iterations is positive.

    Raises:
        ValueError: If iterations < 1
    """
    if value < 1:
        raise ValueError(f"Max iterations must be >= 1, got: {value}")
    return value
```

**Requirements**: FR-005

---

### Screenshot URL Validation (--screenshot-url)

```python
def validate_screenshot_url(url: str | None) -> str | None:
    """
    Validates screenshot URL format.

    Raises:
        ValueError: If URL is malformed
    """
    if url is None:
        return None

    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid URL format: {url}")

    return url
```

**Requirements**: FR-013, FR-014

---

## Output Behavior

### Standard Output (stdout)

**Normal Mode** (not verbose):
```
Resume Review Starting...
✓ Content review completed (Score: 8.2/10.0)
✓ Portfolio analysis completed (2 suggestions)
✓ Design review skipped (no screenshot URL provided)

Summary:
- Integrated Score: 8.2/10.0 (threshold: 8.0)
- Iterations Used: 2/3
- Changes Applied: 5
- Portfolio Projects Suggested: 2

Review completed successfully. Resume saved to: public/assets/resume-ja.qmd
```

**Verbose Mode** (`--verbose`):
```
[2026-01-09 10:30:00] Resume Review Starting...
[2026-01-09 10:30:01] Loading resume from: /Users/user/resume/public/assets/resume-ja.qmd
[2026-01-09 10:30:01] Resume loaded (1234 chars, valid YAML frontmatter)
[2026-01-09 10:30:01] Initializing review session (session_id: abc123)
[2026-01-09 10:30:02] Starting content review iteration 1/3

[2026-01-09 10:30:05] Recruiter feedback received (score: 7.5)
  - Strengths: Strong LLM project experience
  - Issues: Missing LangGraph experience (high priority)

[2026-01-09 10:30:08] Technical Writer feedback received (score: 8.0)
  - Strengths: Clear technical depth
  - Issues: RAG metrics not quantified (medium priority)

[2026-01-09 10:30:11] Copywriter feedback received (score: 7.2)
  - Strengths: Good professional tone
  - Issues: Missing tagline for impact (high priority)

[2026-01-09 10:30:12] Integrated score: 7.6/10.0 (below threshold 8.0)
[2026-01-09 10:30:12] Applying revisions...
[2026-01-09 10:30:13] ✓ Added tagline to summary section
[2026-01-09 10:30:13] ✓ Quantified RAG improvement metrics
[2026-01-09 10:30:13] ✓ Restructured skills section for emphasis

[2026-01-09 10:30:13] Starting content review iteration 2/3

[2026-01-09 10:30:16] Recruiter feedback received (score: 8.5)
[2026-01-09 10:30:19] Technical Writer feedback received (score: 8.2)
[2026-01-09 10:30:22] Copywriter feedback received (score: 8.0)

[2026-01-09 10:30:23] Integrated score: 8.2/10.0 (meets threshold 8.0)
[2026-01-09 10:30:23] Content review completed

[2026-01-09 10:30:23] Starting portfolio gap analysis...
[2026-01-09 10:30:25] Identified skill gap: LangGraph (not in work experience)
[2026-01-09 10:30:25] Suggested portfolio project: langgraph-multi-agent
[2026-01-09 10:30:26] Identified skill gap: RAG Evaluation (not in work experience)
[2026-01-09 10:30:26] Suggested portfolio project: rag-evaluation-toolkit
[2026-01-09 10:30:26] Portfolio analysis completed (2 suggestions)

[2026-01-09 10:30:26] Skipping design review (no screenshot URL provided)

[2026-01-09 10:30:26] Finalizing review session...
[2026-01-09 10:30:27] Saving revised resume to: public/assets/resume-ja.qmd

Summary:
- Integrated Score: 8.2/10.0 (threshold: 8.0)
- Iterations Used: 2/3
- Changes Applied:
  1. Added tagline to summary section
  2. Quantified RAG improvement metrics
  3. Restructured skills section for emphasis
  4. Added portfolio section with 2 projects
  5. Updated metadata timestamp
- Portfolio Projects Suggested:
  1. langgraph-multi-agent (LangGraph, Multi-agent systems, Claude API)
     - GitHub: https://github.com/spin-glass/langgraph-multi-agent
     - Demo: https://langgraph-multi-agent.vercel.app
  2. rag-evaluation-toolkit (RAG, Evaluation, LangChain)
     - GitHub: https://github.com/spin-glass/rag-evaluation-toolkit
     - Demo: https://rag-evaluation-toolkit.vercel.app

Review completed successfully.
```

**Dry-Run Mode** (`--dry-run`):
```
Resume Review Starting (DRY RUN - no changes will be saved)...
✓ Content review completed (Score: 8.2/10.0)
✓ Portfolio analysis completed (2 suggestions)

Preview of Proposed Changes:
[... same summary as normal mode ...]

DRY RUN: Original file unchanged. Run without --dry-run to apply changes.
```

**Requirements**: FR-012 (verbose), FR-010 (dry-run), FR-011 (summary)

---

### Standard Error (stderr)

**Error Output**:
```
Error: Resume file not found: /path/to/resume.qmd

Error: YAML frontmatter is invalid:
  Line 5: Unexpected token '}'

Error: Network connectivity lost during review. Original file preserved.

Warning: Screenshot URL provided but development server not responding.
  Design review phase will be skipped.

Error: Maximum iterations (3) reached without meeting threshold (8.0/10.0).
  Final score: 7.8/10.0. Best effort revision saved.
```

**Requirements**: Edge cases from spec

---

## Exit Codes

| Code | Meaning | Example Scenario |
|------|---------|------------------|
| 0 | Success | Review completed, score >= threshold |
| 1 | File error | Input file not found, invalid QMD, YAML parse error |
| 2 | Validation error | Invalid CLI arguments (threshold out of range, etc.) |
| 3 | Network error | Cannot connect to Anthropic API, retries exhausted |
| 4 | Threshold not met | Max iterations reached, score < threshold |
| 5 | Screenshot error | Development server not running (design review skipped, continues) |
| 6 | Partial failure | Some phases succeeded, others failed (see details below) |

**Note**: Exit code 5 is a warning, not a failure. The tool continues without design review.

---

## Error Recovery & Partial Success Handling

### Partial Success Scenarios

**Scenario 1: Content Review Succeeds, Portfolio Analysis Fails**

```
✓ Content review completed (Score: 8.2/10.0)
✗ Portfolio analysis failed: API rate limit exceeded

Summary:
- Content changes applied successfully
- Resume saved with improved content
- Portfolio suggestions unavailable (run again later)

Exit code: 6 (partial success)
```

**Behavior**:
- Content revisions are saved
- Portfolio section is not added
- User can re-run with `--skip-content` flag (future: resume from checkpoint)

---

**Scenario 2: Multiple Agent Failures**

```
✓ Recruiter feedback received (score: 8.0)
✗ Technical Writer agent failed: API timeout
✗ Copywriter agent failed: API timeout
⚠ Falling back to partial scoring with available feedback

Integrated Score: 8.0/10.0 (based on 1/3 agents)
Warning: Score may be incomplete. Consider re-running for full evaluation.

Exit code: 6 (partial success)
```

**Behavior**:
- Calculate score using only successful agents
- Apply weight normalization (redistribute weights of failed agents)
- Flag result as "partial" in output
- Suggest re-run for complete evaluation

---

**Scenario 3: Revision Application Partial Failure**

```
✓ Content review completed (Score: 8.2/10.0)
✓ 4/5 revisions applied successfully:
  1. ✓ Added tagline to summary section
  2. ✓ Quantified RAG improvement metrics
  3. ✗ Failed to add portfolio section: YAML corruption risk detected
  4. ✓ Restructured skills section for emphasis
  5. ✓ Emphasized LangGraph experience

Warning: 1 revision failed. Original file preserved.
Review the failed revision and consider manual edit.

Exit code: 6 (partial success)
```

**Behavior**:
- Abort all revisions if any would corrupt YAML (FR-009 compliance)
- Save partial revisions only if YAML integrity is guaranteed
- Log failed revisions to `~/.resume-review/failed-revisions.log`

---

### Checkpoint & Resume (LangGraph Feature)

**Implementation** (Phase 2 enhancement):

```bash
# Enable checkpoint persistence
python -m src.cli review --checkpoint-dir ./.resume-review/checkpoints

# If review fails mid-execution, resume from last checkpoint
python -m src.cli review --resume-from-checkpoint abc123
```

**Checkpoints saved at**:
- After each agent evaluation completes
- After each revision iteration
- Before file write operations

**Benefits**:
- Resume from failure without re-running expensive LLM calls
- Inspect intermediate states for debugging
- Rollback to previous iteration if needed

**Example**:

```
[2026-01-09 10:30:10] ✓ Checkpoint saved: iteration-1-evaluation (id: abc123)
[2026-01-09 10:30:15] ✓ Checkpoint saved: iteration-1-revision (id: def456)
[2026-01-09 10:30:20] ✗ Network error during iteration 2

To resume: python -m src.cli review --resume-from-checkpoint def456
```

---

### Network Error Recovery

**Strategy**: Exponential backoff with jitter

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def call_agent(agent, resume_content):
    # API call with automatic retry
    pass
```

**Retry Policy**:
- Attempt 1: Immediate
- Attempt 2: Wait 2-4 seconds (exponential + jitter)
- Attempt 3: Wait 4-8 seconds
- After 3 attempts: Raise `NetworkError`, exit code 3

**User Notification**:

```
Attempt 1/3 failed: Connection timeout. Retrying in 2s...
Attempt 2/3 failed: Connection timeout. Retrying in 4s...
Attempt 3/3 failed: Connection timeout.

Error: Network connectivity lost during review.
Original file preserved. Please check your internet connection and try again.

Exit code: 3
```

---

### File Integrity Safeguards

**Pre-Save Validation**:

```python
def validate_before_save(original: str, revised: str) -> None:
    """
    Validate revised content before saving.

    Raises:
        YAMLPreservationError: If YAML frontmatter corrupted
        MarkdownSyntaxError: If markdown syntax invalid
    """
    # 1. Parse YAML from both
    original_yaml = frontmatter.loads(original).metadata
    revised_yaml = frontmatter.loads(revised).metadata

    # 2. Verify all original keys present
    for key in original_yaml:
        if key not in revised_yaml and key != 'last_modified':
            raise YAMLPreservationError(f"YAML key '{key}' was lost")

    # 3. Validate markdown syntax
    # (use markdown parser or Quarto validation)

    # 4. Check file size (should not change drastically)
    size_diff = abs(len(revised) - len(original)) / len(original)
    if size_diff > 0.5:  # 50% size change is suspicious
        logger.warning(f"File size changed by {size_diff:.0%}. Review carefully.")
```

**Backup Strategy**:

```python
def save_with_backup(file_path: Path, new_content: str) -> None:
    """
    Save file with automatic backup.

    Creates .bak file before overwriting original.
    """
    backup_path = file_path.with_suffix(file_path.suffix + '.bak')

    # Create backup
    shutil.copy(file_path, backup_path)

    try:
        # Write new content
        file_path.write_text(new_content, encoding='utf-8')

        logger.info(f"Backup saved: {backup_path}")
    except Exception as e:
        # Restore from backup
        shutil.copy(backup_path, file_path)
        logger.error(f"Save failed. Restored from backup: {e}")
        raise
```

---

### Graceful Degradation

**Priority Levels**:

1. **Critical** (must succeed): Content review, file integrity
2. **High** (important but optional): Portfolio analysis, design review
3. **Low** (nice to have): Verbose logging, screenshot capture

**Degradation Strategy**:

- If **portfolio analysis** fails → continue with content revisions only
- If **design review** fails → skip visual feedback, exit code 5 (warning)
- If **content review** fails → abort entire operation, exit code 3

---

### User-Friendly Error Messages

**Bad**:
```
Error: APIError at line 142 in agents/recruiter.py
```

**Good**:
```
Error: Unable to connect to AI service (Anthropic API).

Possible causes:
- No internet connection
- API key is invalid or expired
- Anthropic service is down

Troubleshooting:
1. Check your internet connection
2. Verify ANTHROPIC_API_KEY environment variable: echo $ANTHROPIC_API_KEY
3. Check Anthropic status: https://status.anthropic.com

Original resume file has not been modified.
```

---

## Implementation Checklist

- [ ] Implement exit codes 0-6
- [ ] Add partial success handling for each phase
- [ ] Implement checkpoint save/resume using LangGraph
- [ ] Add exponential backoff retry logic
- [ ] Implement pre-save validation
- [ ] Add automatic backup before file write
- [ ] Implement graceful degradation for optional features
- [ ] Write user-friendly error messages
- [ ] Log all errors to `~/.resume-review/error.log`
- [ ] Add `--resume-from-checkpoint` CLI option (Phase 2)

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | N/A | API key for Claude access |
| `RESUME_REVIEW_LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARN, ERROR) |
| `RESUME_REVIEW_TIMEOUT` | No | `300` | Timeout in seconds for AI API calls |

**Configuration Method**:

Environment variables should be stored in a `.env` file in the `agents/` directory:

```bash
# agents/.env
ANTHROPIC_API_KEY=sk-ant-...
RESUME_REVIEW_LOG_LEVEL=INFO
RESUME_REVIEW_TIMEOUT=300
```

The CLI tool automatically loads variables from `.env` using `python-dotenv`.

**Loading Priority**:
1. CLI flag (e.g., `--api-key`)
2. Environment variable from `.env` file
3. System environment variable (e.g., `$ANTHROPIC_API_KEY`)
4. Config file (future: `~/.resume-review/config.toml`)

**Security**: Add `.env` to `.gitignore` to prevent committing API keys.

---

## Usage Examples

### Basic Usage

**Note**: Commands assume you're in the `agents/` directory. If running from repository root, use `cd agents` first.

```bash
# Review with defaults (input: ../public/assets/resume-ja.qmd, threshold: 8.0)
python -m src.cli review

# Specify custom input file (absolute or relative path)
python -m src.cli review --input /path/to/my-resume.qmd
python -m src.cli review --input ../custom/resume.qmd

# Dry run to preview changes
python -m src.cli review --dry-run

# Verbose output for debugging
python -m src.cli review --verbose
```

### Advanced Usage

```bash
# Custom threshold and max iterations
python -m src.cli review --threshold 9.0 --max-iterations 5

# Full review with visual design analysis
python -m src.cli review --screenshot-url http://localhost:3000/ja

# Target different role
python -m src.cli review --target-role "Senior Backend Engineer"

# Combined options
python -m src.cli review \
  --input ./resume.qmd \
  --output ./resume-improved.qmd \
  --threshold 8.5 \
  --max-iterations 4 \
  --screenshot-url http://localhost:3000/ja \
  --verbose
```

### Integration with Build Pipeline

```bash
# Review and build in one command (from package.json)
npm run review:build

# Expands to:
# python -m src.cli review --input ../public/assets/resume-ja.qmd
# npm run resume:build
```

---

## Future Extensions

### Config File Support (v2.0)

```toml
# ~/.resume-review/config.toml
[defaults]
threshold = 8.5
max_iterations = 4
target_role = "LLM/Multi-Agent Engineer"

[api]
provider = "anthropic"
model = "claude-sonnet-4.5"
timeout = 300

[output]
verbose = true
log_file = "~/.resume-review/logs/review.log"
```

### Interactive Mode (v2.0)

```bash
# Prompt for approval after each iteration
python -m src.cli review --interactive
```

### Multiple Output Formats (v3.0)

```bash
# Generate PDF diff alongside revised QMD
python -m src.cli review --output-diff pdf
```

---

## Implementation Notes

### Click vs Argparse

**Recommendation**: Use `click` for better UX:
- Automatic help generation
- Type validation
- Better error messages
- Environment variable integration
- Easy testing via `CliRunner`

Example with Click:

```python
import click
from pathlib import Path

@click.command()
@click.option(
    '--input', '-i',
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default='public/assets/resume-ja.qmd',
    help='Path to QMD resume file'
)
@click.option(
    '--dry-run', '-n',
    is_flag=True,
    help='Preview changes without modifying files'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable detailed progress output'
)
@click.option(
    '--threshold', '-t',
    type=click.FloatRange(1.0, 10.0),
    default=8.0,
    help='Minimum score to pass'
)
def review(input, dry_run, verbose, threshold):
    """Review and improve resume content using multi-agent system."""
    # Implementation here
    pass
```

### Testing Strategy

```python
from click.testing import CliRunner

def test_review_dry_run():
    runner = CliRunner()
    result = runner.invoke(review, ['--dry-run', '--input', 'fixtures/sample.qmd'])
    assert result.exit_code == 0
    assert 'DRY RUN' in result.output
```
