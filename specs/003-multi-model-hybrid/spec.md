# Feature Specification: Multi-Model Hybrid Configuration

**Feature Branch**: `003-multi-model-hybrid`
**Created**: 2026-01-09
**Status**: Draft
**Input**: Multi-Model Hybrid Configuration for cost optimization and quality improvement using Gemini, OpenAI, and Claude models

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fast and Cost-Effective Review Execution (Priority: P1)

As a resume owner, I want my resume reviews to complete quickly and at low cost, so I can iterate rapidly without worrying about API expenses.

**Why this priority**: This is the core value proposition - reducing both cost (50%) and execution time (70-80%) makes the tool practical for frequent use.

**Independent Test**: Can be fully tested by running a single resume review with hybrid configuration and measuring total execution time and API cost compared to baseline.

**Acceptance Scenarios**:

1. **Given** a resume file and hybrid configuration enabled, **When** I run a full review, **Then** the total execution time is 2-3 minutes (compared to 10 minutes baseline)
2. **Given** a resume file and hybrid configuration enabled, **When** I run a full review, **Then** the total API cost is approximately $0.50 (compared to $1.00 baseline)
3. **Given** a resume file, **When** I run a review without specifying model override, **Then** the system automatically uses optimal models for each agent (Gemini Flash for Recruiter, o3-mini for Technical Writer, Claude Sonnet for Copywriter, Gemini Pro for Designers/Revisor)

---

### User Story 2 - Reliable Resume Revision (Priority: P1)

As a resume owner, I want the revision process to succeed consistently without fuzzy replacement errors, so I can trust that my resume improvements will be applied correctly.

**Why this priority**: The current fuzzy replacement approach fails 30-40% of the time, making the tool unreliable. This must be fixed for the tool to be production-ready.

**Independent Test**: Can be fully tested by running 10 revision cycles and verifying 100% success rate with no "Fuzzy replacement failed" errors.

**Acceptance Scenarios**:

1. **Given** a resume and feedback from multiple agents, **When** the Revisor agent applies revisions, **Then** the complete revised resume is generated without partial replacement errors
2. **Given** a resume with YAML frontmatter, **When** revisions are applied, **Then** the YAML frontmatter is preserved exactly without modifications
3. **Given** complex revision instructions (deletions, fixes, completions), **When** the Revisor applies them, **Then** all instructions are correctly reflected in the output with no markdown structure corruption

---

### User Story 3 - Enhanced Technical Evaluation (Priority: P2)

As a resume owner targeting technical roles, I want my technical skills and project descriptions to be evaluated with deep engineering understanding, so I can ensure my resume is technically accurate and credible.

**Why this priority**: Using code-specialized models (o3-mini) for technical evaluation improves the depth and accuracy of technical feedback, but the tool is still valuable without this enhancement.

**Independent Test**: Can be tested by running technical evaluation on a resume with intentional technical inconsistencies (e.g., anachronistic technologies, incompatible tech stacks) and verifying that issues are detected.

**Acceptance Scenarios**:

1. **Given** a resume with anachronistic technology claims (e.g., "used Next.js 14 in 2015"), **When** Technical Writer agent evaluates it, **Then** the temporal inconsistency is flagged as an issue
2. **Given** a resume with incompatible technology combinations (e.g., "Django + Flask in the same project"), **When** Technical Writer agent evaluates it, **Then** the unusual combination is questioned or flagged
3. **Given** a resume with duplicate project descriptions, **When** Technical Writer agent evaluates it, **Then** the duplication is detected and a recommendation to merge/remove is provided

---

### User Story 4 - Flexible Model Override for Testing (Priority: P3)

As a developer or power user, I want to override the default hybrid configuration to use a single model for all agents, so I can test different models or work around API availability issues.

**Why this priority**: This is a convenience feature for testing and troubleshooting, not essential for core functionality.

**Independent Test**: Can be tested by running a review with `--model gemini-3.0-flash` flag and verifying all agents use Gemini 3 Flash.

**Acceptance Scenarios**:

1. **Given** the `--model gemini-3.0-flash` flag, **When** I run a review, **Then** all agents use Gemini 3 Flash instead of their default models
2. **Given** the `--model claude-sonnet-4-5-20250929` flag, **When** I run a review, **Then** all agents use Claude Sonnet 4.5
3. **Given** no `--model` flag, **When** I run a review, **Then** the hybrid configuration is used (different models per agent)

---

### User Story 5 - Verbose Model Selection Reporting (Priority: P3)

As a user, I want to see which models are being used for each agent when verbose mode is enabled, so I can understand the system's behavior and verify the hybrid configuration is working.

**Why this priority**: This is useful for transparency and debugging but not essential for core functionality.

**Independent Test**: Can be tested by running a review with `--verbose` flag and verifying that model assignments are printed for each agent.

**Acceptance Scenarios**:

1. **Given** verbose mode enabled, **When** I run a review, **Then** the CLI outputs which model is assigned to each agent
2. **Given** verbose mode enabled with hybrid configuration, **When** I run a review, **Then** I see different models listed for different agents
3. **Given** verbose mode enabled with model override, **When** I run a review, **Then** I see the same model listed for all agents

---

### Edge Cases

- What happens when only some API keys are provided (e.g., only Anthropic API key but not OpenAI/Gemini)?
- What happens when an API call fails for one specific agent/model but others succeed?
- What happens when the Revisor generates incomplete output (e.g., accidentally truncates the resume)?
- What happens when a model doesn't support the required token limits (e.g., if a model has max_tokens < 8000 for full rewrite)?
- What happens when the user provides an invalid model name in `--model` override?
- What happens when multiple API keys are set for the same provider (e.g., both `GOOGLE_API_KEY` and `GEMINI_API_KEY`)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support multiple LLM providers (Gemini, OpenAI, Claude) with a unified client interface
- **FR-002**: System MUST automatically assign optimal models to each agent based on their role (Recruiter → Gemini Flash, Technical Writer → o3-mini, Copywriter → Claude Sonnet, Designers/Revisor → Gemini Pro)
- **FR-003**: System MUST accept API keys for all three providers via environment variables (`GOOGLE_API_KEY` or `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)
- **FR-004**: System MUST provide a `--model` CLI option to override default hybrid configuration and force all agents to use a single specified model
- **FR-005**: Revisor agent MUST generate complete resume output (full rewrite) rather than partial replacements
- **FR-006**: Revisor agent MUST preserve YAML frontmatter exactly without modifications during full rewrite
- **FR-007**: Revisor agent MUST apply all revision instructions (DELETE, KEEP, FIX commands) from all agents
- **FR-008**: System MUST validate that required API keys are available for the selected models before starting review
- **FR-009**: System MUST provide verbose output mode (`--verbose`) that displays which model is assigned to each agent
- **FR-010**: System MUST handle API errors gracefully and provide clear error messages indicating which agent/model failed
- **FR-011**: Technical Writer agent MUST detect temporal inconsistencies (anachronistic technology claims)
- **FR-012**: Technical Writer agent MUST detect incompatible technology combinations
- **FR-013**: Technical Writer agent MUST detect duplicate project descriptions
- **FR-014**: Copywriter agent MUST detect and fix incomplete sentence endings (e.g., "従事していま" → "従事しています。")
- **FR-015**: Copywriter agent MUST detect and unify notation inconsistencies (e.g., "Python" vs "python")
- **FR-016**: Recruiter agent MUST detect date conflicts and overlaps in work history
- **FR-017**: System MUST log token usage (input/output) for each agent to enable cost tracking

### Key Entities

- **LLM Client**: Represents an abstract interface to a language model provider (Gemini, OpenAI, Claude), handling authentication, request formatting, and response parsing
- **Model Configuration**: Defines the mapping between agent roles and optimal LLM models, including provider type and model identifier
- **Agent Role**: Represents the specialized function of each review agent (Recruiter, Technical Writer, Copywriter, UX Designer, Visual Designer, Revisor) with assigned model
- **Revision Instruction**: Represents a structured command from evaluation agents to the Revisor (DELETE, KEEP, FIX, WARNING) with target location and reasoning
- **Full Rewrite Output**: Represents the complete revised resume in Markdown format, including preserved YAML frontmatter and all applied changes

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Review execution time is reduced by at least 70% (10 minutes → 3 minutes or less)
- **SC-002**: Review API cost is reduced by at least 45% ($1.00 → $0.55 or less per review)
- **SC-003**: Revision success rate is 100% with zero "Fuzzy replacement failed" errors over 20 consecutive reviews
- **SC-004**: Technical Writer agent detects at least 90% of intentional technical inconsistencies in test resumes (e.g., anachronistic tech, incompatible stacks)
- **SC-005**: Copywriter agent detects and corrects 100% of incomplete sentence endings in test resumes
- **SC-006**: YAML frontmatter preservation is 100% accurate across all reviews (no modifications to metadata)
- **SC-007**: All agents successfully execute with their assigned models in hybrid configuration without manual intervention
- **SC-008**: Model override functionality works correctly for all supported models (Gemini 3 Flash, Gemini 3 Pro, o3-mini, Claude Sonnet 4.5)
- **SC-009**: Users can view model assignments for each agent when verbose mode is enabled

## Assumptions

1. **API Availability**: All three LLM providers (Google/Gemini, OpenAI, Anthropic) have stable APIs with consistent response formats
2. **Default Token Limits**: Standard token limits are sufficient - 2000 tokens for evaluation agents, 8000 tokens for Revisor full rewrite
3. **Model Pricing**: Pricing information from future-specs.md is current and accurate (Gemini Flash $0.50/$3.00, o3-mini $1.10/$4.40, Claude Sonnet $3.00/$15.00, Gemini Pro $2.00/$12.00 per 1M input/output tokens)
4. **API Key Precedence**: When multiple environment variables are set (e.g., both `GOOGLE_API_KEY` and `GEMINI_API_KEY`), the system will use the first one found in a defined order
5. **Async Support**: All three LLM client libraries support async/await patterns for concurrent execution
6. **JSON Output**: All models can reliably produce JSON-formatted feedback as required by the agent prompts
7. **Japanese Language Support**: All three model providers support Japanese language evaluation and generation at production quality
8. **Context Window**: All selected models have sufficient context windows to handle typical resume lengths (8000-10000 tokens including prompts)
9. **Rate Limits**: Default rate limits for all providers are sufficient for sequential agent execution (no parallel API calls to the same provider)
10. **Model Names**: Model identifiers used in the spec (e.g., "gemini-3-flash", "o3-mini", "claude-sonnet-4-5-20250929") are the actual model names accepted by each provider's API

## Dependencies

- **Python Packages**: `google-generativeai>=0.8.0`, `openai>=1.0.0`, `anthropic>=0.25.0`
- **Existing Components**: Current agent implementations (RecruiterAgent, TechnicalWriterAgent, CopywriterAgent, UXDesignerAgent, VisualDesignerAgent), ReviewState, ReviewWorkflow, CLI framework
- **External Services**: Google Gemini API, OpenAI API, Anthropic Claude API
- **Configuration**: Environment variable support in CLI and deployment environment

## Out of Scope

- LangChain integration (optional, not required for MVP)
- Real-time cost tracking dashboard (tracking is logged but not visualized)
- Automatic fallback to alternative models when primary model fails (fails with clear error instead)
- Model performance benchmarking and A/B testing framework (manual testing only)
- Custom model configuration via config file (environment variables and CLI flags only)
- Support for additional LLM providers beyond Gemini, OpenAI, and Claude
- Batch processing of multiple resumes with hybrid configuration
- Caching of agent responses to reduce costs on repeated reviews
- Fine-tuned models or custom prompts per provider
- Resume versioning or backup system before full rewrite
