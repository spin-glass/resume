# Implementation Plan: Design Auto-Fix

**Branch**: `013-design-auto-fix` | **Date**: 2026-01-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/013-design-auto-fix/spec.md`

## Summary

Implement automated design modification system that analyzes design feedback from UX and Visual Designer agents and generates CSS modifications, section reordering, and theme recommendations to improve resume visual quality without requiring CSS expertise from users.

**Primary Requirements**:
- Generate targeted CSS from design feedback (spacing, typography, color, hierarchy)
- Preview design changes with before/after screenshots
- Reorder QMD sections based on UX feedback while preserving content
- Recommend alternative Quarto themes with configuration

**Technical Approach** (from research):
- New agent: `CSSGeneratorAgent` for translating design issues to CSS rules
- LLM-powered CSS generation with validation and print media support
- Integration with existing workflow via new StateGraph nodes
- Leverage existing screenshot service (Playwright) for preview generation
- CSS custom properties (--variables) for maintainability and user overrides

## Technical Context

**Language/Version**: Python 3.13 (matching existing resume-review package)
**Primary Dependencies**:
- LangGraph 1.0.0+ (existing workflow framework)
- Anthropic/Google Genai/OpenAI (existing multi-provider LLM support)
- Playwright 1.40.0+ (existing screenshot capability)
- Pydantic 2.0+ (existing data modeling)
- cssutils (new - for CSS validation)
- Quarto CLI (existing - for theme validation and rendering)

**Storage**: File system (CSS output files, backups, screenshots)
**Testing**: pytest 7.4.0+, pytest-asyncio 0.21.0+ (existing test framework)
**Target Platform**: macOS/Linux command-line tool (existing platform)
**Project Type**: Single Python package within monorepo (packages/resume-review/)
**Performance Goals**:
- CSS generation: <5 seconds per iteration
- Preview screenshot generation: <10 seconds total
- Section reordering: <2 seconds

**Constraints**:
- Must preserve YAML frontmatter in all QMD modifications
- Generated CSS must maintain PDF/print compatibility
- File modifications require atomic operations with backup/rollback
- No breaking changes to existing CLI or workflow

**Scale/Scope**:
- ~5 new Python modules (~500-800 LOC total)
- 3 new StateGraph nodes
- 1 new agent class
- Integration with existing 5-agent workflow
- CLI extension: 3 new flags

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Single Source of Truth
**Status**: ✅ PASS

- Feature maintains `resume/resume-ja.qmd` as canonical source
- CSS modifications are generated externally in `styles/resume-custom.css`
- Section reordering modifies QMD file but preserves all content
- No direct editing of generated PDF/HTML/MDX outputs

**Justification**: Design modifications either (1) generate external CSS files that augment but don't replace QMD source, or (2) reorder sections within QMD while keeping it as single source.

### Principle II: Automated Generation
**Status**: ✅ PASS

- All CSS generation is automated via `CSSGeneratorAgent`
- Preview screenshots generated via existing automated Playwright service
- Theme recommendations provide automated `_quarto.yml` configuration
- Section reordering is programmatic, not manual editing

**Justification**: Feature fully automates design modification pipeline. Users trigger via CLI flags; all generation is scripted.

### Principle III: Preview-First Workflow
**Status**: ✅ PASS with Extension

- Feature adds `--design-preview` flag for before/after screenshot generation
- Preview mode generates changes without modifying files (dry-run for design)
- Existing `--dry-run` flag continues to work for text review
- Users can validate design changes before application

**Justification**: Extends preview-first principle to design domain. Recommended workflow: `--design-preview` → review → `--auto-design`.

### Principle IV: Deployment Simplicity
**Status**: ✅ PASS

- No changes to deployment process
- Generated CSS/reordered QMD files commit via standard git workflow
- Vercel auto-deploy continues to work unchanged

**Justification**: Feature operates within existing deployment pipeline.

### Principle V: Toolchain Consistency
**Status**: ✅ PASS with Addition

- Adds `cssutils` library for CSS validation (minor addition)
- Continues using Quarto CLI for rendering and theme validation
- No changes to LuaLaTeX, fonts, or core toolchain
- New dependency is Python-only (no system-level changes)

**Justification**: Minimal toolchain addition (CSS validator) aligns with Python ecosystem. No system-level dependencies added.

### Summary
**Overall**: ✅ ALL CHECKS PASS

No constitution violations. Feature extends existing automation capabilities while respecting all core principles. Preview-first workflow is enhanced (not violated) by design preview capability.

## Project Structure

### Documentation (this feature)

```text
specs/013-design-auto-fix/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── css-generator-agent.md     # CSSGeneratorAgent interface
│   ├── design-nodes.md            # StateGraph node contracts
│   └── cli-extensions.md          # New CLI flags and behavior
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
packages/resume-review/
├── src/
│   ├── agents/
│   │   ├── base.py                      # (existing)
│   │   ├── visual_designer.py           # (existing)
│   │   ├── ux_designer.py               # (existing)
│   │   └── css_generator.py             # NEW - CSS generation agent
│   │
│   ├── models/
│   │   ├── feedback.py                  # (existing)
│   │   └── design.py                    # NEW - Design-specific models
│   │                                    #   - CSSModification
│   │                                    #   - SectionReorder
│   │                                    #   - ThemeRecommendation
│   │                                    #   - DesignPreview
│   │                                    #   - DesignIssueType (enum)
│   │
│   ├── services/
│   │   ├── llm_client.py                # (existing)
│   │   ├── llm_factory.py               # (existing)
│   │   ├── screenshot.py                # (existing)
│   │   ├── css_service.py               # NEW - CSS file operations
│   │   ├── section_reorder.py           # NEW - QMD section manipulation
│   │   └── theme_recommender.py         # NEW - Theme analysis
│   │
│   ├── workflow/
│   │   ├── state.py                     # MODIFY - Add design-related state fields
│   │   ├── nodes/
│   │   │   ├── supervisor.py            # (existing)
│   │   │   ├── design.py                # (existing - design review node)
│   │   │   └── design_applier.py        # NEW - Apply design modifications
│   │   └── graph.py                     # MODIFY - Add design applier node
│   │
│   ├── config/
│   │   ├── prompts.py                   # MODIFY - Add CSS generator prompt
│   │   └── settings.py                  # MODIFY - Add design-related settings
│   │
│   └── cli.py                           # MODIFY - Add CLI flags
│
└── tests/
    ├── unit/
    │   ├── agents/
    │   │   └── test_css_generator.py    # NEW
    │   ├── services/
    │   │   ├── test_css_service.py      # NEW
    │   │   └── test_section_reorder.py  # NEW
    │   └── models/
    │       └── test_design.py           # NEW
    └── integration/
        └── test_design_workflow.py      # NEW - End-to-end design workflow

styles/                                  # NEW - CSS output directory
└── resume-custom.css                    # Generated CSS file
```

**Structure Decision**: Extending existing monorepo package structure (`packages/resume-review/`) rather than creating separate package. Design auto-fix is tightly coupled with existing review workflow (depends on design agent feedback, integrates with StateGraph, shares CLI). New components follow established patterns: agents in `agents/`, services in `services/`, models in `models/`, workflow nodes in `workflow/nodes/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - All constitution checks passed. No violations to justify.
