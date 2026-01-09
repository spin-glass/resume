"""Application settings and configuration constants."""

import os
from pathlib import Path

# API Configuration
DEFAULT_MODEL = "claude-opus-4-5-20251101"
DEFAULT_MAX_TOKENS = 4000

# Workflow Configuration
DEFAULT_SCORE_THRESHOLD = 8.0
DEFAULT_MAX_ITERATIONS = 3
DEFAULT_TARGET_ROLE = "LLM/Multi-Agent Engineer"

# Validation Configuration
DEFAULT_MAX_VALIDATION_RETRIES = 3
DEFAULT_STRICT_VALIDATION = False

# Rate Limits (for future use)
MAX_REQUESTS_PER_MINUTE = 60
MAX_TOKENS_PER_MINUTE = 100000

# File Paths
def get_output_dir() -> Path:
    """Get the default output directory for review sessions."""
    return Path(os.environ.get("RESUME_REVIEW_OUTPUT_DIR", "."))


def get_api_key() -> str:
    """Get Anthropic API key from environment."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")
    return api_key
