# Contract: CLI Extensions

**Module**: `packages/resume-review/src/cli.py`
**Purpose**: Command-line interface extensions for design auto-fix
**Type**: CLI Options and Behavior

---

## New CLI Flags

### --auto-design

**Purpose**: Enable automatic application of design modifications

**Type**: Boolean flag (no value)

**Default**: `False`

**Mutually Exclusive With**: `--design-preview`

**Behavior**:
- When enabled, design modifications are automatically applied to files
- Creates backups before modifying files
- Modifies `styles/resume-custom.css` and/or `resume/resume-ja.qmd`
- Sets `ReviewState.auto_design_enabled = True`

**Example Usage**:
```bash
resume-review review --input resume/resume-ja.qmd --auto-design
```

**CLI Definition**:
```python
@click.option(
    "--auto-design",
    is_flag=True,
    default=False,
    help="Automatically apply design improvements from feedback"
)
```

---

### --design-preview

**Purpose**: Generate before/after preview without modifying files

**Type**: Boolean flag (no value)

**Default**: `False`

**Mutually Exclusive With**: `--auto-design`

**Behavior**:
- Generates design modifications (CSS, section reordering)
- Creates before/after screenshots
- Generates diff image highlighting changes
- Does NOT modify any files
- Sets `ReviewState.design_preview_enabled = True`

**Example Usage**:
```bash
resume-review review --input resume/resume-ja.qmd --design-preview
```

**CLI Definition**:
```python
@click.option(
    "--design-preview",
    is_flag=True,
    default=False,
    help="Generate before/after preview without applying changes"
)
```

---

### --css-output

**Purpose**: Specify custom output path for generated CSS

**Type**: File path (string)

**Default**: `styles/resume-custom.css`

**Requires**: `--auto-design` or `--design-preview`

**Behavior**:
- Overrides default CSS output location
- Path is relative to repository root
- Directory must exist (or will be created)
- Sets `ReviewState.css_output_path` to provided path

**Example Usage**:
```bash
resume-review review --input resume/resume-ja.qmd --auto-design --css-output custom-styles/my-theme.css
```

**CLI Definition**:
```python
@click.option(
    "--css-output",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    default=None,
    help="Custom output path for generated CSS (default: styles/resume-custom.css)"
)
```

---

## Updated CLI Function Signature

```python
@click.command()
@click.option(
    "--input",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to resume QMD file"
)
@click.option(
    "--target-role",
    default="LLM/Multi-Agent Engineer",
    help="Target job role for resume optimization"
)
@click.option(
    "--api-key",
    envvar="ANTHROPIC_API_KEY",
    default=None,
    help="Anthropic API key (or set ANTHROPIC_API_KEY env var)"
)
@click.option(
    "--gemini-api-key",
    envvar=["GOOGLE_API_KEY", "GEMINI_API_KEY"],
    default=None,
    help="Google/Gemini API key (or set GOOGLE_API_KEY env var)"
)
@click.option(
    "--openai-api-key",
    envvar="OPENAI_API_KEY",
    default=None,
    help="OpenAI API key (or set OPENAI_API_KEY env var)"
)
@click.option(
    "--model",
    default=None,
    help="Override model for all agents (e.g., 'gemini-3-pro', 'claude-sonnet-4')"
)
@click.option(
    "--screenshot-url",
    default=None,
    help="URL of rendered resume for screenshot-based design review"
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview content changes without modifying files"
)
@click.option(
    "--auto-design",              # NEW
    is_flag=True,
    default=False,
    help="Automatically apply design improvements from feedback"
)
@click.option(
    "--design-preview",           # NEW
    is_flag=True,
    default=False,
    help="Generate before/after preview without applying changes"
)
@click.option(
    "--css-output",               # NEW
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    default=None,
    help="Custom output path for generated CSS (default: styles/resume-custom.css)"
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose output"
)
@click.option(
    "--save-iterations",
    is_flag=True,
    default=False,
    help="Save intermediate outputs from each iteration"
)
def review(
    input: Path,
    target_role: str,
    api_key: Optional[str],
    gemini_api_key: Optional[str],
    openai_api_key: Optional[str],
    model: Optional[str],
    screenshot_url: Optional[str],
    dry_run: bool,
    auto_design: bool,              # NEW
    design_preview: bool,           # NEW
    css_output: Optional[Path],     # NEW
    verbose: bool,
    save_iterations: bool,
):
    """Review and improve resume using multi-agent workflow with optional design auto-fix."""
    pass
```

---

## Validation Rules

### Mutual Exclusivity

**Rule**: `--auto-design` and `--design-preview` cannot both be enabled

**Implementation**:
```python
if auto_design and design_preview:
    raise click.UsageError(
        "--auto-design and --design-preview are mutually exclusive. "
        "Use --design-preview to review changes first, then run with --auto-design to apply."
    )
```

### CSS Output Requirement

**Rule**: `--css-output` requires either `--auto-design` or `--design-preview`

**Implementation**:
```python
if css_output and not (auto_design or design_preview):
    raise click.UsageError(
        "--css-output requires either --auto-design or --design-preview"
    )
```

### Screenshot URL for Preview

**Rule**: `--design-preview` requires `--screenshot-url` for visual comparison

**Implementation**:
```python
if design_preview and not screenshot_url:
    click.echo(
        "Warning: --design-preview works best with --screenshot-url. "
        "Preview will be text-only without screenshots.",
        err=True
    )
```

### Dry Run Precedence

**Rule**: `--dry-run` takes precedence over `--auto-design` (design changes not applied)

**Implementation**:
```python
if dry_run and auto_design:
    click.echo(
        "Note: --dry-run enabled. Design modifications will be generated but not applied.",
        err=True
    )
    auto_design = False  # Override to prevent file modification
```

---

## State Initialization

### ReviewState Setup

```python
def review(...):
    """CLI entry point."""

    # Existing validation
    if not api_key and not gemini_api_key and not openai_api_key:
        raise click.ClickException("At least one API key required")

    # New validation
    if auto_design and design_preview:
        raise click.UsageError(
            "--auto-design and --design-preview are mutually exclusive"
        )

    if css_output and not (auto_design or design_preview):
        raise click.UsageError(
            "--css-output requires either --auto-design or --design-preview"
        )

    if design_preview and not screenshot_url:
        click.echo(
            "Warning: --design-preview works best with --screenshot-url",
            err=True
        )

    # Dry run precedence
    if dry_run and auto_design:
        click.echo(
            "Note: --dry-run enabled. Design modifications will not be applied.",
            err=True
        )
        auto_design = False

    # Initialize state
    initial_state = {
        "resume": resume,
        "target_role": target_role,
        "api_key": api_key,
        "gemini_api_key": gemini_api_key,
        "openai_api_key": openai_api_key,
        "anthropic_api_key": api_key,
        "override_model": model,
        "screenshot_url": screenshot_url,
        "dry_run": dry_run,
        "verbose": verbose,
        "save_iterations": save_iterations,

        # NEW: Design-related fields
        "auto_design_enabled": auto_design,
        "design_preview_enabled": design_preview,
        "css_output_path": str(css_output) if css_output else "styles/resume-custom.css",

        # ... other existing fields ...
    }

    # Run workflow
    result = await workflow.ainvoke(initial_state)

    # Handle design output
    if result.get("design_changes_applied"):
        _display_design_changes(result)
    elif result.get("design_changes_pending"):
        _display_design_preview(result)
```

---

## Output Formatting

### Design Changes Applied

```python
def _display_design_changes(result: dict[str, Any]):
    """Display design modifications that were applied."""
    click.echo("\n" + "=" * 60)
    click.echo("DESIGN MODIFICATIONS APPLIED")
    click.echo("=" * 60 + "\n")

    changes_list = result.get("design_changes_list", [])
    for change in changes_list:
        click.echo(f"  ✓ {change}")

    # CSS Modification
    css_mod = result.get("css_modification")
    if css_mod:
        click.echo(f"\n📄 CSS Modifications ({css_mod.target_file}):")
        for change in css_mod.changes:
            click.echo(f"  • {change}")

    # Section Reorder
    section_reorder = result.get("section_reorder")
    if section_reorder and section_reorder.is_changed():
        click.echo(f"\n📋 Section Reordering:")
        click.echo(f"  Rationale: {section_reorder.rationale}")
        movements = section_reorder.get_movements()
        for section, old_idx, new_idx in movements:
            direction = "↑" if new_idx < old_idx else "↓"
            click.echo(f"  {direction} {section}: position {old_idx+1} → {new_idx+1}")

    # Theme Recommendation
    theme_rec = result.get("theme_recommendation")
    if theme_rec:
        click.echo(f"\n🎨 Theme Recommendation:")
        click.echo(f"  Suggested: {theme_rec.theme_name}")
        click.echo(f"  Reason: {theme_rec.rationale}")
        click.echo(f"  Apply with: {theme_rec.installation_command}")

    # Backups
    backup_paths = result.get("design_backup_paths", {})
    if backup_paths:
        click.echo(f"\n💾 Backups Created:")
        for original, backup in backup_paths.items():
            click.echo(f"  {Path(original).name} → {backup}")

    click.echo("\n✅ Design modifications complete!")
```

### Design Preview

```python
def _display_design_preview(result: dict[str, Any]):
    """Display design preview without applying changes."""
    click.echo("\n" + "=" * 60)
    click.echo("DESIGN PREVIEW (NO CHANGES APPLIED)")
    click.echo("=" * 60 + "\n")

    # CSS Modification
    css_mod = result.get("css_modification")
    if css_mod:
        click.echo(f"📄 Proposed CSS Changes ({css_mod.target_file}):")
        for change in css_mod.changes:
            click.echo(f"  • {change}")

    # Section Reorder
    section_reorder = result.get("section_reorder")
    if section_reorder and section_reorder.is_changed():
        click.echo(f"\n📋 Proposed Section Reordering:")
        click.echo(f"  {section_reorder.rationale}")
        movements = section_reorder.get_movements()
        for section, old_idx, new_idx in movements:
            direction = "↑" if new_idx < old_idx else "↓"
            click.echo(f"  {direction} {section}: {old_idx+1} → {new_idx+1}")

    # Theme Recommendation
    theme_rec = result.get("theme_recommendation")
    if theme_rec:
        click.echo(f"\n🎨 Theme Recommendation:")
        click.echo(f"  {theme_rec.theme_name}: {theme_rec.rationale}")

    # Preview Paths
    preview = result.get("design_preview_paths")
    if preview:
        click.echo(f"\n🖼️  Preview Screenshots:")
        click.echo(f"  Before:    {preview.before_screenshot}")
        click.echo(f"  After:     {preview.after_screenshot}")
        click.echo(f"  Diff:      {preview.diff_screenshot}")
        click.echo(f"  Composite: {preview.composite_screenshot}")
        if preview.diff_percentage:
            click.echo(f"  Changes: {preview.diff_percentage:.2f}% of pixels")

    click.echo("\n" + "-" * 60)
    click.echo("To apply these changes, run with --auto-design:")
    click.echo(f"  resume-review review --input {result['resume'].file_path} --auto-design")
    click.echo("-" * 60)
```

---

## Help Text Examples

### Full Help

```bash
$ resume-review review --help

Usage: resume-review review [OPTIONS]

  Review and improve resume using multi-agent workflow with optional design
  auto-fix.

Options:
  --input PATH              Path to resume QMD file  [required]
  --target-role TEXT        Target job role for resume optimization
                           [default: LLM/Multi-Agent Engineer]
  --api-key TEXT            Anthropic API key (or set ANTHROPIC_API_KEY)
  --gemini-api-key TEXT     Google/Gemini API key (or set GOOGLE_API_KEY)
  --openai-api-key TEXT     OpenAI API key (or set OPENAI_API_KEY)
  --model TEXT              Override model for all agents
  --screenshot-url TEXT     URL of rendered resume for screenshot-based review
  --dry-run                 Preview content changes without modifying files
  --auto-design             Automatically apply design improvements from
                           feedback
  --design-preview          Generate before/after preview without applying
                           changes
  --css-output PATH         Custom output path for generated CSS (default:
                           styles/resume-custom.css)
  --verbose                 Enable verbose output
  --save-iterations         Save intermediate outputs from each iteration
  --help                    Show this message and exit.
```

---

## Usage Examples

### Example 1: Full Review with Auto-Design

```bash
# Run complete review with automatic design improvements
resume-review review \
  --input resume/resume-ja.qmd \
  --target-role "Senior Backend Engineer" \
  --screenshot-url http://localhost:3000/ja \
  --auto-design \
  --verbose
```

**Output**:
```
=== DESIGN MODIFICATIONS APPLIED ===

  ✓ CSS: styles/resume-custom.css
  ✓ Sections reordered

📄 CSS Modifications (styles/resume-custom.css):
  • Increased h2 font size from 1.2rem to 1.4rem
  • Added bottom border to h2 for hierarchy
  • Increased section gap from 1.5rem to 2rem

📋 Section Reordering:
  Rationale: Skills should appear before experience for better impact
  ↑ Skills section: position 4 → 2

💾 Backups Created:
  resume-custom.css → backups/resume-custom_20260109_143022.css
  resume-ja.qmd → backups/resume-ja_20260109_143022.qmd

✅ Design modifications complete!
```

### Example 2: Preview Before Applying

```bash
# Preview changes without modifying files
resume-review review \
  --input resume/resume-ja.qmd \
  --screenshot-url http://localhost:3000/ja \
  --design-preview
```

**Output**:
```
=== DESIGN PREVIEW (NO CHANGES APPLIED) ===

📄 Proposed CSS Changes:
  • Increased heading font sizes for better hierarchy
  • Improved section spacing for readability

🖼️  Preview Screenshots:
  Before:    review_20260109_143022/preview/before.png
  After:     review_20260109_143022/preview/after.png
  Diff:      review_20260109_143022/preview/diff.png
  Composite: review_20260109_143022/preview/composite.png
  Changes: 12.45% of pixels

------------------------------------------------------------
To apply these changes, run with --auto-design:
  resume-review review --input resume/resume-ja.qmd --auto-design
------------------------------------------------------------
```

### Example 3: Custom CSS Output Path

```bash
# Generate CSS to custom location
resume-review review \
  --input resume/resume-ja.qmd \
  --auto-design \
  --css-output themes/my-custom-theme.css
```

---

## Testing

### CLI Integration Tests

**File**: `tests/integration/test_cli_design.py`

**Test Cases**:

1. `test_cli_auto_design_flag`
2. `test_cli_design_preview_flag`
3. `test_cli_mutual_exclusivity_error`
4. `test_cli_css_output_custom_path`
5. `test_cli_dry_run_overrides_auto_design`
6. `test_cli_design_preview_without_screenshot_warning`

---

**Contract Version**: 1.0
**Last Updated**: 2026-01-09
