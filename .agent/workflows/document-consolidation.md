---
description: Consolidate and organize repository documentation to prevent bloat and duplication.
---
# Document Consolidation Workflow

This workflow guides the process of auditing, organizing, and consolidating project documentation. It is designed to prevent "document bloat" where specifications become outdated, duplicated, or scattered.

## 1. Inventory & Analysis

First, identify all markdown files in the repository to understand the current state.

```bash
# List all markdown files, excluding dependencies and temporary folders
find . -name "*.md" -not -path "./node_modules/*" -not -path "./.venv/*" -not -path "./.git/*" -not -path "./resume/review_*" 2>/dev/null
```

**Analysis Checklist:**
- [ ] Are there large monolithic files (e.g., `future-specs.md`) containing mixed statuses (Completed/Planned)?
- [ ] Are there duplicate files (e.g., `docs/SPEC-xxx.md` vs `specs/xxx/`)?
- [ ] Are there "dead" documents that are no longer accurate or referenced?
- [ ] Do any files violate the [Document Governance](../docs/roadmap.md#ドキュメントガバナンス) rules?

## 2. Archiving Completed Features

If you find a roadmap or spec file containing **Completed** features mixed with future plans:

1.  **Extract Completed Items**: Move the content of completed features to an archive file.
    -   Target: `docs/archive/{original-filename}-{YYYY-MM}.md`
    -   *Example*: `docs/future-specs.md` -> `docs/archive/future-specs-2026-01.md`
2.  **Verify specs/**: Ensure the detailed specifications for these completed features exist in `specs/{NNN}-{name}/`.
    -   If detailed specs exist, the single large roadmap file is redundant for those items.

## 3. Roadmapping Active/Planned Features

For features that are **Unstarted** or **In Progress**:

1.  **Consolidate to Roadmap**: specific active planning should live in `docs/roadmap.md`.
2.  **Link to Specs**: If a feature is complex enough to have started implementation, ensure it lists a link to `specs/{NNN}-{name}/`.

## 4. Deduplication

Remove redundancy to establish a Single Source of Truth (SSOT).

-   **Delete** `docs/SPEC-{feature}.md` if `specs/{feature}/` exists.
    -   *Rule*: `specs/` folder is the master source for functional specifications.
-   **Delete** content from `docs/roadmap.md` if it is fully detailed in a specific `specs/` folder (keep only a summary link).

## 5. Metadata & Content Governance

Verify non-development documents:

-   **Resume Content**: Ensure `resume/resume-ja.qmd` is treated as the SSOT.
    -   Do not edit generated files (`.mdx`, `.html`, `.pdf`) manually.
-   **Templates**: Ensure `.specify/templates/` are used for new files, rather than ad-hoc copying.

## 6. Final Review

1.  Update `docs/roadmap.md` status table.
2.  Run `git status` to ensure `docs/archive/` and deletions are staged correctly.
3.  Commit with a clear message: `docs: consolidate documentation and archive completed specs`
