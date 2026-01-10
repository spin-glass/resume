# Feature Specification: Design Auto-Fix

**Feature Branch**: `013-design-auto-fix`
**Created**: 2026-01-09
**Status**: Draft
**Input**: User description: "デザイン自動修正機能 - Automatically apply design review feedback to resume QMD file, adjusting visual elements like spacing, hierarchy, and layout to improve visual quality"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic CSS Generation from Design Feedback (Priority: P1)

A resume author receives design feedback from UX and Visual Designer agents (e.g., "spacing too cramped", "headings lack visual weight") and wants to automatically generate CSS that addresses these issues without manually writing style rules.

**Why this priority**: This is the core value proposition - automating the most time-consuming part of applying design feedback. Without this, users must manually translate subjective feedback into CSS rules, requiring both design knowledge and CSS expertise.

**Independent Test**: Can be fully tested by running review with `--auto-design` flag and validating that generated CSS file addresses specific design issues from feedback, delivers immediate value even without other features.

**Acceptance Scenarios**:

1. **Given** design feedback contains "spacing issues", **When** auto-design is enabled, **Then** system generates CSS with improved spacing rules (margin, padding, section gaps)
2. **Given** design feedback contains "typography problems", **When** auto-design is enabled, **Then** system generates CSS with improved font sizes, weights, and hierarchy
3. **Given** design feedback contains "color contrast issues", **When** auto-design is enabled, **Then** system generates CSS with improved color values meeting accessibility standards
4. **Given** generated CSS conflicts with existing styles, **When** CSS is applied, **Then** system preserves existing custom styles while adding new improvements via CSS custom properties
5. **Given** design feedback contains print-specific issues, **When** CSS is generated, **Then** system includes `@media print` rules ensuring PDF compatibility

---

### User Story 2 - Preview Design Changes Before Application (Priority: P2)

A resume author wants to preview how design changes will look before permanently applying them to their resume, allowing them to accept or reject modifications.

**Why this priority**: Provides safety and control. Users need confidence that automated changes improve rather than harm their resume's appearance. This enables experimentation without risk.

**Independent Test**: Can be tested independently by running review with `--design-preview` flag, verifying before/after screenshots are generated, and confirming no files are modified. Delivers value by letting users evaluate changes risk-free.

**Acceptance Scenarios**:

1. **Given** design feedback is available, **When** user runs review with `--design-preview`, **Then** system generates before/after screenshots without modifying any files
2. **Given** preview screenshots show design changes, **When** user reviews them, **Then** system highlights specific differences (spacing, typography, layout changes)
3. **Given** user approves preview, **When** user runs review with `--auto-design`, **Then** system applies the previously previewed changes
4. **Given** user rejects preview, **When** user exits without applying, **Then** no files are modified and original resume remains unchanged

---

### User Story 3 - Section Reordering Based on UX Feedback (Priority: P3)

A resume author receives UX feedback suggesting better information hierarchy (e.g., "move skills section higher") and wants the system to automatically reorder sections in the QMD file for optimal impact.

**Why this priority**: Addresses structural layout issues that CSS alone cannot fix. Lower priority than styling because it modifies content structure, requiring more user trust and validation.

**Independent Test**: Can be tested independently by providing UX feedback about section priority, verifying QMD content is reordered appropriately while preserving all section content intact. Delivers value by optimizing information architecture automatically.

**Acceptance Scenarios**:

1. **Given** UX feedback suggests "skills should appear before experience", **When** section reorder is applied, **Then** system moves skills section above experience section in QMD file
2. **Given** sections are reordered, **When** content is examined, **Then** section headings and content remain unchanged (only order changes)
3. **Given** sections are reordered, **When** YAML frontmatter is examined, **Then** frontmatter remains completely unchanged
4. **Given** multiple sections need reordering, **When** changes are applied, **Then** system maintains logical groupings (e.g., keeps related sections together)

---

### User Story 4 - Quarto Theme Recommendations (Priority: P4)

A resume author whose current theme has fundamental design limitations receives recommendations for alternative Quarto themes that better address their resume's needs.

**Why this priority**: Provides strategic guidance but requires significant manual work (theme installation, configuration). Lower priority because it's advisory rather than automated.

**Independent Test**: Can be tested independently by analyzing design feedback patterns and outputting theme recommendations with rationale. Delivers value as guidance even if user doesn't immediately switch themes.

**Acceptance Scenarios**:

1. **Given** design feedback shows systematic layout issues, **When** theme analysis runs, **Then** system recommends specific Quarto themes addressing those issues
2. **Given** theme recommendation is provided, **When** user reviews it, **Then** recommendation includes rationale explaining why suggested theme solves specific problems
3. **Given** theme recommendation is provided, **When** user reviews it, **Then** recommendation includes exact `_quarto.yml` configuration and installation commands
4. **Given** recommended theme is applied, **When** resume is rendered, **Then** theme addresses the original design issues from feedback

---

### Edge Cases

- What happens when generated CSS causes layout breaks or rendering errors?
  - System includes CSS validation and generates preview screenshots to detect visual regressions
  - All changes are reversible via backup files
  - Users can disable auto-design and use preview mode for safety

- How does system handle conflicting design feedback from multiple agents?
  - System prioritizes critical issues (accessibility, readability) over subjective preferences
  - CSS generation uses specificity rules to avoid conflicts with existing styles
  - User can override automated decisions via manual CSS edits

- What happens when section reordering breaks semantic structure?
  - System validates that reordered content maintains logical flow
  - YAML frontmatter and section content remain untouched (only order changes)
  - Users can preview reordering before application

- How does system ensure print/PDF compatibility of generated CSS?
  - All generated CSS includes `@media print` rules
  - CSS validation checks for print-breaking properties (e.g., fixed positioning)
  - Preview includes both screen and print rendering tests

- What happens when custom CSS conflicts with generated styles?
  - System uses CSS custom properties (variables) to enable easy overrides
  - Generated CSS includes comments explaining each rule's purpose
  - Users can specify custom CSS output path to separate generated from manual styles

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST analyze design feedback from UX and Visual Designer agents and identify specific design issues (spacing, typography, color, hierarchy, layout)
- **FR-002**: System MUST generate valid CSS that addresses identified design issues using minimal, targeted modifications
- **FR-003**: System MUST output generated CSS to configurable file path (default: `styles/resume-custom.css`)
- **FR-004**: System MUST automatically update `_quarto.yml` configuration to reference generated CSS file
- **FR-005**: System MUST generate CSS using CSS custom properties (--variables) for maintainability and easy overrides
- **FR-006**: System MUST include `@media print` rules in generated CSS for PDF compatibility
- **FR-007**: System MUST provide `--auto-design` CLI flag to enable automatic design modification application
- **FR-008**: System MUST provide `--design-preview` CLI flag to generate before/after screenshots without applying changes
- **FR-009**: System MUST provide `--css-output` CLI flag to specify custom output path for generated CSS
- **FR-010**: System MUST create backup of original files before applying design modifications
- **FR-011**: System MUST validate generated CSS for syntax errors before application
- **FR-012**: System MUST analyze UX feedback to determine optimal section ordering
- **FR-013**: System MUST reorder sections in QMD file while preserving all content and YAML frontmatter unchanged
- **FR-014**: System MUST analyze current theme and design issues to recommend alternative Quarto themes
- **FR-015**: System MUST provide theme recommendations with rationale, configuration snippets, and installation commands
- **FR-016**: System MUST generate before/after screenshots when preview mode is enabled
- **FR-017**: System MUST highlight visual differences between before/after states in preview
- **FR-018**: System MUST log all design modifications applied (CSS rules, section reordering, theme changes)
- **FR-019**: System MUST skip design modification application when `--dry-run` flag is enabled (report only)
- **FR-020**: System MUST preserve existing custom CSS styles when generating new CSS modifications

### Key Entities *(include if feature involves data)*

- **DesignFeedback**: Feedback from UX/Visual Designer agents containing specific design issues, issue types (spacing/typography/color/hierarchy/layout), severity, and suggested improvements
- **CSSModification**: Generated CSS content, target output file path, list of changes made, design issue types addressed, and validation status
- **SectionReorder**: Original section order, recommended new order, rationale for reordering, and affected section names
- **ThemeRecommendation**: Recommended Quarto theme name, rationale for recommendation, required `_quarto.yml` configuration, installation commands, and preview URL if available
- **DesignPreview**: Before/after screenshot paths, highlighted differences, design metrics comparison (spacing measurements, contrast ratios, hierarchy scores)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can apply design improvements in under 10 minutes (down from 30-60 minutes manual effort)
- **SC-002**: Generated CSS addresses at least 80% of design issues identified in feedback
- **SC-003**: 95% of generated CSS passes validation without syntax errors
- **SC-004**: All generated CSS maintains PDF/print compatibility when resume is rendered
- **SC-005**: Section reordering preserves 100% of original content without modification
- **SC-006**: Theme recommendations include installation instructions for all suggested themes
- **SC-007**: Preview screenshots accurately represent final rendered output
- **SC-008**: Design modifications can be rolled back within 30 seconds using backup files
- **SC-009**: Users require zero CSS knowledge to apply design improvements successfully
- **SC-010**: Generated CSS follows consistent naming conventions (BEM) for maintainability

## Assumptions

- Design feedback from agents contains specific, actionable issues (not vague subjective opinions)
- Users have Quarto installed and configured for resume rendering
- Resume source files are valid QMD (Quarto Markdown) format
- Users have write permissions to output directories for CSS and backup files
- Screenshot capability (via Playwright or similar) is available for preview generation
- Resume uses standard Quarto themes or custom themes following Quarto conventions
- Users prefer minimal CSS changes over comprehensive redesigns
- PDF rendering uses Quarto's standard PDF engine (not custom LaTeX configurations)

## Out of Scope

- Interactive WYSIWYG editor for real-time design adjustments
- AI-generated resume content or text modifications (only visual/structural changes)
- Design modifications for non-resume document types
- Automated A/B testing of different design variations
- Integration with external design tools (Figma, Sketch, etc.)
- Custom theme development from scratch
- Accessibility auditing beyond color contrast (screen reader compatibility, etc.)
- Multi-page layout optimization (assumes single-page resume format)
- Responsive design for mobile devices (focus on desktop/print layout)

## Dependencies

- Existing design review agents (UX Designer, Visual Designer) must provide structured feedback
- Screenshot service (Playwright) must be functional for preview generation
- Quarto rendering pipeline must be operational for theme validation
- File system write access for CSS output, backups, and configuration updates
- Revision service for applying section reordering to QMD content

## Notes

- CSS generation uses conservative defaults to avoid breaking existing layouts
- Preview mode is recommended workflow for first-time users building trust
- Section reordering is opt-in via separate flag to prevent unexpected content moves
- Theme recommendations are advisory only - application requires manual user action
- All design modifications maintain single source of truth in resume QMD file
- Generated CSS uses comments extensively for transparency and maintainability
