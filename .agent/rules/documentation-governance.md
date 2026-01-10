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

**Trigger**: When a feature branch is merged or a feature is marked as complete.

**Action**: You MUST perform ALL of the following updates to `docs/roadmap.md`:

### Required Updates Checklist

1. **Update Status Summary Table** (top of file)
   - Change status from `🔵 未着手` or `🟡 進行中` to `✅ 完了`

2. **Remove from "未着手機能" Section**
   - Delete the entire subsection (e.g., `### 13. Feature Name` and all its content)
   - ⚠️ This is the most commonly missed step!

3. **Add to "完了済み機能" Table**
   - Add a new row with: `| # | 機能名 | 完了日 | specs フォルダ |`
   - Use today's date for 完了日

4. **Update Last Modified Date**
   - Update `**最終更新**:` at the top of the file

### Verification

Before completing the task, verify:
- [ ] Feature is NOT in "未着手機能" section
- [ ] Feature IS in "完了済み機能" table
- [ ] Status summary shows `✅ 完了`
- [ ] Last modified date is current
