# Feature Specification: Monorepo Refactor - Repository Architecture Reorganization

**Feature Branch**: `002-monorepo-refactor`
**Created**: 2026-01-09
**Status**: Draft
**Input**: User description: "リポジトリ全体のディレクトリ構成・アーキテクチャ整理" (Repository-wide directory structure and architecture reorganization)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Developer Navigates Repository Structure (Priority: P1)

As a developer, I want the repository structure to clearly separate different packages (Web app, Python AI tools, Resume source) so that I can quickly find and work on the relevant component.

**Why this priority**: Clear separation of concerns is the foundation for all other improvements. Without a logical structure, developers waste time navigating and understanding the codebase.

**Independent Test**: Can be verified by checking that a new developer can identify where to make changes for a specific component within 2 minutes of examining the structure.

**Acceptance Scenarios**:

1. **Given** the repository root, **When** I look at the top-level directories, **Then** I can immediately identify three distinct packages: web application, AI review tool, and resume source files
2. **Given** I need to modify the resume content, **When** I search for the source file, **Then** I find it in a dedicated `resume/` directory at the project root
3. **Given** I need to modify the AI agents, **When** I navigate to the packages directory, **Then** I find a clearly named package with its own configuration files

---

### User Story 2 - Developer Runs Package-Specific Commands (Priority: P2)

As a developer, I want to run package-specific commands from the repository root so that I can manage all packages without changing directories.

**Why this priority**: Efficient development workflow depends on easy command access. Once structure is clear, commands need to work seamlessly.

**Independent Test**: Run `pnpm dev`, `pnpm review`, and `pnpm quarto:pdf` from root directory and verify each executes correctly.

**Acceptance Scenarios**:

1. **Given** I am at the repository root, **When** I run a web development command, **Then** the web application starts from its package location
2. **Given** I am at the repository root, **When** I run a review command, **Then** the AI review tool executes against the resume
3. **Given** I am at the repository root, **When** I run a Quarto build command, **Then** PDF output is generated in the designated output directory

---

### User Story 3 - Developer Adds New Package (Priority: P3)

As a developer, I want to add new packages to the monorepo so that I can extend functionality while maintaining consistent structure.

**Why this priority**: Future extensibility ensures the architecture scales. After basic structure and commands work, supporting growth becomes important.

**Independent Test**: Add a new test package to `packages/` directory and verify it integrates with workspace commands.

**Acceptance Scenarios**:

1. **Given** I create a new package in the packages directory, **When** I update the workspace configuration, **Then** the new package is recognized by pnpm
2. **Given** a new package exists, **When** I run workspace-wide commands, **Then** the new package is included in operations

---

### User Story 4 - Developer Maintains Workflow Module (Priority: P4)

As a developer maintaining the AI review system, I want the workflow code split into manageable files so that I can understand and modify specific parts without reading hundreds of lines.

**Why this priority**: Maintainability within packages improves developer velocity. After overall structure is set, internal organization becomes valuable.

**Independent Test**: Verify that workflow logic is distributed across multiple files, each under 200 lines, and all tests pass.

**Acceptance Scenarios**:

1. **Given** I need to modify the aggregator logic, **When** I look for the relevant code, **Then** I find it in a dedicated node file under `workflow/nodes/`
2. **Given** I need to add a new conditional edge, **When** I look for condition functions, **Then** I find them in a dedicated `conditions.py` file
3. **Given** I modify one node file, **When** I run the test suite, **Then** only relevant tests are affected

---

### User Story 5 - Resume Output Files Organized (Priority: P5)

As a user generating resume outputs, I want all generated files (PDF, HTML) in a dedicated output directory so that I can easily find and share them.

**Why this priority**: Output organization is a quality-of-life improvement that becomes valuable once core structure is in place.

**Independent Test**: Run resume generation and verify outputs appear in `resume/output/` directory.

**Acceptance Scenarios**:

1. **Given** I run the PDF generation command, **When** the build completes, **Then** the PDF appears in `resume/output/resume-ja.pdf`
2. **Given** multiple output formats exist, **When** I list the output directory, **Then** all generated files are organized by format and language

---

### Edge Cases

- What happens when a package has dependencies on another package in the monorepo?
  - Workspace dependencies should be properly linked via pnpm workspace protocol
- How does the system handle relative paths that reference the old structure?
  - All scripts and configurations must be updated to use new paths
- What happens if the web package cannot find resume content after migration?
  - The sync script and paths must be updated to reference new locations
- How does the system handle incomplete migrations?
  - Migration should be atomic per phase; rollback via git if phase fails

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Repository MUST have a `packages/` directory containing all workspace packages
- **FR-002**: Repository MUST have a `resume/` directory at root level containing resume source files
- **FR-003**: Resume source file MUST be located at `resume/resume-ja.qmd`
- **FR-004**: Resume outputs MUST be generated to `resume/output/` directory
- **FR-005**: Web application package MUST be located at `packages/web/`
- **FR-006**: AI review tool package MUST be located at `packages/resume-review/`
- **FR-007**: Root `package.json` MUST include scripts to run commands for each package from root
- **FR-008**: pnpm workspace configuration MUST recognize all packages under `packages/`
- **FR-009**: Workflow code in resume-review package MUST be split into separate files, each under 200 lines
- **FR-010**: Workflow nodes MUST be organized in `workflow/nodes/` directory with one file per node type
- **FR-011**: Workflow state definitions MUST be in `workflow/state.py`
- **FR-012**: Workflow graph construction MUST be in `workflow/graph.py`
- **FR-013**: Workflow condition functions MUST be in `workflow/conditions.py`
- **FR-014**: Package configurations (settings, prompts, weights) MUST be centralized in `config/` directory
- **FR-015**: All existing tests MUST pass after migration
- **FR-016**: CLI interface MUST remain compatible with existing commands
- **FR-017**: Web application MUST start successfully from new location
- **FR-018**: Resume PDF/HTML generation MUST work with new file paths

### Key Entities

- **Workspace Package**: A self-contained module with its own configuration files (`package.json` for Node.js, `pyproject.toml` for Python), located under `packages/`
- **Resume Source**: The authoritative Quarto markdown file containing resume content, located in `resume/` directory
- **Resume Output**: Generated files (PDF, HTML) from resume source, located in `resume/output/`
- **Workflow Node**: A discrete function handling one step in the AI review process, located in `workflow/nodes/`
- **Configuration**: Centralized settings, prompts, and scoring weights for the AI review tool, located in `config/`

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new developer can identify where to make changes for any component within 2 minutes of examining the repository structure
- **SC-002**: All package-specific commands execute successfully from the repository root
- **SC-003**: No single Python file in the workflow module exceeds 200 lines of code
- **SC-004**: Test suite passes with 100% of existing tests succeeding after migration
- **SC-005**: Web application loads successfully with no broken references
- **SC-006**: Resume PDF generation completes successfully with output in designated directory
- **SC-007**: All existing functionality works without requiring users to learn new command interfaces

## Assumptions

- pnpm is the package manager and workspace feature is available
- The current functionality is working correctly before migration begins
- Git version control allows rollback if any phase fails
- No changes to external APIs or service integrations are needed
- Python virtual environment setup will be preserved in the new package location
- The migration can be done incrementally by phase without breaking functionality between phases
