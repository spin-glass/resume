# Verification Governance

## Purpose
Ensure that all implemented features are verified for functionality and user experience before considering the task complete.

## Rules

### 1. Mandatory Operation Verification
-   **Rule**: Every implementation task MUST include a verification step.
-   **Guideline**: Do not assume code works just because it builds. Run the application and check.
-   **Methods**:
    -   **Browser Verification**: Use the `browser_subagent` or manual checking to verify UI/UX changes on a running server.
    -   **Automated Tests**: Run existing or new tests (`pnpm test`, `pytest`, etc.).
    -   **Generated Artifacts**: Inspect generated files (PDFs, HTMLs) if applicable.

### 2. Evidence
-   **Rule**: Provide evidence of verification in the `walkthrough.md` or task summary.
-   **Guideline**: Screenshots, logs, or detailed descriptions of what was checked are required.

### 3. Edge Case Handling
-   **Rule**: Consider environment differences (e.g., specific base paths, build modes).
-   **Guideline**: If multiple environments exist (local vs Vercel), verify logic handles them (e.g., `import.meta.env.BASE_URL`).
