# Contract: Design Workflow Nodes

**Module**: `packages/resume-review/src/workflow/nodes/design_applier.py`
**Purpose**: StateGraph nodes for applying design modifications
**Type**: Workflow Node Functions

---

## Overview

This contract defines the StateGraph node functions that coordinate design modification application, including CSS generation, section reordering, theme recommendations, and preview generation.

---

## Node: design_applier_node

**Purpose**: Main orchestration node for design modifications

**Type**: Async function returning state dict

### Signature

```python
async def design_applier_node(state: ReviewState) -> dict[str, Any]:
    """
    Apply design modifications based on feedback and CLI flags.

    Orchestrates:
    - CSS generation (if design issues exist)
    - Section reordering (if UX feedback suggests)
    - Theme recommendation (if systematic issues)
    - Preview generation (if --design-preview enabled)
    - File modification (if --auto-design enabled)

    Args:
        state: Current workflow state

    Returns:
        State updates dict with design modification results
    """
```

### Input Requirements

**From State**:
- `design_feedback: list[Feedback]` - REQUIRED, non-empty
- `auto_design_enabled: bool` - REQUIRED, determines if changes applied
- `design_preview_enabled: bool` - REQUIRED, determines if preview generated
- `resume: Resume` - REQUIRED, for section reordering
- `api_key: str` - REQUIRED for LLM clients
- `gemini_api_key, openai_api_key, anthropic_api_key: str` - Optional API keys
- `override_model: Optional[str]` - Optional model override
- `css_output_path: Optional[str]` - Optional custom CSS path

### Output Guarantees

**Returned Dict Keys**:
- `css_modification: Optional[CSSModification]` - Always present if design issues exist
- `section_reorder: Optional[SectionReorder]` - Present if UX suggests reordering
- `theme_recommendation: Optional[ThemeRecommendation]` - Present if systematic issues
- `design_preview_paths: Optional[DesignPreview]` - Present if preview mode enabled
- `design_changes_applied: bool` - True if files modified, False if preview only
- `design_changes_pending: bool` - True if preview mode (changes not applied)
- `design_changes_list: list[str]` - Human-readable list of modifications
- `design_backup_paths: dict[str, str]` - Mapping of original to backup paths

### Behavior Logic

```python
async def design_applier_node(state: ReviewState) -> dict[str, Any]:
    """Apply design modifications."""
    logger.info("Design Applier: Starting design modification workflow")

    design_feedback = state.get("design_feedback", [])
    if not design_feedback:
        logger.info("Design Applier: No design feedback, skipping")
        return {
            "design_changes_applied": False,
            "design_changes_pending": False,
            "design_changes_list": []
        }

    auto_design = state.get("auto_design_enabled", False)
    preview_mode = state.get("design_preview_enabled", False)
    result = {
        "design_changes_applied": False,
        "design_changes_pending": False,
        "design_changes_list": [],
        "design_backup_paths": {}
    }

    # 1. CSS Generation (always run if feedback exists)
    css_mod = await _generate_css(state, design_feedback)
    if css_mod and css_mod.validation_passed:
        result["css_modification"] = css_mod
        logger.info(f"CSS generated: {css_mod.get_summary()}")

    # 2. Section Reordering (only if UX feedback suggests)
    section_reorder = _analyze_section_order(state, design_feedback)
    if section_reorder and section_reorder.is_changed():
        result["section_reorder"] = section_reorder
        logger.info(f"Section reorder proposed: {len(section_reorder.get_movements())} moves")

    # 3. Theme Recommendation (if systematic issues)
    theme_rec = _recommend_theme(design_feedback)
    if theme_rec:
        result["theme_recommendation"] = theme_rec
        logger.info(f"Theme recommended: {theme_rec.theme_name}")

    # 4. Preview Generation (if preview mode)
    if preview_mode and css_mod:
        preview = await _generate_preview(state, css_mod, section_reorder)
        result["design_preview_paths"] = preview
        result["design_changes_pending"] = True
        logger.info("Preview generated, no files modified")
        return result

    # 5. Apply Modifications (if auto-design mode)
    if auto_design:
        changes_list = []
        backup_paths = {}

        # Apply CSS
        if css_mod and css_mod.validation_passed:
            css_service = CSSService()
            backup = css_service.write_with_backup(
                css_mod.css_content,
                css_mod.target_file
            )
            if backup:
                backup_paths[str(css_mod.target_file)] = str(backup)
            changes_list.append(f"CSS: {css_mod.target_file}")

        # Apply Section Reordering
        if section_reorder and section_reorder.is_changed():
            reorder_service = SectionReorderService()
            qmd_path = state["resume"].file_path
            backup = reorder_service.reorder_with_backup(qmd_path, section_reorder)
            if backup:
                backup_paths[str(qmd_path)] = str(backup)
            changes_list.append("Sections reordered")

        result["design_changes_applied"] = True
        result["design_changes_list"] = changes_list
        result["design_backup_paths"] = backup_paths
        logger.info(f"Design modifications applied: {changes_list}")

    return result
```

### Error Handling

1. **No Design Feedback**: Return early with no modifications
2. **CSS Generation Failure**: Log error, continue with other modifications
3. **CSS Validation Failure**: Don't apply CSS, log validation errors
4. **Section Reorder Failure**: Log error, continue (CSS can still apply)
5. **Preview Generation Failure**: Log error, degrade to text-only output
6. **File Write Failure**: Rollback from backups, raise exception

### Conditional Execution

**When Node Runs**:
```python
def should_run_design_applier(state: ReviewState) -> str:
    """
    Decide if design applier should run.

    Returns:
        "design_applier" if design modifications enabled
        "skip_design" otherwise
    """
    auto_design = state.get("auto_design_enabled", False)
    preview = state.get("design_preview_enabled", False)
    has_feedback = len(state.get("design_feedback", [])) > 0

    if (auto_design or preview) and has_feedback:
        return "design_applier"
    return "skip_design"
```

**Graph Integration**:
```python
# In workflow/graph.py
workflow.add_node("design_applier", design_applier_node)

# After design_review node
workflow.add_conditional_edges(
    "design_review",
    should_run_design_applier,
    {
        "design_applier": "design_applier",
        "skip_design": "portfolio"  # Continue normal flow
    }
)

# After design_applier, continue to portfolio
workflow.add_edge("design_applier", "portfolio")
```

---

## Helper Functions

### _generate_css

**Purpose**: Generate CSS using CSSGeneratorAgent

```python
async def _generate_css(
    state: ReviewState,
    design_feedback: list[Feedback]
) -> Optional[CSSModification]:
    """
    Generate CSS modifications from design feedback.

    Args:
        state: Workflow state
        design_feedback: Design feedback list

    Returns:
        CSSModification or None if generation fails
    """
    try:
        # Create LLM client for CSS generator
        llm_client = LLMClientFactory.create_client(
            agent_name=AgentName.CSS_GENERATOR,
            gemini_api_key=state.get("gemini_api_key"),
            openai_api_key=state.get("openai_api_key"),
            anthropic_api_key=state.get("anthropic_api_key"),
            override_model=state.get("override_model"),
        )

        # Initialize CSS generator agent
        css_agent = CSSGeneratorAgent(llm_client=llm_client)

        # Read current CSS if exists
        css_path = Path(state.get("css_output_path") or "styles/resume-custom.css")
        current_css = ""
        if css_path.exists():
            current_css = css_path.read_text()

        # Generate CSS
        css_mod = await css_agent.generate_css(
            design_feedback=design_feedback,
            current_css=current_css,
            target_role=state.get("target_role", "LLM Engineer")
        )

        return css_mod

    except Exception as e:
        logger.error(f"CSS generation failed: {e}", exc_info=True)
        return None
```

### _analyze_section_order

**Purpose**: Analyze UX feedback for section reordering

```python
def _analyze_section_order(
    state: ReviewState,
    design_feedback: list[Feedback]
) -> Optional[SectionReorder]:
    """
    Analyze UX feedback to determine if section reordering is needed.

    Args:
        state: Workflow state
        design_feedback: Design feedback list

    Returns:
        SectionReorder or None if no reordering needed
    """
    try:
        # Filter for UX feedback only
        ux_feedback = [f for f in design_feedback if f.agent_name == "ux_designer"]
        if not ux_feedback:
            return None

        # Check if any issues suggest section order problems
        order_keywords = ["order", "sequence", "priority", "hierarchy", "placement", "move", "reorder"]
        has_order_issue = any(
            any(keyword in issue.description.lower() for keyword in order_keywords)
            for feedback in ux_feedback
            for issue in feedback.issues
        )

        if not has_order_issue:
            return None

        # Use section reorder service
        reorder_service = SectionReorderService()
        resume = state["resume"]
        section_reorder = reorder_service.analyze_and_recommend(
            resume_content=resume.content,
            ux_feedback=ux_feedback,
            target_role=state.get("target_role", "LLM Engineer")
        )

        return section_reorder

    except Exception as e:
        logger.error(f"Section order analysis failed: {e}", exc_info=True)
        return None
```

### _recommend_theme

**Purpose**: Recommend Quarto theme for systematic issues

```python
def _recommend_theme(
    design_feedback: list[Feedback]
) -> Optional[ThemeRecommendation]:
    """
    Recommend Quarto theme based on design issue patterns.

    Args:
        design_feedback: Design feedback list

    Returns:
        ThemeRecommendation or None if current theme is adequate
    """
    try:
        # Check if issues are systematic (affecting multiple areas)
        issue_counts = Counter(
            issue.issue_type if hasattr(issue, 'issue_type') else _classify_issue(issue.description)
            for feedback in design_feedback
            for issue in feedback.issues
        )

        # Theme recommendation only if 3+ systematic issues
        if len(issue_counts) < 3:
            return None

        # Use theme recommender service
        recommender = ThemeRecommenderService()
        theme_rec = recommender.recommend(
            design_feedback=design_feedback,
            issue_counts=issue_counts
        )

        return theme_rec

    except Exception as e:
        logger.error(f"Theme recommendation failed: {e}", exc_info=True)
        return None
```

### _generate_preview

**Purpose**: Generate before/after preview screenshots

```python
async def _generate_preview(
    state: ReviewState,
    css_mod: Optional[CSSModification],
    section_reorder: Optional[SectionReorder]
) -> Optional[DesignPreview]:
    """
    Generate preview screenshots with before/after comparison.

    Args:
        state: Workflow state
        css_mod: CSS modifications (if any)
        section_reorder: Section reordering (if any)

    Returns:
        DesignPreview or None if preview generation fails
    """
    try:
        screenshot_url = state.get("screenshot_url")
        if not screenshot_url:
            logger.warning("No screenshot URL provided, skipping preview")
            return None

        screenshot_service = ScreenshotService()

        # 1. Capture before screenshot
        before_path = await screenshot_service.capture(
            url=screenshot_url,
            output_path="preview/before.png"
        )

        # 2. Apply modifications temporarily
        temp_css_path = None
        temp_qmd_path = None

        if css_mod:
            temp_css_path = Path("preview/temp-custom.css")
            temp_css_path.write_text(css_mod.css_content)

        if section_reorder:
            # Create temp QMD with reordered sections
            temp_qmd_path = Path("preview/temp-resume.qmd")
            # ... (reorder logic)

        # 3. Capture after screenshot
        after_path = await screenshot_service.capture(
            url=screenshot_url,  # Re-render with temp files
            output_path="preview/after.png"
        )

        # 4. Generate diff
        diff_path = screenshot_service.generate_diff(
            before_path,
            after_path,
            output_path="preview/diff.png"
        )

        # 5. Create composite
        composite_path = screenshot_service.create_composite(
            before_path,
            diff_path,
            after_path,
            output_path="preview/composite.png"
        )

        # 6. Clean up temp files
        if temp_css_path:
            temp_css_path.unlink()
        if temp_qmd_path:
            temp_qmd_path.unlink()

        return DesignPreview(
            before_screenshot=before_path,
            after_screenshot=after_path,
            diff_screenshot=diff_path,
            composite_screenshot=composite_path,
            diff_pixel_count=screenshot_service.last_diff_pixels,
            diff_percentage=screenshot_service.last_diff_percentage,
        )

    except Exception as e:
        logger.error(f"Preview generation failed: {e}", exc_info=True)
        return None
```

---

## State Transitions

### Entry State

```python
{
    "design_feedback": [Feedback(...)],  # From design_review node
    "auto_design_enabled": True,         # From CLI
    "design_preview_enabled": False,
    "resume": Resume(...),
    "api_key": "sk-...",
    # ... other existing state
}
```

### Exit State (Auto-Design)

```python
{
    # ... existing state ...
    "css_modification": CSSModification(...),
    "section_reorder": SectionReorder(...),
    "theme_recommendation": ThemeRecommendation(...),
    "design_changes_applied": True,
    "design_changes_pending": False,
    "design_changes_list": [
        "CSS: styles/resume-custom.css",
        "Sections reordered"
    ],
    "design_backup_paths": {
        "styles/resume-custom.css": "backups/resume-custom_20260109_143022.css",
        "resume/resume-ja.qmd": "backups/resume-ja_20260109_143022.qmd"
    }
}
```

### Exit State (Preview Mode)

```python
{
    # ... existing state ...
    "css_modification": CSSModification(...),
    "section_reorder": SectionReorder(...),
    "theme_recommendation": ThemeRecommendation(...),
    "design_preview_paths": DesignPreview(...),
    "design_changes_applied": False,
    "design_changes_pending": True,
    "design_changes_list": []
}
```

---

## Testing

### Unit Tests

**File**: `tests/unit/workflow/nodes/test_design_applier.py`

**Test Cases**:

1. `test_design_applier_with_css_only`
2. `test_design_applier_with_section_reorder`
3. `test_design_applier_preview_mode`
4. `test_design_applier_no_feedback`
5. `test_design_applier_css_validation_failure`
6. `test_design_applier_rollback_on_error`

### Integration Tests

**File**: `tests/integration/test_design_workflow.py`

**Test Cases**:

1. `test_end_to_end_auto_design`
2. `test_end_to_end_preview_mode`
3. `test_workflow_with_existing_css`

---

**Contract Version**: 1.0
**Last Updated**: 2026-01-09
