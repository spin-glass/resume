# Service Contract: QuartoValidator

**Service**: `QuartoValidator`
**Module**: `packages/resume-review/src/services/quarto_validator.py`
**Purpose**: Validate QMD content and generate structured feedback from Quarto errors

## Public Methods

### `validate(qmd_content: str) -> tuple[bool, Optional[str]]`

**Description**: Validate QMD content by attempting to render it with Quarto (EXISTING METHOD - no changes)

**Parameters**:
- `qmd_content` (str): The QMD file content to validate

**Returns**:
- `tuple[bool, Optional[str]]`:
  - `[0]`: `True` if validation passed, `False` if failed
  - `[1]`: Error message from Quarto if failed, `None` if passed

**Behavior**:
- Creates temporary QMD file with `qmd_content`
- Runs `quarto render <file> --to html --quiet`
- Captures stderr and stdout
- Returns success/failure with error details

**Exceptions**:
- Does not raise exceptions - returns `(True, None)` if Quarto not installed
- Logs errors but doesn't fail the workflow

**Example**:
```python
validator = QuartoValidator()
is_valid, error = validator.validate("---\ntitle: Resume\n---\n# Valid content")
# Returns: (True, None)

is_valid, error = validator.validate("# Standalone marker\n#")
# Returns: (False, "ERROR: Invalid markdown: Unexpected '#' at line 2")
```

---

### `create_validation_feedback(error_message: str) -> Feedback` (NEW)

**Description**: Parse Quarto error message and generate structured Feedback object for revisor

**Parameters**:
- `error_message` (str): Error message from `validate()` method

**Returns**:
- `Feedback`: Structured feedback with Issues parsed from error message

**Behavior**:
- Checks `error_message` against known error patterns (see Error Patterns below)
- Creates Issue objects with appropriate severity, action_type, and description
- Returns Feedback with:
  - `agent_name="quarto_validator"`
  - `score=3.0` (low score to trigger revision)
  - `strengths=[]`
  - `issues=[parsed Issues]`
  - `suggestions=["Quarto構文エラーを修正してください"]`

**Error Patterns**:

| Pattern Check | Issue Generated |
|---------------|-----------------|
| `"invalid heading" in error_msg.lower()` or `"unexpected #" in error_msg.lower()` | `Issue(description="単独の # 記号が検出されました", severity=CRITICAL, action_type=REMOVE, location=None)` |
| `"yaml" in error_msg.lower()` or `"frontmatter" in error_msg.lower()` | `Issue(description="YAMLフロントマターに構文エラー", severity=CRITICAL, action_type=RESTRUCTURE, location="## YAML Header")` |
| `"code block" in error_msg.lower()` or `"```" in error_msg` | `Issue(description="コードブロックが正しく閉じられていません", severity=HIGH, action_type=RESTRUCTURE, location=None)` |
| `"table" in error_msg.lower()` or `"column" in error_msg.lower()` | `Issue(description="Markdownテーブルの列数が不一致", severity=HIGH, action_type=REMOVE, location=None)` |
| No pattern match | `Issue(description=f"Quarto検証エラー: {error_msg}", severity=HIGH, action_type=RESTRUCTURE, location=None)` |

**Exceptions**:
- Does not raise exceptions
- Always returns valid Feedback (at least one Issue with raw error if no pattern matches)

**Example**:
```python
validator = QuartoValidator()
error = "ERROR: Invalid markdown: Unexpected '#' at line 34"
feedback = validator.create_validation_feedback(error)

# Returns Feedback with:
# - agent_name="quarto_validator"
# - score=3.0
# - issues=[Issue(description="単独の # 記号が検出されました", severity=CRITICAL, action_type=REMOVE)]
# - suggestions=["Quarto構文エラーを修正してください"]
```

---

## Internal Methods (Not part of public contract)

### `_parse_error_pattern(error_message: str) -> Optional[Issue]`

**Purpose**: Helper to match error message against known patterns

**Not exposed publicly** - implementation detail

---

## Dependencies

**Imports**:
- `subprocess` - Run Quarto CLI
- `tempfile` - Create temporary QMD files
- `pathlib.Path` - File path handling
- `typing.Optional` - Type hints
- `models.feedback.Feedback, Issue` - Return types
- `models.ActionType, Severity` - Issue construction

**External Tools**:
- Quarto CLI (must be in PATH)

---

## Testing Contract

### Unit Tests Required

**File**: `tests/unit/test_quarto_validator.py`

**Test Cases**:

1. `test_validate_valid_qmd()` - Returns `(True, None)` for valid content
2. `test_validate_invalid_qmd()` - Returns `(False, error_msg)` for syntax errors
3. `test_validate_quarto_not_installed()` - Returns `(True, None)` when Quarto missing
4. `test_create_validation_feedback_standalone_marker()` - Parses "#" error correctly
5. `test_create_validation_feedback_yaml_error()` - Parses YAML error correctly
6. `test_create_validation_feedback_code_block()` - Parses code block error correctly
7. `test_create_validation_feedback_table_error()` - Parses table error correctly
8. `test_create_validation_feedback_unknown_error()` - Handles unparseable errors
9. `test_create_validation_feedback_multiple_patterns()` - Generates multiple Issues if applicable

**Mocking Requirements**:
- Mock `subprocess.run()` to simulate Quarto output
- Don't require actual Quarto installation for tests

---

## Integration Points

**Called By**:
- `ReviewWorkflow._validate_and_retry()` - Calls `validate()` and `create_validation_feedback()`

**Calls**:
- Quarto CLI via subprocess
- No other services

**State Dependencies**:
- Stateless service - can be instantiated once and reused
- No workflow state required

---

## Performance Contract

**Constraints** (from Technical Context):
- `validate()` must complete within 30 seconds (existing timeout)
- `create_validation_feedback()` must complete within 100ms (pattern matching is fast)

**Expected Behavior**:
- Validation typically completes in 5-15 seconds for small QMD files
- Error parsing is synchronous and immediate (<1ms)

---

## Backward Compatibility

**Existing Method**:
- `validate(qmd_content: str) -> tuple[bool, Optional[str]]` - NO CHANGES to signature or behavior

**New Method**:
- `create_validation_feedback(error_message: str) -> Feedback` - Additive, doesn't break existing code

**Migration**: None required - existing code continues to work
