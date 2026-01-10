# Node Contracts: StateGraph Agent Node Separation

**Feature**: 011-stategraph-node-separation
**Date**: 2026-01-09

This directory contains API contracts for all node functions in the refactored workflow.

---

## Contract Index

1. **[router_node.md](./router_node.md)** - Fan-out coordinator (stateless)
2. **Agent Nodes** (all follow same pattern):
   - **recruiter_node** - Recruiter agent evaluation
   - **tech_writer_node** - Technical writer agent evaluation
   - **copywriter_node** - Copywriter agent evaluation
3. **[aggregator_node.md](./aggregator_node.md)** - Fan-in collector (modified)
4. **[graph_edges.md](./graph_edges.md)** - Graph structure and edge definitions

---

## Agent Node Pattern (Recruiter, Tech Writer, Copywriter)

All three agent nodes follow this identical contract pattern:

### Signature

```python
async def <agent>_node(state: ReviewState) -> dict[str, Any]:
    """Execute <agent> agent evaluation and store result."""
```

### Input State Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `resume` | `Resume` | ✅ | Resume to evaluate |
| `target_role` | `str` | ✅ | Target role (e.g., "LLM Engineer") |
| `gemini_api_key` | `Optional[str]` | ❌ | Gemini API key |
| `openai_api_key` | `Optional[str]` | ❌ | OpenAI API key |
| `anthropic_api_key` | `Optional[str]` | ❌ | Anthropic/Claude API key |
| `override_model` | `Optional[str]` | ❌ | Model override for testing |

### Output

Returns partial state update with agent-specific feedback field:

```python
# recruiter_node
{"recruiter_feedback": Feedback(...)}

# tech_writer_node
{"tech_writer_feedback": Feedback(...)}

# copywriter_node
{"copywriter_feedback": Feedback(...)}
```

### Behavior

1. **Start timer**: `start_time = time.perf_counter()`
2. **Log start**: `logger.info("Starting <agent> node")`
3. **Create LLM client**: Using `LLMClientFactory` with agent-specific model
4. **Initialize agent**: `agent = <Agent>Agent(llm_client=client)`
5. **Evaluate**: `feedback = await agent.evaluate_async(resume, target_role)`
6. **Log success**: Score and duration
7. **Return feedback**: In agent-specific state field

### Error Handling

On exception, return minimal feedback with neutral score:

```python
except Exception as e:
    logger.error(f"Error in <agent> node: {e}")
    return {
        "<agent>_feedback": Feedback(
            agent_name="<agent>",
            score=5.0,  # Neutral score
            strengths=["Evaluation failed"],
            issues=[],
            suggestions=[f"Error: {str(e)}"],
        )
    }
```

**Rationale**: Allows workflow to continue with degraded feedback rather than cascading failure.

### Logging

```python
logger.info("Starting <agent> node")
logger.debug(f"<Agent> score: {feedback.score}/10.0")
logger.info(f"<Agent> node completed in {duration:.2f}s")

# On error
logger.error(f"Error in <agent> node after {duration:.2f}s: {exception}")
```

### Performance

- **Expected duration**: 10-30s per agent (LLM API call)
- **Parallelism**: All three agents run concurrently
- **Total latency**: max(recruiter, tech_writer, copywriter), not sum

---

## Agent-Specific Differences

| Agent | Model (Default) | AgentName Enum | State Field | Agent Class |
|-------|----------------|----------------|-------------|-------------|
| Recruiter | Gemini 3 Flash | `AgentName.RECRUITER` | `recruiter_feedback` | `RecruiterAgent` |
| Tech Writer | o3-mini / GPT-4o | `AgentName.TECHNICAL_WRITER` | `tech_writer_feedback` | `TechnicalWriterAgent` |
| Copywriter | Claude Sonnet 4.5 | `AgentName.COPYWRITER` | `copywriter_feedback` | `CopywriterAgent` |

See `packages/resume-review/src/config/model_config.py` for full model mapping.

---

## Implementation Template

```python
import logging
import time
from typing import Any

from ...agents.<agent> import <Agent>Agent
from ...config.model_config import AgentName
from ...models.feedback import Feedback
from ...services.llm_factory import LLMClientFactory
from ..state import ReviewState

logger = logging.getLogger("resume_review")


async def <agent>_node(state: ReviewState) -> dict[str, Any]:
    """
    <Agent> agent node for evaluating resume.

    Args:
        state: Workflow state with resume and configuration

    Returns:
        Partial state update with <agent>_feedback field
    """
    start_time = time.perf_counter()
    logger.info("Starting <agent> node")

    try:
        # Extract required fields
        resume = state["resume"]
        target_role = state["target_role"]

        # Create LLM client for this agent
        client = LLMClientFactory.create_client(
            agent_name=AgentName.<AGENT>,
            gemini_api_key=state.get("gemini_api_key"),
            openai_api_key=state.get("openai_api_key"),
            anthropic_api_key=state.get("anthropic_api_key"),
            override_model=state.get("override_model"),
        )

        # Initialize agent with client
        agent = <Agent>Agent(llm_client=client)

        # Evaluate resume
        feedback = await agent.evaluate_async(resume, target_role)

        # Log success
        duration = time.perf_counter() - start_time
        logger.debug(f"<Agent> score: {feedback.score}/10.0")
        logger.info(f"<Agent> node completed in {duration:.2f}s")

        return {"<agent>_feedback": feedback}

    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.error(f"Error in <agent> node after {duration:.2f}s: {e}")

        # Return minimal feedback to allow workflow to continue
        return {
            "<agent>_feedback": Feedback(
                agent_name="<agent>",
                score=5.0,
                strengths=["Evaluation failed"],
                issues=[],
                suggestions=[f"Error: {str(e)}"],
            )
        }
```

**File Locations**:
- `packages/resume-review/src/workflow/nodes/recruiter.py`
- `packages/resume-review/src/workflow/nodes/tech_writer.py`
- `packages/resume-review/src/workflow/nodes/copywriter.py`

---

## Testing Agent Nodes

### Unit Test Template

```python
import pytest
from unittest.mock import AsyncMock, Mock

@pytest.mark.asyncio
async def test_<agent>_node_success():
    """<Agent> node returns feedback on success."""
    # Setup
    state = {
        "resume": mock_resume,
        "target_role": "Engineer",
        "anthropic_api_key": "test-key",
    }
    mock_feedback = Feedback(agent_name="<agent>", score=8.5, ...)

    # Mock factory and agent
    with patch("...LLMClientFactory.create_client") as mock_factory:
        mock_client = Mock()
        mock_factory.return_value = mock_client

        with patch("...<Agent>Agent") as mock_agent_class:
            mock_agent = Mock()
            mock_agent.evaluate_async = AsyncMock(return_value=mock_feedback)
            mock_agent_class.return_value = mock_agent

            # Execute
            result = await <agent>_node(state)

            # Assert
            assert "<agent>_feedback" in result
            assert result["<agent>_feedback"].score == 8.5


@pytest.mark.asyncio
async def test_<agent>_node_handles_exception():
    """<Agent> node returns minimal feedback on exception."""
    state = {"resume": mock_resume, "target_role": "Engineer"}

    with patch("...LLMClientFactory.create_client") as mock_factory:
        mock_factory.side_effect = Exception("API timeout")

        # Execute
        result = await <agent>_node(state)

        # Assert graceful degradation
        assert "<agent>_feedback" in result
        assert result["<agent>_feedback"].score == 5.0
        assert "Error: API timeout" in result["<agent>_feedback"].suggestions
```

---

## Related Documentation

- [data-model.md](../data-model.md): State schema with new feedback fields
- [research.md](../research.md): Research findings on LangGraph patterns
- [plan.md](../plan.md): Full implementation plan

---

## Contract Change History

| Date | Change | Files Affected |
|------|--------|----------------|
| 2026-01-09 | Initial contracts | All |

---

## Approval

**Status**: Design phase - awaiting implementation
**Reviewers**: TBD
**Approved**: Pending
