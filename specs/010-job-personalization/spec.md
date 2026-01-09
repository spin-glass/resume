# Feature Specification: Job Personalization

**Feature Branch**: `010-job-personalization`
**Created**: 2026-01-09
**Status**: Draft
**Input**: User description: "Personalize resume based on specific job postings by accepting job description files or URLs, analyzing requirements, and providing match scores and tailored recommendations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Job Description File Input (Priority: P1)

A user has a job posting saved as a text or Markdown file and wants to tailor their resume to match that specific role.

**Why this priority**: This is the foundational use case that enables all personalization features. Without the ability to input a job description, no other personalization features can function.

**Independent Test**: Can be fully tested by running `resume-review review --input resume.qmd --job-posting ./job.md` and verifying that the system successfully parses the job description and incorporates it into the review process. Delivers immediate value by contextualizing all feedback against the specific job requirements.

**Acceptance Scenarios**:

1. **Given** a valid resume file and a job posting Markdown file, **When** user runs the review command with `--job-posting ./jobs/backend-role.md`, **Then** the system parses the job description and displays extracted requirements (skills, responsibilities, qualifications)

2. **Given** a job posting file in various text formats (MD, TXT), **When** user provides the file path, **Then** the system successfully extracts structured information regardless of format

3. **Given** a job posting with clearly marked sections (Required Skills, Nice-to-have, Responsibilities), **When** the system parses it, **Then** extracted data correctly categorizes requirements into required vs. preferred

4. **Given** a malformed or empty job posting file, **When** user attempts to run personalized review, **Then** the system displays a clear error message and provides guidance on expected format

---

### User Story 2 - Job URL Input and Web Scraping (Priority: P2)

A user finds a job posting online and wants to personalize their resume by providing the URL instead of manually copying the content.

**Why this priority**: While file input (P1) covers basic functionality, URL input significantly improves user experience by eliminating manual copy-paste work. Most users discover jobs online, making this a high-value convenience feature.

**Independent Test**: Can be tested independently by running `resume-review review --input resume.qmd --job-url "https://example.com/jobs/123"` and verifying successful content extraction. Delivers value by automating the job description acquisition step.

**Acceptance Scenarios**:

1. **Given** a valid job posting URL, **When** user provides it via `--job-url`, **Then** the system fetches the page content and extracts the job description

2. **Given** a job posting on a major job board (LinkedIn, Indeed, company career pages), **When** content is fetched, **Then** the system successfully extracts relevant information despite varying HTML structures

3. **Given** an invalid or inaccessible URL, **When** user attempts to fetch it, **Then** the system displays an error and suggests using `--job-posting` with a file instead

4. **Given** a URL that returns a page with minimal job information, **When** parsing is attempted, **Then** the system extracts what's available and warns the user about incomplete data

---

### User Story 3 - Match Score and Gap Analysis (Priority: P1)

A user wants to understand how well their resume matches a specific job posting and identify skills or experiences they're missing.

**Why this priority**: This is core value delivery - users need to know their match percentage and what's missing. This directly impacts decision-making about whether to apply and what to emphasize.

**Independent Test**: Can be tested by providing a resume and job posting, then verifying that the output includes a match score (0-100%), lists of matched skills, missing skills, and gap analysis. Delivers actionable insights that guide resume improvements.

**Acceptance Scenarios**:

1. **Given** a resume and job posting with clearly defined required skills, **When** personalization analysis runs, **Then** the system displays a match score (0-100%) and lists matched skills with counts (e.g., "Matched 8 of 12 required skills")

2. **Given** a job posting with both required and preferred qualifications, **When** gap analysis is performed, **Then** the system separately identifies missing required skills vs. missing preferred skills with appropriate severity levels

3. **Given** a resume with skills phrased differently than the job posting (e.g., "JavaScript" vs "JS"), **When** matching is performed, **Then** the system recognizes synonyms and variations

4. **Given** a high match score (>80%), **When** analysis completes, **Then** the system provides encouragement and focuses suggestions on optimization rather than major changes

5. **Given** a low match score (<50%), **When** analysis completes, **Then** the system clearly flags critical missing requirements and suggests whether this role is suitable

---

### User Story 4 - Personalized Feedback Integration (Priority: P2)

A user wants all agent feedback (Recruiter, Technical Writer, Copywriter) to be contextualized against the specific job requirements rather than generic advice.

**Why this priority**: This elevates the entire review system from generic advice to job-specific guidance. Each agent's evaluation becomes more relevant and actionable when filtered through the lens of the target role.

**Independent Test**: Can be tested by comparing feedback from a standard review vs. a personalized review for the same resume. Personalized feedback should reference specific job requirements in suggestions. Delivers value by making all feedback more relevant and actionable.

**Acceptance Scenarios**:

1. **Given** a job posting requiring specific technologies (e.g., Kubernetes, GraphQL), **When** agents provide feedback, **Then** suggestions explicitly reference these technologies and recommend highlighting or adding relevant experience

2. **Given** a job posting emphasizing certain soft skills (e.g., team leadership), **When** Copywriter agent reviews content, **Then** feedback includes suggestions to emphasize relevant experiences demonstrating those skills

3. **Given** a job posting with specific domain knowledge requirements (e.g., healthcare, finance), **When** Technical Writer evaluates projects, **Then** feedback suggests reframing or emphasizing relevant domain experience

4. **Given** a job posting with specific metrics expectations (e.g., "experience with 10,000+ user systems"), **When** Recruiter evaluates achievements, **Then** feedback suggests adding or emphasizing scale-related metrics

---

### User Story 5 - Emphasis and Keyword Suggestions (Priority: P3)

A user wants specific recommendations on which experiences to emphasize, how to reframe content, and which keywords to add for ATS optimization.

**Why this priority**: While valuable, this is enhancement-level functionality that builds on the core personalization features. Users can manually apply insights from P1-P2 features even without explicit emphasis suggestions.

**Independent Test**: Can be tested by verifying that personalization output includes a dedicated "Emphasis Suggestions" section with specific actionable recommendations and a "Keyword Additions" section with relevant terms. Delivers value by providing concrete next steps for optimization.

**Acceptance Scenarios**:

1. **Given** a job posting emphasizing certain skills more than others, **When** emphasis suggestions are generated, **Then** the system recommends which resume sections to expand or move higher

2. **Given** a resume lacking certain keywords from the job posting, **When** keyword suggestions are generated, **Then** the system provides a list of relevant terms to naturally incorporate (e.g., "distributed systems", "microservices")

3. **Given** multiple projects with varying relevance to the job, **When** emphasis suggestions are provided, **Then** the system ranks projects by relevance and suggests prioritization

4. **Given** a job posting with ATS-specific terminology, **When** keyword analysis is performed, **Then** the system identifies terms likely to improve ATS match rates

---

### Edge Cases

- What happens when a job posting file contains no structured information (pure prose with no clear sections)? The system should extract requirements using LLM-based semantic analysis rather than relying solely on section headers.

- How does the system handle job postings in multiple languages? Initially scope to English and Japanese only, with clear error messaging for unsupported languages.

- What happens when a job URL redirects, requires authentication, or uses heavy JavaScript rendering? The system should handle standard redirects, provide clear errors for auth-required pages, and support common job board structures without requiring JavaScript execution.

- How does the system handle very broad job postings with 30+ required skills? The system should prioritize the most frequently mentioned or highest-impact skills, and warn the user when requirements seem unrealistic.

- What happens when the resume already has a perfect match (100%)? The system should celebrate the match and provide minor optimization suggestions rather than forcing unnecessary changes.

- How does the system handle conflicting requirements in a job posting (e.g., "entry-level position requiring 10 years experience")? The system should flag the inconsistency in the analysis and provide balanced guidance.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-P01**: System MUST accept a local file path via `--job-posting` option for job description input in text or Markdown format

- **FR-P02**: System MUST accept a URL via `--job-url` option and fetch the job posting content from the web

- **FR-P03**: System MUST parse job descriptions and extract structured information including: required skills, preferred skills, responsibilities, qualifications, salary range (if present), and contract type (if present)

- **FR-P04**: System MUST calculate a match score (0-100%) comparing the resume against job requirements

- **FR-P05**: System MUST identify and list matched skills with counts (e.g., "12 of 15 required skills")

- **FR-P06**: System MUST identify and list missing skills categorized by severity (required vs. preferred)

- **FR-P07**: System MUST provide personalized feedback from all agents (Recruiter, Technical Writer, Copywriter) that references specific job requirements

- **FR-P08**: System MUST generate emphasis suggestions recommending which experiences or projects to highlight based on job relevance

- **FR-P09**: System MUST generate keyword suggestions identifying terms from the job posting that should be incorporated into the resume

- **FR-P10**: System MUST preserve existing review workflow functionality when no job personalization options are provided (backward compatibility)

- **FR-P11**: System MUST store job posting data in the review session for traceability and debugging

- **FR-P12**: System MUST handle synonym and variation matching for skills (e.g., "JavaScript" matches "JS", "React.js" matches "React")

- **FR-P13**: System MUST display the original job posting source (file path or URL) in the output for reference

- **FR-P14**: System MUST validate job posting content before proceeding with analysis and provide clear error messages for invalid or empty inputs

- **FR-P15**: System MUST prioritize required skills over preferred skills in match score calculation

### Key Entities

- **JobPosting**: Represents structured data extracted from a job description, including title, company, required skills, preferred skills, responsibilities, qualifications, salary range, contract type, original source (file path or URL), and raw text content

- **PersonalizationResult**: Represents the outcome of matching a resume against a job posting, including match score (0-100%), matched skills list, missing required skills list, missing preferred skills list, emphasis suggestions, and keyword additions

- **ReviewState (extended)**: Enhanced to include optional job posting data and personalization results, maintaining backward compatibility with existing workflow

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-P01**: Users can provide a job description file or URL and receive a complete personalized review in under 5 minutes

- **SC-P02**: Match score accurately reflects resume-job alignment, with user-validated accuracy of 85%+ (based on user agreement with skill matching)

- **SC-P03**: System successfully extracts structured requirements from 90%+ of common job posting formats (major job boards and company career pages)

- **SC-P04**: All agent feedback explicitly references at least 2 specific job requirements per agent when personalization is enabled

- **SC-P05**: Emphasis suggestions and keyword recommendations are relevant to the job posting in 95%+ of cases (based on manual review)

- **SC-P06**: System handles edge cases (empty files, invalid URLs, malformed content) gracefully with clear error messages in 100% of cases

- **SC-P07**: Personalized reviews provide actionable insights that help users decide whether to apply for a role (measured by user feedback)

- **SC-P08**: Match score calculation completes in under 10 seconds after job parsing

## Assumptions *(document reasonable defaults)*

1. **Job Posting Format**: Assumes most job postings follow common patterns with sections like "Requirements", "Qualifications", "Responsibilities", even if wording varies. LLM-based parsing will handle variations.

2. **Language Support**: Initially supporting English and Japanese only, as these are the primary languages for the resume system.

3. **Web Scraping Limitations**: Assumes static or server-rendered HTML content. JavaScript-heavy SPAs or authentication-protected job boards may not be supported in initial version.

4. **Skill Matching Approach**: Using LLM-based semantic similarity for skill matching rather than exact string matching, allowing for synonym recognition.

5. **Match Score Calculation**: Required skills weighted more heavily than preferred skills (e.g., 70% weight for required, 30% for preferred).

6. **URL Fetching**: Using simple HTTP requests with user-agent headers. Not implementing browser automation or JavaScript execution in initial version.

7. **File Format Support**: Supporting plain text (.txt) and Markdown (.md) formats. PDF parsing is out of scope for initial version.

8. **Integration with Existing Workflow**: Job personalization features are optional add-ons to the existing review workflow. Standard review flow continues to work without changes.

9. **Privacy**: Job posting content is processed locally and not stored permanently. Only summary data (source URL/path) is saved in review sessions.

10. **ATS Optimization**: Keyword suggestions focus on natural language incorporation, not keyword stuffing. Emphasis on maintaining readability.

## Dependencies

- **Existing Review Workflow**: This feature extends the current multi-agent review system and requires all existing agents (Recruiter, Technical Writer, Copywriter) to be functional

- **LLM Access**: Requires access to the multi-model LLM infrastructure established in 003-multi-model-hybrid for parsing and analysis

- **Web Fetching Capability**: Requires HTTP client functionality for fetching job posting URLs (can use Python requests library)

- **ReviewState Schema**: Requires extension of the existing ReviewState to include job posting and personalization result fields

## Constraints

- **No PDF Parsing**: Initial version will not support PDF job descriptions. Users must convert PDFs to text manually.

- **No Authentication**: System cannot fetch job postings from pages requiring login credentials.

- **No JavaScript Execution**: System cannot handle job boards that require JavaScript to render content (e.g., heavy SPAs).

- **Language Limitation**: Only English and Japanese job postings are supported initially.

- **No Historical Tracking**: System does not maintain a database of previously analyzed job postings or match scores across multiple applications.

- **Backward Compatibility**: All existing CLI commands and workflow behavior must remain unchanged when job personalization options are not used.
