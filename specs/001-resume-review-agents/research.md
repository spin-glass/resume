# Research: AI SDK Selection for Multi-Agent Resume Review System

**Branch**: `001-resume-review-agents` | **Date**: 2026-01-09 | **Related**: [spec.md](./spec.md), [plan.md](./plan.md)

## Executive Summary

**DECISION**: Use **LangGraph** with Anthropic's Claude SDK for the multi-agent resume review system.

**RATIONALE**: LangGraph provides the most robust solution for this use case, combining:
- Production-ready multi-agent orchestration with explicit state management
- Superior structured output support via JSON schema enforcement
- Flexible control flow for iterative review cycles
- Direct integration with Anthropic's Claude API (including Sonnet 4.5)
- Battle-tested enterprise deployments and v1.0 stable release

**CAVEAT**: Python 3.14 compatibility is not yet confirmed for LangGraph (currently supports 3.10-3.13). However, this is a minor concern as:
1. Python 3.14 is not yet released (expected late 2026)
2. LangGraph team announced "Python 3.14 support coming soon" in their November 2025 v1.0 release
3. The project can start on Python 3.13 and upgrade when 3.14 support is available

---

## Decision Matrix

| Framework | Multi-Agent | Structured Output | Python 3.14 | Claude Support | State Management | Verdict |
|-----------|-------------|-------------------|-------------|----------------|------------------|---------|
| **LangGraph** | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐⭐ Excellent | ⚠️ Pending | ⭐⭐⭐⭐⭐ Native | ⭐⭐⭐⭐⭐ Explicit | **RECOMMENDED** |
| **CrewAI** | ⭐⭐⭐⭐ Good | ⭐⭐⭐ Good | ❓ Unknown | ⭐⭐⭐⭐ Good | ⭐⭐⭐ Role-based | Alternative |
| **Anthropic SDK** | ⭐⭐ Manual | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐ Likely | ⭐⭐⭐⭐⭐ Official | ⭐⭐ Manual | Not Recommended |
| **AutoGen/AG2** | ⭐⭐⭐⭐ Good | ⭐⭐⭐ Moderate | ❓ Unknown | ⭐⭐⭐ Good | ⭐⭐⭐ Conversation | Not Recommended |

---

## Detailed Analysis

### 1. LangGraph (RECOMMENDED)

**Overview**: Graph-based multi-agent orchestration framework from the LangChain team, reached v1.0 stable in November 2025.

#### Strengths for This Use Case

**Multi-Agent Orchestration** (⭐⭐⭐⭐⭐)
- Explicit graph-based architecture where each agent is a node with its own state
- Supports hierarchical teams, supervisor control, and collaboration patterns
- Centralized StateGraph maintains overall context and enables parallel execution
- Native streaming support for real-time agent reasoning visibility

**Structured Output Support** (⭐⭐⭐⭐⭐)
- Shared State Schema using TypedDict or Pydantic models
- Strict format enforcement through state graphs
- Superior control over data flow between nodes
- Perfect for score-based review workflows with schema validation

**State Management** (⭐⭐⭐⭐⭐)
- Explicit state schema definition with type safety
- Built-in memory stores conversation histories and maintains context
- Checkpointing for resuming failed workflows
- Human-in-the-loop integration for review approvals

**Claude Integration** (⭐⭐⭐⭐⭐)
- Direct integration with Anthropic's Claude API
- Supports all Claude models including Sonnet 4.5
- Vision capabilities for screenshot analysis (needed for visual design review)
- Native support for structured outputs via Claude's beta feature

**Production Readiness**
- 6.17M monthly downloads (as of 2026)
- Enterprise deployments at LinkedIn, Replit, Elastic, Klarna
- Durable execution with failure recovery
- Comprehensive documentation and active community

#### Weaknesses

**Python 3.14 Compatibility** (⚠️)
- Currently supports Python 3.10-3.13
- Python 3.14 support announced as "coming soon" but not yet implemented
- Open GitHub issue (#5253) tracking Python 3.14 support

**Mitigation**: Start development on Python 3.13 (fully supported), upgrade when 3.14 support lands.

#### Code Example

```python
from langgraph.graph import StateGraph
from typing import TypedDict
from anthropic import Anthropic

# Define state schema
class ReviewState(TypedDict):
    resume_content: str
    recruiter_score: float
    tech_writer_score: float
    copywriter_score: float
    feedback: list[dict]
    iteration: int

# Create state graph
workflow = StateGraph(ReviewState)

# Add agent nodes
workflow.add_node("recruiter", recruiter_agent)
workflow.add_node("tech_writer", tech_writer_agent)
workflow.add_node("copywriter", copywriter_agent)
workflow.add_node("aggregator", score_aggregator)

# Define control flow
workflow.set_entry_point("recruiter")
workflow.add_edge("recruiter", "tech_writer")
workflow.add_edge("tech_writer", "copywriter")
workflow.add_edge("copywriter", "aggregator")
workflow.add_conditional_edges(
    "aggregator",
    should_continue_reviewing,
    {
        "continue": "recruiter",
        "finish": END
    }
)
```

#### Best Practices for This Use Case

1. **Supervisor Pattern**: Use a coordinator agent to manage review cycles and enforce iteration limits
2. **State Schema**: Define strict Pydantic models for feedback structures and scores
3. **Checkpointing**: Enable state persistence for long-running reviews
4. **Command Objects**: Use for agent handoffs with context passing
5. **Conditional Routing**: Implement score-based routing to exit review cycles

#### Resources
- [LangGraph Official Documentation](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangGraph v1.0 Release](https://blog.langchain.com/langchain-langgraph-1dot0/)
- [Multi-Agent Workflows Guide](https://blog.langchain.com/langgraph-multi-agent-workflows/)

---

### 2. CrewAI

**Overview**: Lightweight, team-based multi-agent framework built from scratch, independent of LangChain.

#### Strengths

**Multi-Agent Coordination** (⭐⭐⭐⭐)
- Role-playing agents with specialized goals
- Built-in task delegation based on agent capabilities
- Optimized for team-based coordination patterns
- 100,000+ certified developers

**Performance** (⭐⭐⭐⭐⭐)
- Built from scratch for speed and minimal resource usage
- No dependency on LangChain or other heavy frameworks
- Faster execution compared to LangGraph

**Structured Output** (⭐⭐⭐)
- Supports JSON and Pydantic models for task outputs
- Role-based output structure
- Good for predictable workflows

**Vision Support** (⭐⭐⭐⭐)
- Built-in multimodal support via `multimodal=True` agent configuration
- Simpler than manual vision model integration

#### Weaknesses

**State Management** (⭐⭐⭐)
- Less explicit than LangGraph's state graphs
- Role-based rather than schema-enforced
- Not ideal for complex, iterative workflows with strict schemas

**Structured Output** (⭐⭐⭐)
- Less strict than LangGraph's state schema approach
- Output aligned with agent responsibilities rather than enforced schemas

**Python 3.14 Compatibility** (❓)
- No information found about Python version requirements or roadmap
- Likely supports recent Python versions but unconfirmed

#### Use Case Fit

CrewAI is better suited for:
- Simpler, linear multi-agent workflows
- Team-based coordination without complex state requirements
- Production systems prioritizing speed over control

For this resume review use case, the need for **strict structured output schemas**, **iterative review cycles**, and **score-based routing** makes LangGraph a better fit.

#### Resources
- [CrewAI Official Documentation](https://docs.crewai.com/en/introduction)
- [CrewAI Framework 2025 Review](https://latenode.com/blog/ai-frameworks-technical-infrastructure/crewai-framework/crewai-framework-2025-complete-review-of-the-open-source-multi-agent-ai-platform)

---

### 3. Anthropic SDK (Direct)

**Overview**: Official Python SDK for Claude API with new Agent SDK for building agentic workflows.

#### Strengths

**Claude Integration** (⭐⭐⭐⭐⭐)
- Official SDK from Anthropic
- First-class support for all Claude features
- Structured outputs with guaranteed JSON schema compliance
- Vision capabilities for image analysis

**Structured Output** (⭐⭐⭐⭐⭐)
- Beta feature: `anthropic-beta: structured-outputs-2025-11-13`
- Compiles JSON schema into grammar, actively restricts token generation
- Pydantic support via `.parse()` method
- Zero parsing errors guaranteed

**Python 3.14 Compatibility** (⭐⭐⭐⭐)
- Currently requires Python 3.9+
- Tested on Python 3.9-3.13
- Likely to support 3.14 when released (official SDK gets priority updates)

**Performance** (⭐⭐⭐⭐⭐)
- In-process MCP servers for custom tools
- No subprocess management overhead
- Better performance than external MCP

#### Weaknesses

**Multi-Agent Orchestration** (⭐⭐)
- No built-in multi-agent framework
- Requires manual implementation of agent coordination
- State management is manual
- No graph-based workflow support

**State Management** (⭐⭐)
- Must implement custom state tracking
- No built-in checkpointing or persistence
- Context passing requires manual design

#### Use Case Fit

The Anthropic SDK alone is **not recommended** for this use case because:
- **No multi-agent orchestration**: Would require building custom coordinator logic
- **Manual state management**: Need to implement score aggregation, iteration tracking, and context passing from scratch
- **No workflow control flow**: Would need custom routing logic for iterative reviews

However, the SDK is excellent for **individual agent implementations** within LangGraph or CrewAI.

#### Best Practice

**Recommended Approach**: Use Anthropic SDK **within LangGraph** for individual agent calls:

```python
from anthropic import Anthropic
from langgraph.graph import StateGraph

client = Anthropic()

async def recruiter_agent(state: ReviewState):
    response = client.messages.create(
        model="claude-sonnet-4.5-20241022",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": f"Review this resume: {state['resume_content']}"
        }],
        # Use structured outputs for guaranteed schema compliance
        response_format={
            "type": "json_schema",
            "json_schema": RecruiterFeedbackSchema
        }
    )
    return {"recruiter_feedback": response.parsed}
```

#### Resources
- [Anthropic SDK Python GitHub](https://github.com/anthropics/anthropic-sdk-python)
- [Structured Outputs Documentation](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python)
- [Building Agents with Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)

---

### 4. AutoGen / Microsoft Agent Framework

**Overview**: Microsoft's framework for multi-agent AI applications, transitioning to Microsoft Agent Framework (GA Q1 2026).

#### Strengths

**Multi-Agent Patterns** (⭐⭐⭐⭐)
- Event-driven programming framework
- Supports single-agent, multi-agent, and hierarchical patterns
- Graph-based workflows with data flows

**Enterprise Features** (⭐⭐⭐⭐)
- Microsoft backing and enterprise support
- Thread-based state management
- Telemetry and monitoring
- Cross-language support (.NET and Python)

#### Weaknesses

**Transition Period** (⚠️)
- AutoGen is being deprecated in favor of Microsoft Agent Framework
- Agent Framework is in public preview, GA scheduled for Q1 2026
- Migration path exists but adds complexity
- Community fork (AG2) continues original AutoGen

**Structured Output** (⭐⭐⭐)
- Conversation-driven outputs are less consistent
- Not as strict as LangGraph's state schema approach

**Python 3.14 Compatibility** (❓)
- No information found about version requirements

**Vision Support** (⭐⭐⭐)
- Requires manual integration of vision models (e.g., LLaVA)
- More complex than CrewAI's built-in support

#### Use Case Fit

AutoGen/Agent Framework is better suited for:
- .NET + Python cross-language environments
- Enterprise deployments with Microsoft ecosystem integration
- Open-ended problem-solving and iterative workflows

For this resume review use case, the **transition period uncertainty** and **less strict structured output** make it a poor choice compared to LangGraph's stable v1.0 release.

#### Resources
- [Microsoft Agent Framework Documentation](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview)
- [AutoGen to Agent Framework Migration Guide](https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/)
- [AG2 Community Fork](https://github.com/ag2ai/ag2)

---

## Key Capabilities Mapping

### Requirement Coverage Analysis

| Requirement | LangGraph | CrewAI | Anthropic SDK | AutoGen |
|-------------|-----------|--------|---------------|---------|
| **Python 3.14+** | ⚠️ 3.10-3.13 (3.14 pending) | ❓ Unknown | ⭐ 3.9+ (likely 3.14) | ❓ Unknown |
| **Claude Sonnet 4.5** | ✅ Full support | ✅ Full support | ✅ Official SDK | ✅ Supported |
| **Multi-agent orchestration** | ✅ Graph-based | ✅ Team-based | ❌ Manual | ✅ Event-driven |
| **Structured JSON schemas** | ✅ Pydantic + StateGraph | ⚠️ Pydantic (less strict) | ✅ Native feature | ⚠️ Moderate |
| **Context passing** | ✅ Shared state | ✅ Role-based | ❌ Manual | ✅ Thread-based |
| **Screenshot analysis** | ✅ Vision via Claude | ✅ Multimodal support | ✅ Vision API | ⚠️ Manual integration |
| **Iterative cycles** | ✅ Conditional routing | ⚠️ Less flexible | ❌ Manual | ✅ Supported |
| **Score aggregation** | ✅ State schema | ⚠️ Role outputs | ❌ Manual | ⚠️ Conversation-based |
| **Production readiness** | ✅ v1.0, 6.17M DL | ✅ 100K+ devs | ✅ Official SDK | ⚠️ In transition |

---

## Specific Feature Support

### 1. Multi-Agent Orchestration

**LangGraph**: ⭐⭐⭐⭐⭐
- Supervisor pattern for coordinator agent
- Hierarchical teams for specialized review agents
- Collaboration pattern with shared scratchpad
- Command objects for agent handoffs

**CrewAI**: ⭐⭐⭐⭐
- Role-playing agents (Recruiter, TechWriter, Copywriter)
- Task delegation based on agent capabilities
- Teams and flows for structured workflows

**Anthropic SDK**: ⭐⭐
- Manual implementation required
- Subagent support in Agent SDK
- No built-in coordination

**AutoGen**: ⭐⭐⭐⭐
- Multi-agent patterns supported
- Graph-based workflows
- Transition uncertainty

**Winner**: **LangGraph** - Most flexible and explicit control

---

### 2. Structured Output (JSON Schemas)

**LangGraph**: ⭐⭐⭐⭐⭐
- Shared State Schema with TypedDict/Pydantic
- Strict format enforcement
- Perfect for feedback structures:

```python
class FeedbackItem(BaseModel):
    category: Literal["content", "structure", "keywords", "portfolio"]
    severity: Literal["high", "medium", "low"]
    message: str
    suggestion: str

class ReviewFeedback(BaseModel):
    agent_role: str
    score: float  # 0.0-10.0
    feedback: list[FeedbackItem]
    portfolio_suggestions: list[PortfolioProject] | None
```

**CrewAI**: ⭐⭐⭐
- JSON and Pydantic support
- Role-aligned outputs
- Less strict enforcement

**Anthropic SDK**: ⭐⭐⭐⭐⭐
- Guaranteed schema compliance
- Native structured outputs feature
- Best for individual agent responses

**AutoGen**: ⭐⭐⭐
- Conversation-driven, less consistent

**Winner**: **LangGraph + Anthropic SDK** (combined) - LangGraph for workflow state, Anthropic SDK for agent responses

---

### 3. Context Passing Between Agents

**LangGraph**: ⭐⭐⭐⭐⭐
- Shared state mechanism for real-time updates
- InjectedState for tools to access state
- Command objects for agent routing with context

Example:
```python
# Agent 1 updates state
return {
    "recruiter_score": 7.5,
    "recruiter_feedback": feedback_list
}

# Agent 2 accesses shared state
def tech_writer_agent(state: ReviewState):
    # Has access to recruiter_score and recruiter_feedback
    previous_feedback = state["recruiter_feedback"]
```

**CrewAI**: ⭐⭐⭐
- Shared context within crews
- Role-based state management

**Anthropic SDK**: ⭐⭐
- Manual context tracking required

**AutoGen**: ⭐⭐⭐
- Thread-based state management

**Winner**: **LangGraph** - Explicit, type-safe shared state

---

### 4. Screenshot/Image Analysis

**LangGraph**: ⭐⭐⭐⭐⭐
- Full Claude vision API support
- Can pass images in state

```python
def visual_designer_agent(state: ReviewState):
    response = client.messages.create(
        model="claude-sonnet-4.5-20241022",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": state["screenshot_base64"]
                    }
                },
                {
                    "type": "text",
                    "text": "Review this resume's visual design"
                }
            ]
        }]
    )
```

**CrewAI**: ⭐⭐⭐⭐
- Built-in multimodal support
- `multimodal=True` in agent config

**Anthropic SDK**: ⭐⭐⭐⭐⭐
- Native vision capabilities
- Supports base64, URLs, and Files API

**AutoGen**: ⭐⭐⭐
- Requires manual vision model integration

**Winner**: **LangGraph + Anthropic SDK** (combined) or **CrewAI** (simpler setup)

---

### 5. Iterative Review Cycles

**Requirement**: Review content, get feedback, revise, re-review until score ≥ 8.0 (max 3 iterations)

**LangGraph**: ⭐⭐⭐⭐⭐
```python
workflow.add_conditional_edges(
    "aggregator",
    should_continue_reviewing,
    {
        "continue": "revisor",
        "finish": END
    }
)

def should_continue_reviewing(state: ReviewState):
    avg_score = (
        state["recruiter_score"] +
        state["tech_writer_score"] +
        state["copywriter_score"]
    ) / 3

    if avg_score >= 8.0 or state["iteration"] >= 3:
        return "finish"
    return "continue"
```

**CrewAI**: ⭐⭐⭐
- Flows support iteration
- Less flexible than LangGraph's conditional routing

**Anthropic SDK**: ⭐⭐
- Manual loop implementation required

**AutoGen**: ⭐⭐⭐
- Event-driven loops supported

**Winner**: **LangGraph** - Explicit conditional routing with state-based decisions

---

## Implementation Recommendations

### Recommended Architecture: LangGraph + Anthropic SDK

```python
# File: agents/src/workflow.py

from langgraph.graph import StateGraph, END
from anthropic import Anthropic
from typing import TypedDict
from pydantic import BaseModel

# State schema
class ReviewState(TypedDict):
    resume_qmd: str
    recruiter_score: float
    tech_writer_score: float
    copywriter_score: float
    ux_designer_score: float | None
    visual_designer_score: float | None
    all_feedback: list[dict]
    iteration: int
    screenshot_base64: str | None
    revised_qmd: str | None

# Individual agents using Anthropic SDK
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

async def recruiter_agent(state: ReviewState):
    response = client.messages.create(
        model="claude-sonnet-4.5-20241022",
        max_tokens=4096,
        temperature=0.0,
        system="You are a recruiter specializing in 100万円+ LLM/AI engineer positions...",
        messages=[{
            "role": "user",
            "content": f"Review this resume:\n\n{state['resume_qmd']}"
        }],
        # Use structured outputs
        response_format={
            "type": "json_schema",
            "json_schema": RecruiterFeedbackSchema
        }
    )

    feedback = response.parsed
    return {
        "recruiter_score": feedback["score"],
        "all_feedback": state["all_feedback"] + [feedback]
    }

# Build workflow graph
workflow = StateGraph(ReviewState)

workflow.add_node("recruiter", recruiter_agent)
workflow.add_node("tech_writer", tech_writer_agent)
workflow.add_node("copywriter", copywriter_agent)
workflow.add_node("aggregator", score_aggregator)
workflow.add_node("revisor", content_revisor)

workflow.set_entry_point("recruiter")
workflow.add_edge("recruiter", "tech_writer")
workflow.add_edge("tech_writer", "copywriter")
workflow.add_edge("copywriter", "aggregator")
workflow.add_conditional_edges(
    "aggregator",
    should_continue,
    {
        "revise": "revisor",
        "design_review": "ux_designer",
        "finish": END
    }
)
workflow.add_edge("revisor", "recruiter")

app = workflow.compile()
```

### Key Implementation Decisions

1. **Framework**: LangGraph for multi-agent orchestration
2. **Model Client**: Anthropic SDK for Claude API calls
3. **State Schema**: Pydantic models for type safety
4. **Structured Outputs**: Use Anthropic's native feature for agent responses
5. **Vision Analysis**: Claude vision API for screenshot review
6. **Iteration Control**: Conditional edges based on scores and iteration count
7. **Python Version**: Start with 3.13, upgrade to 3.14 when LangGraph support lands

### Dependencies

```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.13"  # Upgrade to ^3.14 when LangGraph supports it
langgraph = "^0.2.0"  # v1.0 stable release
anthropic = "^0.40.0"  # Latest SDK with structured outputs
pydantic = "^2.0.0"
playwright = "^1.40.0"  # For screenshot capture
```

---

## Risk Assessment

### Python 3.14 Compatibility Risk

**Risk Level**: 🟡 Low-Medium

**Issue**: LangGraph currently supports Python 3.10-3.13, not 3.14

**Mitigation Strategies**:

1. **Start with Python 3.13** (fully supported)
   - Develop and test on Python 3.13
   - Upgrade to 3.14 when support lands

2. **Monitor LangGraph releases**
   - GitHub issue #5253 tracks Python 3.14 support
   - LangGraph team announced support is "coming soon"
   - Likely available by Q2 2026

3. **Fallback Plan**
   - If Python 3.14 is hard requirement and LangGraph support is delayed:
     - Option A: Use Python 3.13 temporarily (no functional impact)
     - Option B: Switch to CrewAI (Python version requirements TBD)
     - Option C: Use Anthropic SDK directly with custom orchestration (high effort)

**Recommendation**: Accept the risk. Python 3.13 is fully capable, and 3.14 support will arrive before it becomes critical.

---

## Alternative Considered: CrewAI

### When to Use CrewAI Instead

Choose CrewAI over LangGraph if:

1. **Performance is critical**: CrewAI is faster due to minimal dependencies
2. **Simpler workflows**: Linear, team-based coordination without complex state schemas
3. **Faster development**: Role-based patterns are quicker to set up
4. **Python 3.14 is required immediately**: (Pending confirmation of CrewAI's version support)

### Why LangGraph is Still Better for This Use Case

1. **Iterative workflows**: Resume review requires multiple cycles with score-based routing
2. **Strict schemas**: Feedback structures must be consistent and validated
3. **Complex state**: Need to track scores, feedback, iterations, screenshots across agents
4. **Production readiness**: v1.0 stable release with enterprise backing

---

## Conclusion

### Final Recommendation

**Use LangGraph with Anthropic SDK** for the resume review multi-agent system:

1. **LangGraph** provides robust multi-agent orchestration with explicit state management
2. **Anthropic SDK** delivers guaranteed structured outputs and vision capabilities
3. **Combined approach** leverages strengths of both: workflow control from LangGraph, API quality from Anthropic
4. **Python 3.13** is sufficient for development; upgrade to 3.14 when support arrives

### Implementation Path

1. **Phase 1**: Build core workflow on Python 3.13 + LangGraph + Anthropic SDK
2. **Phase 2**: Implement content review agents (recruiter, tech_writer, copywriter)
3. **Phase 3**: Add visual review agents (ux_designer, visual_designer) with screenshot analysis
4. **Phase 4**: Upgrade to Python 3.14 when LangGraph support is available

### Success Criteria

- ✅ Multi-agent coordination with score aggregation
- ✅ Structured JSON feedback with Pydantic validation
- ✅ Iterative review cycles with configurable thresholds
- ✅ Screenshot analysis for visual design review
- ✅ Context passing between agents via shared state
- ✅ Production-ready with error handling and checkpointing

---

## Sources

### LangGraph
- [LangGraph Official Documentation](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangGraph v1.0 Release Announcement](https://blog.langchain.com/langchain-langgraph-1dot0/)
- [LangGraph Multi-Agent Workflows](https://blog.langchain.com/langgraph-multi-agent-workflows/)
- [LangGraph Python 3.13 Compatibility](https://changelog.langchain.com/announcements/langgraph-is-now-compatible-with-python-3-13)
- [LangGraph Python 3.14 Support Issue](https://github.com/langchain-ai/langgraph/issues/5253)
- [Top 5 Open-Source Agentic Frameworks in 2026](https://research.aimultiple.com/agentic-frameworks/)
- [LangGraph Multi-Agent Orchestration Guide](https://latenode.com/blog/ai-frameworks-technical-infrastructure/langgraph-multi-agent-orchestration/langgraph-multi-agent-orchestration-complete-framework-guide-architecture-analysis-2025)

### Anthropic Claude SDK
- [Structured Outputs - Claude Docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- [Anthropic SDK Python GitHub](https://github.com/anthropics/anthropic-sdk-python)
- [Claude API Structured Output Guide](https://thomas-wiegold.com/blog/claude-api-structured-output/)
- [Zero-Error JSON with Claude](https://medium.com/@meshuggah22/zero-error-json-with-claude-how-anthropics-structured-outputs-actually-work-in-real-code-789cde7aff13)
- [Vision - Claude Docs](https://docs.claude.com/en/docs/build-with-claude/vision)
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python)
- [Building Agents with Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)

### CrewAI
- [CrewAI Introduction](https://docs.crewai.com/en/introduction)
- [CrewAI GitHub Repository](https://github.com/crewAIInc/crewAI)
- [CrewAI Framework 2025 Review](https://latenode.com/blog/ai-frameworks-technical-infrastructure/crewai-framework/crewai-framework-2025-complete-review-of-the-open-source-multi-agent-ai-platform)
- [What is CrewAI? | IBM](https://www.ibm.com/think/topics/crew-ai)
- [Agent Orchestration 2026: LangGraph, CrewAI & AutoGen Guide](https://iterathon.tech/blog/ai-agent-orchestration-frameworks-2026)

### AutoGen / Microsoft Agent Framework
- [AutoGen Official Documentation](https://microsoft.github.io/autogen/stable//index.html)
- [Microsoft Agent Framework Overview](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview)
- [AutoGen to Microsoft Agent Framework Migration](https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/)
- [AG2 (Community Fork)](https://github.com/ag2ai/ag2)

### Framework Comparisons
- [CrewAI vs LangGraph vs AutoGen | DataCamp](https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen)
- [LangGraph vs CrewAI - ZenML Blog](https://www.zenml.io/blog/langgraph-vs-crewai)
- [Technical Comparison of AutoGen, CrewAI, LangGraph, and OpenAI Swarm](https://ai.plainenglish.io/technical-comparison-of-autogen-crewai-langgraph-and-openai-swarm-1e4e9571d725)
- [First Hand Comparison of LangGraph, CrewAI and AutoGen](https://aaronyuqi.medium.com/first-hand-comparison-of-langgraph-crewai-and-autogen-30026e60b563)
- [LangGraph vs CrewAI: Comparison Guide for Production Agents](https://xcelore.com/blog/langgraph-vs-crewai/)

### State Management & Context Passing
- [LangGraph State Management Guide](https://medium.com/@jayhardikar/state-management-of-ai-agents-in-langgraph-45f9975f2af2)
- [Understanding State in LangGraph](https://medium.com/@gitmaxd/understanding-state-in-langgraph-a-comprehensive-guide-191462220997)
- [LangGraph State Machines for Production](https://dev.to/jamesli/langgraph-state-machines-managing-complex-agent-task-flows-in-production-36f4)
- [Graph API Overview - LangChain Docs](https://docs.langchain.com/oss/python/langgraph/graph-api)
