# Feature Specification: Quarto Validation Auto-Retry Loop

**Feature Branch**: `009-quarto-retry-loop`
**Created**: 2026-01-09
**Status**: Draft
**Input**: User description: "Quarto検証失敗時の自動リトライループ機能を実装。検証が失敗した場合、自動的に修正を行い、正常なQMDが生成されるまでループする。"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Automatic Recovery from Validation Failures (Priority: P1)

When the resume review workflow generates a QMD file with Quarto syntax errors, the system automatically detects the errors, generates corrective feedback, and retries the revision process without user intervention until the QMD file passes validation or reaches the maximum retry limit.

**Why this priority**: This is the core functionality that ensures resume quality and eliminates manual intervention. Without this, users must manually inspect error logs and re-run the entire workflow, defeating the purpose of automation.

**Independent Test**: Can be fully tested by intentionally introducing Quarto syntax errors (e.g., standalone `#` symbols) into a resume file, running the review workflow, and verifying that the system automatically corrects the errors within the retry limit.

**Acceptance Scenarios**:

1. **Given** a resume iteration produces a QMD file with a standalone `#` marker, **When** Quarto validation runs, **Then** the system detects the syntax error, creates fix feedback describing the issue, triggers the revisor to apply corrections, and validates the corrected file
2. **Given** validation fails on the first retry, **When** the system applies corrections, **Then** it re-validates the corrected QMD and continues retrying up to the maximum retry limit
3. **Given** validation succeeds after 2 retries, **When** the workflow continues, **Then** the system logs the successful validation, saves the corrected QMD file, and proceeds to the next iteration
4. **Given** validation fails after all retries are exhausted, **When** the maximum retry limit is reached, **Then** the system logs a final error, saves all retry attempts for debugging, and either exits gracefully or continues based on strict validation settings

---

### User Story 2 - Transparent Retry Visibility (Priority: P2)

Users can review detailed logs showing each validation attempt, the specific errors detected, corrections applied, and whether validation ultimately succeeded or failed.

**Why this priority**: While automatic retry is the primary value, transparency builds user trust and enables debugging when automatic corrections fail. This is secondary because the system should work without users needing to inspect logs in most cases.

**Independent Test**: Can be tested by running a workflow with validation failures, then checking that a retry log file exists with timestamped entries for each attempt, error descriptions, and final outcomes.

**Acceptance Scenarios**:

1. **Given** the system performs 3 validation retries, **When** a user inspects the retry log file, **Then** they see timestamped entries for each attempt with error messages, corrections applied, and validation results
2. **Given** validation succeeds on retry 2, **When** the workflow completes, **Then** the summary report shows the total number of retries and final success status
3. **Given** validation fails after all retries, **When** the user reviews the logs, **Then** they can identify which specific Quarto errors could not be automatically corrected

---

### User Story 3 - Configurable Retry Behavior (Priority: P3)

Users can configure the maximum number of validation retries and choose whether validation failures should terminate the workflow or continue with warnings.

**Why this priority**: Configuration provides flexibility for different use cases (strict CI/CD pipelines vs. exploratory development), but default settings should work for most users without customization.

**Independent Test**: Can be tested by running the workflow with `--max-validation-retries=1` and verifying only 1 retry occurs, then running with `--strict-validation` and verifying the workflow exits on validation failure.

**Acceptance Scenarios**:

1. **Given** a user sets `--max-validation-retries=5`, **When** validation fails, **Then** the system retries up to 5 times instead of the default 3
2. **Given** a user enables `--strict-validation`, **When** all retries are exhausted, **Then** the workflow terminates with a non-zero exit code
3. **Given** strict validation is disabled (default), **When** retries are exhausted, **Then** the workflow logs a warning but continues to completion

---

### Edge Cases

- What happens when Quarto validation times out during a retry attempt?
- How does the system handle Quarto errors that cannot be parsed into structured feedback (e.g., cryptic internal errors)?
- What happens if the revisor introduces new validation errors while fixing previous ones?
- How does the system prevent infinite loops if corrections repeatedly fail validation in the same way?
- What happens if the maximum retry limit is set to 0?
- How are retry artifacts (intermediate QMD files) cleaned up or preserved for debugging?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST validate QMD content using Quarto render after each resume revision iteration
- **FR-002**: System MUST parse Quarto error messages to identify specific syntax issues (e.g., invalid headers, YAML errors, unclosed code blocks)
- **FR-003**: System MUST generate structured feedback objects from Quarto validation errors that describe the issue, severity, and recommended action
- **FR-004**: System MUST trigger the revisor node with validation feedback when Quarto validation fails
- **FR-005**: System MUST re-validate the corrected QMD file after each revision attempt
- **FR-006**: System MUST retry validation and correction up to a configurable maximum number of times (default: 3)
- **FR-007**: System MUST save each retry attempt as a separate QMD file for debugging (e.g., `resume_retry1.qmd`, `resume_retry2.qmd`)
- **FR-008**: System MUST log each validation attempt with timestamp, error details, corrections applied, and validation result
- **FR-009**: System MUST create a retry log file containing the complete history of validation attempts for each iteration
- **FR-010**: System MUST terminate the retry loop when validation succeeds or maximum retries are exhausted
- **FR-011**: System MUST support configuration of maximum retry attempts via CLI option and settings file
- **FR-012**: System MUST support strict validation mode where workflow exits on validation failure after all retries
- **FR-013**: System MUST distinguish between validation feedback and normal agent feedback in the revisor node
- **FR-014**: System MUST recognize common Quarto error patterns including standalone `#` markers, YAML syntax errors, unclosed code blocks, and invalid markdown tables
- **FR-015**: System MUST prevent infinite retry loops by enforcing the maximum retry limit

### Key Entities

- **ValidationResult**: Represents the outcome of a Quarto validation attempt, containing success/failure status, error message, and timestamp
- **ValidationFeedback**: Structured feedback generated from Quarto errors, containing issues list, severity levels, and recommended actions for the revisor
- **RetryAttempt**: Record of a single retry iteration, including attempt number, error detected, correction applied, and validation outcome
- **RetryLog**: Aggregated log of all retry attempts for a single resume iteration, used for transparency and debugging

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: When Quarto validation fails, the system automatically corrects the errors and achieves validation success within 3 retries in at least 90% of cases
- **SC-002**: Users no longer need to manually inspect validation error files or re-run the workflow for common Quarto syntax errors
- **SC-003**: The system prevents invalid QMD files from being marked as final resume output
- **SC-004**: Retry logs provide sufficient detail for users to understand and debug validation failures that could not be automatically corrected
- **SC-005**: The retry mechanism adds no more than 30 seconds of overhead per validation failure
- **SC-006**: Configuration options allow users to customize retry behavior for their specific workflows without code changes

## Assumptions *(mandatory)*

- Quarto is installed and accessible via command line in the execution environment
- The existing QuartoValidator service (#7) is functional and returns structured error messages
- The revisor node can accept and process validation-specific feedback in addition to normal agent feedback
- Common Quarto syntax errors (standalone `#`, YAML errors, unclosed code blocks) have predictable error message patterns that can be parsed
- Most validation errors can be corrected within 3 retry attempts (configurable default)
- Users running the workflow have write permissions to save retry artifacts and log files
- The retry mechanism should be transparent to users who don't need to inspect logs in normal cases
- Strict validation mode is opt-in, with the default behavior allowing workflows to continue with warnings

## Dependencies *(mandatory)*

- **Feature #7 (Quarto Syntax Validation)**: This feature extends the existing QuartoValidator service to add retry logic
- **Existing Workflow Architecture**: Requires integration points in the workflow runner to inject validation retry loops after revisor node execution
- **Revisor Node**: Must support processing validation feedback alongside normal agent feedback
- **Feedback and Issue Models**: Uses existing data structures for representing issues and feedback

## Out of Scope *(mandatory)*

- Fixing Quarto errors unrelated to syntax (e.g., missing dependencies, file system permissions)
- Validating PDF or HTML rendering quality (only syntax validation is in scope)
- User interface for visualizing retry attempts (CLI logs and file-based logs only)
- Machine learning-based error prediction or prevention
- Integration with external validation services beyond Quarto's built-in validator
- Rollback mechanisms to restore previous valid QMD versions
- Real-time validation during editing (only post-iteration validation)
