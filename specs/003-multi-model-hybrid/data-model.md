# Data Model: Multi-Model Hybrid Configuration

**Feature**: Multi-Model Hybrid Configuration
**Date**: 2026-01-09

## Overview

This document defines the data entities and their relationships for the multi-model hybrid configuration feature.

---

## Core Entities

### 1. LLMResponse

Unified response format returned by all LLM providers.

**Fields**:
- `content` (str): Generated text content from the model
- `model` (str): Model identifier used for generation (e.g., "gemini-3.0-flash")
- `input_tokens` (int): Number of tokens in the input prompt
- `output_tokens` (int): Number of tokens in the generated output
- `provider` (str): Provider name ("gemini", "openai", "anthropic")

**Validation Rules**:
- `content` must not be empty
- `input_tokens` and `output_tokens` must be non-negative integers
- `provider` must be one of the supported providers

**Relationships**:
- Produced by: `BaseLLMClient`
- Consumed by: `BaseAgent.evaluate_async()`

**Purpose**: Normalizes responses across different LLM providers to enable uniform handling in agent code.

---

### 2. ModelConfiguration

Defines the mapping between agent roles and optimal LLM models.

**Fields**:
- `agent_name` (AgentName enum): The agent role (RECRUITER, TECHNICAL_WRITER, COPYWRITER, UX_DESIGNER, VISUAL_DESIGNER, REVISOR)
- `provider` (str): Provider identifier ("gemini", "openai", "anthropic")
- `model_id` (str): Specific model identifier (e.g., "gemini-3.0-flash", "o3-mini")

**Validation Rules**:
- `agent_name` must be a valid AgentName enum value
- `provider` must have corresponding API key in environment
- `model_id` must be a valid model for the specified provider

**Relationships**:
- Used by: `LLMClientFactory.create_client()`
- Referenced in: `AGENT_MODEL_MAP` constant

**Purpose**: Central registry of optimal model assignments for cost and quality optimization.

**Example**:
```python
AGENT_MODEL_MAP = {
    AgentName.RECRUITER: ModelConfiguration(
        agent_name=AgentName.RECRUITER,
        provider="gemini",
        model_id="gemini-3.0-flash"
    ),
    AgentName.TECHNICAL_WRITER: ModelConfiguration(
        agent_name=AgentName.TECHNICAL_WRITER,
        provider="openai",
        model_id="o3-mini"
    ),
    # ...
}
```

---

### 3. AgentName (Enum)

Enumeration of all agent roles in the system.

**Values**:
- `RECRUITER`: Evaluates resume from hiring perspective
- `TECHNICAL_WRITER`: Evaluates technical accuracy and clarity
- `COPYWRITER`: Evaluates language quality and consistency
- `UX_DESIGNER`: Evaluates information architecture
- `VISUAL_DESIGNER`: Evaluates visual design and layout
- `REVISOR`: Applies revisions to resume content

**Purpose**: Type-safe agent identification for model assignment and logging.

---

### 4. ProviderConfig

Configuration for a specific LLM provider.

**Fields**:
- `provider_name` (str): Provider identifier ("gemini", "openai", "anthropic")
- `api_key` (str): API key for authentication
- `models_available` (list[str]): List of supported model IDs
- `enabled` (bool): Whether this provider is currently active

**Validation Rules**:
- `api_key` must not be empty if `enabled` is True
- `models_available` must contain at least one model ID

**Relationships**:
- Used by: `LLMClientFactory` to instantiate clients
- Source: Environment variables or config

**Purpose**: Encapsulates provider-specific configuration for clean initialization.

---

### 5. TokenUsage

Tracks token consumption for a single agent invocation.

**Fields**:
- `agent_name` (str): Name of the agent (e.g., "recruiter")
- `model` (str): Model used (e.g., "gemini-3.0-flash")
- `input_tokens` (int): Tokens consumed in prompt
- `output_tokens` (int): Tokens generated in response
- `total_tokens` (int): Sum of input and output
- `estimated_cost_usd` (float): Calculated cost in USD

**Validation Rules**:
- `total_tokens` must equal `input_tokens + output_tokens`
- `estimated_cost_usd` must be non-negative

**Relationships**:
- Aggregated in: `ReviewState.token_usage`
- Logged by: Each agent after generation

**Purpose**: Enables cost tracking and validation of SC-002 (cost reduction).

**State Transitions**:
```
Created (tokens=0) → Updated (after API call) → Logged (persisted)
```

---

### 6. RevisionInstruction

Structured command from evaluation agents to the Revisor.

**Fields**:
- `command_type` (str): Command type ("DELETE", "KEEP", "FIX", "WARNING")
- `target` (str): Description of target location (e.g., "Section: 職務経歴 > Project A")
- `description` (str): Explanation of the issue or instruction
- `suggested_fix` (Optional[str]): Recommended correction (for FIX commands)
- `severity` (str): Issue severity ("critical", "medium", "low")
- `agent_source` (str): Agent that issued this instruction

**Validation Rules**:
- `command_type` must be one of: DELETE, KEEP, FIX, WARNING
- `severity` must be one of: critical, medium, low
- `suggested_fix` is required if `command_type` is "FIX"

**Relationships**:
- Produced by: Evaluation agents (Recruiter, Technical Writer, Copywriter)
- Consumed by: `RevisorAgent.apply_revisions_async()`

**Purpose**: Standardizes feedback format for consistent revision application.

**Example**:
```python
RevisionInstruction(
    command_type="FIX",
    target="技術スタック section",
    description="Inconsistent capitalization: 'python' should be 'Python'",
    suggested_fix="Change 'python' to 'Python'",
    severity="medium",
    agent_source="copywriter"
)
```

---

## Extended Entities (Modifications to Existing)

### 7. ReviewState (Extended)

Additions to existing `ReviewState` TypedDict to support multi-model configuration.

**New Fields**:
- `gemini_api_key` (Optional[str]): API key for Google Gemini
- `openai_api_key` (Optional[str]): API key for OpenAI
- `anthropic_api_key` (Optional[str]): API key for Anthropic (replaces `api_key`)
- `override_model` (Optional[str]): CLI override to force all agents to use single model
- `token_usage` (dict[str, TokenUsage]): Mapping of agent name to token usage

**Validation Rules**:
- At least one API key must be provided
- If `override_model` is set, corresponding provider API key must be available
- For hybrid mode (no override), all three API keys should be provided

**Relationships**:
- Flows through: Entire LangGraph workflow
- Initialized by: `ReviewWorkflow._create_initial_state()`
- Updated by: Each agent node after generation

**Migration Notes**:
- Existing `api_key` field renamed to `anthropic_api_key`
- Backward compatibility maintained via CLI alias

---

### 8. Feedback (Existing, No Changes)

Existing entity from `models/feedback.py` - used as-is.

**Fields** (for reference):
- `agent_name` (str)
- `score` (float)
- `strengths` (list[str])
- `issues` (list[Issue])
- `suggestions` (list[str])

**Note**: No structural changes required. Feedback parsing logic in agents may be enhanced to extract `RevisionInstruction` objects.

---

## Relationships Diagram

```
┌─────────────────┐
│  ReviewState    │
│  (LangGraph)    │
└────────┬────────┘
         │ contains
         ├─────────────────┬─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────────┐ ┌───────────────┐ ┌──────────────┐
│ ProviderConfig  │ │ TokenUsage    │ │ ReviewConfig │
│ (per provider)  │ │ (per agent)   │ │ (existing)   │
└─────────┬───────┘ └───────────────┘ └──────────────┘
          │
          │ used by
          ▼
┌─────────────────────┐
│ LLMClientFactory    │
│ create_client()     │
└─────────┬───────────┘
          │ creates
          ├──────────────┬──────────────┬─────────────┐
          ▼              ▼              ▼             ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐  ┌──────────┐
   │ Gemini   │   │ OpenAI   │   │ Anthropic│  │ BaseLLM  │
   │ Client   │   │ Client   │   │ Client   │  │ Client   │
   └────┬─────┘   └────┬─────┘   └────┬─────┘  └────┬─────┘
        │              │              │             │
        │ implements   │ implements   │ implements  │ (ABC)
        └──────────────┴──────────────┴─────────────┘
                       │
                       │ returns
                       ▼
               ┌──────────────┐
               │ LLMResponse  │
               └──────┬───────┘
                      │ used by
                      ▼
               ┌──────────────┐
               │  BaseAgent   │
               │  .evaluate() │
               └──────┬───────┘
                      │ produces
                      ▼
               ┌──────────────────┐
               │    Feedback      │
               │ + RevisionInstr. │
               └──────────────────┘
```

---

## Data Flow: Hybrid Configuration Review

1. **Initialization**: CLI parses API keys → `ReviewState` created with 3 provider configs
2. **Agent Construction**:
   - `LLMClientFactory.create_client(agent_name)` looks up `AGENT_MODEL_MAP`
   - Returns provider-specific client (e.g., GeminiClient for Recruiter)
3. **Evaluation**:
   - Agent calls `llm_client.generate_async(system_prompt, user_prompt)`
   - Client returns `LLMResponse` with tokens and content
   - Agent logs `TokenUsage` to ReviewState
4. **Aggregation**:
   - Supervisor collects all Feedback objects
   - Calculates integrated score
5. **Revision**:
   - Revisor extracts `RevisionInstruction` objects from Feedback
   - Calls `llm_client.generate_async()` (Gemini for Revisor)
   - Returns full revised resume content
6. **Completion**:
   - ReviewState accumulated token usage logged
   - Total cost calculated and displayed

---

## Data Flow: Override Mode

Same as hybrid mode, except:
- Step 2: `LLMClientFactory.create_client()` ignores `AGENT_MODEL_MAP` and uses `override_model` for all agents
- All agents use same provider/model (e.g., all use Claude if `--model claude-sonnet-4-5-20250929`)

---

## Validation & Constraints

### API Key Validation (FR-008)

**When**: Before workflow starts
**Where**: `ReviewWorkflow._create_initial_state()` or CLI
**Logic**:
```python
if override_model:
    provider = detect_provider(override_model)
    if not get_api_key(provider):
        raise ValueError(f"API key required for {provider}")
else:  # hybrid mode
    missing = []
    if not gemini_api_key:
        missing.append("GEMINI_API_KEY")
    if not openai_api_key:
        missing.append("OPENAI_API_KEY")
    if not anthropic_api_key:
        missing.append("ANTHROPIC_API_KEY")
    if missing:
        raise ValueError(f"Missing API keys: {', '.join(missing)}")
```

### Token Limit Validation

**When**: Before API call
**Where**: `BaseLLMClient.generate_async()`
**Logic**:
```python
if max_tokens > MODEL_MAX_TOKENS[self.model]:
    logger.warning(
        f"Requested {max_tokens} exceeds {self.model} limit "
        f"({MODEL_MAX_TOKENS[self.model]}). Capping to model limit."
    )
    max_tokens = MODEL_MAX_TOKENS[self.model]
```

### YAML Frontmatter Validation (FR-006)

**When**: After revision generation
**Where**: `RevisorAgent.apply_revisions_async()`
**Logic**:
```python
original_frontmatter = parse_yaml_frontmatter(original_resume)
revised_frontmatter = parse_yaml_frontmatter(revised_resume)

if original_frontmatter != revised_frontmatter:
    logger.error("YAML frontmatter was modified by Revisor. Using original.")
    revised_resume = original_frontmatter + "\n---\n" + revised_body
```

---

## Storage & Persistence

**Note**: This feature does not introduce persistent storage. All data is in-memory during workflow execution.

**Logged Data** (to files/console):
- Token usage per agent (structured logs)
- Total cost per review (summary log)
- Model assignments (if verbose mode enabled)

**Future Enhancement** (Out of Scope for MVP):
- Database storage of token usage for historical analysis
- Cost tracking dashboard
- Model performance metrics (latency, quality scores)

---

## Testing Data

### Mock Data for Unit Tests

```python
# Mock LLMResponse
MOCK_RESPONSE = LLMResponse(
    content="This is mock feedback...",
    model="mock-model",
    input_tokens=100,
    output_tokens=50,
    provider="mock"
)

# Mock TokenUsage
MOCK_TOKEN_USAGE = TokenUsage(
    agent_name="recruiter",
    model="gemini-3.0-flash",
    input_tokens=500,
    output_tokens=300,
    total_tokens=800,
    estimated_cost_usd=0.0024
)

# Mock RevisionInstruction
MOCK_INSTRUCTION = RevisionInstruction(
    command_type="FIX",
    target="Project A description",
    description="Incomplete sentence ending",
    suggested_fix="Add period at end of sentence",
    severity="medium",
    agent_source="copywriter"
)
```

### Test Resume with Known Issues

```markdown
---
title: Test Resume
author: Test User
date: 2026-01-09
---

# 職務経歴書

## プロジェクト経験

### Project A (2015-2016)
- Used Next.js 14 for frontend development  # Anachronistic!
- Technologies: Django + Flask  # Incompatible combination!
- 開発を担  # Incomplete sentence!

### Project B (2024-2025)
- Used Next.js 14 for frontend development
- Technologies: Django
- 開発を担当しました。

### Project A (2024-2025)  # Duplicate!
- Used React for frontend
```

**Expected Detections**:
- Technical Writer: Anachronistic tech (Next.js 14 in 2015)
- Technical Writer: Incompatible stack (Django + Flask)
- Technical Writer: Duplicate project (Project A appears twice)
- Copywriter: Incomplete sentence ("開発を担")

---

## Summary

This data model provides:
- **Abstraction**: Unified LLMResponse across providers
- **Configuration**: ModelConfiguration for agent-to-model mapping
- **Tracking**: TokenUsage for cost validation
- **Instructions**: RevisionInstruction for structured feedback
- **Validation**: Clear rules for API keys, tokens, YAML preservation

All entities are designed for **testability**, **type safety**, and **minimal state complexity**.
