# Feature Specification: Resume Review Multi-Agent System

**Feature Branch**: `001-resume-review-agents`
**Created**: 2026-01-08
**Status**: Draft
**Input**: User description: "CLI tool using multi-agent workflow to automatically review and improve resumes for high-value contract positions (110-140万円/month)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Content Review and Improvement (Priority: P1)

As a freelance engineer seeking high-value contracts, I want my resume content automatically reviewed and improved so that it better matches what recruiters for 100万円+ LLM/AI positions are looking for.

**Why this priority**: Content is the foundation - without compelling, well-structured content that highlights relevant skills and experience, visual improvements are meaningless. This delivers immediate value by improving resume quality.

**Independent Test**: Can be fully tested by running the review command on a sample QMD file and verifying the output contains structured feedback and content improvements.

**Acceptance Scenarios**:

1. **Given** a resume QMD file with basic content, **When** I run the review command, **Then** the system provides scored feedback from multiple perspectives (recruiter, technical writer, copywriter) with specific improvement suggestions.

2. **Given** feedback identifies missing high-value skills (e.g., LangGraph, RAG), **When** the system cannot find evidence in work experience, **Then** it suggests adding a portfolio project to demonstrate the skill rather than fabricating experience.

3. **Given** the content review identifies issues, **When** the system applies revisions, **Then** it adds taglines, restructures content for emphasis, and quantifies achievements where possible.

4. **Given** content has been revised, **When** the review score meets the threshold (default 8.0/10), **Then** the content phase completes and outputs the improved QMD.

---

### User Story 2 - Portfolio Gap Analysis (Priority: P2)

As a freelance engineer, I want the system to identify skills I'm missing for high-value positions and suggest specific portfolio projects I can create to fill those gaps.

**Why this priority**: High-value contracts (120万円+) require specific skills like LangGraph, RAG evaluation, and MLOps. If these aren't in work experience, portfolio projects provide credible evidence of capability.

**Independent Test**: Can be tested by providing a resume lacking specific target skills and verifying the system outputs portfolio recommendations with consistent naming and URL patterns.

**Acceptance Scenarios**:

1. **Given** a resume lacking LangGraph experience, **When** reviewed against 100万円+ position requirements, **Then** the system suggests a specific portfolio project (e.g., "langgraph-multi-agent") with GitHub and demo URLs.

2. **Given** multiple skill gaps are identified, **When** generating portfolio suggestions, **Then** each portfolio follows the naming convention `{technology}-{type}` with consistent URL patterns.

3. **Given** portfolio suggestions are accepted, **When** revisions are applied, **Then** a portfolio section is added to the resume with properly formatted links.

---

### User Story 3 - Visual Design Review (Priority: P3)

As a freelance engineer, I want my resume's visual presentation reviewed to ensure it makes a strong first impression and is easy to scan quickly.

**Why this priority**: Visual presentation matters for first impressions, but only after content is solid. Recruiters spend seconds on initial screening, so clear visual hierarchy is important but secondary to content quality.

**Independent Test**: Can be tested by providing a resume HTML screenshot and verifying the system returns UX and visual design feedback.

**Acceptance Scenarios**:

1. **Given** a resume with generated HTML, **When** I run the full review with screenshot capture, **Then** the system evaluates visual hierarchy, scannability, and professional appearance.

2. **Given** visual issues are identified (e.g., poor information hierarchy, missing CTAs), **When** revisions are suggested, **Then** they focus on structural changes that can be made in the QMD source.

3. **Given** design review completes, **When** score meets threshold, **Then** the system outputs a summary of all changes across both content and design phases.

---

### User Story 4 - Dry Run Preview (Priority: P4)

As a user, I want to preview what changes the system would make without actually modifying my resume file, so I can review suggestions before committing to them.

**Why this priority**: Users need control over changes to their professional documents. Dry run capability builds trust and allows informed decision-making.

**Independent Test**: Can be tested by running with dry-run flag and verifying no file modifications occur while still receiving full feedback.

**Acceptance Scenarios**:

1. **Given** I run the review with `--dry-run` flag, **When** the review completes, **Then** I see all feedback and suggested changes but my original file remains unmodified.

2. **Given** dry-run output shows proposed changes, **When** I review the suggestions, **Then** I can decide whether to run the full review to apply changes.

---

### Edge Cases

- What happens when the QMD file has invalid YAML frontmatter?
  - System reports a clear error message and exits without making changes.

- What happens when the resume already scores above threshold?
  - System reports the score and confirms no changes needed.

- What happens when network connectivity to AI service is lost mid-review?
  - System preserves original file, reports error, and allows retry.

- What happens when screenshot URL is provided but the development server is not running?
  - System completes content review phase and warns that design phase was skipped.

- What happens when maximum iterations are reached without meeting threshold?
  - System outputs best effort revision and reports final score with explanation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a QMD file path as input and validate it exists and is readable.
- **FR-002**: System MUST evaluate resume content from three perspectives: recruiter appeal, technical depth, and marketing effectiveness.
- **FR-003**: System MUST produce a numerical score (1-10) for each evaluation perspective with specific strengths and issues identified.
- **FR-004**: System MUST integrate individual scores using weighted averaging to produce an overall score.
- **FR-005**: System MUST iterate on revisions until the integrated score meets a configurable threshold (default 8.0) or maximum iterations (default 3) are reached.
- **FR-006**: System MUST identify skill gaps compared to target role requirements (default: "LLM/Multi-Agent Engineer").
- **FR-007**: System MUST suggest portfolio projects for skills not evidenced in work experience, following consistent naming conventions.
- **FR-008**: System MUST never fabricate work experience or add untrue claims to the resume.
- **FR-009**: System MUST preserve the QMD file's YAML frontmatter when making revisions.
- **FR-010**: System MUST support a dry-run mode that shows proposed changes without modifying files.
- **FR-011**: System MUST output a summary of all changes made, final scores, and any portfolio projects to be created.
- **FR-012**: System MUST support verbose mode for detailed progress output during execution.
- **FR-013**: System SHOULD evaluate visual design when a screenshot URL is provided, assessing first-view impact and information hierarchy.
- **FR-014**: System SHOULD capture screenshots automatically using a headless browser when screenshot URL is specified.

### Key Entities

- **Resume**: The QMD document being reviewed, containing professional experience, skills, and portfolio sections.
- **Feedback**: Evaluation output from a single perspective, including score, strengths, issues, and improvement suggestions.
- **Issue**: A specific problem identified during review, categorized by action type (add content, add portfolio, restructure, emphasize).
- **Portfolio Item**: A suggested project to demonstrate a skill, with repository name, associated skills, and generated URLs.
- **Review Session**: The complete workflow from input to output, tracking iterations, score progression, and applied changes.

## Assumptions

- User has a working QMD file with valid Quarto/Markdown syntax.
- User has access to an AI service API key for the evaluation agents.
- Portfolio projects suggested are assumed to be buildable quickly ("vibe coding" approach mentioned in source).
- Target role and skill requirements are based on Japanese freelance market for LLM/AI positions (100-140万円/month range).
- Score weights prioritize recruiter perspective (30%) and marketing impact (25%) as most important for contract acquisition.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete a full content review cycle in under 5 minutes.
- **SC-002**: 80% of reviewed resumes improve their integrated score by at least 1.5 points after revision.
- **SC-003**: Users report that suggested improvements align with their actual experience (no fabricated claims) in 100% of cases.
- **SC-004**: Portfolio suggestions follow consistent naming patterns and produce valid GitHub/demo URLs in 100% of cases.
- **SC-005**: Dry-run mode accurately predicts all changes that would be made in a live run.
- **SC-006**: Users can understand the reasoning behind each suggested change from the feedback output.
- **SC-007**: System completes review without data loss or file corruption in 100% of runs.
