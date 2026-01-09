# Research: Quarto Validation Auto-Retry Loop

**Phase**: 0 (Outline & Research)
**Date**: 2026-01-09
**Branch**: 009-quarto-retry-loop

## Research Questions

### Q1: How to integrate retry loop into existing LangGraph workflow?

**Decision**: Inject retry logic in `_handle_node_persistence()` method after revisor node execution

**Rationale**:
- The existing workflow already has a hook point in `runner.py:_handle_node_persistence()` that executes after each node
- This method currently handles iteration persistence and Quarto validation (from feature #7)
- Adding retry logic here maintains separation of concerns - the workflow graph remains unchanged
- Revisor node can be re-invoked without modifying the LangGraph StateGraph structure

**Alternatives considered**:
1. Create a new "validation" node in the StateGraph
   - **Rejected**: Would require modifying the graph structure and routing logic, increasing complexity
   - Would need to handle state transitions and conditional edges
2. Add retry logic inside the revisor node itself
   - **Rejected**: Violates single responsibility principle - revisor should only apply revisions, not validate
   - Would couple validation concerns with revision logic
3. Use LangGraph's built-in retry mechanism
   - **Rejected**: LangGraph retries are for handling transient failures (API errors), not semantic validation failures

**Implementation approach**:
- After revisor node completes, check if validation is enabled
- Run QuartoValidator on the revised QMD content
- If validation fails, create ValidationFeedback and re-invoke revisor
- Track retry count in state to enforce max_retries limit
- Save retry artifacts after each attempt

---

### Q2: How to parse Quarto error messages into structured feedback?

**Decision**: Pattern-based error message parsing with fallback for unparseable errors

**Rationale**:
- Quarto error messages follow predictable patterns for common syntax errors
- Pattern matching allows targeted feedback generation (e.g., "standalone # detected" → specific Issue)
- Fallback to generic feedback ensures graceful handling of cryptic/unknown errors
- From docs/future-specs.md #8, common patterns include: invalid headers, YAML errors, unclosed code blocks, invalid tables

**Alternatives considered**:
1. Use Quarto's JSON output format for errors
   - **Rejected**: Quarto doesn't provide structured error output in `--quiet` mode
   - Would require parsing stderr which is unstructured text
2. Build a full Quarto AST parser
   - **Rejected**: Overly complex for the scope - we only need error detection, not full syntax tree
   - Quarto already does this internally
3. Use regex to extract line numbers and error types
   - **Partially accepted**: Regex is suitable for pattern matching but we'll use string matching for simplicity

**Implementation approach**:
- Define error patterns as constants in `quarto_validator.py`:
  - `invalid heading`, `unexpected #` → Standalone marker issue
  - `yaml`, `frontmatter` → YAML syntax issue
  - `code block`, ` ``` ` → Unclosed code block
  - `table` → Invalid table formatting
- Create `_parse_quarto_error()` method that checks error message against patterns
- Generate corresponding Issue objects with appropriate severity (CRITICAL for syntax errors)
- If no pattern matches, create generic Issue with the raw error message

**Error pattern mapping** (from future-specs.md #8, line 2983):

| Error Pattern | Quarto Message Contains | Issue Description | ActionType |
|---------------|-------------------------|-------------------|------------|
| Standalone `#` | "invalid heading", "unexpected #" | 単独の # 記号が検出されました | REMOVE |
| YAML error | "yaml", "frontmatter" | YAMLフロントマターに構文エラー | RESTRUCTURE |
| Unclosed code block | "code block", "```" | コードブロックが正しく閉じられていません | RESTRUCTURE |
| Invalid table | "table", "column" | Markdownテーブルの列数が不一致 | REMOVE or RESTRUCTURE |
| Excessive blank lines | N/A (handled by existing Fix 5) | N/A | N/A |

---

### Q3: How to prevent infinite retry loops?

**Decision**: Enforce strict max_retries limit with state tracking and exit conditions

**Rationale**:
- FR-015 requires preventing infinite loops
- Edge case: revisor might introduce new errors while fixing previous ones
- Need deterministic termination to satisfy SC-005 (30 second overhead limit)

**Alternatives considered**:
1. Track error message hashes to detect identical failures
   - **Rejected**: Same error message doesn't guarantee identical issue - line numbers might differ
   - Adds complexity without solving the core problem
2. Timeout-based termination
   - **Rejected**: Doesn't prevent wasted retry attempts - could fail fast instead of timing out
   - Timeout should be per-attempt, not total retries
3. Allow unlimited retries with user intervention
   - **Rejected**: Violates automation principle - defeats purpose of auto-retry

**Implementation approach**:
- Add `validation_retry_count` to ReviewState
- Initialize to 0 at start of iteration
- Increment after each validation failure
- Check `retry_count >= max_validation_retries` before retrying
- If limit exceeded:
  - If `strict_validation=True`: Raise exception and exit workflow
  - If `strict_validation=False`: Log warning and continue to next iteration
- Reset retry count to 0 when moving to next iteration

**Termination conditions**:
1. Validation succeeds → reset counter, proceed to next iteration
2. Max retries exhausted + strict mode → exit with error
3. Max retries exhausted + non-strict mode → log warning, proceed

---

### Q4: How to structure retry logs for debugging?

**Decision**: Markdown-formatted log file per iteration with timestamped entries

**Rationale**:
- Consistent with existing feedback logging (uses markdown)
- Human-readable for debugging
- Structured enough for programmatic parsing if needed later
- Supports SC-004 (logs provide sufficient debugging detail)

**Alternatives considered**:
1. JSON-formatted logs
   - **Rejected**: Less human-readable, existing system uses markdown
   - Would require separate viewer/parser for users
2. Append to single log file for entire session
   - **Rejected**: Harder to correlate with specific iterations
   - Large sessions would produce unwieldy log files
3. Structured logging to stdout only
   - **Rejected**: Logs would be lost after workflow completes
   - Users need persistent records for debugging

**Implementation approach**:
- Create `retry_logger.py` service with `RetryLogger` class
- Generate file: `{session_dir}/iter{N}_validation_retry.md`
- Log format (from future-specs.md #8, line 3029):

```markdown
# Iteration {N} - Validation Retry Log

## Initial Validation (Failed)
- Timestamp: {ISO datetime}
- Error: {Quarto error message}
- Action: Creating fix feedback

## Retry 1
- Timestamp: {ISO datetime}
- Fix Applied: {Issue descriptions from feedback}
- Validation Result: Failed/Success
- Error: {Quarto error message if failed}
- Action: {Next action or completion}

[... up to max_retries entries ...]
```

- Append entry after each retry attempt
- Include final summary (success/failure, total retries)

---

### Q5: How to configure retry behavior (CLI + settings)?

**Decision**: Add CLI options that override default settings from config file

**Rationale**:
- Supports FR-011 (CLI + settings configuration)
- Follows existing pattern in cli.py (--dry-run, --max-iterations, etc.)
- CLI options take precedence for per-run customization
- Settings provide sensible defaults

**Alternatives considered**:
1. Configuration file only (no CLI options)
   - **Rejected**: Less flexible for one-off runs with different retry behavior
   - Users would need to edit config for experiments
2. Environment variables
   - **Rejected**: CLI options are more discoverable and explicit
   - Existing system doesn't use env vars for workflow config
3. Interactive prompts
   - **Rejected**: Breaks automation and CI/CD workflows

**Implementation approach**:
- Update `config/settings.py`:
  ```python
  DEFAULT_MAX_VALIDATION_RETRIES = 3
  DEFAULT_STRICT_VALIDATION = False
  DEFAULT_VALIDATION_TIMEOUT = 30  # seconds (already exists)
  ```
- Update `cli.py` with Click options:
  ```python
  @click.option("--max-validation-retries", type=int, default=None,
                help="Max validation retry attempts (default: 3)")
  @click.option("--strict-validation", is_flag=True, default=False,
                help="Exit on validation failure after retries")
  ```
- Pass options to ReviewSession via ReviewWorkflow constructor
- Add fields to ReviewSession model:
  - `max_validation_retries: int`
  - `strict_validation: bool`

---

## Best Practices Research

### Python Async/Await Patterns in LangGraph

**Finding**: LangGraph workflows use async/await for node execution

**Application**:
- Validation retry logic must be async-compatible
- Use `async def` for new validation methods in runner.py
- QuartoValidator.validate() is currently sync - keep it that way (subprocess.run is blocking)
- Wrap sync validation calls in async context using `asyncio.run_in_executor()` if needed
  - **Decision**: Not needed - validation is fast (<30s), blocking is acceptable within async context

**Source**: Existing code in runner.py:_run_workflow_async() uses `async for` over workflow stream

---

### Pydantic Model Design for Validation Entities

**Finding**: Existing models use Pydantic BaseModel with validators

**Application**:
- New ValidationResult model should follow existing pattern in models/feedback.py
- Use Pydantic validators for:
  - `retry_count >= 0`
  - `timestamp` auto-generation
  - `error_message` not empty when `is_valid=False`
- Use `Field()` for defaults and documentation

**Pattern to follow** (from feedback.py):
```python
class ValidationResult(BaseModel):
    is_valid: bool
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("error_message")
    @classmethod
    def validate_error_message(cls, v: Optional[str], info) -> Optional[str]:
        is_valid = info.data.get("is_valid", True)
        if not is_valid and not v:
            raise ValueError("error_message required when is_valid=False")
        return v
```

---

### File I/O Best Practices for Retry Artifacts

**Finding**: Existing persistence.py uses atomic writes and proper error handling

**Application**:
- Save retry artifacts with atomic writes (write to temp, then rename)
- Use `Path.write_text()` with explicit encoding="utf-8"
- Handle `PermissionError` and `OSError` gracefully
- Create parent directories with `Path.mkdir(parents=True, exist_ok=True)`

**Pattern to follow** (from persistence.py):
```python
def save_retry_attempt(qmd_content: str, retry_path: Path) -> None:
    """Save retry QMD with atomic write."""
    retry_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = retry_path.with_suffix(".tmp")
    temp_path.write_text(qmd_content, encoding="utf-8")
    temp_path.rename(retry_path)
```

---

## Technology Decisions Summary

| Decision Area | Choice | Rationale |
|--------------|--------|-----------|
| Retry integration point | `_handle_node_persistence()` in runner.py | Existing hook, no graph modifications needed |
| Error parsing strategy | Pattern-based string matching | Quarto errors are predictable, no JSON API |
| Infinite loop prevention | max_retries counter + strict_validation flag | Deterministic termination, configurable behavior |
| Retry log format | Markdown per-iteration files | Consistent with existing logs, human-readable |
| Configuration approach | CLI options + settings defaults | Flexible per-run, sensible defaults |
| Async handling | Keep validation sync, run in async context | Validation is fast enough, simpler code |
| Model design | Pydantic BaseModel with validators | Consistent with existing codebase |
| File I/O | Atomic writes with error handling | Follows existing persistence patterns |

---

## Open Questions (None)

All technical unknowns from spec and Technical Context have been resolved through research.
