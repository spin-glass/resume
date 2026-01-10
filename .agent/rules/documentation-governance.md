---
trigger: model_decision
description: When adding, moving, or modifying markdown files in docs/ or specs/, or when completing a feature development task.
---
# Documentation Governance Rules

These rules ensure that the documentation structure remains clean and compliant with the project's governance model defined in `docs/roadmap.md`.

## 1. Automatic Detection of New Documents

**Action**: Verify compliance of new files and suggest organization if needed.

1.  **Check Compliance**: Verify if the new file falls into one of the 4 allowed categories:
    -   **Guide**: Root (`README.md`, `CLAUDE.md`)
    -   **Roadmap**: `docs/roadmap.md`
    -   **Spec**: `specs/{NNN}-{name}/` (must include `spec.md`, `plan.md`, `tasks.md`)
    -   **Package Doc**: `packages/*/README.md`
    -   *(Product Content `resume/resume-ja.qmd` is also allowed)*

2.  **Evaluate & Suggest**:
    -   **Context Assessment**: Determine if the file appears to be a temporary draft, a quick note, or a permanent specification.
    -   **Decision**:
        -   If it seems to be a **permanent document** placed incorrectly (e.g., a full spec in `docs/`), you **SHOULD** suggest running the `document-consolidation` workflow.
        -   If it seems to be a **WIP draft** or you are unsure, you may ask the user for clarification first.
    -   *Goal*: Prevent chaos without being annoying. Only intervene when the governance structure is clearly being degraded.

## 2. Maintenance of Roadmap

**Action**: Keep the roadmap up-to-date with development progress.

1.  **Check Roadmap**: Check `docs/roadmap.md`.
2.  **Update Status**: If completed features are still listed as "Unstarted", suggest updating the status or archiving them using the consolidation workflow.
