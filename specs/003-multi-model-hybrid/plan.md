# Implementation Plan: Multi-Model Hybrid Configuration

**Branch**: `003-multi-model-hybrid` | **Date**: 2026-01-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-multi-model-hybrid/spec.md`

## Summary

Implement multi-provider LLM support (Gemini, OpenAI, Anthropic) with role-based optimal model assignment to achieve 50% cost reduction ($1.00 → $0.50), 70% speed improvement (10 min → 2-3 min), and 100% elimination of fuzzy replacement errors through full-rewrite architecture.

**Technical Approach**:
- Create `BaseLLMClient` abstraction layer with provider-specific implementations
- Configure agent-to-model mapping: Recruiter→Gemini Flash, Technical Writer→o3-mini, Copywriter→Claude Sonnet, Designers/Revisor→Gemini Flash
- Replace fuzzy string matching in RevisionService with full-file rewrite using Gemini's long-context capabilities
- Add CLI options for 3 API keys with `--model` override for testing
- Log token usage per agent for cost validation

## Technical Context

**Language/Version**: Python 3.13 (existing, LangGraph compatible)
**Primary Dependencies**:
- Existing: `anthropic>=0.25.0`, `langgraph>=1.0.0`, `click>=8.1.0`
- New: `google-genai[aiohttp]>=1.0.0`, `openai>=1.0.0`

**Storage**: In-memory state (LangGraph StateGraph), filesystem for resume files
**Testing**: pytest with async support (`pytest-asyncio`)
**Target Platform**: macOS/Linux CLI tool (existing)
**Project Type**: Single Python package (monorepo package `packages/resume-review`)

**Performance Goals**:
- Review execution time ≤ 3 minutes (SC-001)
- API cost ≤ $0.55 per review (SC-002)

**Constraints**:
- Must maintain backward compatibility with existing CLI
- Must preserve YAML frontmatter exactly (SC-006)
- Zero tolerance for revision errors (SC-003)

**Scale/Scope**:
- 6 agents (Recruiter, Technical Writer, Copywriter, 2 Designers, Revisor)
- 3 LLM providers (Gemini, OpenAI, Anthropic)
- ~500 new lines of code, ~100 lines modified

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Single Source of Truth
**Status**: ✅ **PASS** - Not applicable (no resume content changes)

**Reasoning**: Feature modifies evaluation/revision system, not resume source files. `resume/resume-ja.qmd` remains sole source.

---

### II. Automated Generation
**Status**: ✅ **PASS** - Not applicable (no build pipeline changes)

**Reasoning**: Feature enhances AI review process but doesn't change Quarto build pipeline (QMD→PDF/HTML/MDX).

---

### III. Preview-First Workflow
**Status**: ✅ **PASS** - Compatible with existing workflow

**Reasoning**: Feature improves quality of generated revisions, making preview step even more valuable. No changes to preview commands.

---

### IV. Deployment Simplicity
**Status**: ✅ **PASS** - No deployment changes

**Reasoning**: Feature is CLI tool enhancement, not web deployment change. Vercel auto-deploy unaffected.

---

### V. Toolchain Consistency
**Status**: ✅ **PASS** - Adds new optional toolchain components

**Reasoning**:
- Adds optional API keys for Gemini/OpenAI (users can still use Claude-only mode)
- No changes to Quarto/LaTeX/font requirements
- New Python dependencies documented in `pyproject.toml`

**Documentation Updates Required**:
- README: Add Gemini/OpenAI API key setup instructions (optional)
- README: Document `--model` override flag for testing

---

### Constitution Compliance Summary

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Single Source of Truth | ✅ PASS | No resume source changes |
| II. Automated Generation | ✅ PASS | No build pipeline changes |
| III. Preview-First | ✅ PASS | Compatible with existing workflow |
| IV. Deployment Simplicity | ✅ PASS | CLI-only changes |
| V. Toolchain Consistency | ✅ PASS | Adds optional dependencies |

**Gate Result**: ✅ **PROCEED** - No violations, all principles satisfied

---

## Project Structure

### Documentation (this feature)

```text
specs/003-multi-model-hybrid/
├── spec.md                         # Feature specification (P0, P1, P2 user stories)
├── plan.md                         # This file (implementation plan)
├── research.md                     # Phase 0: API research, model names, best practices
├── data-model.md                   # Phase 1: LLMResponse, ModelConfig, TokenUsage entities
├── quickstart.md                   # Phase 1: Developer onboarding guide
├── contracts/                      # Phase 1: Interface contracts
│   └── llm-client-interface.md     # BaseLLMClient contract with 3 implementations
└── tasks.md                        # Phase 2: NOT created by /speckit.plan (see /speckit.tasks)
```

### Source Code (repository root)

**Existing Structure** (no changes):
```text
packages/resume-review/             # Python package root
├── src/
│   ├── agents/                     # Existing agents (MODIFIED)
│   │   ├── base.py                 # BaseAgent (MODIFIED: accept llm_client param)
│   │   ├── recruiter.py            # RecruiterAgent (minimal changes)
│   │   ├── technical_writer.py     # TechnicalWriterAgent (minimal changes)
│   │   ├── copywriter.py           # CopywriterAgent (minimal changes)
│   │   ├── ux_designer.py          # UXDesignerAgent (minimal changes)
│   │   └── visual_designer.py      # VisualDesignerAgent (minimal changes)
│   │
│   ├── models/                     # Existing data models (unchanged)
│   │   ├── feedback.py
│   │   ├── portfolio.py
│   │   └── session.py
│   │
│   ├── workflow/                   # Existing workflow (MODIFIED)
│   │   ├── state.py                # ReviewState (MODIFIED: add API key fields)
│   │   ├── nodes/
│   │   │   ├── supervisor.py       # MODIFIED: construct clients for agents
│   │   │   ├── revisor.py          # MODIFIED: full rewrite logic
│   │   │   ├── aggregator.py       # (unchanged)
│   │   │   └── portfolio.py        # (unchanged)
│   │   ├── graph.py                # (unchanged)
│   │   ├── runner.py               # ReviewWorkflow (MODIFIED: pass API keys to state)
│   │   └── conditions.py           # (unchanged)
│   │
│   ├── services/                   # NEW FILES HERE
│   │   ├── llm_client.py           # NEW: BaseLLMClient + 3 implementations
│   │   ├── llm_factory.py          # NEW: LLMClientFactory
│   │   ├── qmd_parser.py           # (existing, unchanged)
│   │   ├── quarto_validator.py     # (existing, unchanged)
│   │   └── screenshot.py           # (existing, unchanged)
│   │
│   ├── config/                     # Existing config (MODIFIED)
│   │   ├── model_config.py         # NEW: Agent-to-model mappings
│   │   ├── settings.py             # (existing, possibly extended)
│   │   ├── prompts.py              # (existing, possibly extended for Revisor)
│   │   └── weights.py              # (existing, unchanged)
│   │
│   ├── utils/                      # (existing, unchanged)
│   └── cli.py                      # MODIFIED: add --gemini/openai/anthropic-api-key options
│
├── tests/
│   ├── unit/
│   │   ├── services/
│   │   │   ├── test_llm_client.py          # NEW: Test 3 client implementations
│   │   │   └── test_llm_factory.py         # NEW: Test model selection logic
│   │   ├── agents/
│   │   │   └── test_base.py                # MODIFIED: Test with injected clients
│   │   └── workflow/
│   │       └── test_state.py               # MODIFIED: Test new state fields
│   │
│   └── integration/
│       └── test_multi_model.py             # NEW: End-to-end with real APIs
│
├── pyproject.toml                          # MODIFIED: add google-genai, openai deps
└── README.md                               # MODIFIED: document new API keys
```

**Structure Decision**: Monorepo package structure (existing). New code fits cleanly into existing `services/` and `config/` directories. Agents modified via dependency injection (no structural changes).

---

## Complexity Tracking

> **Not applicable** - No constitution violations to justify.

---

## Implementation Phases

### Phase 0: Research ✅ COMPLETE

**Artifact**: `research.md` (generated)

**Key Findings**:
- Gemini uses `google-genai` SDK with `gemini-3.0-flash` model (stable, recommended)
- OpenAI uses `AsyncOpenAI` with `o3-mini` model
- Anthropic already integrated, no changes needed
- Full rewrite eliminates 30-40% fuzzy matching error rate

---

### Phase 1: Design & Contracts ✅ COMPLETE

**Artifacts**:
- `data-model.md`: Entities (LLMResponse, ModelConfiguration, TokenUsage, RevisionInstruction)
- `contracts/llm-client-interface.md`: BaseLLMClient interface with 3 implementations
- `quickstart.md`: Developer onboarding guide

**Key Designs**:
- `BaseLLMClient` abstract base class with `generate_async()` method
- `LLMClientFactory` for model selection (hybrid vs override mode)
- `AGENT_MODEL_MAP` for agent-to-model assignments
- Token usage tracking via `ReviewState.token_usage` dict

---

### Phase 2: Tasks (Next Step)

**Command**: `/speckit.tasks`

**Purpose**: Generate detailed task breakdown for implementation (NOT done by `/speckit.plan`)

---

## File-Level Change Summary

### New Files (Create)

| File | Lines | Purpose |
|------|-------|---------|
| `src/services/llm_client.py` | ~400 | BaseLLMClient + Gemini/OpenAI/Anthropic implementations |
| `src/services/llm_factory.py` | ~150 | LLMClientFactory with model selection logic |
| `src/config/model_config.py` | ~50 | AGENT_MODEL_MAP, MODEL_PRICING constants |
| `tests/unit/services/test_llm_client.py` | ~200 | Unit tests for 3 clients |
| `tests/unit/services/test_llm_factory.py` | ~100 | Unit tests for factory |
| `tests/integration/test_multi_model.py` | ~150 | Integration tests with real APIs |

**Total New**: ~1050 lines

---

### Modified Files (Edit)

| File | Changes | Impact |
|------|---------|--------|
| `src/agents/base.py` | ~20 lines | Change `__init__` to accept `llm_client`, update `evaluate_async` |
| `src/workflow/state.py` | ~10 lines | Add `gemini_api_key`, `openai_api_key`, `anthropic_api_key`, `token_usage` fields |
| `src/workflow/nodes/supervisor.py` | ~30 lines | Construct clients via `LLMClientFactory`, pass to agents |
| `src/workflow/nodes/revisor.py` | ~50 lines | Implement full rewrite logic, YAML validation |
| `src/workflow/runner.py` | ~15 lines | Pass 3 API keys to initial state |
| `src/cli.py` | ~40 lines | Add 3 API key options, `--model` override, verbose output |
| `pyproject.toml` | ~5 lines | Add `google-genai[aiohttp]`, `openai` dependencies |
| `README.md` | ~20 lines | Document new API keys, hybrid mode, override mode |

**Total Modified**: ~190 lines

---

### Deleted Files (Optional Cleanup)

| File | Reason |
|------|--------|
| `src/services/revision.py` | Replaced by full rewrite logic in RevisorAgent |

**Note**: Can be kept initially and marked deprecated, removed in future cleanup.

---

## Critical Implementation Decisions

### Decision 1: Dependency Injection vs Direct Construction

**Chosen**: Dependency injection (pass `llm_client` to agent constructor)

**Rationale**:
- Enables testing with `MockLLMClient`
- Agents don't need provider-specific knowledge
- Factory pattern centralizes model selection logic

**Alternative Rejected**: Agents construct clients directly
- Would require agents to know about providers
- Harder to test (need to mock SDK clients)
- Duplicates model selection logic across 6 agents

---

### Decision 2: Full Rewrite vs Improved Fuzzy Matching

**Chosen**: Full rewrite (Revisor generates complete file)

**Rationale**:
- Eliminates 30-40% error rate completely (SC-003)
- Simpler implementation (remove RevisionService complexity)
- Gemini 2.0 Flash handles 8000 token output efficiently (~$0.024 per rewrite)

**Alternative Rejected**: Improve fuzzy matching with AST parsing
- Still error-prone (markdown structure variability)
- More complex code to maintain
- Doesn't address root cause (string matching fragility)

---

### Decision 3: Static Config vs Dynamic Config

**Chosen**: Static `AGENT_MODEL_MAP` with environment variable override

**Rationale**:
- Simple, no external files or databases
- Easy to test (hardcoded mappings)
- `--model` flag provides flexibility when needed

**Alternative Rejected**: YAML/JSON config file
- Adds file I/O complexity
- Users unlikely to change mappings (optimized based on research)
- Harder to version control (separate config file)

---

### Decision 4: LiteLLM vs Custom Abstraction

**Chosen**: Custom `BaseLLMClient` abstraction

**Rationale**:
- Only 3 providers (LiteLLM overkill for 100+ providers)
- Full control over error handling and token tracking
- No external service dependencies
- ~400 lines of code (manageable)

**Alternative Rejected**: LiteLLM router
- Heavy dependency for simple use case
- Adds complexity (router, load balancing, fallback logic)
- Overkill for sequential agent execution (no load balancing needed)

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Gemini model names change | Medium | High | Use versioned IDs (`gemini-3.0-flash`), add alias support |
| Provider rate limits hit | Medium | Medium | Exponential backoff (tenacity), clear error messages |
| Full rewrite truncates content | Low | High | Validate output length, max_tokens=8000, explicit "no truncation" prompt |
| YAML frontmatter corruption | Low | High | Post-generation validation, use original frontmatter if mismatch |
| Cost exceeds projections | Medium | Low | Log every API call cost, warn if exceeds $0.70 threshold |
| Japanese quality degrades | Medium | Medium | Keep Copywriter on Claude (Japanese specialist), test with real resumes |
| API key management confusion | High | Low | Clear error messages, README documentation, backward compatibility |

---

## Testing Strategy

### Unit Tests (No API Calls)

**Coverage**:
- `test_llm_client.py`: Test `MockLLMClient`, interface compliance
- `test_llm_factory.py`: Test model selection (hybrid vs override)
- `test_base.py`: Test agent with injected client

**Run**:
```bash
pytest tests/unit -v
```

---

### Integration Tests (Real API Calls)

**Coverage**:
- `test_multi_model.py`: Full review with all 3 providers
- Validate SC-001 through SC-009

**Run**:
```bash
pytest tests/integration -v -m integration
```

**Note**: Marked with `@pytest.mark.integration`, skipped by default

---

### End-to-End Validation

**Test Resume**: Create test file with known issues:
- Anachronistic technology (Next.js 14 in 2015)
- Incompatible stack (Django + Flask)
- Incomplete sentences ("開発を担")
- Duplicate projects

**Validation**:
1. Run review: `resume-review review --input test_resume.qmd --save-iterations`
2. Verify SC-001: Time < 3 minutes
3. Verify SC-002: Cost < $0.55 (check logs)
4. Verify SC-003: No "Fuzzy replacement failed" errors
5. Verify SC-004: Technical Writer detects anachronistic tech
6. Verify SC-005: Copywriter fixes incomplete sentences
7. Verify SC-006: YAML frontmatter unchanged

---

## Success Criteria Validation

| ID | Criteria | Measurement | Target | Test Method |
|----|----------|-------------|--------|-------------|
| SC-001 | Execution time | `time` command | ≤ 3 min | End-to-end test |
| SC-002 | API cost | Sum of token_usage logs | ≤ $0.55 | Cost calculation script |
| SC-003 | Revision success | Count errors in 20 runs | 0 errors | Batch test script |
| SC-004 | Technical detection | Inject test inconsistencies | ≥ 90% | Test resume with issues |
| SC-005 | Copywriter corrections | Inject incomplete sentences | 100% | Test resume with issues |
| SC-006 | YAML preservation | Compare pre/post frontmatter | 100% | YAML diff validation |
| SC-007 | Hybrid execution | Check logs for different models | All agents | Verbose output check |
| SC-008 | Override functionality | Run with `--model` flag | All use override | Override test |
| SC-009 | Verbose reporting | Run with `--verbose` | Model assignments visible | Output inspection |

---

## Rollout Plan

### Step 1: Feature Flag (Optional)

Add `--enable-hybrid-models` flag to CLI, default `False` initially.

**Rationale**: Allows users to opt-in while feature stabilizes.

---

### Step 2: Phased Rollout

1. **Week 1**: Test with personal resume (author)
2. **Week 2**: Share with early adopters (document findings)
3. **Week 3**: Make default (remove feature flag)

---

### Step 3: Monitoring

- Log token usage for first 100 reviews
- Track cost distribution across providers
- Monitor for unexpected errors (rate limits, API failures)

---

### Step 4: Documentation Updates

- README: Add "Multi-Model Configuration" section
- Add troubleshooting guide for API key issues
- Document cost optimization benefits

---

## Dependencies & Prerequisites

### Python Packages

**Add to `pyproject.toml`**:
```toml
[project.dependencies]
google-genai = {version = ">=1.0.0", extras = ["aiohttp"]}
openai = ">=1.0.0"
anthropic = ">=0.25.0"  # Already present
```

### API Keys

**Required for Hybrid Mode**:
- `GEMINI_API_KEY` or `GOOGLE_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`

**Required for Override Mode**:
- API key for the provider of `--model`

### Development Environment

- Python 3.13
- pytest with `pytest-asyncio`
- Access to Gemini, OpenAI, Anthropic APIs (free tier OK for testing)

---

## Next Steps

1. ✅ **Phase 0 Complete**: Research documented in `research.md`
2. ✅ **Phase 1 Complete**: Design artifacts created (`data-model.md`, `contracts/`, `quickstart.md`)
3. **Phase 2 Next**: Run `/speckit.tasks` to generate detailed task breakdown
4. **Implementation**: Follow task order from `tasks.md` (after `/speckit.tasks`)
5. **Validation**: Run success criteria tests (SC-001 through SC-009)
6. **Review**: Get user feedback on cost/speed improvements
7. **Merge**: Integrate into main branch after validation

---

## Implementation Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 0: Research | ✅ Complete | research.md |
| Phase 1: Design | ✅ Complete | data-model.md, contracts/, quickstart.md |
| Phase 2: Tasks | 1 hour | tasks.md (run `/speckit.tasks`) |
| Phase 3: LLM Clients | 2 days | llm_client.py, llm_factory.py, model_config.py |
| Phase 4: Agent Integration | 1 day | Modified agents + workflow nodes |
| Phase 5: Full Rewrite | 1 day | New revisor logic |
| Phase 6: CLI & Logging | 1 day | CLI options, token logging |
| Phase 7: Testing | 2 days | Unit + integration tests |
| Phase 8: Validation | 1 day | SC-001 through SC-009 verification |

**Total**: ~9 working days (1.8 weeks)

---

## Maintenance & Future Enhancements

### Maintenance Tasks

- Monitor model deprecations (Gemini, OpenAI, Anthropic)
- Update pricing constants if API costs change
- Test compatibility with new SDK versions

### Future Enhancements (Out of Scope for MVP)

- **Cost tracking dashboard**: Visualize token usage over time
- **Automatic fallback**: Retry with alternative provider if primary fails
- **Model benchmarking**: A/B test different model combinations
- **Streaming responses**: Use `generate_stream_async()` for real-time feedback
- **Custom prompts per provider**: Fine-tune prompts for each model's strengths

---

## Summary

This plan provides a complete blueprint for implementing multi-model hybrid configuration:

- **Architecture**: Dependency-injected `BaseLLMClient` with 3 provider implementations
- **Configuration**: Static agent-to-model mapping with CLI override
- **Reliability**: Full rewrite eliminates fuzzy matching errors
- **Cost**: 50% reduction through optimal model selection
- **Speed**: 70% improvement through faster models
- **Testing**: Comprehensive unit, integration, and end-to-end tests
- **Validation**: 9 measurable success criteria

**Ready for**: Phase 2 task generation (`/speckit.tasks`)

---

## Artifacts Generated

✅ `specs/003-multi-model-hybrid/spec.md` (user scenarios, requirements, success criteria)
✅ `specs/003-multi-model-hybrid/research.md` (API research, model selection, best practices)
✅ `specs/003-multi-model-hybrid/data-model.md` (entities, relationships, validation rules)
✅ `specs/003-multi-model-hybrid/contracts/llm-client-interface.md` (interface contract)
✅ `specs/003-multi-model-hybrid/quickstart.md` (developer onboarding guide)
✅ `specs/003-multi-model-hybrid/plan.md` (this file - implementation plan)

**Next**: Run `/speckit.tasks` to generate `tasks.md` with detailed implementation steps.
