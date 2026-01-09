# Quickstart Guide: Quarto Validation Auto-Retry Loop

**Feature**: Automatic retry loop for Quarto validation failures
**Branch**: 009-quarto-retry-loop
**Audience**: Developers implementing this feature

## What This Feature Does

When the resume review workflow generates a QMD file with Quarto syntax errors, the system:

1. Detects the error via Quarto validation
2. Parses the error into structured feedback
3. Re-invokes the revisor to apply corrections
4. Retries validation up to 3 times (configurable)
5. Logs all attempts for debugging
6. Exits gracefully or continues based on strict mode

This eliminates manual intervention for common syntax errors (standalone `#`, YAML errors, unclosed code blocks, etc.).

## High-Level Architecture

```
ReviewWorkflow._handle_node_persistence()
  └─> After revisor node completes:
      └─> _validate_and_retry()
          ├─> QuartoValidator.validate() → FAIL
          ├─> QuartoValidator.create_validation_feedback()
          ├─> _invoke_revisor_for_retry(validation_feedback)
          ├─> QuartoValidator.validate() → SUCCESS/FAIL
          ├─> RetryLogger.log_attempt()
          └─> [Repeat up to max_retries times]
```

## Key Components

### 1. Data Models (NEW)

**File**: `packages/resume-review/src/models/validation.py`

```python
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path

class ValidationResult(BaseModel):
    """Outcome of a Quarto validation attempt."""
    is_valid: bool
    error_message: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)
    attempt_number: int

class RetryAttempt(BaseModel):
    """Record of a retry iteration."""
    attempt_number: int
    timestamp: datetime = Field(default_factory=datetime.now)
    error_detected: str
    correction_applied: str
    validation_result: ValidationResult
    qmd_snapshot_path: Path | None = None
```

### 2. QuartoValidator Service (MODIFIED)

**File**: `packages/resume-review/src/services/quarto_validator.py`

**New Method**:
```python
def create_validation_feedback(self, error_message: str) -> Feedback:
    """Parse Quarto error and generate structured feedback."""
    issues = []

    # Pattern matching for common errors
    if "invalid heading" in error_message.lower() or "unexpected #" in error_message.lower():
        issues.append(Issue(
            description="単独の # 記号が検出されました",
            severity=Severity.CRITICAL,
            action_type=ActionType.REMOVE,
            location=None
        ))
    # ... more patterns (YAML, code blocks, tables, etc.)

    return Feedback(
        agent_name="quarto_validator",
        score=3.0,  # Low score triggers revision
        strengths=[],
        issues=issues,
        suggestions=["Quarto構文エラーを修正してください"]
    )
```

### 3. RetryLogger Service (NEW)

**File**: `packages/resume-review/src/services/retry_logger.py`

```python
class RetryLogger:
    """Manage retry log files."""

    def __init__(self, session_dir: Path, iteration: int):
        self.session_dir = session_dir
        self.iteration = iteration
        self.log_path = session_dir / f"iter{iteration}_validation_retry.md"

    def log_initial_validation(self, result: ValidationResult) -> None:
        """Log initial validation result."""
        # Write markdown header and initial section

    def log_retry_attempt(self, retry: RetryAttempt) -> None:
        """Log a retry attempt."""
        # Append retry section to markdown file

    def finalize_log(self, success: bool, total_retries: int, final_file: Path) -> None:
        """Write summary section."""
        # Append summary and close log
```

### 4. Workflow Integration (MODIFIED)

**File**: `packages/resume-review/src/workflow/runner.py`

**Modified Method**:
```python
def _handle_node_persistence(self, node_name: str, node_state: dict,
                              accumulated_state: dict) -> None:
    # ... existing persistence logic ...

    if node_name == "revisor":
        # NEW: Validation retry loop
        await self._validate_and_retry(accumulated_state)
```

**New Method**:
```python
async def _validate_and_retry(self, state: dict) -> None:
    """Execute validation retry loop."""
    max_retries = state["max_validation_retries"]
    retry_count = 0

    validator = QuartoValidator()
    logger = RetryLogger(self.session_dir, state["current_iteration"])

    while retry_count < max_retries:
        # Validate current QMD content
        is_valid, error_msg = validator.validate(state["revised_content"])

        if is_valid:
            logger.log_initial_validation(ValidationResult(is_valid=True, ...))
            logger.finalize_log(success=True, total_retries=retry_count, ...)
            return  # Success!

        # Generate validation feedback
        feedback = validator.create_validation_feedback(error_msg)

        # Re-invoke revisor
        revised_content = await self._invoke_revisor_for_retry(state, feedback)
        state["revised_content"] = revised_content

        # Save retry artifact
        retry_path = self._save_retry_artifact(revised_content, state["current_iteration"], retry_count + 1)

        # Log attempt
        retry_attempt = RetryAttempt(
            attempt_number=retry_count + 1,
            error_detected=error_msg,
            correction_applied=f"Applied {len(feedback.issues)} fixes",
            validation_result=ValidationResult(is_valid=is_valid, ...),
            qmd_snapshot_path=retry_path
        )
        logger.log_retry_attempt(retry_attempt)

        retry_count += 1

    # Max retries exhausted
    logger.finalize_log(success=False, total_retries=retry_count, ...)
    if state["strict_validation"]:
        raise ValidationError("Validation failed after max retries")
    else:
        logger.warning("Validation failed, continuing anyway")
```

## Implementation Checklist

### Phase 1: Data Models
- [ ] Create `models/validation.py` with ValidationResult and RetryAttempt
- [ ] Add validators for ValidationResult (error_message required when is_valid=False)
- [ ] Add validators for RetryAttempt (attempt_number > 0)
- [ ] Write unit tests for validation models

### Phase 2: QuartoValidator Extension
- [ ] Add `create_validation_feedback()` method to QuartoValidator
- [ ] Implement error pattern matching (standalone #, YAML, code blocks, tables)
- [ ] Add fallback for unparseable errors
- [ ] Write unit tests for each error pattern
- [ ] Test that Feedback objects are valid (agent_name, score, issues)

### Phase 3: RetryLogger Service
- [ ] Create `services/retry_logger.py` with RetryLogger class
- [ ] Implement `log_initial_validation()` with markdown formatting
- [ ] Implement `log_retry_attempt()` with markdown formatting
- [ ] Implement `finalize_log()` with summary section
- [ ] Write unit tests for log file creation and formatting
- [ ] Test error handling (permission errors, disk full)

### Phase 4: Workflow Integration
- [ ] Add validation retry state fields to ReviewState (workflow/state.py)
- [ ] Add `max_validation_retries` and `strict_validation` to ReviewSession
- [ ] Modify `_handle_node_persistence()` to call `_validate_and_retry()`
- [ ] Implement `_validate_and_retry()` with retry loop logic
- [ ] Implement `_invoke_revisor_for_retry()` to re-call revisor node
- [ ] Implement `_save_retry_artifact()` for QMD snapshots
- [ ] Add retry count reset when incrementing iteration

### Phase 5: Configuration
- [ ] Add `DEFAULT_MAX_VALIDATION_RETRIES` to config/settings.py
- [ ] Add `DEFAULT_STRICT_VALIDATION` to config/settings.py
- [ ] Add `--max-validation-retries` CLI option to cli.py
- [ ] Add `--strict-validation` CLI option to cli.py
- [ ] Pass options through to ReviewSession initialization

### Phase 6: Integration Tests
- [ ] Test successful validation (no retries needed)
- [ ] Test validation fails, retry succeeds
- [ ] Test max retries exhausted with strict mode (exits)
- [ ] Test max retries exhausted with non-strict mode (continues)
- [ ] Test retry artifacts are saved correctly
- [ ] Test retry log file is generated with all sections
- [ ] Test validation feedback is applied by revisor
- [ ] Test retry count resets between iterations
- [ ] Test custom max_retries configuration

### Phase 7: Documentation
- [ ] Update CLAUDE.md with retry commands
- [ ] Add retry log example to docs/
- [ ] Update README with --max-validation-retries and --strict-validation options

## Testing the Feature

### Manual Test with Intentional Error

```bash
# 1. Introduce a validation error (edit resume-ja.qmd)
echo -e "\n#\n" >> resume/resume-ja.qmd  # Add standalone # marker

# 2. Run review with retry enabled (default)
pnpm review

# 3. Check retry log
cat output/session_<timestamp>/iter1_validation_retry.md

# 4. Verify retry QMD files exist
ls output/session_<timestamp>/iter1_retry*.qmd

# 5. Test strict mode
pnpm review --strict-validation
# Should exit with error if validation still fails
```

### Unit Test Examples

```python
# tests/unit/test_quarto_validator.py
def test_create_validation_feedback_standalone_marker():
    validator = QuartoValidator()
    error = "ERROR: Invalid markdown: Unexpected '#' at line 34"
    feedback = validator.create_validation_feedback(error)

    assert feedback.agent_name == "quarto_validator"
    assert feedback.score == 3.0
    assert len(feedback.issues) == 1
    assert feedback.issues[0].severity == Severity.CRITICAL
    assert feedback.issues[0].action_type == ActionType.REMOVE

# tests/integration/test_retry_workflow.py
@pytest.mark.asyncio
async def test_validation_fails_retry_succeeds(mock_quarto, tmp_path):
    # Mock Quarto to fail once, then succeed
    mock_quarto.side_effect = [
        (False, "Invalid heading"),
        (True, None)
    ]

    workflow = ReviewWorkflow(api_key="test")
    session = ReviewSession(max_validation_retries=3, ...)
    result = workflow.run_review(session)

    assert result.status == SessionStatus.COMPLETED
    assert (tmp_path / "iter1_validation_retry.md").exists()
    assert (tmp_path / "iter1_retry1.qmd").exists()
```

## Common Pitfalls

### 1. Forgetting to Reset Retry Count

**Problem**: Retry count accumulates across iterations

**Solution**: Reset `state["validation_retry_count"] = 0` when incrementing `current_iteration`

### 2. Mixing Validation and Agent Feedback

**Problem**: ValidationFeedback contaminates normal feedback history

**Solution**: Use `agent_name="quarto_validator"` to distinguish, and only temporarily add to `current_feedback`

### 3. Infinite Loop on Same Error

**Problem**: Revisor doesn't fix error, retry loops infinitely

**Solution**: Enforce `max_retries` limit - always terminate after N attempts regardless of error

### 4. Not Handling Quarto Timeout

**Problem**: Quarto hangs for >30 seconds

**Solution**: Existing QuartoValidator has 30s timeout - count timeout as validation failure

## Performance Considerations

- **Validation overhead**: ~10-25 seconds per retry (Quarto render + LLM call)
- **Max retries default**: 3 attempts = ~30-75 seconds total
- **File I/O**: Negligible (<100ms for retry artifacts and logs)
- **Total impact**: Within SC-005 constraint (<30 seconds per failure is optimistic, but 3 retries at ~75s is acceptable for rare failures)

## Next Steps After Implementation

1. Run `/speckit.tasks` to generate detailed task breakdown
2. Implement in priority order: Models → Services → Workflow → Config → Tests
3. Test with real resume review workflow
4. Monitor retry success rate (should be >90% within 3 retries per SC-001)
5. Adjust error patterns if needed based on real-world Quarto errors

## Key Files Reference

| File | Purpose | Type |
|------|---------|------|
| `models/validation.py` | ValidationResult, RetryAttempt models | NEW |
| `services/quarto_validator.py` | Error parsing, ValidationFeedback generation | MODIFIED |
| `services/retry_logger.py` | Retry log file management | NEW |
| `workflow/runner.py` | Retry loop integration | MODIFIED |
| `workflow/state.py` | Retry state fields | MODIFIED |
| `config/settings.py` | Retry configuration defaults | MODIFIED |
| `cli.py` | CLI options for retry config | MODIFIED |
| `tests/unit/test_quarto_validator.py` | Error parsing tests | MODIFIED |
| `tests/unit/test_validation_models.py` | Model validation tests | NEW |
| `tests/unit/test_retry_logger.py` | Logger tests | NEW |
| `tests/integration/test_retry_workflow.py` | End-to-end retry tests | NEW |

## Questions?

Refer to:
- [spec.md](spec.md) for requirements and success criteria
- [research.md](research.md) for technical decisions and rationale
- [data-model.md](data-model.md) for entity details
- [contracts/](contracts/) for service interfaces
