# Implementation Plan: Job Personalization

**Branch**: `010-job-personalization` | **Date**: 2026-01-09 | **Spec**: [spec.md](./spec.md)

## Summary

Extend the multi-agent resume review system to accept job descriptions (via file or URL) and personalize all feedback, scoring, and recommendations to match specific job requirements. This includes parsing job postings, extracting structured requirements, calculating match scores, identifying skill gaps, and integrating personalized context into all agent evaluations.

## Technical Context

**Language/Version**: Python 3.13 (existing project requirement)
**Primary Dependencies**:
- LangGraph >=1.0.0 (workflow orchestration)
- Anthropic SDK >=0.25.0, Google GenAI >=1.0.0, OpenAI >=1.0.0 (multi-model LLM)
- Pydantic >=2.0.0 (data validation)
- python-frontmatter >=1.0.0 (QMD parsing)
- requests >=2.31.0 (NEW: HTTP client for URL fetching)
- beautifulsoup4 >=4.12.0 (NEW: HTML parsing)

**Storage**: File-based (QMD files, session JSON outputs) - no database
**Testing**: pytest >=7.4.0, pytest-asyncio >=0.21.0
**Target Platform**: macOS/Linux CLI tool (existing)
**Project Type**: Single Python package (monorepo structure: `packages/resume-review/`)
**Performance Goals**:
- Job posting parsing: <5 seconds
- Match score calculation: <10 seconds
- Total personalized review: <5 minutes (same as standard review)

**Constraints**:
- Must maintain backward compatibility with existing CLI (no breaking changes)
- Job personalization is optional (existing `--target-role` workflow unchanged)
- No PDF parsing support initially
- No authentication for URL fetching
- No JavaScript execution for dynamic content

**Scale/Scope**:
- Single-user CLI tool
- Processing 1 resume + 1 job posting per invocation
- Job postings: typically 500-2000 words
- ~200 LOC for new data models, ~300 LOC for parsing service, ~150 LOC for CLI changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Gate 1: Single Source of Truth (✅ PASS)
- **Principle**: `resume/resume-ja.qmd` remains the canonical source
- **Impact**: This feature only reads resume content (already parsed via QMD parser) and does not modify the resume generation pipeline
- **Status**: No violation - personalization analyzes existing resume, does not alter source

### Gate 2: Automated Generation (✅ PASS)
- **Principle**: All output formats via automated scripts
- **Impact**: This feature extends the review process (which is analysis/feedback), not the generation process (PDF/HTML/MDX)
- **Status**: No violation - job personalization is part of review, not generation

### Gate 3: Preview-First Workflow (✅ PASS)
- **Principle**: Changes verified via live preview before build
- **Impact**: Review workflow (including personalization) does not modify resume content directly. Revisor agent suggestions are previewed in dry-run mode before applying
- **Status**: No violation - existing dry-run workflow covers this

### Gate 4: Deployment Simplicity (✅ PASS)
- **Principle**: Deployment via `git push` to Vercel
- **Impact**: This is a CLI tool feature, not a web deployment concern. No changes to deployment process
- **Status**: No violation - CLI tool independent of web deployment

### Gate 5: Toolchain Consistency (✅ PASS)
- **Principle**: Quarto CLI, LuaLaTeX, Hiragino font
- **Impact**: This feature extends Python CLI tool, does not alter Quarto/LaTeX toolchain
- **Status**: No violation - new dependencies (requests, beautifulsoup4) are Python-only

**Summary**: All constitution gates passed. No complexity justification required.

## Project Structure

### Documentation (this feature)

```text
specs/010-job-personalization/
├── plan.md              # This file
├── research.md          # Phase 0: Web scraping, LLM parsing patterns
├── data-model.md        # Phase 1: JobPosting, PersonalizationResult models
├── quickstart.md        # Phase 1: Usage examples
├── contracts/           # Phase 1: (N/A - internal Python API, no external contracts)
└── checklists/
    └── requirements.md  # Spec validation (already exists)
```

### Source Code (repository root)

```text
packages/resume-review/
├── src/
│   ├── models/
│   │   ├── feedback.py           # [existing]
│   │   ├── portfolio.py          # [existing]
│   │   ├── session.py            # [existing]
│   │   └── job_posting.py        # [NEW] JobPosting, PersonalizationResult
│   │
│   ├── services/
│   │   ├── llm_client.py         # [existing]
│   │   ├── qmd_parser.py         # [existing]
│   │   └── job_parser.py         # [NEW] Job description parsing
│   │
│   ├── agents/
│   │   ├── base.py               # [MODIFY] Add job_posting parameter to prompts
│   │   ├── recruiter.py          # [MODIFY] Integrate job requirements
│   │   ├── technical_writer.py   # [MODIFY] Integrate job requirements
│   │   ├── copywriter.py         # [MODIFY] Integrate job requirements
│   │   └── personalizer.py       # [NEW] Match score and gap analysis agent
│   │
│   ├── workflow/
│   │   ├── state.py              # [MODIFY] Add job_posting, personalization fields
│   │   ├── nodes/
│   │   │   ├── job_parser.py    # [NEW] Parse job posting node
│   │   │   ├── personalizer.py  # [NEW] Calculate match score node
│   │   │   ├── supervisor.py    # [MODIFY] Pass job_posting to agents
│   │   │   └── aggregator.py    # [MODIFY] Include personalization in output
│   │   ├── graph.py              # [MODIFY] Add new nodes to workflow
│   │   └── runner.py             # [MODIFY] Initialize job_posting in state
│   │
│   ├── config/
│   │   └── prompts.py            # [MODIFY] Add job-aware prompt templates
│   │
│   └── cli.py                    # [MODIFY] Add --job-posting, --job-url options
│
└── tests/
    ├── unit/
    │   ├── test_job_posting_models.py   # [NEW]
    │   └── test_job_parser.py           # [NEW]
    │
    └── integration/
        ├── test_job_personalization.py  # [NEW] End-to-end test
        └── test_job_url_fetching.py     # [NEW] URL parsing test
```

**Structure Decision**: Single Python package structure (existing). This feature extends the existing `packages/resume-review/` package with:
1. New models for job posting data
2. New service for parsing job descriptions
3. New agent for match score calculation
4. Modifications to existing agents to accept job context
5. New workflow nodes for job parsing and personalization

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*N/A - No constitution violations detected.*

---

# Phase 0: Outline & Research

## Research Tasks

### R1: Job Description Parsing Strategies
**Question**: What's the most reliable way to extract structured requirements from unstructured job postings?

**Research Focus**:
1. LLM-based semantic extraction (prompt engineering for section identification)
2. Rule-based section detection (regex patterns for "Requirements", "Qualifications")
3. Hybrid approach: rules + LLM fallback

**Decision Criteria**:
- Accuracy on diverse job posting formats (LinkedIn, Indeed, company sites)
- Cost (LLM tokens vs. computation)
- Maintainability

### R2: HTML Content Extraction from Job URLs
**Question**: How to reliably extract job description text from various job board HTML structures?

**Research Focus**:
1. BeautifulSoup strategies (main content detection, boilerplate removal)
2. Common job board selectors (LinkedIn: `.job-description`, Indeed: `.jobsearch-JobComponent-description`)
3. Fallback strategies for unknown sites (extract all text, filter by length)

**Decision Criteria**:
- Coverage of major job boards (LinkedIn, Indeed, Glassdoor)
- Robustness to HTML structure changes
- Simplicity (no headless browser required)

### R3: Skill Matching and Synonym Handling
**Question**: How to match resume skills against job requirements when wording differs?

**Research Focus**:
1. Exact string matching with normalization (case, spacing)
2. Synonym mapping (manual dictionary: "JS" → "JavaScript", "React.js" → "React")
3. LLM-based semantic similarity (embedding or prompt-based)

**Decision Criteria**:
- Accuracy of matches (minimize false positives/negatives)
- Speed (match score calculation <10 seconds)
- User trust (explainable matches)

### R4: Match Score Calculation Algorithm
**Question**: How to calculate a meaningful 0-100% match score from skill lists?

**Research Focus**:
1. Weighted scoring (required skills: 70%, preferred: 30%)
2. Partial credit for related skills (e.g., Python experience partially covers "scripting")
3. Penalty for major gaps vs. minor gaps

**Decision Criteria**:
- Alignment with user expectations (manual validation)
- Differentiates strong vs. weak matches
- Stable across job types (technical vs. non-technical roles)

### R5: Integration with Existing Agent Prompts
**Question**: How to inject job requirements into agent prompts without breaking existing behavior?

**Research Focus**:
1. Conditional prompt sections (append job context if present)
2. Prompt template versioning (job-aware vs. standard)
3. Testing backward compatibility

**Decision Criteria**:
- Existing tests pass unchanged (no `--job-posting`)
- Personalized feedback explicitly references job requirements
- No prompt bloat (keep under LLM context limits)

---

# Phase 1: Design & Contracts

## Phase 1.1: Data Models

**File**: `specs/010-job-personalization/data-model.md`

### JobPosting Model
- **Purpose**: Store structured job description data
- **Fields**:
  - `title: str` - Job title (e.g., "Senior Backend Engineer")
  - `company: Optional[str]` - Company name (if detected)
  - `required_skills: list[str]` - Must-have skills/qualifications
  - `preferred_skills: list[str]` - Nice-to-have skills
  - `responsibilities: list[str]` - Key job duties
  - `qualifications: list[str]` - Education/experience requirements
  - `salary_range: Optional[str]` - Compensation info (if present)
  - `contract_type: Optional[str]` - Full-time, contract, etc.
  - `raw_text: str` - Original job description (for reference)
  - `source: str` - File path or URL
- **Validation**:
  - At least one of `required_skills` or `responsibilities` must be non-empty
  - `raw_text` cannot be empty

### PersonalizationResult Model
- **Purpose**: Store match analysis results
- **Fields**:
  - `match_score: float` - Overall match (0-100)
  - `required_match_score: float` - Required skills match (0-100)
  - `preferred_match_score: float` - Preferred skills match (0-100)
  - `matched_required_skills: list[str]` - Skills from resume matching required
  - `matched_preferred_skills: list[str]` - Skills from resume matching preferred
  - `missing_required_skills: list[str]` - Critical gaps
  - `missing_preferred_skills: list[str]` - Nice-to-have gaps
  - `emphasis_suggestions: list[str]` - What to highlight in resume
  - `keyword_additions: list[str]` - Terms to naturally incorporate
- **Calculations**:
  - `match_score = (required_match_score * 0.7) + (preferred_match_score * 0.3)`
  - `required_match_score = len(matched_required) / len(required_skills) * 100`

### ReviewState Extensions
- **New Fields**:
  - `job_posting: Optional[JobPosting]` - Parsed job data
  - `personalization_result: Optional[PersonalizationResult]` - Match analysis

## Phase 1.2: API Contracts

*N/A for this feature - internal Python API only. No external REST/GraphQL contracts.*

Internal Python interfaces documented in data-model.md:
- `JobParserService.parse_file(file_path: Path) -> JobPosting`
- `JobParserService.parse_url(url: str) -> JobPosting`
- `PersonalizerAgent.analyze_match(resume: Resume, job: JobPosting) -> PersonalizationResult`

## Phase 1.3: Quickstart Guide

**File**: `specs/010-job-personalization/quickstart.md`

**Contents**:
1. Installation (no new dependencies visible to user - internal only)
2. Basic usage: `resume-review review --input resume.qmd --job-posting job.md`
3. URL usage: `resume-review review --input resume.qmd --job-url "https://..."`
4. Output interpretation: match score, skill gaps, emphasis suggestions
5. Integration with existing options: `--dry-run`, `--save-iterations`, `--verbose`
6. Troubleshooting: common errors (invalid URL, empty file, parsing failures)

## Phase 1.4: Agent Context Update

**Command**: `.specify/scripts/bash/update-agent-context.sh claude`

**Expected Changes**:
- Add "Job Personalization" to active technologies in CLAUDE.md
- Update commands section with new CLI options
- Add note about backward compatibility

---

# Phase 2: Implementation Tasks

*Tasks will be generated via `/speckit.tasks` command after Phase 1 completion.*

**High-Level Task Groups** (for planning reference):

1. **T-GROUP-1: Data Models** (~2 files, 200 LOC)
   - Create `JobPosting` and `PersonalizationResult` Pydantic models
   - Add validation rules
   - Extend `ReviewState` with new optional fields
   - Write unit tests for models

2. **T-GROUP-2: Job Parsing Service** (~1 file, 300 LOC)
   - Implement `JobParserService` with file parsing (text/Markdown)
   - Implement URL fetching with requests + BeautifulSoup
   - Add LLM-based section extraction (structured output prompt)
   - Handle errors gracefully (invalid URLs, empty content)
   - Write unit tests for parsing logic

3. **T-GROUP-3: Personalizer Agent** (~1 file, 250 LOC)
   - Create `PersonalizerAgent` extending `BaseAgent`
   - Implement skill matching logic (with synonym handling)
   - Calculate match scores (required/preferred weighting)
   - Generate emphasis suggestions and keyword additions
   - Write unit tests for matching algorithm

4. **T-GROUP-4: Agent Integration** (~4 files, 150 LOC)
   - Update `BaseAgent.get_system_prompt()` to accept optional `job_posting`
   - Modify `RecruiterAgent`, `TechnicalWriterAgent`, `CopywriterAgent` prompts
   - Add conditional job context sections to prompts
   - Write tests to verify backward compatibility (no job = unchanged output)

5. **T-GROUP-5: Workflow Integration** (~5 files, 200 LOC)
   - Add `job_parser_node` to workflow (parses if `--job-posting` provided)
   - Add `personalizer_node` after aggregator (calculates match score)
   - Update `supervisor_node` to pass `job_posting` to agents
   - Update `aggregator_node` to include personalization in summary
   - Modify `graph.py` to conditionally add personalization nodes
   - Update `runner.py` to initialize job data in state

6. **T-GROUP-6: CLI Updates** (~1 file, 50 LOC)
   - Add `--job-posting` option (click.Path)
   - Add `--job-url` option (string)
   - Validate mutual exclusivity (cannot provide both)
   - Pass job source to workflow runner
   - Update help text and examples

7. **T-GROUP-7: Output Formatting** (~1 file, 100 LOC)
   - Extend session summary to include personalization results
   - Format match score display (visual indicators, color)
   - List matched/missing skills with counts
   - Display emphasis suggestions and keywords
   - Ensure output works in both verbose and standard modes

8. **T-GROUP-8: Testing** (~5 files, 400 LOC)
   - Unit tests: models, parsing, matching algorithm
   - Integration tests: file input, URL input, end-to-end personalization
   - Edge case tests: empty files, invalid URLs, malformed HTML
   - Backward compatibility tests: verify standard review unchanged
   - Performance tests: verify <5 second parsing, <10 second matching

9. **T-GROUP-9: Documentation** (~3 files)
   - Update README with job personalization examples
   - Add troubleshooting guide for common errors
   - Document match score calculation logic
   - Update CLI help text

**Estimated Total**: ~1,650 LOC (including tests)

---

# Dependencies Between Phases

- **Phase 0 → Phase 1**: Research decisions inform data model design (e.g., synonym handling strategy determines `PersonalizationResult` fields)
- **Phase 1 → Phase 2**: Data models and contracts define implementation interfaces
- **T-GROUP-1 → all others**: Models must exist before services/agents can reference them
- **T-GROUP-2 → T-GROUP-3**: Parsing service must exist before personalizer agent can analyze
- **T-GROUP-3 → T-GROUP-5**: Personalizer agent must exist before workflow integration
- **T-GROUP-4 → T-GROUP-5**: Agent modifications must exist before workflow can pass job context
- **T-GROUP-6 → T-GROUP-5**: CLI options must exist before runner can initialize job data
- **T-GROUP-7 → T-GROUP-3,5**: Output formatting depends on personalization result structure

---

# Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM parsing fails on uncommon job formats | Medium | Medium | Graceful degradation: extract raw text, warn user, continue review |
| URL fetching blocked by rate limits | Low | Low | Add user-agent header, implement basic retry with backoff |
| Match score doesn't align with user expectations | Medium | High | User validation during testing, adjust weights based on feedback |
| Existing tests break due to agent prompt changes | Low | High | Conditional prompt injection (only when job_posting present), run full test suite |
| Job URL requires JavaScript (SPA) | High | Medium | Document limitation, suggest manual copy-paste to file |
| Match score calculation too slow | Low | Medium | Profile and optimize skill matching, use caching for repeated skills |

---

# Success Metrics

- **Functional**: All 15 FR-P requirements met, verified by integration tests
- **Performance**: Job parsing <5s, match score <10s (SC-P01, SC-P08)
- **Quality**: 85%+ user-validated match accuracy (SC-P02)
- **Coverage**: 90%+ success on major job boards (SC-P03)
- **Backward Compatibility**: 100% existing tests pass unchanged
- **User Satisfaction**: Positive feedback on relevance of personalized suggestions (SC-P07)

---

# Next Steps

1. Run `/speckit.tasks` to generate detailed implementation tasks
2. Proceed with T-GROUP-1 (data models) implementation
3. Iterate through task groups in dependency order
4. Run full test suite after each group
5. User validation testing with real job postings after T-GROUP-8
