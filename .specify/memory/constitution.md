<!--
## Sync Impact Report

**Version change**: 0.0.0 → 1.0.0 (Initial ratification)

### Modified Principles
- N/A (initial version)

### Added Sections
- Core Principles (5 principles)
- Quality Standards section
- Development Workflow section
- Governance section

### Removed Sections
- N/A (initial version)

### Templates Requiring Updates
- `.specify/templates/plan-template.md`: ✅ No changes needed (Constitution Check section already references constitution)
- `.specify/templates/spec-template.md`: ✅ No changes needed (technology-agnostic)
- `.specify/templates/tasks-template.md`: ✅ No changes needed (generic task structure)

### Follow-up TODOs
- None
-->

# Resume Project Constitution

## Core Principles

### I. Single Source of Truth

`resume/resume-ja.qmd` is the sole canonical source for all resume content. All output formats (PDF, HTML, MDX) MUST be generated from this file. Direct editing of generated files is prohibited.

**Rationale**: Eliminates content drift between formats and ensures consistency across all published versions.

### II. Automated Generation

All output formats MUST be produced via automated scripts (`pnpm resume:build`). Manual creation or modification of generated artifacts (`resume/output/resume-ja.pdf`, `resume/output/resume-ja.html`, `packages/web/pages/ja/index.mdx`) is prohibited.

**Build pipeline**:
- QMD → PDF via Quarto + LuaLaTeX
- QMD → HTML via Quarto
- QMD → MDX via sync script

**Rationale**: Guarantees reproducibility and prevents accidental overwrites of generated content.

### III. Preview-First Workflow

Changes MUST be verified via live preview (`pnpm quarto:preview:html` or `pnpm quarto:preview`) before running the full build. Committing untested changes is prohibited.

**Rationale**: Catches formatting issues and content errors early, reducing broken deployments.

### IV. Deployment Simplicity

Deployment MUST occur via `git push` triggering Vercel auto-deploy. Manual deployment steps, custom CI scripts, or platform-specific commands are prohibited unless absolutely necessary.

**Rationale**: Minimizes deployment friction and human error; leverages platform automation.

### V. Toolchain Consistency

The project MUST use the documented toolchain: Quarto CLI, LuaLaTeX (TeX Live), and Hiragino Mincho Pro font. Changes to the toolchain require updating README requirements and testing across all output formats.

**Rationale**: Ensures local and CI environments produce identical outputs; prevents "works on my machine" issues.

## Quality Standards

### Content Quality

- Resume content MUST be factually accurate and up-to-date
- All dates, company names, and role titles MUST match official records
- Links MUST be verified before each deployment

### Output Quality

- PDF MUST render correctly with proper Japanese typography
- HTML MUST display consistently across modern browsers
- MDX MUST integrate seamlessly with Nextra theme

### Accessibility

- Generated HTML SHOULD follow WCAG 2.1 AA guidelines where feasible
- PDF SHOULD maintain readable text structure

## Development Workflow

### Change Process

1. Edit `resume-ja.qmd` only
2. Preview changes via `pnpm quarto:preview:html`
3. Run full build via `pnpm resume:build`
4. Verify all outputs (PDF, HTML, MDX)
5. Commit and push to trigger deployment

### Dependency Management

- Use `pnpm` for Node.js dependencies
- Document Quarto and TeX Live version requirements in README
- Pin critical dependencies to avoid breaking changes

## Governance

This constitution supersedes all other development practices for the resume project. Amendments require:

1. Documentation of the proposed change
2. Testing across all output formats
3. Update to this constitution file with version increment

All changes to the codebase MUST verify compliance with these principles. Complexity or deviations MUST be justified in the commit message or pull request description.

**Version**: 1.0.0 | **Ratified**: 2026-01-08 | **Last Amended**: 2026-01-08
