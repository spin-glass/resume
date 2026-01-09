# Service Contract: RetryLogger

**Service**: `RetryLogger`
**Module**: `packages/resume-review/src/services/retry_logger.py` (NEW)
**Purpose**: Manage retry log files for validation attempts

## Public Methods

### `__init__(session_dir: Path, iteration: int)`

**Description**: Initialize retry logger for a specific iteration

**Parameters**:
- `session_dir` (Path): Session directory where logs will be saved
- `iteration` (int): Current iteration number (used in log filename)

**Behavior**:
- Stores session_dir and iteration
- Does NOT create log file yet (lazy creation on first log entry)

**Example**:
```python
logger = RetryLogger(
    session_dir=Path("output/session_20260109_181500"),
    iteration=2
)
```

---

### `log_initial_validation(result: ValidationResult) -> None`

**Description**: Log the initial validation result before retries

**Parameters**:
- `result` (ValidationResult): Result from first validation attempt

**Behavior**:
- Creates log file if it doesn't exist
- Writes "Initial Validation" section with timestamp and error
- Determines next action based on result (retry or success)

**Log Format**:
```markdown
# Iteration {iteration} - Validation Retry Log

## Initial Validation ({PASSED|FAILED})
- Timestamp: {result.timestamp in ISO format}
- Error: {result.error_message or "None"}
- Action: {Creating fix feedback | Proceeding to next iteration}
```

**Exceptions**:
- May raise `OSError` or `PermissionError` if file cannot be written
- Logs warning but doesn't crash workflow

**Example**:
```python
logger.log_initial_validation(ValidationResult(
    is_valid=False,
    error_message="Invalid markdown: Unexpected '#'",
    timestamp=datetime.now(),
    attempt_number=0
))
```

---

### `log_retry_attempt(retry: RetryAttempt) -> None`

**Description**: Log a single retry attempt

**Parameters**:
- `retry` (RetryAttempt): Record of retry attempt with corrections and result

**Behavior**:
- Appends "Retry N" section to existing log file
- Includes fix applied, validation result, error (if failed), next action

**Log Format**:
```markdown
## Retry {retry.attempt_number}
- Timestamp: {retry.timestamp in ISO format}
- Fix Applied: {retry.correction_applied}
- Validation Result: {PASSED|FAILED}
- Error: {retry.validation_result.error_message if failed}
- Action: {Validation passed | Creating fix feedback | Max retries exhausted}
```

**Exceptions**:
- May raise `OSError` or `PermissionError` if file cannot be written
- Logs warning but doesn't crash workflow

**Example**:
```python
logger.log_retry_attempt(RetryAttempt(
    attempt_number=1,
    timestamp=datetime.now(),
    error_detected="Invalid markdown",
    correction_applied="Removed standalone # markers",
    validation_result=ValidationResult(is_valid=True, ...),
    qmd_snapshot_path=Path("iter2_retry1.qmd")
))
```

---

### `finalize_log(success: bool, total_retries: int, final_file: Path) -> None`

**Description**: Write summary section and close log

**Parameters**:
- `success` (bool): Whether validation ultimately succeeded
- `total_retries` (int): Total number of retry attempts made
- `final_file` (Path): Path to final QMD file (successful or last attempt)

**Behavior**:
- Appends "Summary" section with final status
- Flushes and closes log file

**Log Format**:
```markdown
## Summary
- Total Retries: {total_retries}
- Final Status: {SUCCESS ✅ | FAILED ❌}
- Final File: {final_file}
```

**Exceptions**:
- May raise `OSError` or `PermissionError` if file cannot be written
- Logs warning but doesn't crash workflow

**Example**:
```python
logger.finalize_log(
    success=True,
    total_retries=2,
    final_file=Path("resume.qmd")
)
```

---

### `get_log_path() -> Path`

**Description**: Get the path to the retry log file

**Returns**:
- `Path`: Absolute path to log file

**Behavior**:
- Returns `{session_dir}/iter{iteration}_validation_retry.md`
- File may not exist yet if no logs have been written

**Example**:
```python
log_path = logger.get_log_path()
# Returns: Path("output/session_20260109_181500/iter2_validation_retry.md")
```

---

## Internal Methods (Not part of public contract)

### `_ensure_log_file() -> None`

**Purpose**: Create log file and parent directories if they don't exist

**Not exposed publicly** - implementation detail

### `_append_to_log(content: str) -> None`

**Purpose**: Append markdown content to log file

**Not exposed publicly** - implementation detail

---

## Dependencies

**Imports**:
- `pathlib.Path` - File path handling
- `datetime` - Timestamp formatting
- `typing.Optional` - Type hints
- `models.validation.ValidationResult, RetryAttempt` - Parameter types

**External Tools**: None

---

## Testing Contract

### Unit Tests Required

**File**: `tests/unit/test_retry_logger.py`

**Test Cases**:

1. `test_init_creates_logger()` - Logger initializes without creating file
2. `test_log_initial_validation_passed()` - Logs initial success correctly
3. `test_log_initial_validation_failed()` - Logs initial failure correctly
4. `test_log_retry_attempt_success()` - Logs successful retry
5. `test_log_retry_attempt_failure()` - Logs failed retry
6. `test_finalize_log_success()` - Finalizes with success summary
7. `test_finalize_log_failure()` - Finalizes with failure summary
8. `test_get_log_path()` - Returns correct log file path
9. `test_multiple_retries()` - Logs sequence of retries correctly
10. `test_file_permission_error()` - Handles write failures gracefully

**Mocking Requirements**:
- Use `tmp_path` pytest fixture for session directories
- Don't mock file I/O - test real file creation

---

## Integration Points

**Called By**:
- `ReviewWorkflow._validate_and_retry()` - Creates logger and logs all attempts

**Calls**:
- File system (Path.write_text, Path.mkdir)
- No other services

**State Dependencies**:
- Stateful - maintains log file handle across calls
- One instance per iteration

---

## Performance Contract

**Constraints**:
- Log writing should not add more than 100ms per retry attempt
- File I/O is synchronous but fast for small markdown files

**Expected Behavior**:
- Initial log creation: <10ms
- Append retry entry: <5ms
- Finalize log: <5ms

---

## File Format Specification

**File Name Pattern**: `iter{iteration}_validation_retry.md`

**Example**: `iter2_validation_retry.md` for iteration 2

**Markdown Structure**:

```markdown
# Iteration {iteration} - Validation Retry Log

## Initial Validation ({PASSED|FAILED})
- Timestamp: {ISO 8601 datetime}
- Error: {error_message or "None"}
- Action: {next_action}

## Retry 1
- Timestamp: {ISO 8601 datetime}
- Fix Applied: {correction_summary}
- Validation Result: {PASSED|FAILED}
- Error: {error_message or "None"}
- Action: {next_action}

## Retry 2
[... same structure ...]

## Summary
- Total Retries: {count}
- Final Status: {SUCCESS ✅ | FAILED ❌}
- Final File: {relative_path}
```

**Timestamp Format**: ISO 8601 with timezone (e.g., `2026-01-09T18:15:23+09:00`)

---

## Error Handling

**Failure Modes**:
1. Session directory doesn't exist → Create with `mkdir(parents=True, exist_ok=True)`
2. Permission denied → Log warning, return gracefully (don't crash workflow)
3. Disk full → Log error, return gracefully

**Recovery Strategy**:
- Retry logs are supplementary - workflow can continue without them
- Log errors to stderr but don't fail validation retry loop
