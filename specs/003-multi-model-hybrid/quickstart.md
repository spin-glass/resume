# Quickstart: Multi-Model Hybrid Configuration

**Feature**: Multi-Model Hybrid Configuration
**Audience**: Developers implementing this feature
**Est. Reading Time**: 10 minutes

## Overview

This guide provides a rapid onboarding path for implementing the multi-model hybrid configuration feature. Read this BEFORE diving into detailed implementation.

---

## What We're Building

**Goal**: Enable the resume-review system to use optimal LLM models for each agent role, reducing cost by 50% and execution time by 70% while eliminating fuzzy replacement errors.

**Current State**:
- All agents use Claude Opus 4.5 (`claude-opus-4-5-20251101`)
- Cost: ~$1.00 per review
- Time: ~10 minutes per review
- Revision failure rate: 30-40% ("Fuzzy replacement failed")

**Target State**:
- Recruiter → Gemini 3.0 Flash (fast screening, released 2025/12/17)
- Technical Writer → OpenAI o3-mini (code analysis)
- Copywriter → Claude Sonnet 4.5 (language quality)
- Designers/Revisor → Gemini 3.0 Flash (layout analysis, full rewrites)
- Cost: ~$0.50 per review
- Time: ~2-3 minutes per review
- Revision failure rate: 0% (full rewrite approach)

---

## Architecture at a Glance

```
┌─────────────┐
│     CLI     │  --gemini-api-key, --openai-api-key, --anthropic-api-key
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ ReviewWorkflow   │  Creates ReviewState with 3 API keys
└────────┬─────────┘
         │
         ▼
┌───────────────────┐
│ LangGraph Nodes   │  Each node constructs agent with appropriate model
└────────┬──────────┘
         │
         ├──────────────┬─────────────┬────────────┐
         ▼              ▼             ▼            ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
   │Recruiter │  │Technical │  │Copywriter│  │ Revisor  │
   │  Agent   │  │Writer Agt│  │  Agent   │  │  Agent   │
   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
        │             │              │             │
        │ uses        │ uses         │ uses        │ uses
        ▼             ▼              ▼             ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ Gemini   │  │ OpenAI   │  │Anthropic │  │ Gemini   │
   │ Client   │  │ Client   │  │ Client   │  │ Client   │
   └──────────┘  └──────────┘  └──────────┘  └──────────┘
```

**Key Insight**: Agents don't know which provider they're using. They just call `llm_client.generate_async()`.

---

## Core Components (5 New Files)

| File | Purpose | Lines | Complexity |
|------|---------|-------|------------|
| `services/llm_client.py` | Base interface + 3 provider implementations | ~400 | Medium |
| `services/llm_factory.py` | Model selection logic + client instantiation | ~150 | Low |
| `config/model_config.py` | Agent-to-model mapping constants | ~50 | Low |
| `agents/base.py` | Modified to accept `llm_client` parameter | ~20 changes | Low |
| `workflow/state.py` | Add 3 API key fields + token_usage dict | ~10 changes | Low |

**Total New Code**: ~500 lines
**Modified Code**: ~100 lines

---

## Implementation Sequence (5 Phases)

### Phase 1: LLM Client Layer (Day 1-2)

**Goal**: Create provider-agnostic client interface

**Tasks**:
1. Create `services/llm_client.py`:
   - `LLMResponse` dataclass
   - `BaseLLMClient` ABC
   - `GeminiClient`, `OpenAIClient`, `AnthropicClient` implementations
2. Add dependencies: `google-genai[aiohttp]`, `openai`
3. Write unit tests with `MockLLMClient`

**Validation**: All 3 clients return `LLMResponse` with correct token counts

---

### Phase 2: Model Configuration (Day 2)

**Goal**: Define agent-to-model mappings

**Tasks**:
1. Create `config/model_config.py`:
   - `AgentName` enum
   - `AGENT_MODEL_MAP` dictionary
   - `MODEL_PRICING` dictionary
2. Create `services/llm_factory.py`:
   - `LLMClientFactory.create_client()` method
   - API key validation logic
   - Override model detection

**Validation**: `create_client(AgentName.RECRUITER)` returns `GeminiClient`

---

### Phase 3: Agent Integration (Day 3)

**Goal**: Modify agents to use injected clients

**Tasks**:
1. Update `agents/base.py`:
   - Change `__init__` signature to accept `llm_client`
   - Remove direct `Anthropic` client construction
   - Update `evaluate_async` to use `self.llm_client`
2. Update workflow nodes (e.g., `workflow/nodes/supervisor.py`):
   - Construct `llm_client` using `LLMClientFactory`
   - Pass to agent constructors

**Validation**: Run existing tests (should pass with `AnthropicClient`)

---

### Phase 4: Full Rewrite Architecture (Day 4)

**Goal**: Eliminate fuzzy replacement errors

**Tasks**:
1. Implement new `RevisorAgent.apply_revisions_async()`:
   - Prompt for full file output (8000 max_tokens)
   - Parse YAML frontmatter separately
   - Validate frontmatter preservation
2. Remove `services/revision.py` (fuzzy matching code)
3. Update `workflow/nodes/revisor.py` to use new method

**Validation**: 10 consecutive reviews with 0 replacement errors

---

### Phase 5: CLI & Logging (Day 5)

**Goal**: Expose configuration to users, track costs

**Tasks**:
1. Update `cli.py`:
   - Add `--gemini-api-key`, `--openai-api-key`, `--anthropic-api-key` options
   - Add `--model` override option
   - Add verbose model selection output
2. Add token usage logging in each agent
3. Calculate and display total cost at end of review

**Validation**: Run review with `--verbose`, see model assignments and costs

---

## Development Environment Setup

### Install Dependencies

```bash
cd packages/resume-review

# Add new dependencies to pyproject.toml
[project.dependencies]
google-genai = {version = ">=1.0.0", extras = ["aiohttp"]}
openai = ">=1.0.0"
# anthropic already installed

# Install
pip install -e .
```

### API Keys for Testing

**Option 1: Environment Variables** (temporary)
```bash
export GEMINI_API_KEY="your-google-api-key"
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

**Option 2: .env File** (recommended for development)
```bash
# Update packages/resume-review/.env
echo "GEMINI_API_KEY=your-google-api-key" >> packages/resume-review/.env
echo "OPENAI_API_KEY=your-openai-api-key" >> packages/resume-review/.env
# ANTHROPIC_API_KEY should already exist
```

Get free tier keys:
- Gemini: https://ai.google.dev/ (free tier available)
- OpenAI: https://platform.openai.com/api-keys ($5 credit for new users)
- Anthropic: https://console.anthropic.com/ (existing key)

---

## Testing Strategy

### Unit Tests (Fast, No API Calls)

```bash
# Test individual clients with mocks
pytest tests/unit/services/test_llm_client.py -v

# Test model selection logic
pytest tests/unit/services/test_llm_factory.py -v

# Test agent integration
pytest tests/unit/agents/test_base.py -v
```

### Integration Tests (Slow, Real API Calls)

```bash
# Test with real APIs (mark as integration to skip by default)
pytest tests/integration/test_multi_model.py -v -m integration

# Skip integration tests in normal runs
pytest -m "not integration"
```

### End-to-End Validation

```bash
# Dry run with verbose output
resume-review review \
  --input ../../resume/resume-ja.qmd \
  --dry-run \
  --verbose

# Expected output:
# 🔧 Mode: Hybrid configuration (optimal model per agent)
#    - Recruiter: Gemini 3.0 Flash
#    - Technical Writer: o3-mini
#    - Copywriter: Claude Sonnet 4.5
#    - Visual/UX Designer: Gemini 3.0 Flash
#    - Revisor: Gemini 3.0 Flash
```

---

## Common Pitfalls & Solutions

### Pitfall 1: Model Name Mismatches

**Problem**: Model names must match Google's official API identifiers

**Solution**: Use the correct Gemini 3.0 Flash model name (released 2025/12/17):
- ✅ `gemini-3.0-flash` (correct - stable, production-ready)
- ❌ `gemini-3-flash` (incorrect - missing version number)
- ❌ `gemini-3.0-flash-preview` (incorrect - no preview suffix for stable release)
- ❌ `gemini-2.5-flash` (outdated - previous generation)

### Pitfall 2: Token Usage Calculation

**Problem**: Different providers use different field names

**Solution**: Extract tokens in each client implementation:
- Gemini: `response.usage_metadata.prompt_token_count`
- OpenAI: `response.usage.prompt_tokens`
- Anthropic: `response.usage.input_tokens` (+ cache tokens!)

### Pitfall 3: System Prompt Format

**Problem**: Gemini, OpenAI, Anthropic handle system prompts differently

**Solution**: Abstract in `BaseLLMClient.generate_async()`:
- Gemini: Pass as `config.system_instruction`
- OpenAI: First message with `role="system"`
- Anthropic: Separate `system` parameter

### Pitfall 4: Async Client Initialization

**Problem**: Some SDKs require event loop context for async clients

**Solution**: Use `AsyncOpenAI()`, `genai.Client()` (not sync versions)

### Pitfall 5: YAML Frontmatter Corruption

**Problem**: Model might modify metadata despite instructions

**Solution**: Validate frontmatter after generation, use original if mismatch

---

## Debugging Tips

### Enable Verbose Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("resume_review")
```

### Inspect Token Usage

```python
# Add to each agent after generate_async
logger.info(
    f"{self.agent_name}: "
    f"in={response.input_tokens}, "
    f"out={response.output_tokens}, "
    f"cost=${cost:.4f}"
)
```

### Test Individual Clients

```python
# Test Gemini client directly
import asyncio
from services.llm_client import GeminiClient

async def test_gemini():
    client = GeminiClient(api_key="...", model="gemini-3.0-flash")
    response = await client.generate_async(
        system_prompt="You are a test assistant.",
        user_prompt="Say hello.",
        max_tokens=50
    )
    print(response)

asyncio.run(test_gemini())
```

### Override Model for Testing

```bash
# Force all agents to use Claude (no Gemini/OpenAI needed)
resume-review review \
  --input resume.qmd \
  --model claude-sonnet-4-5-20250929 \
  --anthropic-api-key $ANTHROPIC_API_KEY \
  --dry-run
```

---

## Success Metrics Checklist

After implementation, verify:

- [ ] **SC-001**: Full review completes in ≤ 3 minutes
- [ ] **SC-002**: Total cost ≤ $0.55 per review
- [ ] **SC-003**: 20 consecutive reviews with 0 replacement errors
- [ ] **SC-004**: Technical Writer detects 90%+ of test inconsistencies
- [ ] **SC-005**: Copywriter fixes 100% of incomplete sentences
- [ ] **SC-006**: YAML frontmatter unchanged in 100% of revisions
- [ ] **SC-007**: Hybrid mode uses different models for each agent
- [ ] **SC-008**: Override mode (`--model`) works for all models
- [ ] **SC-009**: Verbose mode displays model assignments

---

## Next Steps

1. **Read**: `research.md` for API details
2. **Review**: `data-model.md` for entity definitions
3. **Study**: `contracts/llm-client-interface.md` for interface contract
4. **Start**: Phase 1 (LLM Client Layer) implementation
5. **Test**: Unit tests after each phase

---

## Help & Resources

**Documentation**:
- Research findings: `specs/003-multi-model-hybrid/research.md`
- Data model: `specs/003-multi-model-hybrid/data-model.md`
- Interface contract: `specs/003-multi-model-hybrid/contracts/llm-client-interface.md`

**External Docs**:
- Gemini API: https://ai.google.dev/gemini-api/docs
- OpenAI API: https://platform.openai.com/docs/api-reference
- Anthropic API: https://docs.anthropic.com/

**Code References**:
- Existing agents: `packages/resume-review/src/agents/`
- Workflow nodes: `packages/resume-review/src/workflow/nodes/`
- Current BaseAgent: `packages/resume-review/src/agents/base.py`

---

## Estimated Timeline

| Phase | Duration | Depends On | Deliverable |
|-------|----------|------------|-------------|
| Phase 1: LLM Clients | 2 days | None | Working client implementations |
| Phase 2: Configuration | 1 day | Phase 1 | Model selection logic |
| Phase 3: Agent Integration | 1 day | Phase 2 | Agents using clients |
| Phase 4: Full Rewrite | 1 day | Phase 3 | Revisor rewrite logic |
| Phase 5: CLI & Logging | 1 day | Phase 4 | User-facing features |
| **Testing & Validation** | 2 days | All phases | SC-001 through SC-009 |

**Total**: 8 working days (1.6 weeks)

---

## Quick Reference: File Changes

### New Files (Create)
- `packages/resume-review/src/services/llm_client.py`
- `packages/resume-review/src/services/llm_factory.py`
- `packages/resume-review/src/config/model_config.py`

### Modified Files (Edit)
- `packages/resume-review/src/agents/base.py`
- `packages/resume-review/src/workflow/state.py`
- `packages/resume-review/src/workflow/nodes/supervisor.py`
- `packages/resume-review/src/workflow/nodes/revisor.py`
- `packages/resume-review/src/cli.py`
- `packages/resume-review/pyproject.toml`

### Deleted Files (Remove)
- `packages/resume-review/src/services/revision.py` (optional cleanup)

---

Ready to start? Begin with Phase 1 (LLM Client Layer) and work through sequentially. Good luck! 🚀
