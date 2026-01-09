"""Configuration module for resume review agents."""

from .prompts import get_system_prompt
from .settings import (
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_SCORE_THRESHOLD,
    DEFAULT_TARGET_ROLE,
)
from .weights import AGENT_WEIGHTS, get_agent_weight

__all__ = [
    # Settings
    "DEFAULT_MODEL",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_SCORE_THRESHOLD",
    "DEFAULT_MAX_ITERATIONS",
    "DEFAULT_TARGET_ROLE",
    # Weights
    "AGENT_WEIGHTS",
    "get_agent_weight",
    # Prompts
    "get_system_prompt",
]
