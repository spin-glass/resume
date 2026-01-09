"""Model configuration for multi-provider LLM support.

This module defines agent-to-model mappings, pricing information, and helper
functions for cost calculation in the multi-model hybrid configuration.
"""

from enum import Enum


class AgentName(Enum):
    """Agent role identifiers for model assignment."""

    RECRUITER = "recruiter"
    TECHNICAL_WRITER = "technical_writer"
    COPYWRITER = "copywriter"
    UX_DESIGNER = "ux_designer"
    VISUAL_DESIGNER = "visual_designer"
    REVISOR = "revisor"


# Agent-to-model mapping for optimal cost and quality
# Reference: specs/003-multi-model-hybrid/data-model.md
AGENT_MODEL_MAP = {
    AgentName.RECRUITER: {
        "provider": "gemini",
        "model_id": "gemini-2.0-flash-exp",
    },
    AgentName.TECHNICAL_WRITER: {
        "provider": "anthropic",  # Changed from openai due to o3-mini availability
        "model_id": "claude-sonnet-4-5-20250929",
    },
    AgentName.COPYWRITER: {
        "provider": "anthropic",
        "model_id": "claude-sonnet-4-5-20250929",
    },
    AgentName.UX_DESIGNER: {
        "provider": "gemini",
        "model_id": "gemini-2.0-flash-exp",
    },
    AgentName.VISUAL_DESIGNER: {
        "provider": "gemini",
        "model_id": "gemini-2.0-flash-exp",
    },
    AgentName.REVISOR: {
        "provider": "gemini",
        "model_id": "gemini-2.0-flash-exp",
    },
}

# Model pricing (USD per 1M tokens)
# Reference: specs/003-multi-model-hybrid/research.md
MODEL_PRICING = {
    "gemini-2.0-flash-exp": {
        "input": 0.0,  # Free during preview
        "output": 0.0,  # Free during preview
    },
    "o3-mini": {
        "input": 1.1,  # $1.10 per 1M input tokens
        "output": 4.4,  # $4.40 per 1M output tokens
    },
    "claude-sonnet-4-5-20250929": {
        "input": 3.0,  # $3.00 per 1M input tokens
        "output": 15.0,  # $15.00 per 1M output tokens
    },
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate API cost in USD for given token usage.

    Args:
        model: Model identifier (e.g., "gemini-3.0-flash")
        input_tokens: Number of input tokens consumed
        output_tokens: Number of output tokens generated

    Returns:
        Estimated cost in USD

    Raises:
        KeyError: If model is not found in MODEL_PRICING
    """
    pricing = MODEL_PRICING[model]
    input_cost = (input_tokens * pricing["input"]) / 1_000_000
    output_cost = (output_tokens * pricing["output"]) / 1_000_000
    return input_cost + output_cost
