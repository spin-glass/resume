# Integration Contract: Workflow Retry Loop

**Component**: `ReviewWorkflow` (workflow/runner.py)
**Purpose**: Integration point for validation retry loop in LangGraph workflow
**Type**: Method extension (not a service)

## Modified Methods

### `_handle_node_persistence(node_name: str, node_state: dict, accumulated_state: dict) -> None`

**Description**: EXISTING method extended with validation retry logic

**Current Behavior** (before this feature):
- Saves feedback and iteration artifacts after specific nodes
- Runs Quarto validation after revisor node
- Logs validation errors to file but doesn't retry

**New Behavior** (after this feature):
- After revisor node: Run validation retry loop
- If validation fails: Create ValidationFeedback, re-invoke revisor, retry up to max_retries
- If validation succeeds: Continue to router node
- If max retries exhausted: Exit (strict mode) or continue with warning (non-strict mode)

**Integration Point**:
```python
def _handle_node_persistence(self, node_name: str, node_state: dict,
                              accumulated_state: dict) -> None:
    # ... existing persistence logic ...

    if node_name == "revisor":
        # NEW: Validation retry loop
        await self._validate_and_retry(accumulated_state)
```

---

## New Methods (Private)

### `async _validate_and_retry(state: dict) -> None`

**Description**: Execute validation retry loop after revisor node

**Parameters**:
- `state` (dict): Current accumulated workflow state (ReviewState)

**Behavior**:

1. **Initialize retry tracking**:
   - Reset `state["validation_retry_count"] = 0`
   - Reset `state["current_retry_attempts"] = []`
   - Create RetryLogger for current iteration

2. **Initial validation**:
   - Get revised QMD content from `state["revised_content"]`
   - Call `QuartoValidator.validate(qmd_content)`
   - Log initial result with `RetryLogger.log_initial_validation()`
   - If valid: Return (no retries needed)

3. **Retry loop** (while retry_count < max_retries):
   - Create ValidationFeedback from error message
   - Add feedback to `state["current_feedback"]`
   - Re-invoke revisor node with validation feedback
   - Validate revised content
   - Increment `state["validation_retry_count"]`
   - Save retry artifact to `{session_dir}/iter{N}_retry{count}.qmd`
   - Create RetryAttempt record
   - Log attempt with `RetryLogger.log_retry_attempt()`
   - If valid: Break loop (success)
   - If retry_count >= max_retries: Break loop (exhausted)

4. **Finalize**:
   - Call `RetryLogger.finalize_log()`
   - If strict_validation and validation failed: Raise exception
   - If non-strict and validation failed: Log warning, continue

**State Mutations**:
- `state["validation_retry_count"]` - Incremented on each retry
- `state["current_retry_attempts"]` - Appends RetryAttempt records
- `state["revised_content"]` - Updated by revisor re-invocation
- `state["current_feedback"]` - Temporarily set to ValidationFeedback

**Exceptions**:
- Raises `ValidationError` if strict_validation=True and retries exhausted
- Otherwise logs warnings and continues

**Example Flow**:

```
Initial: validate(qmd) → FAIL (standalone #)
Retry 1: create_feedback → revisor → validate(qmd) → FAIL (different error)
Retry 2: create_feedback → revisor → validate(qmd) → SUCCESS
Result: state["validation_retry_count"] = 2, workflow continues
```

---

### `async _invoke_revisor_for_retry(state: dict, validation_feedback: Feedback) -> str`

**Description**: Re-invoke revisor node with validation feedback

**Parameters**:
- `state` (dict): Current workflow state
- `validation_feedback` (Feedback): Feedback generated from validation error

**Returns**:
- `str`: Revised QMD content from revisor

**Behavior**:
- Temporarily replace `state["current_feedback"]` with `[validation_feedback]`
- Call revisor node directly (not via graph routing)
- Extract revised content from revisor output
- Restore original `state["current_feedback"]`

**Rationale**:
- Revisor node already knows how to apply feedback
- Reusing revisor logic avoids code duplication
- Isolation prevents validation feedback from mixing with agent feedback

**Implementation Note**:
- Import revisor node function from workflow/graph.py
- Call it directly as `revised_output = await revisor_node(state)`

---

### `_save_retry_artifact(qmd_content: str, iteration: int, retry_count: int) -> Path`

**Description**: Save intermediate QMD file from retry attempt

**Parameters**:
- `qmd_content` (str): QMD content to save
- `iteration` (int): Current iteration number
- `retry_count` (int): Current retry attempt number

**Returns**:
- `Path`: Path to saved retry file

**Behavior**:
- Generate filename: `iter{iteration}_retry{retry_count}.qmd`
- Save to session directory with atomic write
- Return absolute path

**File Persistence**:
- Files are NOT cleaned up automatically
- Preserved for debugging purposes
- Users can manually delete session directories

---

## State Schema Extensions

**New Fields in ReviewState**:

```python
# workflow/state.py additions
class ReviewState(TypedDict):
    # ... existing fields ...

    # Validation retry fields
    validation_retry_count: int          # Current retry count (reset per iteration)
    max_validation_retries: int          # Max retries allowed (from config)
    strict_validation: bool              # Exit on failure (from config)
    current_retry_attempts: list[dict]   # Retry history (serialized RetryAttempts)
```

**State Initialization** (in `_create_initial_state`):

```python
def _create_initial_state(self, session: ReviewSession) -> ReviewState:
    return {
        # ... existing initialization ...
        "validation_retry_count": 0,
        "max_validation_retries": session.max_validation_retries,
        "strict_validation": session.strict_validation,
        "current_retry_attempts": [],
    }
```

**State Reset** (between iterations):

```python
# After incrementing current_iteration:
state["validation_retry_count"] = 0
state["current_retry_attempts"] = []
```

---

## Configuration Extensions

**CLI Options** (cli.py):

```python
@click.option(
    "--max-validation-retries",
    type=int,
    default=None,
    help="Maximum validation retry attempts per iteration (default: 3)"
)
@click.option(
    "--strict-validation",
    is_flag=True,
    default=False,
    help="Exit workflow if validation fails after all retries"
)
```

**Settings Defaults** (config/settings.py):

```python
# Validation Configuration
DEFAULT_MAX_VALIDATION_RETRIES = 3
DEFAULT_STRICT_VALIDATION = False
```

**ReviewSession Extensions** (models/session.py):

```python
class ReviewSession(BaseModel):
    # ... existing fields ...
    max_validation_retries: int = DEFAULT_MAX_VALIDATION_RETRIES
    strict_validation: bool = DEFAULT_STRICT_VALIDATION
```

---

## Testing Contract

### Integration Tests Required

**File**: `tests/integration/test_retry_workflow.py`

**Test Cases**:

1. `test_validation_succeeds_no_retry()` - Initial validation passes, no retries
2. `test_validation_fails_retry_succeeds()` - Retry 1 fixes error, validation passes
3. `test_validation_exhausts_retries_strict_mode()` - 3 retries fail, workflow exits
4. `test_validation_exhausts_retries_non_strict()` - 3 retries fail, workflow continues
5. `test_retry_artifacts_saved()` - Retry QMD files are created
6. `test_retry_log_generated()` - Retry log file contains all attempts
7. `test_validation_feedback_applied()` - Revisor receives and applies validation feedback
8. `test_multiple_iterations_reset_retry_count()` - Retry count resets between iterations
9. `test_max_retries_configurable()` - Respects custom max_retries setting
10. `test_revisor_introduces_new_error()` - Handles case where retry creates new validation error

**Test Setup**:
- Use fixtures with intentionally invalid QMD content
- Mock Quarto validator to control pass/fail results
- Verify state mutations and file artifacts

---

## Error Handling

**Validation Timeout**:
- If Quarto validation times out (>30s): Count as validation failure
- Create generic ValidationFeedback with timeout error
- Retry as normal (revisor may reduce content size)

**Revisor Failure During Retry**:
- If revisor node raises exception: Log error, count as failed retry
- Continue retry loop (may succeed on next attempt)
- If all retries fail due to revisor errors: Follow strict_validation behavior

**Infinite Loop Prevention**:
- Hard limit: `max_validation_retries` (default: 3)
- No same-error detection (could miss subtle differences)
- Relies on retry limit for deterministic termination

---

## Performance Expectations

**Timing Budget** (from SC-005):
- Validation retry adds <30 seconds overhead per failure
- Per-attempt breakdown:
  - Quarto validation: ~5-15 seconds
  - Error parsing: <1ms
  - Revisor re-invocation: ~5-10 seconds (LLM call)
  - File I/O (retry artifact + log): <100ms
- Total per retry: ~10-25 seconds
- 3 retries: ~30-75 seconds (within acceptable range)

**Optimization Opportunities**:
- Quarto validation timeout is already 30s (prevents runaway)
- Revisor uses same LLM call performance as normal iterations
- File I/O is negligible

---

## Backward Compatibility

**Existing Workflow**:
- If `max_validation_retries=0`: Retry logic is skipped entirely (backward compatible)
- Default behavior (3 retries, non-strict) enhances existing workflow without breaking changes
- Existing validation error logging (from #7) still works alongside retry

**Migration**:
- No migration needed for existing code
- New CLI options are optional (defaults preserve old behavior with retry enhancement)
