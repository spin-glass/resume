# Quickstart: Design Auto-Fix

**Feature**: Automated Design Modifications for Resume Review
**Target Users**: Developers implementing the design auto-fix feature
**Prerequisites**: Familiarity with existing resume-review workflow

---

## Overview

This quickstart guide helps developers understand and implement the design auto-fix feature in minimal time. It covers the essential components, their interactions, and common development tasks.

---

## 5-Minute Conceptual Overview

### What It Does

**Input**: Design feedback from UX/Visual agents (e.g., "spacing too cramped", "headings lack hierarchy")

**Output**:
1. **CSS File**: Generated CSS targeting specific design issues
2. **Preview Screenshots**: Before/after comparison (optional)
3. **Section Reordering**: Optimized QMD section arrangement (optional)
4. **Theme Recommendation**: Suggested Quarto theme (advisory)

### How It Works

```
Design Review Node (existing)
    ↓ produces design_feedback
    ↓
Design Applier Node (NEW)
    ├─→ CSSGeneratorAgent: feedback → CSS rules
    ├─→ SectionReorderService: analyze section priority
    ├─→ ThemeRecommenderService: match patterns → theme
    └─→ If --auto-design: write files (with backups)
        If --design-preview: generate screenshots only
```

### Key Architectural Decisions

1. **LLM-Powered CSS Generation**: Translates natural language design feedback to CSS rules
2. **Validation Before Application**: CSS must pass cssutils validation
3. **Atomic Operations**: All file modifications use backup + atomic write
4. **Preview-First Workflow**: Users can review changes before applying
5. **Non-Breaking Integration**: Feature is opt-in via CLI flags

---

## Essential Files to Know

### Core Implementation (Must Understand)

| File | Purpose | Complexity |
|------|---------|------------|
| `src/agents/css_generator.py` | LLM agent that generates CSS from feedback | Medium |
| `src/services/css_service.py` | File operations for CSS (write, backup, validate) | Low |
| `src/workflow/nodes/design_applier.py` | Orchestrates all design modifications | Medium |
| `src/models/design.py` | Data models (CSSModification, SectionReorder, etc.) | Low |
| `src/cli.py` | CLI extensions (--auto-design, --design-preview flags) | Low |

### Supporting Services (Reference as Needed)

| File | Purpose |
|------|---------|
| `src/services/section_reorder.py` | QMD section manipulation with content preservation |
| `src/services/theme_recommender.py` | Heuristic-based theme recommendations |
| `src/workflow/state.py` | ReviewState extensions for design fields |

---

## Quick Start Development Path

### Phase 1: Data Models (1-2 hours)

**Goal**: Define all design-related entities

**File**: `src/models/design.py`

**What to Implement**:
```python
# 1. Enum for design issue types
class DesignIssueType(str, Enum):
    SPACING = "spacing"
    TYPOGRAPHY = "typography"
    # ...

# 2. CSS modification model
class CSSModification(BaseModel):
    css_content: str
    target_file: Path
    changes: list[str]
    # ...

# 3. Other models: SectionReorder, ThemeRecommendation, DesignPreview
```

**Reference**: [data-model.md](./data-model.md)

**Test**: Create instances, verify validation rules work

---

### Phase 2: CSS Service (2-3 hours)

**Goal**: Handle CSS file operations safely

**File**: `src/services/css_service.py`

**What to Implement**:
```python
class CSSService:
    def write_with_backup(
        self,
        css_content: str,
        target_file: Path
    ) -> Path:
        """Write CSS with automatic backup."""
        # 1. Create backup if file exists
        # 2. Write to temp file
        # 3. Validate CSS
        # 4. Atomic rename
        # 5. Return backup path

    def validate_css(self, css_content: str) -> tuple[bool, list[str]]:
        """Validate CSS using cssutils."""
        # 1. Parse CSS
        # 2. Check for syntax errors
        # 3. Check forbidden @media print properties
        # 4. Return (passed, errors)
```

**Reference**: [research.md](./research.md) - Backup and Rollback Strategy

**Test**: Write CSS, verify backup created, test validation

---

### Phase 3: CSS Generator Agent (3-4 hours)

**Goal**: LLM agent that generates CSS from feedback

**File**: `src/agents/css_generator.py`

**What to Implement**:
```python
class CSSGeneratorAgent(BaseAgent):
    def get_system_prompt(self, target_role: str) -> str:
        """Return CSS generation prompt with constraints."""
        # See prompt template in research.md

    async def generate_css(
        self,
        design_feedback: list[Feedback],
        current_css: str = ""
    ) -> CSSModification:
        """Generate CSS from feedback."""
        # 1. Parse feedback, classify issues
        # 2. Build prompt
        # 3. Call LLM
        # 4. Extract CSS from response
        # 5. Validate
        # 6. Return CSSModification
```

**Reference**: [css-generator-agent.md](./contracts/css-generator-agent.md)

**Test**: Mock feedback, verify CSS generated, check validation

---

### Phase 4: Design Applier Node (2-3 hours)

**Goal**: Orchestrate all design modifications

**File**: `src/workflow/nodes/design_applier.py`

**What to Implement**:
```python
async def design_applier_node(state: ReviewState) -> dict[str, Any]:
    """Apply design modifications."""
    # 1. Check if design feedback exists
    # 2. Generate CSS (call CSSGeneratorAgent)
    # 3. Analyze section order (if UX feedback)
    # 4. Recommend theme (if systematic issues)
    # 5. If preview mode: generate screenshots
    # 6. If auto-design mode: apply modifications
    # 7. Return state updates
```

**Reference**: [design-nodes.md](./contracts/design-nodes.md)

**Test**: Mock state, verify orchestration logic, check error handling

---

### Phase 5: CLI Integration (1-2 hours)

**Goal**: Add CLI flags and validation

**File**: `src/cli.py`

**What to Implement**:
```python
@click.option("--auto-design", is_flag=True, ...)
@click.option("--design-preview", is_flag=True, ...)
@click.option("--css-output", type=click.Path(...), ...)
def review(..., auto_design, design_preview, css_output):
    # 1. Validate mutual exclusivity
    # 2. Add flags to initial_state
    # 3. Display design output after workflow
```

**Reference**: [cli-extensions.md](./contracts/cli-extensions.md)

**Test**: Run CLI with flags, verify behavior, check output formatting

---

### Phase 6: State Integration (1 hour)

**Goal**: Extend ReviewState with design fields

**File**: `src/workflow/state.py`

**What to Implement**:
```python
class ReviewState(TypedDict, total=False):
    # ... existing fields ...

    # Design flags
    auto_design_enabled: bool
    design_preview_enabled: bool
    css_output_path: Optional[str]

    # Design outputs
    css_modification: Optional[CSSModification]
    section_reorder: Optional[SectionReorder]
    # ...
```

**Reference**: [data-model.md](./data-model.md) - ReviewState Extensions

---

### Phase 7: Graph Integration (1 hour)

**Goal**: Add design applier node to workflow graph

**File**: `src/workflow/graph.py`

**What to Implement**:
```python
# Add node
workflow.add_node("design_applier", design_applier_node)

# Add conditional edge after design_review
workflow.add_conditional_edges(
    "design_review",
    should_run_design_applier,
    {
        "design_applier": "design_applier",
        "skip_design": "portfolio"
    }
)

# Continue after design_applier
workflow.add_edge("design_applier", "portfolio")
```

**Reference**: [design-nodes.md](./contracts/design-nodes.md) - Conditional Execution

---

### Phase 8: Testing (3-4 hours)

**Goal**: Comprehensive test coverage

**Files**:
- `tests/unit/agents/test_css_generator.py`
- `tests/unit/services/test_css_service.py`
- `tests/integration/test_design_workflow.py`

**What to Test**:
1. Unit: Each component in isolation
2. Integration: End-to-end workflow with --auto-design
3. Integration: Preview mode with screenshots
4. Error handling: Validation failures, rollbacks

**Reference**: Contract files for test case lists

---

## Common Development Tasks

### Task: Add New Design Issue Type

**Steps**:
1. Add enum value to `DesignIssueType` in `src/models/design.py`
2. Update CSS generator prompt to handle new issue type
3. Add classification logic in `_classify_issue()` helper
4. Update theme recommendation knowledge base if relevant

**Example**:
```python
# 1. Add to DesignIssueType
class DesignIssueType(str, Enum):
    # ... existing ...
    ALIGNMENT = "alignment"  # NEW

# 2. Update CSS prompt
SYSTEM_PROMPT = """
...
Focus on: {focus_areas}  # Now includes 'alignment'
"""

# 3. Classification
def _classify_issue(description: str) -> DesignIssueType:
    if any(word in description.lower() for word in ["align", "center", "justify"]):
        return DesignIssueType.ALIGNMENT
    # ...
```

---

### Task: Customize CSS Generation Prompt

**File**: `src/config/prompts.py`

**Steps**:
1. Locate `CSS_GENERATOR_SYSTEM_PROMPT`
2. Modify constraints or examples
3. Test with various feedback inputs

**Tip**: Use few-shot examples for specific CSS patterns you want

---

### Task: Add New Validation Rule

**File**: `src/services/css_service.py`

**Steps**:
1. Add check in `validate_css()` method
2. Append to `errors` list if violation found
3. Update contract documentation

**Example**:
```python
# Forbid !important usage
if '!important' in css_content:
    errors.append("!important is discouraged - use specificity instead")
```

---

### Task: Debug CSS Generation

**Common Issues**:

1. **Empty CSS Generated**:
   - Check design_feedback is not empty
   - Verify LLM response contains CSS code block
   - Check extraction regex in `generate_css()`

2. **Validation Failure**:
   - Run cssutils manually: `cssutils.parseString(css_content)`
   - Check for typos in CSS syntax
   - Verify custom properties defined in `:root`

3. **CSS Not Applied**:
   - Check `validation_passed` is True
   - Verify `auto_design_enabled` flag is set
   - Check file write permissions

**Debug Commands**:
```python
# In CSS generator agent
logger.debug(f"Generated CSS:\n{css_content}")
logger.debug(f"Validation: passed={passed}, errors={errors}")

# In design applier node
logger.debug(f"State flags: auto={auto_design}, preview={preview}")
logger.debug(f"CSS mod: {css_mod}")
```

---

## Testing Strategies

### Unit Testing

**Mock LLM Responses**:
```python
# In test_css_generator.py
@pytest.fixture
def mock_llm_client():
    client = Mock(spec=BaseLLMClient)
    client.generate = AsyncMock(return_value=LLMResponse(
        content="""
/* Generated CSS */
h2 {
  font-size: 1.4rem;
}
        """,
        model="test-model",
        input_tokens=100,
        output_tokens=50
    ))
    return client

async def test_generate_css_success(mock_llm_client):
    agent = CSSGeneratorAgent(llm_client=mock_llm_client)
    feedback = [Feedback(...)]
    css_mod = await agent.generate_css(feedback)
    assert css_mod.validation_passed
```

### Integration Testing

**End-to-End Workflow**:
```python
# In test_design_workflow.py
async def test_auto_design_workflow():
    # Setup
    state = {
        "resume": Resume.from_file("test_resume.qmd"),
        "auto_design_enabled": True,
        "design_feedback": [test_feedback],
        # ... other required state
    }

    # Execute
    workflow = build_review_workflow()
    result = await workflow.ainvoke(state)

    # Assert
    assert result["design_changes_applied"]
    assert Path("styles/resume-custom.css").exists()
    assert len(result["design_backup_paths"]) > 0
```

---

## Troubleshooting

### Issue: CSS File Not Created

**Diagnosis**:
1. Check `auto_design_enabled` is True
2. Verify CSS validation passed
3. Check file permissions
4. Look for errors in logs

**Fix**:
```bash
# Enable verbose logging
resume-review review --input resume.qmd --auto-design --verbose

# Check permissions
ls -l styles/
```

---

### Issue: Preview Screenshots Empty

**Diagnosis**:
1. Check `--screenshot-url` is provided
2. Verify URL is accessible
3. Check Playwright is installed

**Fix**:
```bash
# Test URL manually
curl http://localhost:3000/ja

# Reinstall Playwright
playwright install chromium
```

---

### Issue: Section Reorder Loses Content

**Diagnosis**:
1. Check content hash before/after
2. Verify python-frontmatter parsing
3. Look for YAML frontmatter corruption

**Fix**: This should never happen due to validation. If it does:
```python
# In section_reorder.py, verify hash check
assert content_hash_after == content_hash_before, "Content changed!"
```

---

## Performance Optimization

### CSS Generation Speed

**Target**: <5 seconds

**Optimization**:
- Use smaller/faster LLM model for CSS generation (Gemini Flash)
- Cache LLM responses for identical feedback
- Parallelize validation (if multiple CSS variants)

**Monitoring**:
```python
import time

start = time.time()
css_mod = await css_agent.generate_css(feedback)
logger.info(f"CSS generation took {time.time() - start:.2f}s")
```

---

### Preview Generation Speed

**Target**: <10 seconds

**Optimization**:
- Reuse browser instance (don't restart Playwright)
- Use lower resolution screenshots (1280x720 vs 1920x1080)
- Skip diff generation if changes minimal

---

## Dependencies

### Python Packages (Add to pyproject.toml)

```toml
[project.dependencies]
cssutils = ">=2.0.0,<3.0.0"  # CSS validation
# (existing dependencies remain)
```

### Node Packages (Add to package.json)

```json
{
  "devDependencies": {
    "pixelmatch": "^5.3.0",  # Screenshot diffing
    "pngjs": "^7.0.0"        # PNG handling
  }
}
```

---

## Next Steps After Quickstart

1. **Read Full Contracts**: Understand complete interface specifications
2. **Review Research**: Deep dive into technical decisions
3. **Run Existing Tests**: Familiarize yourself with test patterns
4. **Start with Phase 1**: Begin implementation with data models

---

## Getting Help

**Documentation**:
- [plan.md](./plan.md) - Full implementation plan
- [research.md](./research.md) - Technical research and decisions
- [data-model.md](./data-model.md) - Complete entity specifications
- [contracts/](./contracts/) - Interface contracts for all components

**Code References**:
- Existing agents: `src/agents/visual_designer.py`, `src/agents/ux_designer.py`
- Existing workflow: `src/workflow/nodes/supervisor.py`
- Existing services: `src/services/revision.py` (for file operation patterns)

**Testing Examples**:
- Unit tests: `tests/unit/agents/test_visual_designer.py`
- Integration tests: `tests/integration/test_workflow.py`

---

**Quickstart Version**: 1.0
**Last Updated**: 2026-01-09
**Estimated Implementation Time**: 15-20 hours for complete feature
