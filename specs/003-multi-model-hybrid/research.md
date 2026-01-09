# Research: Multi-Model Hybrid Configuration

**Date**: 2026-01-09
**Feature**: Multi-Model Hybrid Configuration for cost optimization and quality improvement

## Overview

This document consolidates research findings for implementing a multi-provider LLM system supporting Gemini, OpenAI, and Anthropic APIs with role-based model assignment.

---

## 1. Provider API Analysis

### 1.1 Google Gemini API

**Decision**: Use `google-genai` SDK (modern, officially supported)

**Installation**:
```bash
pip install google-genai[aiohttp]>=1.0.0
```

**Key Implementation Details**:
- Client initialization: `genai.Client(api_key="...")`
- Async calls: `await client.aio.models.generate_content(model="gemini-3.0-flash", contents="...", config=...)`
- System instructions: Pass via `config.system_instruction`
- Token usage: Available in `response.usage_metadata` with fields `prompt_token_count`, `response_token_count`, `total_token_count`

**Model Names** (2026):
- **gemini-3.0-flash**: Latest stable model (released 2025/12/17, recommended for production use)
- **gemini-2.5-pro**: Higher capability model for complex reasoning tasks
- **gemini-2.5-flash**: Previous generation (still supported, but 3.0 Flash is faster and cheaper)

**Note**: We use `gemini-3.0-flash` for all Gemini-powered agents (Recruiter, Designers, Revisor). This is Google's latest fast model with improved performance and reduced costs compared to 2.5 Flash.

**Rationale**: Official Google SDK with strong async support, comprehensive token usage tracking, and active maintenance.

**Alternatives Considered**:
- `google-generativeai` (deprecated, older API)
- LiteLLM wrapper (adds complexity, not needed for 3 providers)

---

### 1.2 OpenAI API

**Decision**: Use `openai` SDK v1.0+ with AsyncOpenAI client

**Installation**:
```bash
pip install openai>=1.0.0
```

**Key Implementation Details**:
- Client initialization: `AsyncOpenAI(api_key="...")`
- Async calls: `await client.chat.completions.create(model="gpt-4o", messages=[...])`
- System prompt: First message with `role="system"`
- Token usage: Available in `response.usage` with fields `prompt_tokens`, `completion_tokens`, `total_tokens`

**Model Names** (2026):
- **o3-mini**: Small reasoning model optimized for STEM (recommended for Technical Writer)
- **o4-mini**: Fast, cost-efficient reasoning model (alternative)
- **gpt-4o**: Multimodal flagship model
- **gpt-4.1**: Improved instruction following, 1M token context

**Rationale**: Native async support, stable API, excellent documentation, proven reliability.

**Alternatives Considered**:
- Sync client with asyncio.to_thread (worse performance)
- LangChain OpenAI wrapper (unnecessary abstraction)

---

### 1.3 Anthropic API

**Decision**: Continue using existing `anthropic` SDK with AsyncAnthropic client

**Current Implementation**: Already in use at `packages/resume-review/src/agents/base.py`

**Key Details**:
- Client: `AsyncAnthropic(api_key="...")`
- Async calls: `await client.messages.create(model="...", max_tokens=..., system="...", messages=[...])`
- Token usage: `response.usage.input_tokens`, `response.usage.output_tokens`
- Cache tokens: `response.usage.cache_creation_input_tokens`, `response.usage.cache_read_input_tokens`

**Model Names**:
- **claude-sonnet-4-5-20250929**: High-quality language model (recommended for Copywriter)
- **claude-opus-4-5-20251101**: Most capable model (currently default in codebase)

**Rationale**: Already integrated, no changes needed to client code, excellent Japanese language support.

---

## 2. Abstraction Layer Design

### 2.1 Base Client Interface

**Decision**: Create `BaseLLMClient` abstract base class with provider-specific implementations

**Interface Design**:
```python
class BaseLLMClient(ABC):
    @abstractmethod
    async def generate_async(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> LLMResponse:
        pass

@dataclass
class LLMResponse:
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    provider: str
```

**Rationale**:
- Uniform interface simplifies agent code
- Encapsulates provider-specific details
- Enables easy testing with mocks
- Future-proof for additional providers

**Alternatives Considered**:
- **LiteLLM**: Full-featured router with 100+ LLM support, load balancing, cost tracking
  - Rejected: Overkill for 3 providers, adds dependency complexity
- **Direct provider calls in agents**: No abstraction
  - Rejected: Duplicates error handling, token tracking, makes testing harder
- **LangChain ChatModel wrappers**: Standardized interface
  - Rejected: Already using LangGraph, LangChain wrappers add unnecessary weight

---

### 2.2 Model Configuration Strategy

**Decision**: Static mapping with environment variable override

**Configuration Approach**:
```python
AGENT_MODEL_MAP = {
    AgentName.RECRUITER: ("gemini", "gemini-3.0-flash"),
    AgentName.TECHNICAL_WRITER: ("openai", "o3-mini"),
    AgentName.COPYWRITER: ("anthropic", "claude-sonnet-4-5-20250929"),
    AgentName.UX_DESIGNER: ("gemini", "gemini-3.0-flash"),
    AgentName.VISUAL_DESIGNER: ("gemini", "gemini-3.0-flash"),
    AgentName.REVISOR: ("gemini", "gemini-3.0-flash"),
}
```

**Override Mechanism**: CLI `--model` flag forces all agents to use specified model

**Rationale**:
- Simple, maintainable, no external config files
- Easy to override for testing
- Clear documentation in code

**Alternatives Considered**:
- YAML/JSON config file: More flexible but adds file I/O complexity
- Database storage: Overkill for static mappings
- Environment variables per agent: Too many variables (6 agents × model/provider = 12+ vars)

---

## 3. Error Handling Strategy

### 3.1 Retry Logic

**Decision**: Extend existing tenacity-based retry with provider-specific exception handling

**Current State**: `@retry(stop=stop_after_attempt(3), wait=wait_exponential(...))`

**Enhancement**:
```python
from tenacity import retry, retry_if_exception_type

TRANSIENT_ERRORS = (
    anthropic.APIConnectionError,
    openai.APIConnectionError,
    # Gemini errors TBD
    asyncio.TimeoutError,
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(TRANSIENT_ERRORS),
    reraise=True
)
async def generate_with_retry(client: BaseLLMClient, **kwargs):
    return await client.generate_async(**kwargs)
```

**Rationale**: Leverage existing tenacity infrastructure, add provider-specific awareness

**Alternatives Considered**:
- Manual retry loops: Less declarative, harder to test
- No retries: Unreliable for production use
- Exponential backoff library (backoff): Similar to tenacity, no advantage

---

### 3.2 Failure Handling

**Decision**: Fail fast with clear error messages, no automatic fallback

**Approach**:
- API key validation before workflow starts (FR-008)
- Provider-specific error messages identifying which agent/model failed (FR-010)
- No silent fallback to alternative providers (explicit in Out of Scope)

**Rationale**:
- Predictable behavior for cost tracking
- User controls which providers are used
- Debugging is easier when failures are explicit

**Alternatives Considered**:
- Automatic fallback to Claude if Gemini/OpenAI fail: Unpredictable costs, masks issues
- Graceful degradation (skip failed agent): Incomplete reviews, unpredictable quality

---

## 4. Full Rewrite Architecture

### 4.1 Problem Analysis

**Current Issue**: RevisionService uses fuzzy string matching to find and replace text sections
- Failure rate: 30-40% ("Fuzzy replacement failed" errors)
- Root cause: String matching fails when:
  - Minor formatting differences between prompt and actual text
  - Multiple similar sections exist
  - Markdown structure changes between iterations

**Decision**: Revisor generates complete file content instead of diffs

**Implementation**:
```python
async def apply_revisions_async(
    self,
    resume: Resume,
    feedback_list: list[Feedback],
) -> str:
    """
    Returns complete revised resume Markdown (including YAML frontmatter).

    Prompt instructs model to:
    1. Output full document from line 1 to EOF
    2. Preserve YAML frontmatter exactly
    3. Apply all feedback (DELETE, FIX, KEEP commands)
    4. No truncation or "..." abbreviations
    """
    # Model generates full file in single response
    return revised_markdown  # Complete file content
```

**Token Budget**: 8000 tokens for output (typical resume: 3000-5000 tokens)

**Rationale**:
- Eliminates fuzzy matching errors completely
- Simpler implementation (remove RevisionService complexity)
- Models are reliable at full-text generation
- Gemini 2.0 Flash handles long output efficiently

**Alternatives Considered**:
- Improved fuzzy matching (edit distance, AST parsing): Complex, still error-prone
- Structured diffs (line-based patches): Requires precise line tracking, brittle
- Manual review of each change: Slow, defeats automation purpose

---

### 4.2 YAML Frontmatter Preservation

**Decision**: Explicit instruction in Revisor system prompt + validation

**Approach**:
1. Parse YAML frontmatter from original resume
2. Instruct model: "Preserve YAML frontmatter between `---` delimiters exactly as provided"
3. Post-generation validation: Compare original and generated frontmatter
4. If mismatch: Log error, use original frontmatter + generated body

**Rationale**:
- YAML contains metadata (title, author, date) that must never change
- Models occasionally modify metadata despite instructions
- Validation provides safety net

**Alternatives Considered**:
- Trust model to preserve: Too risky, metadata corruption breaks builds
- Strip and re-inject frontmatter: Simple but loses ability to detect model errors

---

## 5. Token Usage Tracking

### 5.1 Logging Strategy

**Decision**: Log token usage per agent invocation to enable cost analysis

**Implementation**:
```python
logger.info(
    f"Agent {agent_name} completed: "
    f"model={response.model}, "
    f"input_tokens={response.input_tokens}, "
    f"output_tokens={response.output_tokens}, "
    f"estimated_cost=${estimated_cost:.4f}"
)
```

**Cost Calculation**:
```python
PRICING = {
    "gemini-3.0-flash": {"input": 0.5, "output": 3.0},  # per 1M tokens
    "o3-mini": {"input": 1.1, "output": 4.4},
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
}

def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = PRICING[model]
    return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
```

**Rationale**:
- Enables SC-002 validation (cost reduction measurement)
- Helps users understand cost breakdown
- No external service dependencies

**Alternatives Considered**:
- External cost tracking service (e.g., Helicone, LangSmith): Adds API calls, dependencies
- Database storage: Overkill for simple logging
- No tracking: Can't measure cost optimization success

---

## 6. Integration with Existing Codebase

### 6.1 BaseAgent Modification

**Current Signature**:
```python
class BaseAgent(ABC):
    def __init__(self, api_key: str, model: str = "claude-opus-4-5-20251101"):
        self.client = Anthropic(api_key=api_key)
        self.async_client = AsyncAnthropic(api_key=api_key)
```

**New Signature**:
```python
class BaseAgent(ABC):
    def __init__(
        self,
        llm_client: BaseLLMClient,  # Injected, not constructed
        agent_name: AgentName,
    ):
        self.llm_client = llm_client
        self.agent_name = agent_name
```

**Migration Path**:
1. Add `llm_client` parameter (required)
2. Deprecate `api_key`/`model` parameters (remove after migration)
3. Update `evaluate_async` to use `self.llm_client.generate_async()`

**Rationale**: Dependency injection enables testing, supports multiple providers

---

### 6.2 ReviewState Extension

**New Fields**:
```python
class ReviewState(TypedDict, total=False):
    # ... existing fields ...

    # Multi-model configuration (new)
    gemini_api_key: Optional[str]
    openai_api_key: Optional[str]
    anthropic_api_key: Optional[str]  # Replaces api_key
    override_model: Optional[str]  # CLI --model flag

    # Token tracking (new)
    token_usage: dict[str, dict[str, int]]  # {agent_name: {input, output}}
```

**Rationale**:
- Minimal state changes
- Supports both hybrid and override modes
- Tracks token usage for cost calculation

---

### 6.3 CLI Changes

**New Options**:
```python
@click.option("--gemini-api-key", envvar="GEMINI_API_KEY")
@click.option("--openai-api-key", envvar="OPENAI_API_KEY")
@click.option("--anthropic-api-key", envvar="ANTHROPIC_API_KEY")
@click.option("--model", default=None, help="Override model for all agents")
```

**Backward Compatibility**:
- Keep `--api-key` as alias for `--anthropic-api-key`
- Warn if only Anthropic key provided (hybrid mode disabled)

---

## 7. Testing Strategy

### 7.1 Unit Tests

**Approach**: Mock `BaseLLMClient` implementations

```python
class MockLLMClient(BaseLLMClient):
    async def generate_async(self, **kwargs) -> LLMResponse:
        return LLMResponse(
            content="Mock feedback",
            model="mock-model",
            input_tokens=100,
            output_tokens=50,
            provider="mock"
        )
```

**Coverage**:
- Model selection logic (correct provider for each agent)
- Token usage tracking
- Error handling (API failures, missing keys)
- Override mode (all agents use same model)

---

### 7.2 Integration Tests

**Approach**: Real API calls with small prompts (mark with `@pytest.mark.integration`)

**Test Cases**:
- SC-001: Execution time < 3 minutes for full review
- SC-002: Total cost < $0.55 per review
- SC-003: 10 consecutive reviews with 0 "Fuzzy replacement failed" errors
- SC-004: Technical Writer detects anachronistic tech in test resume

---

## 8. Implementation Sequence

### Phase 1: Foundation (No functional changes)
1. Create `BaseLLMClient` interface
2. Implement `AnthropicClient`, `OpenAIClient`, `GeminiClient`
3. Add unit tests for each client

### Phase 2: Agent Integration
4. Update `BaseAgent` to accept `llm_client` parameter
5. Create `LLMClientFactory` with agent-to-model mapping
6. Update workflow nodes to construct clients

### Phase 3: Full Rewrite
7. Create new `RevisorAgent` with full-rewrite logic
8. Remove `RevisionService` (deprecate fuzzy matching)
9. Update `revisor_node` to use new agent

### Phase 4: CLI & Validation
10. Add CLI options for multi-provider API keys
11. Implement API key validation at startup
12. Add token usage logging
13. Run integration tests to validate SC-001 through SC-009

---

## 9. Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Gemini model names change | Medium | High | Use versioned model IDs (e.g., `gemini-3.0-flash`) |
| Provider API rate limits hit | Medium | Medium | Implement exponential backoff, log rate limit errors clearly |
| Full rewrite truncates content | Low | High | Validate output length vs input, max_tokens=8000, explicit "no truncation" prompt |
| YAML frontmatter corruption | Low | High | Post-generation validation, use original frontmatter if mismatch |
| Cost exceeds projections | Medium | Low | Log every API call cost, add cost warnings if threshold exceeded |
| Japanese quality degrades with Gemini/OpenAI | Medium | Medium | Keep Copywriter on Claude (Japanese specialist), test with Japanese resumes |

---

## 10. Success Metrics Validation Plan

| Criteria | Measurement Method | Target |
|----------|-------------------|--------|
| SC-001: Execution time | `time.time()` before/after workflow | ≤ 3 minutes |
| SC-002: API cost | Sum of token_usage × pricing | ≤ $0.55 |
| SC-003: Revision success rate | Count "Fuzzy replacement failed" logs in 20 runs | 0 errors |
| SC-004: Technical detection | Inject test inconsistencies, verify detection | ≥ 90% |
| SC-005: Copywriter corrections | Inject incomplete sentences, verify fixes | 100% |
| SC-006: YAML preservation | Compare frontmatter pre/post revision | 100% match |
| SC-007: Hybrid execution | Run review without --model, verify different models used | All agents execute |
| SC-008: Override functionality | Run with --model flag, verify uniform usage | All agents use override |
| SC-009: Verbose reporting | Run with --verbose, verify model assignments printed | Visible in output |

---

## References

- Google Genai SDK: https://github.com/googleapis/python-genai
- OpenAI Python SDK: https://github.com/openai/openai-python
- Anthropic SDK: https://github.com/anthropics/anthropic-sdk-python
- Tenacity (retry library): https://tenacity.readthedocs.io/
- Gemini API Pricing: https://ai.google.dev/pricing
- OpenAI Pricing: https://openai.com/api/pricing/
- Anthropic Pricing: https://www.anthropic.com/pricing
