# Research: Design Auto-Fix

**Date**: 2026-01-09
**Purpose**: Resolve technical unknowns and document technology decisions for automated design modification feature

## Overview

This document addresses all technical clarifications needed from the Technical Context section and establishes best practices for implementing CSS generation, section reordering, and theme recommendation capabilities.

---

## Research Topics

### 1. CSS Validation Library Selection

**Question**: Which Python CSS validation library provides best balance of features, reliability, and PDF compatibility checking?

**Decision**: **cssutils 2.x**

**Rationale**:
- Industry-standard CSS parser for Python (15+ years active, 1.2k+ GitHub stars)
- Validates CSS syntax and reports errors with line numbers
- Supports CSS custom properties (--variables) which we use heavily
- Parses `@media print` rules for PDF compatibility checks
- Pure Python (no C extensions) - easy installation
- Actively maintained (last release <6 months)
- Pydantic integration via custom validators

**Alternatives Considered**:
1. **tinycss2**: Lighter weight but lower-level - requires more manual validation logic
2. **cssselect**: Only for selector parsing, not full CSS validation
3. **postcss via subprocess**: Requires Node.js - adds toolchain complexity
4. **regex-based validation**: Brittle, error-prone, no AST access

**Implementation Note**: Use `cssutils.parseString()` to validate generated CSS before writing to file. Check for parse errors and forbidden properties in `@media print` context (e.g., fixed positioning, transforms).

---

### 2. QMD Section Parsing Strategy

**Question**: How to reliably parse and manipulate Markdown sections while preserving YAML frontmatter and complex content?

**Decision**: **python-frontmatter + regex-based section splitting**

**Rationale**:
- `python-frontmatter` already in dependencies - extracts YAML cleanly
- Markdown sections defined by headings (`## Heading`) - stable pattern
- Regex pattern: `r'^(#{1,6})\s+(.+)$'` captures heading levels and titles
- Split on headings, preserve everything between (content, lists, code blocks)
- Reconstruct by joining: `YAML + '\n---\n' + sections_in_new_order`
- No need for full Markdown AST (overkill for section reordering)

**Alternatives Considered**:
1. **markdown-it-py**: Full Markdown parser - unnecessary complexity for simple reordering
2. **mistune**: Faster but we only need section boundaries, not full AST
3. **manual string splitting**: Works but python-frontmatter handles YAML edge cases better

**Implementation Pattern**:
```python
import frontmatter
import re

# Parse QMD
doc = frontmatter.load(qmd_path)
content = doc.content  # Body without YAML

# Split into sections
section_pattern = r'^(#{1,6})\s+(.+)$'
sections = []
current_section = {'heading': '', 'level': 0, 'content': []}

for line in content.split('\n'):
    match = re.match(section_pattern, line)
    if match:
        if current_section['heading']:
            sections.append(current_section)
        current_section = {
            'heading': line,
            'level': len(match.group(1)),
            'content': []
        }
    else:
        current_section['content'].append(line)

# Reorder sections (maintain hierarchy)
# Reconstruct: frontmatter.dumps(doc) with reordered sections
```

---

### 3. Screenshot Diffing for Preview

**Question**: How to highlight visual differences between before/after screenshots for preview mode?

**Decision**: **pixelmatch (via node subprocess) + PIL/Pillow for image manipulation**

**Rationale**:
- `pixelmatch` is industry standard for visual regression testing (Playwright uses it)
- Generates diff image with highlighted regions
- Already have Node.js in monorepo - no new toolchain requirement
- Python subprocess call is acceptable (one-time operation per preview)
- PIL/Pillow (likely already installed for screenshot handling) can overlay annotations

**Alternatives Considered**:
1. **OpenCV (cv2.absdiff)**: Adds heavy C++ dependency, overkill for simple diff
2. **scikit-image**: Another heavy ML library for simple task
3. **pure Pillow pixel comparison**: Slower, no anti-aliasing-aware diff
4. **External service (Percy, Chromatic)**: Requires cloud API, adds cost/latency

**Implementation Approach**:
1. Generate before screenshot (existing resume rendered)
2. Apply CSS modifications temporarily
3. Generate after screenshot
4. Call pixelmatch via Node subprocess: `node diff.js before.png after.png diff.png`
5. Create composite image with PIL: before | diff | after side-by-side
6. Return path to composite for user review

**Node.js Diff Script** (scripts/visual-diff.js):
```javascript
const pixelmatch = require('pixelmatch');
const { PNG } = require('pngjs');
const fs = require('fs');

const img1 = PNG.sync.read(fs.readFileSync(process.argv[2]));
const img2 = PNG.sync.read(fs.readFileSync(process.argv[3]));
const diff = new PNG({ width: img1.width, height: img1.height });

const numDiffPixels = pixelmatch(
  img1.data, img2.data, diff.data,
  img1.width, img1.height,
  { threshold: 0.1, includeAA: true }
);

fs.writeFileSync(process.argv[4], PNG.sync.write(diff));
console.log(`Diff pixels: ${numDiffPixels}`);
```

---

### 4. CSS Generation Prompt Engineering

**Question**: What prompt structure ensures LLM generates valid, minimal, print-compatible CSS?

**Decision**: **Structured prompt with examples, constraints, and validation instructions**

**Rationale**:
- LLMs need explicit constraints to avoid over-engineering CSS
- Few-shot examples guide toward minimal, targeted rules
- Explicit `@media print` requirements ensure PDF compatibility
- JSON-structured issues input → structured CSS output
- Request BEM naming convention for maintainability

**Prompt Template**:
```
You are an expert CSS designer specializing in professional document styling.

Given design feedback for a resume, generate CSS modifications that address the issues.

CONSTRAINTS:
1. Generate MINIMAL, targeted CSS changes - don't rewrite everything
2. Use CSS custom properties (--var) for values that users might override
3. Prioritize readability and professionalism over creativity
4. Ensure print compatibility - include @media print rules where needed
5. Follow BEM naming convention for any new classes
6. Include comments explaining each rule's purpose

FORBIDDEN in @media print:
- position: fixed/absolute
- transform properties
- break-inside: avoid (use page-break-inside)
- complex animations

INPUT:
Current CSS (may be empty): {current_css}

Design Issues (from agents):
{json.dumps(issues, indent=2)}
- Type: {issue.type}  (spacing/typography/color/hierarchy/layout)
- Severity: {issue.severity}
- Description: {issue.description}
- Location: {issue.location}

OUTPUT FORMAT:
Return ONLY valid CSS (no markdown code blocks, no explanations before/after).
Include comments within CSS to explain changes.

Example output:
/* Issue: Headings lack visual weight (high severity) */
h2 {
  font-size: 1.4rem;        /* Was: 1.2rem */
  font-weight: 600;         /* Was: 500 */
  border-bottom: 2px solid var(--primary-color);
  padding-bottom: 0.5rem;
}

@media print {
  h2 {
    page-break-after: avoid;
  }
}

Generate CSS:
```

**Validation After Generation**:
1. Parse with cssutils - reject if syntax errors
2. Check for forbidden print properties
3. Verify all custom properties are defined in `:root`
4. Confirm comments exist (quality check)

---

### 5. Backup and Rollback Strategy

**Question**: How to safely modify files with guaranteed rollback capability?

**Decision**: **Atomic file operations with timestamped backups**

**Rationale**:
- Simple, reliable, no database needed
- Timestamped backups enable audit trail
- Atomic writes (write temp → rename) prevent corruption
- Python's `shutil` and `pathlib` provide safe primitives

**Implementation Pattern**:
```python
from pathlib import Path
import shutil
from datetime import datetime

class FileBackupManager:
    def __init__(self, backup_dir: Path = Path("backups")):
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(exist_ok=True)

    def backup(self, file_path: Path) -> Path:
        """Create timestamped backup, return backup path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
        shutil.copy2(file_path, backup_path)
        return backup_path

    def atomic_write(self, file_path: Path, content: str):
        """Write content atomically with backup."""
        if file_path.exists():
            self.backup(file_path)

        # Write to temp file first
        temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
        temp_path.write_text(content, encoding='utf-8')

        # Atomic rename
        temp_path.replace(file_path)

    def rollback(self, original_path: Path, backup_path: Path):
        """Restore from backup."""
        shutil.copy2(backup_path, original_path)
```

**Alternatives Considered**:
1. **Git-based rollback**: Requires commits, pollutes history, slower
2. **In-memory undo stack**: Lost on crash, doesn't help with debugging
3. **SQLite transaction log**: Overkill for simple file operations

---

### 6. Theme Recommendation Logic

**Question**: How to map design issues to appropriate Quarto themes?

**Decision**: **Pattern-matching heuristics + Quarto theme metadata**

**Rationale**:
- Quarto has ~10-15 common themes with known characteristics
- Design issues cluster into patterns: "poor hierarchy" → themes with strong typography
- Metadata from `quarto inspect` command provides theme details
- Simple rule-based system sufficient (no ML needed)

**Theme Knowledge Base**:
```python
THEME_PROFILES = {
    "cosmo": {
        "strengths": ["clean", "modern", "good-spacing"],
        "good_for": ["typography", "hierarchy"],
        "pdf_support": True
    },
    "journal": {
        "strengths": ["professional", "academic", "print-optimized"],
        "good_for": ["typography", "spacing", "layout"],
        "pdf_support": True
    },
    "flatly": {
        "strengths": ["modern", "colorful", "good-contrast"],
        "good_for": ["color", "hierarchy"],
        "pdf_support": True
    },
    # ... more themes
}

def recommend_theme(design_issues: list[DesignIssue]) -> ThemeRecommendation:
    # Count issue types
    issue_counts = Counter(issue.type for issue in design_issues)
    primary_issue = issue_counts.most_common(1)[0][0]

    # Find themes good for primary issue
    candidates = [
        (name, profile)
        for name, profile in THEME_PROFILES.items()
        if primary_issue in profile["good_for"]
        and profile["pdf_support"]
    ]

    # Return top candidate with rationale
    if candidates:
        theme_name, profile = candidates[0]
        return ThemeRecommendation(
            theme_name=theme_name,
            rationale=f"Addresses {primary_issue} issues with {', '.join(profile['strengths'])}",
            quarto_config={"format": {"html": {"theme": theme_name}}},
            installation_command=f"quarto use theme {theme_name}"
        )
```

**Alternatives Considered**:
1. **LLM-based recommendation**: Slower, costs tokens, less deterministic
2. **User survey**: Delays automation, requires UI
3. **A/B testing**: Requires rendering all themes, very slow

---

### 7. StateGraph Integration Pattern

**Question**: Where in the workflow should design modification nodes be placed?

**Decision**: **After design review node, conditional branch to design_applier**

**Rationale**:
- Design feedback must exist before generating CSS (logical dependency)
- Should be optional (only runs if `--auto-design` or `--design-preview` enabled)
- Runs before final output to ensure modifications are included in result
- Parallel to revision loop (different concern - design vs content)

**Workflow Graph Extension**:
```
[existing nodes...]
  ↓
design_review (UX + Visual agents)
  ↓
decision: design modifications needed?
  ↓ YES (if --auto-design or --design-preview)
  ↓
design_applier_node
  ├─→ css_generator (always)
  ├─→ section_reorder (if UX feedback suggests)
  └─→ theme_recommender (if systematic issues)
  ↓
[conditional]
  ├─→ apply modifications (--auto-design)
  └─→ generate preview only (--design-preview)
  ↓
[continue to existing output nodes...]
```

**State Fields**:
```python
class ReviewState(TypedDict, total=False):
    # ... existing fields ...

    # Design modification state
    auto_design_enabled: bool
    design_preview_enabled: bool
    css_modification: Optional[CSSModification]
    section_reorder: Optional[SectionReorder]
    theme_recommendation: Optional[ThemeRecommendation]
    design_preview_paths: Optional[DesignPreview]
```

---

## Best Practices

### CSS Generation
1. Always validate generated CSS before writing to file
2. Use CSS custom properties for any magic numbers
3. Include `@media print` rules for all layout-affecting properties
4. Add comments explaining reasoning (aids user customization)
5. Keep specificity low (no `!important` unless absolutely necessary)

### File Safety
1. Always create backup before modifying resume QMD
2. Use atomic writes (temp file + rename) to prevent corruption
3. Store backups with timestamps for audit trail
4. Validate modifications (Quarto syntax check) before committing

### Preview Generation
1. Render screenshots at consistent resolution (1920x1080 recommended)
2. Use headless browser with same config as production render
3. Generate diff image to highlight changes visually
4. Include side-by-side comparison for user review

### Error Handling
1. CSS validation errors → log and return empty stylesheet (don't break workflow)
2. Section reorder errors → preserve original order (safe fallback)
3. Screenshot failures → provide text-only diff (degraded but functional)
4. Theme recommendation errors → continue without recommendation (optional feature)

---

## Implementation Order

Recommended sequence based on dependencies:

1. **Phase 0**: Data models (`models/design.py`) - foundation for all features
2. **Phase 1**: CSS Service (`services/css_service.py`) - file operations, validation
3. **Phase 2**: CSS Generator Agent (`agents/css_generator.py`) - LLM integration
4. **Phase 3**: Section Reorder (`services/section_reorder.py`) - QMD manipulation
5. **Phase 4**: Theme Recommender (`services/theme_recommender.py`) - heuristics
6. **Phase 5**: Design Applier Node (`workflow/nodes/design_applier.py`) - orchestration
7. **Phase 6**: CLI Integration (`cli.py`) - user interface
8. **Phase 7**: Preview Generation (enhancement to screenshot service)

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Generated CSS breaks layout | High | Validation + preview mode + automatic backup |
| Section reorder loses content | Critical | Python-frontmatter library (battle-tested) + content hash verification |
| LLM generates invalid CSS | Medium | cssutils validation + fallback to no-op |
| Preview screenshots fail | Low | Text-only diff fallback + degraded experience acceptable |
| Theme recommendation irrelevant | Low | Feature is advisory only (user decides) |
| File corruption during write | Medium | Atomic writes + backups + integration tests |

---

## Success Metrics

- **CSS Validation Rate**: >95% of generated CSS passes cssutils validation
- **Content Preservation**: 100% of section reordering preserves all content (verified by hash)
- **Preview Accuracy**: Preview screenshots match final render (manual QA initially)
- **User Trust**: <5% rollback rate (indicates good quality)
- **Performance**: Full design workflow completes in <30 seconds

---

## Dependencies to Add

Add to `packages/resume-review/pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existing ...
    "cssutils>=2.0.0,<3.0.0",  # CSS validation and parsing
]

[project.optional-dependencies]
dev = [
    # ... existing ...
]
```

Add to root `package.json` (for screenshot diffing):

```json
{
  "devDependencies": {
    "pixelmatch": "^5.3.0",
    "pngjs": "^7.0.0"
  }
}
```

---

## Related Documentation

- [Quarto Themes Documentation](https://quarto.org/docs/output-formats/html-themes.html)
- [CSS Custom Properties (MDN)](https://developer.mozilla.org/en-US/docs/Web/CSS/--*)
- [cssutils Documentation](https://cssutils.readthedocs.io/)
- [Playwright Python API](https://playwright.dev/python/docs/api/class-playwright)
- [python-frontmatter](https://python-frontmatter.readthedocs.io/)

---

**Research Complete**: All technical clarifications resolved. Ready for Phase 1 (Data Models & Contracts).
