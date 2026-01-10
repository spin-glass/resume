# Data Model: Design Auto-Fix

**Date**: 2026-01-09
**Purpose**: Define domain entities and their relationships for design modification feature

## Overview

This document specifies the data structures used for automated design modifications, including CSS generation, section reordering, theme recommendations, and preview generation.

---

## Entity Definitions

### 1. DesignIssueType (Enum)

**Purpose**: Categorize types of design problems identified by agents

**Module**: `src/models/design.py`

```python
from enum import Enum

class DesignIssueType(str, Enum):
    """Types of design issues that can be automatically addressed."""

    SPACING = "spacing"           # Margin, padding, gaps between elements
    TYPOGRAPHY = "typography"     # Font size, weight, line height, hierarchy
    COLOR = "color"               # Color contrast, accessibility, consistency
    HIERARCHY = "hierarchy"       # Visual information hierarchy, emphasis
    LAYOUT = "layout"             # Section arrangement, alignment, balance
```

**Validation Rules**:
- Enum values are lowercase strings for JSON serialization
- Immutable once defined
- Used as primary classifier for routing design fixes

---

### 2. CSSModification (Model)

**Purpose**: Represent generated CSS modifications with metadata

**Module**: `src/models/design.py`

```python
from pydantic import BaseModel, Field, validator
from pathlib import Path
from typing import Optional

class CSSModification(BaseModel):
    """CSS modification generated from design feedback."""

    css_content: str = Field(
        ...,
        description="Generated CSS rules as string",
        min_length=1
    )

    target_file: Path = Field(
        default=Path("styles/resume-custom.css"),
        description="Output file path for CSS"
    )

    changes: list[str] = Field(
        default_factory=list,
        description="Human-readable list of changes made (e.g., 'Increased heading font size')"
    )

    issue_types: list[DesignIssueType] = Field(
        default_factory=list,
        description="Types of issues this CSS addresses"
    )

    validation_passed: bool = Field(
        default=False,
        description="Whether CSS passed cssutils validation"
    )

    validation_errors: list[str] = Field(
        default_factory=list,
        description="CSS validation errors (if any)"
    )

    backup_path: Optional[Path] = Field(
        default=None,
        description="Path to backup of previous CSS file (if existed)"
    )

    @validator("css_content")
    def validate_css_content(cls, v):
        """Ensure CSS content is not empty or just comments."""
        stripped = '\n'.join(
            line for line in v.split('\n')
            if line.strip() and not line.strip().startswith('//')
        )
        if not stripped:
            raise ValueError("CSS content is empty or contains only comments")
        return v

    @validator("target_file")
    def validate_target_file(cls, v):
        """Ensure target file has .css extension."""
        if v.suffix != ".css":
            raise ValueError(f"Target file must have .css extension, got {v.suffix}")
        return v

    def get_summary(self) -> str:
        """Get human-readable summary of modifications."""
        issue_types_str = ", ".join(t.value for t in self.issue_types)
        return f"CSS modifications for {issue_types_str} ({len(self.changes)} changes)"
```

**Relationships**:
- **Created by**: `CSSGeneratorAgent`
- **Consumed by**: `CSSService` (for file writing), `DesignApplierNode` (for application)
- **Stored in**: `ReviewState.css_modification`

**Lifecycle**:
1. Agent generates CSS from feedback → `CSSModification` created
2. CSS validation runs → sets `validation_passed`, `validation_errors`
3. If preview mode: stored but not applied
4. If auto-design mode: `CSSService` writes to `target_file` with backup

---

### 3. SectionReorder (Model)

**Purpose**: Represent section reordering operations on QMD content

**Module**: `src/models/design.py`

```python
from pydantic import BaseModel, Field, validator

class SectionReorder(BaseModel):
    """Section reordering operation for QMD content."""

    original_order: list[str] = Field(
        ...,
        description="Original section headings in order",
        min_items=1
    )

    new_order: list[str] = Field(
        ...,
        description="New section headings in desired order",
        min_items=1
    )

    rationale: str = Field(
        ...,
        description="Explanation for why sections were reordered",
        min_length=10
    )

    content_hash_before: Optional[str] = Field(
        default=None,
        description="SHA256 hash of all content (for verification)"
    )

    content_hash_after: Optional[str] = Field(
        default=None,
        description="SHA256 hash after reordering (should match before)"
    )

    @validator("new_order")
    def validate_new_order(cls, v, values):
        """Ensure new_order contains same sections as original_order."""
        if "original_order" in values:
            original_set = set(values["original_order"])
            new_set = set(v)
            if original_set != new_set:
                raise ValueError(
                    f"New order must contain same sections as original. "
                    f"Missing: {original_set - new_set}, "
                    f"Extra: {new_set - original_set}"
                )
        return v

    @validator("content_hash_after")
    def validate_content_preservation(cls, v, values):
        """Ensure content was preserved (hashes match)."""
        if v and "content_hash_before" in values:
            if v != values["content_hash_before"]:
                raise ValueError(
                    "Content hash mismatch - content was modified during reordering. "
                    "Only order should change, not content."
                )
        return v

    def is_changed(self) -> bool:
        """Check if order actually changed."""
        return self.original_order != self.new_order

    def get_movements(self) -> list[tuple[str, int, int]]:
        """Get list of (section, old_index, new_index) for moved sections."""
        movements = []
        for section in self.original_order:
            old_idx = self.original_order.index(section)
            new_idx = self.new_order.index(section)
            if old_idx != new_idx:
                movements.append((section, old_idx, new_idx))
        return movements
```

**Relationships**:
- **Created by**: `SectionReorderService` (analyzes UX feedback)
- **Consumed by**: `DesignApplierNode` (applies reordering)
- **Stored in**: `ReviewState.section_reorder`

**Lifecycle**:
1. UX feedback suggests section priority → `SectionReorder` created
2. Content hash calculated before operation
3. QMD sections reordered using `python-frontmatter`
4. Content hash verified after operation
5. If hashes don't match → rollback + error

---

### 4. ThemeRecommendation (Model)

**Purpose**: Represent Quarto theme recommendation with configuration

**Module**: `src/models/design.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, Any

class ThemeRecommendation(BaseModel):
    """Quarto theme recommendation with configuration."""

    theme_name: str = Field(
        ...,
        description="Name of recommended Quarto theme",
        min_length=1
    )

    rationale: str = Field(
        ...,
        description="Explanation of why this theme is recommended",
        min_length=20
    )

    quarto_config: dict[str, Any] = Field(
        ...,
        description="_quarto.yml configuration snippet for this theme"
    )

    installation_command: str = Field(
        ...,
        description="Command to install/apply theme (e.g., 'quarto use theme cosmo')"
    )

    preview_url: Optional[str] = Field(
        default=None,
        description="URL to theme preview/demo (if available)"
    )

    addresses_issues: list[DesignIssueType] = Field(
        default_factory=list,
        description="Design issue types this theme addresses"
    )

    def get_config_yaml(self) -> str:
        """Generate YAML string for _quarto.yml."""
        import yaml
        return yaml.dump(self.quarto_config, default_flow_style=False, sort_keys=False)

    def get_summary(self) -> str:
        """Get human-readable summary."""
        issues_str = ", ".join(t.value for t in self.addresses_issues)
        return f"Theme '{self.theme_name}' recommended for {issues_str}"
```

**Relationships**:
- **Created by**: `ThemeRecommenderService`
- **Consumed by**: User (advisory output), `DesignApplierNode` (for display)
- **Stored in**: `ReviewState.theme_recommendation`

**Lifecycle**:
1. Design feedback analyzed for patterns
2. Theme matched from knowledge base
3. Configuration generated
4. Recommendation displayed to user (advisory only - requires manual application)

---

### 5. DesignPreview (Model)

**Purpose**: Represent before/after preview with visual comparison

**Module**: `src/models/design.py`

```python
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional

class DesignPreview(BaseModel):
    """Visual preview of design modifications."""

    before_screenshot: Path = Field(
        ...,
        description="Path to screenshot before modifications"
    )

    after_screenshot: Path = Field(
        ...,
        description="Path to screenshot after modifications"
    )

    diff_screenshot: Optional[Path] = Field(
        default=None,
        description="Path to diff image highlighting changes"
    )

    composite_screenshot: Optional[Path] = Field(
        default=None,
        description="Path to side-by-side comparison (before|diff|after)"
    )

    diff_pixel_count: Optional[int] = Field(
        default=None,
        description="Number of pixels that differ between before/after"
    )

    diff_percentage: Optional[float] = Field(
        default=None,
        description="Percentage of pixels that differ (0-100)",
        ge=0.0,
        le=100.0
    )

    metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted design metrics (spacing measurements, contrast ratios, etc.)"
    )

    def get_summary(self) -> str:
        """Get human-readable summary of changes."""
        if self.diff_percentage is not None:
            return f"{self.diff_percentage:.2f}% of pixels changed ({self.diff_pixel_count} pixels)"
        return "Preview generated"

    def has_significant_changes(self, threshold: float = 1.0) -> bool:
        """Check if changes exceed threshold percentage."""
        if self.diff_percentage is None:
            return True  # Assume significant if not measured
        return self.diff_percentage >= threshold
```

**Relationships**:
- **Created by**: `ScreenshotService` (extended functionality)
- **Consumed by**: User (for review), `DesignApplierNode` (for preview mode)
- **Stored in**: `ReviewState.design_preview_paths`

**Lifecycle**:
1. Before screenshot captured (original resume)
2. CSS modifications applied temporarily
3. After screenshot captured
4. Diff generated via pixelmatch
5. Composite image created
6. Preview presented to user for approval

---

## ReviewState Extensions

**Purpose**: Add design-related fields to existing workflow state

**Module**: `src/workflow/state.py` (modifications)

```python
from typing import TypedDict, Optional
from ..models.design import (
    CSSModification,
    SectionReorder,
    ThemeRecommendation,
    DesignPreview
)

class ReviewState(TypedDict, total=False):
    # ... existing fields (resume, api_key, target_role, etc.) ...

    # Design modification flags (from CLI)
    auto_design_enabled: bool           # --auto-design flag
    design_preview_enabled: bool        # --design-preview flag
    css_output_path: Optional[str]      # --css-output override

    # Design modification outputs
    css_modification: Optional[CSSModification]
    section_reorder: Optional[SectionReorder]
    theme_recommendation: Optional[ThemeRecommendation]
    design_preview_paths: Optional[DesignPreview]

    # Design modification status
    design_changes_applied: bool        # Were modifications actually applied?
    design_changes_pending: bool        # Are modifications ready but not applied (preview mode)?
    design_changes_list: list[str]      # Human-readable list of applied changes

    # Backup tracking
    design_backup_paths: dict[str, str]  # {original_path: backup_path} for rollback
```

**Field Descriptions**:

| Field | Type | Purpose | Set By |
|-------|------|---------|--------|
| `auto_design_enabled` | bool | User enabled automatic design application | CLI parser |
| `design_preview_enabled` | bool | User requested preview only (no application) | CLI parser |
| `css_output_path` | str | Custom CSS output path (overrides default) | CLI parser |
| `css_modification` | CSSModification | Generated CSS modifications | CSSGeneratorAgent |
| `section_reorder` | SectionReorder | Section reordering plan | SectionReorderService |
| `theme_recommendation` | ThemeRecommendation | Theme suggestion | ThemeRecommenderService |
| `design_preview_paths` | DesignPreview | Preview screenshots | ScreenshotService |
| `design_changes_applied` | bool | Confirmation that changes were written to files | DesignApplierNode |
| `design_changes_pending` | bool | Changes generated but not applied (preview mode) | DesignApplierNode |
| `design_changes_list` | list[str] | Summary of changes for user display | DesignApplierNode |
| `design_backup_paths` | dict | Mapping of original files to backups for rollback | CSSService, SectionReorderService |

---

## Entity Relationships Diagram

```
┌─────────────────┐
│  Feedback       │ (existing)
│  (from agents)  │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         v                 v
┌────────────────┐  ┌──────────────────┐
│ CSSModification│  │ SectionReorder   │
│                │  │                  │
│ - css_content  │  │ - original_order │
│ - target_file  │  │ - new_order      │
│ - changes[]    │  │ - rationale      │
│ - issue_types[]│  │ - content_hash   │
└────────┬───────┘  └────────┬─────────┘
         │                   │
         └────────┬──────────┘
                  │
                  v
         ┌────────────────────┐
         │ DesignApplierNode  │
         │                    │
         │ Orchestrates:      │
         │ - CSS writing      │
         │ - Section reorder  │
         │ - Preview gen      │
         └────────┬───────────┘
                  │
                  ├──────────────┐
                  │              │
                  v              v
         ┌─────────────┐  ┌──────────────┐
         │ CSSService  │  │DesignPreview │
         │             │  │              │
         │ - write()   │  │ - before_ss  │
         │ - validate()│  │ - after_ss   │
         │ - backup()  │  │ - diff_ss    │
         └─────────────┘  └──────────────┘
```

---

## Validation Rules Summary

### Cross-Entity Rules

1. **Content Preservation**: `SectionReorder.content_hash_before` MUST equal `content_hash_after`
2. **CSS Validation**: `CSSModification.validation_passed` MUST be True before applying
3. **Backup Integrity**: All file modifications MUST have corresponding backup in `design_backup_paths`
4. **Order Consistency**: `SectionReorder.new_order` MUST contain exactly same sections as `original_order`

### State Consistency Rules

1. If `auto_design_enabled` is True, `design_preview_enabled` MUST be False (mutually exclusive)
2. If `design_changes_applied` is True, `design_changes_pending` MUST be False
3. If `design_preview_enabled` is True, `design_preview_paths` MUST be present
4. If `css_modification` is present and applied, `design_backup_paths` MUST contain CSS file backup

---

## Data Flow

### Happy Path (Auto-Design Mode)

```
1. User runs: resume-review review --input resume.qmd --auto-design

2. Workflow reaches design_review node
   → Visual & UX agents generate feedback
   → State updated with design_feedback

3. Conditional: auto_design_enabled? → Yes

4. design_applier_node executes:
   a. CSSGeneratorAgent.generate() → CSSModification
   b. SectionReorderService.analyze() → SectionReorder
   c. ThemeRecommenderService.recommend() → ThemeRecommendation

5. Modifications applied:
   a. CSSService.write(css_modification)
      → Creates backup
      → Writes styles/resume-custom.css
   b. SectionReorderService.reorder(qmd_path, section_reorder)
      → Creates backup
      → Rewrites resume/resume-ja.qmd

6. State updated:
   - design_changes_applied = True
   - design_changes_list = ["CSS: styles/resume-custom.css", "Sections reordered"]
   - design_backup_paths = {original paths: backup paths}

7. Workflow continues to output
```

### Preview Mode

```
1. User runs: resume-review review --input resume.qmd --design-preview

2. [Same steps 2-4 as above]

3. Preview generation:
   a. ScreenshotService.capture(original resume) → before_screenshot
   b. Temporarily apply CSS to temp location
   c. ScreenshotService.capture(modified resume) → after_screenshot
   d. PixelmatchService.diff(before, after) → diff_screenshot
   e. ImageCompositor.create_side_by_side() → composite_screenshot

4. State updated:
   - design_changes_pending = True
   - design_changes_applied = False
   - design_preview_paths = DesignPreview(...)

5. Display preview to user with message:
   "Preview generated. Run with --auto-design to apply changes."

6. Workflow ends (no files modified)
```

---

## File Storage Conventions

### Generated Files

- **CSS Output**: `styles/resume-custom.css` (configurable via `--css-output`)
- **Backups**: `backups/resume-ja_{timestamp}.qmd`, `backups/resume-custom_{timestamp}.css`
- **Previews**: `review_sessions/{session_id}/preview/before.png`, `after.png`, `diff.png`, `composite.png`

### Naming Conventions

- **Backup files**: `{original_stem}_{YYYYMMDD_HHMMSS}{ext}`
- **Preview files**: `{before|after|diff|composite}.png`
- **Session directories**: `review_{YYYYMMDD_HHMMSS}/`

---

**Data Model Complete**: All entities defined with validation rules and relationships. Ready for contracts definition.
